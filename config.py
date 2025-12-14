from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Website Configuration
    WEBSITE_URL: str = "https://eqn.hsc.gov.ua/"
    PRIVATE_KEY_PATH: str
    PRIVATE_KEY_PASSWORD: str
    
    # Bot Configuration
    BOT_TOKEN: str
    LANGUAGE: str = "uk"  # Supported: "uk" (Ukrainian), "en" (English)
    
    # MongoDB Configuration
    MONGODB_URI: str
    MONGODB_DB_NAME: str
    
    # Availability check interval in seconds (default: 300 = 5 minutes)
    AVAILABILITY_CHECK_INTERVAL: int = 300

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

