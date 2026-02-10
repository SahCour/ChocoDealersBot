"""
Square API Integration
Sync inventory, sales, and products with Square POS
"""

from square.client import Client
from loguru import logger
from typing import Dict, List, Optional
from datetime import datetime

from config.config import settings
from database.db import get_db
from database.models import (
    Product, InventoryProduct, Sale, SquareSyncLog,
    SyncType, SyncStatus, SaleSource
)
from sqlalchemy import select


class SquareIntegration:
    """Handle all Square API operations"""

    def __init__(self):
        """Initialize Square client"""
        self.client = Client(
            access_token=settings.square_access_token,
            environment=settings.square_environment
        )
        self.location_id = settings.square_location_id
        logger.info(f"Square API initialized (env: {settings.square_environment})")

    async def sync_inventory(self) -> Dict:
        """
        Sync inventory from database to Square POS
        Updates Square inventory counts based on database values
        """
        logger.info("Starting inventory sync to Square...")

        async with get_db() as db:
            # Create sync log
            sync_log = SquareSyncLog(
                sync_type=SyncType.INVENTORY,
                sync_status=SyncStatus.IN_PROGRESS
            )
            db.add(sync_log)
            await db.commit()

            try:
                # Get all products with inventory
                stmt = select(Product, InventoryProduct).join(InventoryProduct).where(
                    Product.is_active == True,
                    Product.square_item_id.isnot(None)
                )
                result = await db.execute(stmt)
                products = result.all()

                synced_count = 0

                for product, inventory in products:
                    try:
                        # Update Square inventory
                        result = self.client.inventory.batch_change_inventory(
                            body={
                                "idempotency_key": f"inv-{product.id}-{datetime.now().timestamp()}",
                                "changes": [
                                    {
                                        "type": "PHYSICAL_COUNT",
                                        "physical_count": {
                                            "catalog_object_id": product.square_item_id,
                                            "location_id": self.location_id,
                                            "quantity": str(inventory.quantity),
                                            "occurred_at": datetime.utcnow().isoformat()
                                        }
                                    }
                                ]
                            }
                        )

                        if result.is_success():
                            synced_count += 1
                            logger.debug(f"Synced inventory for {product.sku}")
                        else:
                            logger.error(f"Failed to sync {product.sku}: {result.errors}")

                    except Exception as e:
                        logger.error(f"Error syncing {product.sku}: {e}")

                # Update sync log
                sync_log.sync_status = SyncStatus.SUCCESS
                sync_log.completed_at = datetime.now()
                sync_log.records_synced = synced_count
                await db.commit()

                logger.success(f"Inventory sync completed. Synced {synced_count} products.")

                return {
                    "success": True,
                    "synced": synced_count,
                    "total": len(products)
                }

            except Exception as e:
                # Update sync log with error
                sync_log.sync_status = SyncStatus.FAILED
                sync_log.error_message = str(e)
                sync_log.completed_at = datetime.now()
                await db.commit()

                logger.error(f"Inventory sync failed: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }

    async def sync_sales_from_square(self) -> Dict:
        """
        Import sales from Square POS to database
        Fetches recent transactions and creates Sale records
        """
        logger.info("Importing sales from Square...")

        try:
            # Get orders from Square
            result = self.client.orders.search_orders(
                body={
                    "location_ids": [self.location_id],
                    "query": {
                        "filter": {
                            "state_filter": {
                                "states": ["COMPLETED"]
                            },
                            "date_time_filter": {
                                "created_at": {
                                    "start_at": (datetime.now() - timedelta(days=7)).isoformat()
                                }
                            }
                        }
                    }
                }
            )

            if not result.is_success():
                logger.error(f"Failed to fetch orders: {result.errors}")
                return {"success": False, "error": result.errors}

            orders = result.body.get("orders", [])
            imported_count = 0

            async with get_db() as db:
                for order in orders:
                    try:
                        # Process each line item
                        for line_item in order.get("line_items", []):
                            catalog_id = line_item.get("catalog_object_id")

                            # Find product by Square ID
                            stmt = select(Product).where(Product.square_item_id == catalog_id)
                            result = await db.execute(stmt)
                            product = result.scalar_one_or_none()

                            if not product:
                                logger.warning(f"Product not found for catalog ID {catalog_id}")
                                continue

                            # Check if sale already imported
                            stmt_check = select(Sale).where(
                                Sale.square_transaction_id == order.get("id")
                            )
                            existing = await db.execute(stmt_check)
                            if existing.scalar_one_or_none():
                                continue  # Already imported

                            # Create sale record
                            quantity = int(line_item.get("quantity", 1))
                            total_money = line_item.get("total_money", {})
                            amount = float(total_money.get("amount", 0)) / 100  # Convert from cents

                            sale = Sale(
                                product_id=product.id,
                                quantity=quantity,
                                unit_price_thb=amount / quantity if quantity > 0 else 0,
                                final_price_thb=amount,
                                source=SaleSource.SQUARE_POS,
                                square_transaction_id=order.get("id")
                            )
                            db.add(sale)

                            # Update inventory
                            stmt_inv = select(InventoryProduct).where(
                                InventoryProduct.product_id == product.id
                            )
                            inv_result = await db.execute(stmt_inv)
                            inventory = inv_result.scalar_one_or_none()

                            if inventory:
                                inventory.quantity = max(0, inventory.quantity - quantity)

                            imported_count += 1

                await db.commit()

            logger.success(f"Imported {imported_count} sales from Square")
            return {"success": True, "imported": imported_count}

        except Exception as e:
            logger.error(f"Failed to import sales: {e}")
            return {"success": False, "error": str(e)}

    async def create_square_item(self, product: Product) -> Optional[str]:
        """
        Create a new item in Square catalog for a product
        Returns the Square catalog object ID if successful
        """
        try:
            result = self.client.catalog.upsert_catalog_object(
                body={
                    "idempotency_key": f"item-{product.id}",
                    "object": {
                        "type": "ITEM",
                        "id": f"#{product.sku}",
                        "item_data": {
                            "name": product.name,
                            "description": product.notes or "",
                            "category_id": "#CHOCOLATE",
                            "variations": [
                                {
                                    "type": "ITEM_VARIATION",
                                    "id": f"#{product.sku}-VAR",
                                    "item_variation_data": {
                                        "name": "Regular",
                                        "pricing_type": "FIXED_PRICING",
                                        "price_money": {
                                            "amount": int(product.retail_price_thb * 100),
                                            "currency": "THB"
                                        },
                                        "sku": product.sku
                                    }
                                }
                            ]
                        }
                    }
                }
            )

            if result.is_success():
                catalog_object = result.body["catalog_object"]
                square_id = catalog_object["id"]
                logger.info(f"Created Square item for {product.sku}: {square_id}")
                return square_id
            else:
                logger.error(f"Failed to create Square item: {result.errors}")
                return None

        except Exception as e:
            logger.error(f"Error creating Square item: {e}")
            return None


# Export singleton instance
square_integration = SquareIntegration()
