from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Deliberately excludes any service-role / privileged key: this backend
    only ever acts as the requesting user, via their JWT, so Postgres RLS
    is the real enforcement boundary. See docs/architecture-decisions.md ADR-005.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_anon_key: str = ""
    backend_port: int = 8000
    cors_allow_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


settings = Settings()
