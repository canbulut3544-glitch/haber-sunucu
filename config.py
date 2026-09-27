from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./finance_news.db"
    # Simple static API key for the mobile app to communicate with the backend
    MOBILE_API_KEY: str = "super_secret_mobile_api_key_for_demo_purposes"
    
    # 3rd party APIs
    NEWS_API_KEY: str = "YOUR_NEWS_API_KEY"

    class Config:
        env_file = ".env"

settings = Settings()
