"""
Google Notebook LM Integration
AI-powered analytics and insights using Google AI
"""

from loguru import logger
from typing import Dict, Optional
import google.generativeai as genai

from config.config import settings
from database.db import get_db
from database.models import Sale, Product
from sqlalchemy import select, func
from datetime import datetime, timedelta


class NotebookLMIntegration:
    """
    Integration with Google AI (Gemini) for business insights
    Note: Google Notebook LM doesn't have a public API yet,
    so we use Gemini API for similar functionality
    """

    def __init__(self):
        """Initialize Google AI client"""
        if settings.google_ai_api_key:
            genai.configure(api_key=settings.google_ai_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Google AI (Gemini) initialized for analytics")
        else:
            logger.warning("Google AI API key not configured")
            self.model = None

    async def generate_sales_insights(self, days: int = 30) -> Optional[str]:
        """
        Generate AI-powered insights about sales performance
        """
        if not self.model:
            return None

        try:
            async with get_db() as db:
                # Get sales data for the period
                since_date = datetime.now() - timedelta(days=days)

                stmt = select(
                    Product.name,
                    func.count(Sale.id).label('sales_count'),
                    func.sum(Sale.quantity).label('total_quantity'),
                    func.sum(Sale.final_price_thb).label('total_revenue')
                ).join(Product).where(
                    Sale.created_at >= since_date
                ).group_by(Product.name).order_by(
                    func.sum(Sale.final_price_thb).desc()
                )

                result = await db.execute(stmt)
                sales_data = result.all()

                if not sales_data:
                    return "Недостаточно данных для анализа"

                # Prepare data summary for AI
                data_summary = f"Анализ продаж за последние {days} дней:\n\n"
                data_summary += "Топ-5 товаров по выручке:\n"

                for i, row in enumerate(sales_data[:5], 1):
                    data_summary += f"{i}. {row.name}: {row.total_revenue}฿ ({row.total_quantity} шт, {row.sales_count} продаж)\n"

                # Generate insights using AI
                prompt = f"""
Ты аналитик для шоколадной компании Chocodealers на острове Панган в Таиланде.
Проанализируй следующие данные о продажах и дай краткие (3-5 пунктов) инсайты и рекомендации:

{data_summary}

Дай конкретные рекомендации по:
1. Какие товары продвигать активнее
2. Что может быть причиной успеха/неуспеха
3. Предложения по оптимизации ассортимента
"""

                response = self.model.generate_content(prompt)
                return response.text

        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return None

    async def analyze_inventory_optimization(self) -> Optional[str]:
        """
        AI analysis of inventory levels and recommendations
        """
        if not self.model:
            return None

        try:
            async with get_db() as db:
                # Get low stock items
                from database.models import InventoryProduct

                stmt = select(Product, InventoryProduct).join(InventoryProduct).where(
                    InventoryProduct.quantity < InventoryProduct.min_stock_level
                )

                result = await db.execute(stmt)
                low_stock = result.all()

                if not low_stock:
                    return "Все товары в достаточном количестве"

                summary = "Товары с низкими остатками:\n"
                for product, inv in low_stock[:10]:
                    summary += f"- {product.name}: {inv.quantity}/{inv.min_stock_level} шт\n"

                prompt = f"""
Ты логист для шоколадной компании. Проанализируй ситуацию с остатками и дай рекомендации:

{summary}

Предложи:
1. Приоритет докупки товаров
2. Оптимальные уровни запасов
3. Стратегию предотвращения дефицита
"""

                response = self.model.generate_content(prompt)
                return response.text

        except Exception as e:
            logger.error(f"Failed to analyze inventory: {e}")
            return None

    async def get_business_summary(self) -> Optional[str]:
        """
        Get comprehensive business summary and insights
        """
        if not self.model:
            return None

        sales_insights = await self.generate_sales_insights(days=7)
        inventory_insights = await self.analyze_inventory_optimization()

        summary = "📊 **БИЗНЕС-АНАЛИТИКА**\n\n"

        if sales_insights:
            summary += "**Анализ продаж:**\n"
            summary += sales_insights + "\n\n"

        if inventory_insights:
            summary += "**Анализ инвентаря:**\n"
            summary += inventory_insights

        return summary


# Export singleton instance
notebook_integration = NotebookLMIntegration()
