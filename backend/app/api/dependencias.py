"""Dependencias de FastAPI: usuario autenticado y acceso a los datos de ese usuario."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.dominio.puertos import Almacen
from app.infraestructura.almacen_postgres import transaccion_de_usuario
from app.infraestructura.jwt_supabase import TokenInvalido, usuario_del_token

_bearer = HTTPBearer(auto_error=False)

# Abre una transacción para el usuario; se usa con `with abrir() as almacen:` dentro del endpoint,
# así los errores del commit (por ejemplo el cuadre diferido) llegan a los manejadores de errores.
AbrirAlmacen = Callable[[], AbstractContextManager[Almacen]]


def usuario_actual(credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> UUID:
    if credenciales is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Iniciá sesión para continuar")
    try:
        return usuario_del_token(credenciales.credentials)
    except TokenInvalido as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(error)) from error


def abrir_almacen(request: Request, usuario_id: Annotated[UUID, Depends(usuario_actual)]) -> AbrirAlmacen:
    pool = request.app.state.pool
    return lambda: transaccion_de_usuario(pool, usuario_id)


UsuarioActual = Annotated[UUID, Depends(usuario_actual)]
Abrir = Annotated[AbrirAlmacen, Depends(abrir_almacen)]
