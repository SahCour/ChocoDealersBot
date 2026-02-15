import logging
import asyncio

logger = logging.getLogger(__name__)

# SWITCH: True = Mock mode (no real keys), False = Live mode
USE_MOCK = True


class SquareClient:
    def __init__(self):
        self.is_mock = USE_MOCK

    async def get_inventory(self, product_name: str) -> int:
        """Get product stock level (Mock)"""
        if self.is_mock:
            mock_db = {"Eskimo Coconut": 10, "Truffle Classic": 5}
            return mock_db.get(product_name, 0)
        return 0

    async def update_inventory(self, product_name: str, quantity: int):
        """Update stock in Square (Mock)"""
        if self.is_mock:
            logger.info(f"✅ [MOCK SQUARE] Inventory update: {product_name} += {quantity}")
            return True
        return False

    async def get_sales_today(self) -> float:
        """Get total sales amount for today (Mock)"""
        if self.is_mock:
            return 4000.0
        return 0.0

    async def get_total_expected_cash(self) -> float:
        """Get expected cash in drawer based on Square sales (Mock)"""
        if self.is_mock:
            return 4000.0  # Mock: Square expects 4000 THB in drawer
        return 0.0


# Global instance
square_client = SquareClient()
