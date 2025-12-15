import os
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
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"
    
    def print_diagnostics(self):
        """Print diagnostic information about the loaded configuration."""
        print("\n=== Configuration ===")
        print(f"Website URL: {self.WEBSITE_URL}")
        print(f"Private Key Path: {self.PRIVATE_KEY_PATH}")
        print(f"Language: {self.LANGUAGE}")
        print(f"MongoDB Database: {self.MONGODB_DB_NAME}")
        print(f"Check Interval: {self.AVAILABILITY_CHECK_INTERVAL}s ({self.AVAILABILITY_CHECK_INTERVAL // 60}min)")
        print("=====================\n")


settings = Settings()
settings.print_diagnostics()

