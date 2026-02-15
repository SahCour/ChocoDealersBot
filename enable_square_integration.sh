#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "🔌 Wiring up Square API..."

# 1. ADD HTTPX TO REQUIREMENTS (Required for real API calls)
if ! grep -q "httpx" requirements.txt; then
    echo "httpx>=0.27.0" >> requirements.txt
    echo "✅ Added httpx to requirements.txt"
else
    echo "ℹ️  httpx already present in requirements.txt"
fi

# 2. UPDATE SQUARE CLIENT (Hybrid: auto-detects token in env)
cat > integrations/square_client.py << 'PYEOF'
import logging
import httpx
from datetime import datetime, timezone
from config.config import settings

logger = logging.getLogger(__name__)


class SquareClient:
    def __init__(self):
        # Auto-detect mode based on Token presence
        self.token = settings.square_access_token
        self.location_id = settings.square_location_id

        if self.token and self.location_id:
            self.is_mock = False
            self.base_url = "https://connect.squareup.com/v2"
            self.headers = {
                "Square-Version": "2023-12-13",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            logger.info("🟢 Square Client: REAL API MODE ENABLED")
        else:
            self.is_mock = True
            logger.warning("🟡 Square Client: MOCK MODE (No tokens found in env)")

    async def get_total_expected_cash(self) -> float:
        """
        Calculates total CASH sales for the current day.
        Uses real Square Payments API or returns mock value.
        """
        if self.is_mock:
            return 4000.0

        try:
            # Define time range: start of today in UTC
            now = datetime.now(timezone.utc)
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/payments",
                    headers=self.headers,
                    params={
                        "location_id": self.location_id,
                        "begin_time": start_of_day,
                        "sort_order": "DESC"
                    }
                )

                if response.status_code != 200:
                    logger.error(f"Square API Error: {response.text}")
                    return 0.0

                payments = response.json().get("payments", [])

                # Sum only COMPLETED CASH payments
                total_cents = 0
                count = 0
                for p in payments:
                    if (p.get("source_type") == "CASH" and
                            p.get("status") == "COMPLETED"):
                        total_cents += int(p.get("amount_money", {}).get("amount", 0))
                        count += 1

                total_thb = total_cents / 100.0
                logger.info(f"💰 Square API: {count} cash payments = {total_thb} THB")
                return total_thb

        except Exception as e:
            logger.exception(f"❌ Failed to fetch Square data: {e}")
            return 0.0

    async def get_inventory(self, product_name: str) -> int:
        if self.is_mock:
            mock_db = {"Eskimo Coconut": 10, "Truffle Classic": 5}
            return mock_db.get(product_name, 0)
        return 0  # TODO: Real Square Inventory API

    async def update_inventory(self, product_name: str, quantity: int):
        if self.is_mock:
            logger.info(f"✅ [MOCK SQUARE] Inventory update: {product_name} += {quantity}")
            return True
        return False

    async def get_sales_today(self) -> float:
        """Alias for get_total_expected_cash"""
        return await self.get_total_expected_cash()


# Global instance — mode detected at startup from env vars
square_client = SquareClient()
PYEOF

echo "✅ Square Client updated (Hybrid Mode)."
echo ""
echo "🚀 READY. To go live:"
echo "   Add SQUARE_ACCESS_TOKEN + SQUARE_LOCATION_ID to Railway env vars."
echo "   Bot will auto-switch to Real API on next deploy."
