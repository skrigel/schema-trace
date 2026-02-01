from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "SchemaTrace"
    admin_email: str = 'skrigel@mit.edu'
    items_per_user: int = 50
    debug_logs: bool = False
    database_url: str = ""
    secret_key: str = ""

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()