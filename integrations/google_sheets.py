"""
Google Sheets Integration
Bidirectional sync with Google Sheets for reporting and data management
"""

import gspread
from google.oauth2.service_account import Credentials
from loguru import logger
from typing import Dict, List
from datetime import datetime
import asyncio
from functools import partial

from config.config import settings
from database.db import get_db
from database.models import (
    Product, Ingredient, Sale, Production, Purchase,
    InventoryProduct, InventoryIngredient, SheetsSyncLog,
    SyncStatus
)
from sqlalchemy import select


class GoogleSheetsIntegration:
    """Handle all Google Sheets operations"""

    def __init__(self):
        """Initialize Google Sheets client"""
        try:
            self.scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            self.creds = Credentials.from_service_account_file(
                settings.google_credentials_file,
                scopes=self.scopes
            )

            self.client = gspread.authorize(self.creds)
            self.spreadsheet = self.client.open_by_key(settings.google_sheet_id)

            logger.info("Google Sheets API initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            raise

    async def sync_all(self) -> Dict:
        """Sync all data to Google Sheets"""
        logger.info("Starting full sync to Google Sheets...")

        results = {
            "inventory": await self.sync_inventory_to_sheets(),
            "sales": await self.sync_sales_to_sheets(),
            "production": await self.sync_production_to_sheets(),
            "purchases": await self.sync_purchases_to_sheets()
        }

        sheets_updated = sum(1 for r in results.values() if r.get("success"))

        logger.success(f"Full sync completed. Updated {sheets_updated} sheets.")

        return {
            "success": True,
            "sheets_updated": sheets_updated,
            "details": results
        }

    async def sync_inventory_to_sheets(self) -> Dict:
        """Export current inventory to Google Sheets"""
        try:
            async with get_db() as db:
                # Get all products with inventory
                stmt = select(Product, InventoryProduct).join(InventoryProduct)
                result = await db.execute(stmt)
                products = result.all()

                # Prepare data
                headers = [
                    "SKU", "Name", "Category", "Quantity", "Min Stock",
                    "Retail Price", "COGS", "Margin %", "Last Updated"
                ]

                rows = [headers]

                for product, inventory in products:
                    margin = ((product.retail_price_thb - product.cogs_thb) / product.retail_price_thb * 100)
                    rows.append([
                        product.sku,
                        product.name,
                        product.category.value,
                        inventory.quantity,
                        inventory.min_stock_level,
                        f"{product.retail_price_thb:.2f}",
                        f"{product.cogs_thb:.2f}",
                        f"{margin:.1f}%",
                        datetime.now().strftime("%Y-%m-%d %H:%M")
                    ])

                # Write to sheet
                await self._write_to_sheet(settings.sheet_name_inventory, rows)

                logger.info(f"Synced {len(products)} products to Inventory sheet")
                return {"success": True, "records": len(products)}

        except Exception as e:
            logger.error(f"Failed to sync inventory: {e}")
            return {"success": False, "error": str(e)}

    async def sync_sales_to_sheets(self) -> Dict:
        """Export sales records to Google Sheets"""
        try:
            async with get_db() as db:
                # Get recent sales (last 30 days)
                from datetime import timedelta
                since_date = datetime.now() - timedelta(days=30)

                stmt = select(Sale).join(Product).where(
                    Sale.created_at >= since_date
                ).order_by(Sale.created_at.desc())

                result = await db.execute(stmt)
                sales = result.scalars().all()

                # Prepare data
                headers = [
                    "Date", "Time", "SKU", "Product", "Quantity",
                    "Unit Price", "Total", "Payment Method", "Source"
                ]

                rows = [headers]

                for sale in sales:
                    product = await db.get(Product, sale.product_id)
                    rows.append([
                        sale.created_at.strftime("%Y-%m-%d"),
                        sale.created_at.strftime("%H:%M:%S"),
                        product.sku if product else "N/A",
                        product.name if product else "Unknown",
                        sale.quantity,
                        f"{sale.unit_price_thb:.2f}",
                        f"{sale.final_price_thb:.2f}",
                        sale.payment_method.value if sale.payment_method else "N/A",
                        sale.source.value
                    ])

                await self._write_to_sheet(settings.sheet_name_sales, rows)

                logger.info(f"Synced {len(sales)} sales to Sales sheet")
                return {"success": True, "records": len(sales)}

        except Exception as e:
            logger.error(f"Failed to sync sales: {e}")
            return {"success": False, "error": str(e)}

    async def sync_production_to_sheets(self) -> Dict:
        """Export production records to Google Sheets"""
        try:
            async with get_db() as db:
                stmt = select(Production).order_by(Production.production_date.desc()).limit(100)
                result = await db.execute(stmt)
                productions = result.scalars().all()

                headers = [
                    "Date", "Batch #", "Product", "Quantity", "Status",
                    "Material Cost", "Labor Cost", "Total Cost"
                ]

                rows = [headers]

                for prod in productions:
                    product = await db.get(Product, prod.product_id)
                    rows.append([
                        prod.production_date.strftime("%Y-%m-%d"),
                        prod.batch_number or "N/A",
                        product.name if product else "Unknown",
                        prod.quantity_produced,
                        prod.status.value,
                        f"{prod.cost_materials_thb:.2f}" if prod.cost_materials_thb else "N/A",
                        f"{prod.cost_labor_thb:.2f}" if prod.cost_labor_thb else "N/A",
                        f"{prod.total_cost_thb:.2f}" if prod.total_cost_thb else "N/A"
                    ])

                await self._write_to_sheet(settings.sheet_name_production, rows)

                return {"success": True, "records": len(productions)}

        except Exception as e:
            logger.error(f"Failed to sync production: {e}")
            return {"success": False, "error": str(e)}

    async def sync_purchases_to_sheets(self) -> Dict:
        """Export purchase records to Google Sheets"""
        try:
            async with get_db() as db:
                stmt = select(Purchase).order_by(Purchase.purchase_date.desc()).limit(100)
                result = await db.execute(stmt)
                purchases = result.scalars().all()

                headers = [
                    "Date", "Ingredient", "Quantity (kg)", "Unit Price",
                    "Total", "Supplier", "Status"
                ]

                rows = [headers]

                for purchase in purchases:
                    ingredient = await db.get(Ingredient, purchase.ingredient_id)
                    rows.append([
                        purchase.purchase_date.strftime("%Y-%m-%d"),
                        ingredient.name if ingredient else "Unknown",
                        f"{purchase.quantity_kg:.2f}",
                        f"{purchase.unit_price_thb:.2f}",
                        f"{purchase.quantity_kg * purchase.unit_price_thb:.2f}",
                        purchase.supplier or "N/A",
                        purchase.status.value
                    ])

                await self._write_to_sheet(settings.sheet_name_purchases, rows)

                return {"success": True, "records": len(purchases)}

        except Exception as e:
            logger.error(f"Failed to sync purchases: {e}")
            return {"success": False, "error": str(e)}

    async def _write_to_sheet(self, sheet_name: str, data: List[List]):
        """Write data to a specific sheet (create if doesn't exist)"""
        loop = asyncio.get_event_loop()

        def _sync_write():
            try:
                # Try to get existing sheet
                try:
                    worksheet = self.spreadsheet.worksheet(sheet_name)
                except gspread.exceptions.WorksheetNotFound:
                    # Create new sheet
                    worksheet = self.spreadsheet.add_worksheet(
                        title=sheet_name,
                        rows=len(data) + 100,
                        cols=len(data[0]) if data else 10
                    )

                # Clear and update
                worksheet.clear()
                worksheet.update('A1', data)

                # Format header row
                worksheet.format('A1:Z1', {
                    "backgroundColor": {"red": 0.2, "green": 0.5, "blue": 0.8},
                    "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
                })

                return True

            except Exception as e:
                logger.error(f"Error writing to sheet {sheet_name}: {e}")
                raise

        # Run synchronous gspread code in executor
        await loop.run_in_executor(None, _sync_write)

    async def sync_from_sheets(self) -> Dict:
        """
        Import data from Google Sheets to database
        Allows manual updates in sheets to propagate to database
        """
        # TODO: Implement bidirectional sync
        logger.warning("Sync from Sheets not yet implemented")
        return {"success": False, "message": "Not implemented"}


# Export singleton instance
sheets_integration = GoogleSheetsIntegration()
