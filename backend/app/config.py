"""Configuración leída de variables de entorno (o de backend/.env en desarrollo)."""

from functools import lru_cache
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SECRETO_SUPABASE_LOCAL = "super-secret-jwt-token-with-at-least-32-characters-long"


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # "desarrollo" usa los valores de `supabase start`; cualquier otro valor exige las variables de abajo
    entorno: str = "desarrollo"

    # Valores por defecto de `supabase start`
    url_base_datos: str = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_jwt_secret: str = SECRETO_SUPABASE_LOCAL
    origenes_cors: list[str] = ["http://localhost:4200", "http://127.0.0.1:4200"]
    # Cualquier puerto en localhost o en IPs de red local, para usar Bille desde el celular en tu Wi-Fi
    origenes_cors_regex: str = (
        r"^http://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(:\d+)?$"
    )
    zona_horaria: str = "America/Argentina/Buenos_Aires"

    @model_validator(mode="after")
    def _sin_valores_locales_fuera_de_desarrollo(self) -> Self:
        if self.entorno == "desarrollo":
            return self
        obligatorias = ["url_base_datos", "supabase_url", "supabase_jwt_secret"]
        faltantes = [nombre.upper() for nombre in obligatorias if nombre not in self.model_fields_set]
        if faltantes:
            raise ValueError(f"Faltan variables de entorno: {', '.join(faltantes)}")
        if self.supabase_jwt_secret == SECRETO_SUPABASE_LOCAL:
            raise ValueError("SUPABASE_JWT_SECRET no puede ser el de Supabase local")
        return self


@lru_cache
def configuracion() -> Configuracion:
    return Configuracion()
