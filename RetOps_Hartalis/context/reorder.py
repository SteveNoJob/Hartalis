# Prepares structured reorder context for Feq's GLM prompt
# Does NOT call GLM — outputs a string Feq injects into the reorder prompt

from typing import List, Dict, Optional


def build_reorder_context(
    forecast: List[Dict],
    inventory: Optional[List[Dict]] = None,
    budget: Optional[float] = None
) -> str:
    """
    Takes forecast output (from CS/Feq) and optionally inventory data,
    returns a structured plain English string for GLM reorder prompt.

    forecast format (from GLM forecast output):
        [{"product_name": "Milo", "weekly_total": 22.0, "confidence": "high"}, ...]

    inventory format (optional, only if user uploaded inventory data):
        [{"product_name": "Milo", "current_stock": 8, "unit_cost": 8.50}, ...]

    budget: float or None — RM budget for this restock cycle
    """
    if not forecast:
        return "No forecast data available to generate reorder recommendations."

    # Build inventory lookup for fast access
    inventory_map = {}
    if inventory:
        for item in inventory:
            name = item.get("product_name", "").lower().strip()
            inventory_map[name] = item

    lines = []

    # --- Section 1: Demand vs Stock Gap Analysis ---
    lines.append("REORDER ANALYSIS:")
    lines.append(f"Analysing {len(forecast)} products based on 7-day demand forecast.\n")

    high_priority = []
    medium_priority = []
    low_priority = []

    for product in forecast:
        name = product.get("product_name", "Unknown")
        weekly_demand = product.get("weekly_total", 0)
        confidence = product.get("confidence", "medium")

        # Check if we have inventory data for this product
        inv = inventory_map.get(name.lower().strip())
        current_stock = inv.get("current_stock", None) if inv else None
        unit_cost = inv.get("unit_cost", None) if inv else None

        if current_stock is not None:
            stock_days = (current_stock / weekly_demand * 7) if weekly_demand > 0 else 999
            shortage = max(0, weekly_demand - current_stock)

            product_info = {
                "name": name,
                "weekly_demand": round(weekly_demand, 1),
                "current_stock": current_stock,
                "stock_days_remaining": round(stock_days, 1),
                "units_to_reorder": round(shortage * 1.15, 0),  # 15% buffer
                "unit_cost": unit_cost,
                "confidence": confidence,
            }

            if stock_days < 3:
                high_priority.append(product_info)
            elif stock_days < 6:
                medium_priority.append(product_info)
            else:
                low_priority.append(product_info)

        else:
            # No inventory data — recommend based on forecast alone
            suggested_order = round(weekly_demand * 1.2, 0)  # 20% buffer
            medium_priority.append({
                "name": name,
                "weekly_demand": round(weekly_demand, 1),
                "current_stock": "unknown",
                "stock_days_remaining": "unknown",
                "units_to_reorder": suggested_order,
                "unit_cost": None,
                "confidence": confidence,
            })

    # Format priority sections
    if high_priority:
        lines.append("🔴 HIGH PRIORITY — Stock critically low, reorder immediately:")
        for p in high_priority:
            line = _format_product_line(p)
            lines.append(f"  {line}")
        lines.append("")

    if medium_priority:
        lines.append("🟡 MEDIUM PRIORITY — Stock sufficient for now but reorder this week:")
        for p in medium_priority:
            line = _format_product_line(p)
            lines.append(f"  {line}")
        lines.append("")

    if low_priority:
        lines.append("🟢 LOW PRIORITY — Well stocked, no immediate action needed:")
        for p in low_priority:
            lines.append(f"  - {p['name']}: {p['stock_days_remaining']} days of stock remaining")
        lines.append("")

    # --- Section 2: Budget Summary (only if budget provided AND cost data exists) ---
    if budget and budget > 0:
        lines.append(_build_budget_summary(high_priority + medium_priority, budget))

    return "\n".join(lines)


def _format_product_line(p: Dict) -> str:
    """Formats a single product into a readable recommendation line."""
    name = p["name"]
    demand = p["weekly_demand"]
    stock = p["current_stock"]
    reorder = p["units_to_reorder"]
    days = p["stock_days_remaining"]
    cost = p["unit_cost"]
    confidence = p["confidence"]

    line = f"- {name}: forecast demand {demand} units/week"

    if stock != "unknown":
        line += f", current stock {stock} units ({days} days remaining)"
    else:
        line += " (current stock unknown — using forecast only)"

    line += f", recommended reorder: {int(reorder)} units"

    if cost:
        total = reorder * cost
        line += f" (≈ RM{total:.2f} at RM{cost:.2f}/unit)"

    line += f" [forecast confidence: {confidence}]"
    return line


def _build_budget_summary(priority_items: List[Dict], budget: float) -> str:
    """
    Greedy budget allocation — highest priority items first.
    Returns a plain English budget breakdown string.
    """
    lines = [f"BUDGET ALLOCATION SUMMARY (Available: RM{budget:.2f}):"]

    items_with_cost = [p for p in priority_items if p.get("unit_cost")]
    items_without_cost = [p for p in priority_items if not p.get("unit_cost")]

    remaining = budget
    allocated = []
    deferred = []

    for item in items_with_cost:
        total_cost = item["units_to_reorder"] * item["unit_cost"]
        if total_cost <= remaining:
            allocated.append({**item, "total_cost": total_cost})
            remaining -= total_cost
        else:
            # Partial purchase
            affordable = int(remaining / item["unit_cost"])
            if affordable > 0:
                allocated.append({
                    **item,
                    "units_to_reorder": affordable,
                    "total_cost": affordable * item["unit_cost"],
                    "partial": True
                })
                remaining -= affordable * item["unit_cost"]
            else:
                deferred.append(item)

    if allocated:
        lines.append("Items to purchase within budget:")
        for a in allocated:
            suffix = " (partial — buy more next restock)" if a.get("partial") else ""
            lines.append(
                f"  - {a['name']}: {int(a['units_to_reorder'])} units "
                f"= RM{a['total_cost']:.2f}{suffix}"
            )

    lines.append(f"Remaining budget after allocation: RM{remaining:.2f}")

    if deferred:
        lines.append("Cannot afford this week (defer to next restock):")
        for d in deferred:
            lines.append(
                f"  - {d['name']}: needs RM{d['units_to_reorder'] * d['unit_cost']:.2f}"
            )

    if items_without_cost:
        lines.append(
            "Note: The following items have no unit cost data — "
            "budget impact cannot be calculated: "
            + ", ".join(p["name"] for p in items_without_cost)
        )

    return "\n".join(lines)