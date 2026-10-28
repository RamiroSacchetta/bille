"""Configuración leída de variables de entorno (o de backend/.env en desarrollo)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Valores por defecto de `supabase start`
    url_base_datos: str = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_jwt_secret: str = "super-secret-jwt-token-with-at-least-32-characters-long"
    origenes_cors: list[str] = ["http://localhost:4200"]
    zona_horaria: str = "America/Argentina/Buenos_Aires"


@lru_cache
def configuracion() -> Configuracion:
    return Configuracion()
