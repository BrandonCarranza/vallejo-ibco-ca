"""
Application settings and configuration.

Loads configuration from environment variables with validation using Pydantic.
All settings are centralized here for easy management and type safety.
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    # ========================================================================
    # Application Settings
    # ========================================================================
    app_name: str = Field(default="IBCo Vallejo Console", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # ========================================================================
    # API Settings
    # ========================================================================
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    api_prefix: str = Field(default="/api/v1", description="API route prefix")
    cors_origins: list[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    api_workers: int = Field(default=4, description="Number of API workers (production)")
    api_timeout: int = Field(default=60, description="Request timeout in seconds")

    # ========================================================================
    # Database Settings
    # ========================================================================
    database_url: str = Field(
        default="postgresql://ibco:ibcopass@localhost:5432/ibco_vallejo",
        description="PostgreSQL connection URL"
    )
    database_pool_size: int = Field(
        default=20,
        description="Database connection pool size"
    )
    database_max_overflow: int = Field(
        default=10,
        description="Max connections beyond pool size"
    )
    database_pool_timeout: int = Field(
        default=30,
        description="Pool timeout in seconds"
    )
    database_pool_recycle: int = Field(
        default=3600,
        description="Recycle connections after this many seconds"
    )

    # ========================================================================
    # Redis Settings
    # ========================================================================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_cache_ttl: int = Field(
        default=3600,
        description="Default cache TTL in seconds"
    )

    # ========================================================================
    # Celery Settings (Task Queue)
    # ========================================================================
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL"
    )
    celery_task_always_eager: bool = Field(
        default=False,
        description="Execute tasks synchronously (for testing)"
    )

    # ========================================================================
    # Data Storage Paths
    # ========================================================================
    data_directory: str = Field(
        default="./data",
        description="Base data directory"
    )
    raw_data_directory: str = Field(
        default="./data/raw",
        description="Raw source documents directory"
    )
    processed_data_directory: str = Field(
        default="./data/processed",
        description="Processed data directory"
    )
    archive_directory: str = Field(
        default="./data/archive",
        description="Data archive directory"
    )
    samples_directory: str = Field(
        default="./data/samples",
        description="Sample data directory"
    )

    # ========================================================================
    # External Data Sources
    # ========================================================================
    vallejo_cafr_base_url: str = Field(
        default="https://www.cityofvallejo.net/",
        description="City of Vallejo CAFR base URL"
    )
    calpers_api_url: str = Field(
        default="https://www.calpers.ca.gov/",
        description="CalPERS website URL"
    )
    calpers_api_key: Optional[str] = Field(
        default=None,
        description="CalPERS API key (if available)"
    )
    state_controller_api_url: str = Field(
        default="https://bythenumbers.sco.ca.gov/",
        description="CA State Controller API URL"
    )
    user_agent: str = Field(
        default="IBCo-Data-Collector/1.0 (+https://ibco-ca.us)",
        description="User agent for web scraping"
    )
    scraper_rate_limit: float = Field(
        default=1.0,
        description="Requests per second for scrapers"
    )
    external_api_timeout: int = Field(
        default=30,
        description="Timeout for external API requests (seconds)"
    )

    # ========================================================================
    # Data Validation Settings
    # ========================================================================
    strict_validation: bool = Field(
        default=True,
        description="Enable strict data validation"
    )
    max_validation_error_rate: float = Field(
        default=0.01,
        description="Maximum acceptable validation error rate (1%)"
    )
    data_quality_logging: bool = Field(
        default=True,
        description="Enable data quality logging"
    )

    # ========================================================================
    # Risk Scoring Configuration
    # ========================================================================
    risk_score_version: str = Field(
        default="1.0",
        description="Risk scoring methodology version"
    )
    risk_weight_liquidity: float = Field(
        default=0.25,
        description="Weight for liquidity indicators"
    )
    risk_weight_structural: float = Field(
        default=0.25,
        description="Weight for structural balance indicators"
    )
    risk_weight_pension: float = Field(
        default=0.30,
        description="Weight for pension stress indicators"
    )
    risk_weight_revenue: float = Field(
        default=0.10,
        description="Weight for revenue sustainability indicators"
    )
    risk_weight_debt: float = Field(
        default=0.10,
        description="Weight for debt burden indicators"
    )

    # ========================================================================
    # Projection Settings
    # ========================================================================
    projection_years: int = Field(
        default=10,
        description="Default projection horizon in years"
    )
    discount_rate: float = Field(
        default=0.068,
        description="CalPERS discount rate for NPV calculations"
    )
    inflation_rate: float = Field(
        default=0.03,
        description="Assumed annual inflation rate"
    )

    # ========================================================================
    # Logging Configuration
    # ========================================================================
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    log_format: str = Field(
        default="json",
        description="Log format: json or text"
    )

    # ========================================================================
    # Security Settings
    # ========================================================================
    secret_key: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        description="Secret key for session management and JWT"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    jwt_expiration_minutes: int = Field(
        default=60,
        description="JWT token expiration in minutes"
    )
    force_https: bool = Field(
        default=False,
        description="Force HTTPS redirect (production only)"
    )
    require_api_auth: bool = Field(
        default=False,
        description="Require API authentication"
    )
    internal_api_key: Optional[str] = Field(
        default=None,
        description="API key for internal services"
    )

    # ========================================================================
    # Monitoring & Observability
    # ========================================================================
    enable_performance_monitoring: bool = Field(
        default=True,
        description="Enable performance monitoring"
    )
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    sentry_environment: Optional[str] = Field(
        default=None,
        description="Sentry environment name"
    )
    sentry_traces_sample_rate: float = Field(
        default=0.1,
        description="Sentry traces sample rate (0.0 to 1.0)"
    )

    # ========================================================================
    # Email Settings
    # ========================================================================
    enable_email_notifications: bool = Field(
        default=False,
        description="Enable email notifications"
    )
    smtp_host: Optional[str] = Field(
        default=None,
        description="SMTP server host"
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP server port"
    )
    smtp_user: Optional[str] = Field(
        default=None,
        description="SMTP username"
    )
    smtp_password: Optional[str] = Field(
        default=None,
        description="SMTP password"
    )
    smtp_from_email: str = Field(
        default="noreply@ibco-ca.us",
        description="From email address"
    )
    admin_emails: list[str] = Field(
        default=["admin@ibco-ca.us"],
        description="Admin email addresses"
    )

    # ========================================================================
    # Feature Flags
    # ========================================================================
    enable_experimental_features: bool = Field(
        default=False,
        description="Enable experimental features"
    )
    enable_pdf_extraction: bool = Field(
        default=False,
        description="Enable automated PDF extraction"
    )
    enable_web_scraping: bool = Field(
        default=False,
        description="Enable web scraping"
    )
    enable_auto_projections: bool = Field(
        default=True,
        description="Enable automated projections"
    )

    # ========================================================================
    # Development Settings
    # ========================================================================
    seed_sample_data: bool = Field(
        default=False,
        description="Seed database with sample data on startup"
    )
    enable_debug_toolbar: bool = Field(
        default=False,
        description="Enable debug toolbar (development only)"
    )
    auto_reload: bool = Field(
        default=True,
        description="Auto-reload on code changes (development only)"
    )

    # ========================================================================
    # Validators
    # ========================================================================

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the allowed values."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v_upper

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format is valid."""
        allowed = ["json", "text"]
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"Log format must be one of {allowed}")
        return v_lower

    # ========================================================================
    # Computed Properties
    # ========================================================================

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == "staging"

    def validate_risk_weights(self) -> None:
        """Validate that risk weights sum to 1.0."""
        total = (
            self.risk_weight_liquidity +
            self.risk_weight_structural +
            self.risk_weight_pension +
            self.risk_weight_revenue +
            self.risk_weight_debt
        )
        if abs(total - 1.0) > 0.001:  # Allow small floating point errors
            raise ValueError(
                f"Risk weights must sum to 1.0, got {total}. "
                f"Check: {self.risk_weight_liquidity} + {self.risk_weight_structural} + "
                f"{self.risk_weight_pension} + {self.risk_weight_revenue} + "
                f"{self.risk_weight_debt}"
            )


# Global settings instance
# Import this in your application code: from src.config.settings import settings
settings = Settings()

# Validate risk weights on startup
settings.validate_risk_weights()
