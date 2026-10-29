"""Punto de entrada de la API de Bille."""

from contextlib import asynccontextmanager

import psycopg.errors
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg_pool import ConnectionPool

from app.api.limite import LimitePedidos, LimitePedidosMiddleware
from app.api.rutas import rutas
from app.config import configuracion
from app.dominio.errores import DatosInvalidos, NoEncontrado, SaldoInsuficiente


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    # Sin sentencias preparadas: el pooler de Supabase en modo transacción no las soporta
    pool = ConnectionPool(
        configuracion().url_base_datos,
        min_size=1,
        max_size=10,
        open=True,
        kwargs={"prepare_threshold": None},
    )
    app.state.pool = pool
    yield
    pool.close()


def crear_app(con_base_de_datos: bool = True, limite_por_minuto: int | None = None) -> FastAPI:
    app = FastAPI(title="Bille API", version="0.1.0", lifespan=ciclo_de_vida if con_base_de_datos else None)
    # Se agrega antes que CORS para quedar adentro: así el 429 también sale con los encabezados de CORS
    app.add_middleware(
        LimitePedidosMiddleware,
        limite=LimitePedidos(maximo=limite_por_minuto or configuracion().limite_pedidos_por_minuto),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configuracion().origenes_cors,
        allow_origin_regex=configuracion().origenes_cors_regex,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(rutas)

    def _error(codigo: int, mensaje: str) -> JSONResponse:
        return JSONResponse(status_code=codigo, content={"detail": mensaje})

    @app.exception_handler(DatosInvalidos)
    def _datos_invalidos(_: Request, error: DatosInvalidos):
        return _error(422, str(error))

    @app.exception_handler(SaldoInsuficiente)
    def _saldo_insuficiente(_: Request, error: SaldoInsuficiente):
        return _error(409, str(error))

    @app.exception_handler(NoEncontrado)
    def _no_encontrado(_: Request, error: NoEncontrado):
        return _error(404, str(error))

    @app.exception_handler(psycopg.errors.UniqueViolation)
    def _duplicado(_: Request, __: Exception):
        return _error(409, "Ya existe un elemento con ese nombre")

    @app.exception_handler(psycopg.errors.CheckViolation)
    def _restriccion(_: Request, __: Exception):
        return _error(422, "Los datos no cumplen las reglas de Bille")

    return app


app = crear_app()
