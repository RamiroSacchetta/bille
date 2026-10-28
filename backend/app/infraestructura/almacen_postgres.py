"""Implementación del puerto Almacen sobre Postgres (Supabase).

Cada request abre una transacción que toma el rol `authenticated` con el id del usuario,
así las políticas RLS se aplican también al backend: aunque una consulta olvide filtrar,
Postgres no devuelve datos de otro usuario.
"""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.dominio.modelos import Bolsillo, Movimiento, Objetivo, Parte, Saldos, TipoMovimiento, Ubicacion
from app.dominio.puertos import Categoria, FiltroMovimientos, MetodoPago, Perfil


@contextmanager
def transaccion_de_usuario(pool: ConnectionPool, usuario_id: UUID) -> Iterator["AlmacenPostgres"]:
    with pool.connection() as conexion, conexion.transaction():
        conexion.execute("set local role authenticated")
        claims = json.dumps({"sub": str(usuario_id), "role": "authenticated"})
        conexion.execute("select set_config('request.jwt.claims', %s, true)", (claims,))
        yield AlmacenPostgres(conexion)


def _a_movimiento(fila: dict, partes: list[Parte]) -> Movimiento:
    return Movimiento(
        id=fila["id"],
        usuario_id=fila["usuario_id"],
        tipo=TipoMovimiento(fila["tipo"]),
        monto=fila["monto"],
        ocurrido_en=fila["ocurrido_en"],
        descripcion=fila["descripcion"],
        categoria_id=fila["categoria_id"],
        metodo_pago_id=fila["metodo_pago_id"],
        partes=partes,
    )


def _a_parte(fila: dict) -> Parte:
    return Parte(Ubicacion(Bolsillo(fila["bolsillo"]), fila["objetivo_id"]), fila["monto"])


def _a_objetivo(fila: dict) -> Objetivo:
    return Objetivo(
        id=fila["id"],
        usuario_id=fila["usuario_id"],
        nombre=fila["nombre"],
        monto_meta=fila["monto_meta"],
        fecha_meta=fila["fecha_meta"],
        archivado=fila["archivado"],
    )


def _a_categoria(fila: dict) -> Categoria:
    return Categoria(fila["id"], fila["nombre"], TipoMovimiento(fila["tipo"]), fila["icono"])


def _a_metodo(fila: dict) -> MetodoPago:
    return MetodoPago(fila["id"], fila["nombre"], fila["tipo"], fila["activo"])


