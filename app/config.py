from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str

    database_url: str = "sqlite:///./quantum_grow.db"
    webapp_url: str = "http://localhost:8000"

    # Payment settings
    usdt_network: str = "TRC20"
    usdt_address: str = ""

    usdc_network: str = "ERC20"
    usdc_address: str = ""

    btc_network: str = "Bitcoin"
    btc_address: str = ""

    eth_network: str = "ERC20"
    eth_address: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
