# services/coupon_service.py
import os
import aiohttp
from typing import Dict

class CouponService:
    def __init__(self):
        self.api_key = os.getenv('COUPON_API_KEY')
        self.api_url = os.getenv('COUPON_API_URL')

    async def generate_coupon(self, value: int) -> str:
        """クーポンコードを生成"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/generate",
                json={"value": value},
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                data = await response.json()
                return data["coupon_code"]

    async def verify_coupon(self, code: str) -> bool:
        """クーポンコードを検証"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/verify/{code}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                return response.status == 200