class AlmacenPostgres:
    def __init__(self, conexion: Connection) -> None:
        self._cx = conexion
        self._cx.row_factory = dict_row

    def _uno(self, sql: str, parametros: tuple = ()) -> dict | None:
        return self._cx.execute(sql, parametros).fetchone()

    def _todos(self, sql: str, parametros: tuple = ()) -> list[dict]:
        return self._cx.execute(sql, parametros).fetchall()

    # -- Saldos ---------------------------------------------------------------

    def bloquear_usuario(self, usuario_id: UUID) -> None:
        self._uno("select 1 from public.perfiles where id = %s for update", (usuario_id,))

    def saldos(self, usuario_id: UUID) -> Saldos:
        fila = self._uno(
            "select disponible, ahorros from public.saldos_bolsillos where usuario_id = %s", (usuario_id,)
        )
        apartados = self._todos(
            """
            select objetivo_id, sum(monto) as apartado
            from public.partes_movimiento
            where usuario_id = %s and objetivo_id is not null
            group by objetivo_id
            """,
            (usuario_id,),
        )
        if fila is None:
            return Saldos(Decimal(0), Decimal(0), {})
        return Saldos(
            fila["disponible"], fila["ahorros"], {a["objetivo_id"]: a["apartado"] for a in apartados}
        )

    def totales_periodo(self, usuario_id: UUID, desde: datetime, hasta: datetime) -> tuple[Decimal, Decimal]:
        fila = self._uno(
            """
            select
              coalesce(sum(monto) filter (where tipo = 'ingreso'), 0) as ingresos,
              coalesce(sum(monto) filter (where tipo = 'gasto'), 0) as gastos
            from public.movimientos
            where usuario_id = %s and ocurrido_en >= %s and ocurrido_en < %s
            """,
            (usuario_id, desde, hasta),
        )
        return fila["ingresos"], fila["gastos"]

    # -- Movimientos ----------------------------------------------------------

    def guardar_movimiento(self, movimiento: Movimiento) -> Movimiento:
        fila = self._uno(
            """
            insert into public.movimientos
              (usuario_id, tipo, monto, ocurrido_en, descripcion, categoria_id, metodo_pago_id)
            values (%s, %s, %s, %s, %s, %s, %s)
            returning *
            """,
            (
                movimiento.usuario_id,
                movimiento.tipo.value,
                movimiento.monto,
                movimiento.ocurrido_en,
                movimiento.descripcion,
                movimiento.categoria_id,
                movimiento.metodo_pago_id,
            ),
        )
        with self._cx.cursor() as cursor:
            cursor.executemany(
                """
                insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, objetivo_id, monto)
                values (%s, %s, %s, %s, %s)
                """,
                [
                    (
                        fila["id"],
                        movimiento.usuario_id,
                        p.ubicacion.bolsillo.value,
                        p.ubicacion.objetivo_id,
                        p.monto,
                    )
                    for p in movimiento.partes
                ],
            )
        return _a_movimiento(fila, list(movimiento.partes))

    def obtener_movimiento(self, usuario_id: UUID, movimiento_id: UUID) -> Movimiento | None:
        fila = self._uno(
            "select * from public.movimientos where id = %s and usuario_id = %s", (movimiento_id, usuario_id)
        )
        if fila is None:
            return None
        partes = self._todos(
            "select * from public.partes_movimiento where movimiento_id = %s", (movimiento_id,)
        )
        return _a_movimiento(fila, [_a_parte(p) for p in partes])

    def eliminar_movimiento(self, usuario_id: UUID, movimiento_id: UUID) -> None:
        self._cx.execute(
            "delete from public.movimientos where id = %s and usuario_id = %s", (movimiento_id, usuario_id)
        )

    def listar_movimientos(self, usuario_id: UUID, filtro: FiltroMovimientos) -> list[Movimiento]:
        condiciones, parametros = ["usuario_id = %s"], [usuario_id]
        if filtro.desde:
            condiciones.append("ocurrido_en >= %s")
            parametros.append(filtro.desde)
        if filtro.hasta:
            condiciones.append("ocurrido_en < %s")
            parametros.append(filtro.hasta)
        if filtro.tipo:
            condiciones.append("tipo = %s")
            parametros.append(filtro.tipo.value)
        if filtro.categoria_id:
            condiciones.append("categoria_id = %s")
            parametros.append(filtro.categoria_id)
        parametros.append(filtro.limite)
        filas = self._todos(
            f"""
            select * from public.movimientos
            where {" and ".join(condiciones)}
            order by ocurrido_en desc, creado_en desc
            limit %s
            """,
            tuple(parametros),
        )
        if not filas:
            return []
        partes_por_movimiento: dict[UUID, list[Parte]] = {}
        for parte in self._todos(
            "select * from public.partes_movimiento where movimiento_id = any(%s)",
            ([f["id"] for f in filas],),
        ):
            partes_por_movimiento.setdefault(parte["movimiento_id"], []).append(_a_parte(parte))
        return [_a_movimiento(f, partes_por_movimiento.get(f["id"], [])) for f in filas]

    # -- Objetivos ------------------------------------------------------------

    def guardar_objetivo(self, objetivo: Objetivo) -> Objetivo:
        if objetivo.id is None:
            fila = self._uno(
                """
                insert into public.objetivos (usuario_id, nombre, monto_meta, fecha_meta, archivado)
                values (%s, %s, %s, %s, %s) returning *
                """,
                (
                    objetivo.usuario_id,
                    objetivo.nombre,
                    objetivo.monto_meta,
                    objetivo.fecha_meta,
                    objetivo.archivado,
                ),
            )
        else:
            fila = self._uno(
                """
                update public.objetivos
                set nombre = %s, monto_meta = %s, fecha_meta = %s, archivado = %s
                where id = %s and usuario_id = %s
                returning *
                """,
                (
                    objetivo.nombre,
                    objetivo.monto_meta,
                    objetivo.fecha_meta,
                    objetivo.archivado,
                    objetivo.id,
                    objetivo.usuario_id,
                ),
            )
        return _a_objetivo(fila)

    def obtener_objetivo(self, usuario_id: UUID, objetivo_id: UUID) -> Objetivo | None:
        fila = self._uno(
            "select * from public.objetivos where id = %s and usuario_id = %s", (objetivo_id, usuario_id)
        )
        return _a_objetivo(fila) if fila else None

    def listar_objetivos(self, usuario_id: UUID) -> list[Objetivo]:
        filas = self._todos(
            "select * from public.objetivos where usuario_id = %s order by creado_en", (usuario_id,)
        )
        return [_a_objetivo(f) for f in filas]

    def eliminar_objetivo(self, usuario_id: UUID, objetivo_id: UUID) -> None:
        self._cx.execute(
            "delete from public.objetivos where id = %s and usuario_id = %s", (objetivo_id, usuario_id)
        )

    def objetivo_tiene_movimientos(self, usuario_id: UUID, objetivo_id: UUID) -> bool:
        fila = self._uno(
            "select exists (select 1 from public.partes_movimiento where usuario_id = %s and objetivo_id = %s) as hay",
            (usuario_id, objetivo_id),
        )
        return fila["hay"]

    # -- Catálogo -------------------------------------------------------------

    def obtener_perfil(self, usuario_id: UUID) -> Perfil | None:
        fila = self._uno("select * from public.perfiles where id = %s", (usuario_id,))
        return Perfil(fila["id"], fila["nombre_visible"], fila["moneda_predeterminada"]) if fila else None

    def actualizar_perfil(self, usuario_id: UUID, nombre_visible: str) -> Perfil:
        fila = self._uno(
            "update public.perfiles set nombre_visible = %s where id = %s returning *",
            (nombre_visible, usuario_id),
        )
        return Perfil(fila["id"], fila["nombre_visible"], fila["moneda_predeterminada"])

    def obtener_categoria(self, usuario_id: UUID, categoria_id: UUID) -> Categoria | None:
        fila = self._uno(
            "select * from public.categorias where id = %s and usuario_id = %s", (categoria_id, usuario_id)
        )
        return _a_categoria(fila) if fila else None

    def listar_categorias(self, usuario_id: UUID) -> list[Categoria]:
        filas = self._todos(
            "select * from public.categorias where usuario_id = %s order by tipo, nombre", (usuario_id,)
        )
        return [_a_categoria(f) for f in filas]

    def crear_categoria(
        self, usuario_id: UUID, nombre: str, tipo: TipoMovimiento, icono: str | None
    ) -> Categoria:
        fila = self._uno(
            "insert into public.categorias (usuario_id, nombre, tipo, icono) values (%s, %s, %s, %s) returning *",
            (usuario_id, nombre, tipo.value, icono),
        )
        return _a_categoria(fila)

    def eliminar_categoria(self, usuario_id: UUID, categoria_id: UUID) -> None:
        self._cx.execute(
            "delete from public.categorias where id = %s and usuario_id = %s", (categoria_id, usuario_id)
        )

    def obtener_metodo_pago(self, usuario_id: UUID, metodo_pago_id: UUID) -> MetodoPago | None:
        fila = self._uno(
            "select * from public.metodos_pago where id = %s and usuario_id = %s",
            (metodo_pago_id, usuario_id),
        )
        return _a_metodo(fila) if fila else None

    def listar_metodos_pago(self, usuario_id: UUID) -> list[MetodoPago]:
        filas = self._todos(
            "select * from public.metodos_pago where usuario_id = %s order by nombre", (usuario_id,)
        )
        return [_a_metodo(f) for f in filas]

    def crear_metodo_pago(self, usuario_id: UUID, nombre: str, tipo: str) -> MetodoPago:
        fila = self._uno(
            "insert into public.metodos_pago (usuario_id, nombre, tipo) values (%s, %s, %s) returning *",
            (usuario_id, nombre, tipo),
        )
        return _a_metodo(fila)

    def actualizar_metodo_pago(self, usuario_id: UUID, metodo_pago_id: UUID, activo: bool) -> MetodoPago:
        fila = self._uno(
            "update public.metodos_pago set activo = %s where id = %s and usuario_id = %s returning *",
            (activo, metodo_pago_id, usuario_id),
        )
        return _a_metodo(fila)
