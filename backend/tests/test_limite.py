"""Tests del límite de pedidos por minuto (fuerza bruta y abuso)."""

from fastapi.testclient import TestClient

from app.api.limite import LimitePedidos
from app.main import crear_app


class Reloj:
    def __init__(self) -> None:
        self.ahora = 1000.0

    def __call__(self) -> float:
        return self.ahora


def test_pasado_el_limite_responde_429_con_mensaje_y_espera():
    cliente = TestClient(crear_app(con_base_de_datos=False, limite_por_minuto=3))
    for _ in range(3):
        assert cliente.get("/api/salud").status_code == 200

    respuesta = cliente.get("/api/salud")

    assert respuesta.status_code == 429
    assert respuesta.json() == {"detail": "Demasiados pedidos. Esperá un minuto y probá de nuevo."}
    assert 1 <= int(respuesta.headers["Retry-After"]) <= 60


def test_el_429_tambien_lleva_cors_para_que_la_app_lea_el_mensaje():
    cliente = TestClient(crear_app(con_base_de_datos=False, limite_por_minuto=1))
    cliente.get("/api/salud")

    respuesta = cliente.get("/api/salud", headers={"Origin": "http://localhost:4200"})

    assert respuesta.status_code == 429
    assert respuesta.headers["access-control-allow-origin"] == "http://localhost:4200"


def test_al_pasar_el_minuto_vuelve_a_dejar_pasar():
    reloj = Reloj()
    limite = LimitePedidos(maximo=2, reloj=reloj)
    assert limite.esperar("1.2.3.4") is None
    assert limite.esperar("1.2.3.4") is None
    assert limite.esperar("1.2.3.4") == 60

    reloj.ahora += 30
    assert limite.esperar("1.2.3.4") == 30

    reloj.ahora += 31
    assert limite.esperar("1.2.3.4") is None


def test_cada_ip_tiene_su_propio_limite():
    limite = LimitePedidos(maximo=1, reloj=Reloj())
    assert limite.esperar("1.1.1.1") is None
    assert limite.esperar("1.1.1.1") is not None
    assert limite.esperar("2.2.2.2") is None
