# services/glm_client.py
import os
import httpx
from dotenv import load_dotenv 

load_dotenv()

# os.getenv reads the VARIABLE NAME from .env
ZGLM_API_KEY = os.getenv("ZGLM_API_KEY")   # ← variable name
ZGLM_API_URL = os.getenv("ZGLM_API_URL")   # ← variable name

async def call_glm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0,
    max_tokens: int = 1000
) -> str:
    
    print("API URL:", ZGLM_API_URL)
    print("API KEY:", "LOADED" if ZGLM_API_KEY else "MISSING")

    headers = {
        "Authorization": f"Bearer {ZGLM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "glm-5.1",
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            ZGLM_API_URL, 
            json=payload, 
            headers=headers
        )

        print("STATUS:", response.status_code)
        print("RAW RESPONSE:", response.text)

        response.raise_for_status()
        data = response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            print("PARSED JSON:", data)
            raise
    