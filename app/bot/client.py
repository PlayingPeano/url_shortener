import os

import httpx


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


class ApiClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    async def create_link(self, original_url: str) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/links",
                json={"original_url": original_url},
            )
            response.raise_for_status()
            return response.json()

    async def get_link(self, link_id: int) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/links/{link_id}")
            response.raise_for_status()
            return response.json()

    async def delete_link(self, link_id: int) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(f"{self.base_url}/links/{link_id}")
            response.raise_for_status()
