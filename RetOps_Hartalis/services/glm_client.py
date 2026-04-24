import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class GLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or os.getenv("ZGLM_API_KEY")
        self.api_url = api_url or os.getenv("ZGLM_API_URL")
        self.model   = model  or os.getenv("ZGLM_MODEL", "ilmu-glm-5.1")

        if not self.api_key or not self.api_url:
            raise EnvironmentError("Missing ZGLM_API_KEY or ZGLM_API_URL.")

        self._client = httpx.AsyncClient(
            timeout=120.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 5000,
    ) -> str:
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        response = await self._client.post(self.api_url, json=payload)
        response.raise_for_status()

        data = response.json()
        print("[GLM RAW RESPONSE]", data)
        
        if not data.get("success", True) or "choices" not in data:
            raise ValueError(f"GLM API error: {data.get('msg', data)}")

        return data["choices"][0]["message"]["content"]

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.close()


glm_client = GLMClient()