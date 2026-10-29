"""Límite de pedidos por minuto y por IP, en memoria (alcanza para una sola instancia de la API)."""

import math
import time
from collections.abc import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

MENSAJE = "Demasiados pedidos. Esperá un minuto y probá de nuevo."


class LimitePedidos:
    """Ventana fija por clave: cuenta pedidos desde el primero y se reinicia al pasar la ventana."""

    def __init__(self, maximo: int, ventana: float = 60, reloj: Callable[[], float] = time.monotonic) -> None:
        self.maximo = maximo
        self.ventana = ventana
        self.reloj = reloj
        self._ventanas: dict[str, tuple[float, int]] = {}

    def esperar(self, clave: str) -> int | None:
        """Devuelve None si el pedido pasa, o los segundos que faltan para poder volver a pedir."""
        ahora = self.reloj()
        inicio, cantidad = self._ventanas.get(clave, (ahora, 0))
        if ahora - inicio >= self.ventana:
            inicio, cantidad = ahora, 0
        if cantidad >= self.maximo:
            return max(1, math.ceil(inicio + self.ventana - ahora))
        self._ventanas[clave] = (inicio, cantidad + 1)
        if len(self._ventanas) > 10_000:
            self._olvidar_vencidas(ahora)
        return None

    def _olvidar_vencidas(self, ahora: float) -> None:
        self._ventanas = {
            clave: valor for clave, valor in self._ventanas.items() if ahora - valor[0] < self.ventana
        }


class LimitePedidosMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limite: LimitePedidos) -> None:
        super().__init__(app)
        self.limite = limite

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Detrás del proxy de la nube, uvicorn con --proxy-headers pone acá la IP real del cliente
        clave = request.client.host if request.client else "desconocido"
        espera = self.limite.esperar(clave)
        if espera is not None:
            return JSONResponse(
                status_code=429, content={"detail": MENSAJE}, headers={"Retry-After": str(espera)}
            )
        return await call_next(request)
