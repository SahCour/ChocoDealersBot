"""
Configuration management for Chocodealers Bot
Loads environment variables and provides typed settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # ============================================
    # TELEGRAM
    # ============================================
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    admin_telegram_ids: str = Field(..., env="ADMIN_TELEGRAM_IDS")

    @field_validator("admin_telegram_ids")
    @classmethod
    def parse_admin_ids(cls, v: str) -> List[int]:
        """Parse comma-separated admin IDs"""
        return [int(id.strip()) for id in v.split(",") if id.strip()]

    # ============================================
    # DATABASE
    # ============================================
    database_url: str = Field(..., env="DATABASE_URL")

    # ============================================
    # SQUARE API (OPTIONAL)
    # ============================================
    square_access_token: Optional[str] = Field(default=None, env="SQUARE_ACCESS_TOKEN")
    square_location_id: Optional[str] = Field(default=None, env="SQUARE_LOCATION_ID")
    square_environment: str = Field(default="sandbox", env="SQUARE_ENVIRONMENT")
    square_application_id: Optional[str] = Field(default=None, env="SQUARE_APPLICATION_ID")

    # ============================================
    # GOOGLE SHEETS (OPTIONAL)
    # ============================================
    google_credentials_file: Optional[str] = Field(
        default=None,
        env="GOOGLE_CREDENTIALS_FILE"
    )
    google_sheet_id: Optional[str] = Field(default=None, env="GOOGLE_SHEET_ID")
    sheet_name_sales: str = Field(default="Sales", env="SHEET_NAME_SALES")
    sheet_name_inventory: str = Field(default="Inventory", env="SHEET_NAME_INVENTORY")
    sheet_name_purchases: str = Field(default="Purchases", env="SHEET_NAME_PURCHASES")
    sheet_name_production: str = Field(default="Production", env="SHEET_NAME_PRODUCTION")

    # ============================================
    # GOOGLE NOTEBOOK LM (Optional)
    # ============================================
    google_ai_api_key: Optional[str] = Field(default=None, env="GOOGLE_AI_API_KEY")
    notebook_lm_project_id: Optional[str] = Field(default=None, env="NOTEBOOK_LM_PROJECT_ID")

    # ============================================
    # APPLICATION
    # ============================================
    environment: str = Field(default="development", env="ENVIRONMENT")
    timezone: str = Field(default="Asia/Bangkok", env="TIMEZONE")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="./logs/chocodealers_bot.log", env="LOG_FILE")

    # ============================================
    # SYNC SETTINGS
    # ============================================
    square_sync_interval: int = Field(default=30, env="SQUARE_SYNC_INTERVAL")
    sheets_sync_interval: int = Field(default=60, env="SHEETS_SYNC_INTERVAL")
    enable_auto_sync_square: bool = Field(default=True, env="ENABLE_AUTO_SYNC_SQUARE")
    enable_auto_sync_sheets: bool = Field(default=True, env="ENABLE_AUTO_SYNC_SHEETS")

    # ============================================
    # NOTIFICATIONS
    # ============================================
    enable_low_stock_alerts: bool = Field(default=True, env="ENABLE_LOW_STOCK_ALERTS")
    low_stock_check_interval: int = Field(default=120, env="LOW_STOCK_CHECK_INTERVAL")
    notification_channel_id: Optional[str] = Field(default=None, env="NOTIFICATION_CHANNEL_ID")

    # ============================================
    # SECURITY
    # ============================================
    secret_key: str = Field(
        default="change-this-in-production-use-random-string",
        env="SECRET_KEY"
    )
    max_requests_per_minute: int = Field(default=30, env="MAX_REQUESTS_PER_MINUTE")

    # ============================================
    # MONITORING (Optional)
    # ============================================
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def validate_paths(self) -> None:
        """Ensure required directories exist"""
        # Create logs directory
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Check Google credentials file
        if self.google_credentials_file:
            creds_path = Path(self.google_credentials_file)
            if not creds_path.exists():
                print(f"⚠️  Google credentials file not found: {self.google_credentials_file}")

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"


# Global settings instance
try:
    settings = Settings()
    settings.validate_paths()
except Exception as e:
    print(f"❌ Error loading configuration: {e}")
    print("Make sure you have created a .env file with all required variables")
    print("See .env.example for reference")
    raise


# Export for convenience
__all__ = ["settings", "Settings"]
