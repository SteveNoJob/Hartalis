from sqlalchemy.orm import Session
from models.inventory import InventoryResult, InventorySummary, ChatMessage
from services.glm_client import glm_client

CHAT_SYSTEM_PROMPT = """
You are an inventory optimization assistant for a retail business.
You have access to the user's inventory analysis results and data summary.
Help the user understand their inventory situation, answer questions about specific SKUs,
and provide actionable recommendations.

Rules:
- Only use data provided in the context below
- Be concise and direct
- Always reference specific SKUs and numbers when answering
- If asked something outside the inventory data, say you don't have that information
"""


def build_data_context(user_id: int, db: Session) -> str:
    results = db.query(InventoryResult).filter_by(user_id=user_id).order_by(InventoryResult.created_at.desc()).all()
    summary = db.query(InventorySummary).filter_by(user_id=user_id).order_by(InventorySummary.created_at.desc()).all()

    if not results:
        return "No inventory data found for this user."

    lines = ["=== INVENTORY ANALYSIS RESULTS ==="]
    for r in results:
        lines.append(
            f"SKU {r.sku}: status={r.status}, reorder={r.reorder}, "
            f"reorder_qty={r.reorder_qty}, recommendations={r.recommendations}"
        )

    lines.append("\n=== DATA SUMMARY ===")
    for s in summary:
        lines.append(
            f"SKU {s.sku}: avg_daily_sales={s.avg_daily_sales:.2f}, "
            f"stock_level={s.stock_level:.2f}, forecast={s.forecast:.2f}, "
            f"lead_time={s.lead_time_days} days, supplier={s.supplier_name}"
        )

    return "\n".join(lines)


async def chat_with_inventory(user_id: int, user_message: str, db: Session) -> str:
    # load chat history for this user
    history = (
        db.query(ChatMessage)
        .filter_by(user_id=user_id)
        .order_by(ChatMessage.id)
        .all()
    )

    # build data context from stored results
    data_context = build_data_context(user_id, db)

    # build full messages array
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT + "\n\n" + data_context}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})

    # call GLM with full history
    response = await glm_client.call_with_history(messages)

    # persist both turns to DB
    db.add(ChatMessage(user_id=user_id, role="user",      content=user_message))
    db.add(ChatMessage(user_id=user_id, role="assistant", content=response))
    db.commit()

    return response