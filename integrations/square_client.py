import logging
import asyncio

logger = logging.getLogger(__name__)

# ПЕРЕКЛЮЧАТЕЛЬ: True = Тест без ключей, False = Боевой режим
USE_MOCK = True


class SquareClient:
    def __init__(self):
        self.is_mock = USE_MOCK

    async def get_inventory(self, product_name: str) -> int:
        """Узнать остаток товара (Mock)"""
        if self.is_mock:
            # Имитация данных Square
            mock_db = {"Eskimo Coconut": 10, "Truffle Classic": 5}
            return mock_db.get(product_name, 0)
        return 0

    async def update_inventory(self, product_name: str, quantity: int):
        """Изменить остаток в Square (Mock)"""
        if self.is_mock:
            logger.info(f"✅ [MOCK SQUARE] Inventory update: {product_name} += {quantity}")
            return True
        return False

    async def get_sales_today(self) -> float:
        """Получить сумму продаж за сегодня (Mock)"""
        if self.is_mock:
            return 4000.0  # Square думает, что продали на 4000
        return 0.0


# Глобальный экземпляр
square_client = SquareClient()
