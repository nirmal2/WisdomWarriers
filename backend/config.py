from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str

    # Apify
    apify_token: str
    apify_posts_actor_id: str = "xMc5Ga1oCONPmWJIa"
    apify_profiles_actor_id: str = "dSCLg0C3YEZ83HzYX"
    profiles_file: str = "Insta Profiles.txt"

    # OpenAI
    openai_api_key: str

    # Scraping
    profile_scrape_parallelism: int = 6
    apify_actor_timeout_seconds: int = 900

    # Supabase Storage (optional)
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_posts_display_bucket: str = "Posts Display Pictures"
    supabase_profile_picture_bucket: str = "Profile Picture"
    supabase_storage_access_key_id: str | None = None
    supabase_storage_secret_access_key: str | None = None
    supabase_storage_s3_endpoint: str | None = None
    supabase_storage_region: str = "ap-south-1"

    # CORS
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
