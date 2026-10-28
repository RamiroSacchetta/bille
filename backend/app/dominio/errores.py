"""Errores del dominio. La API los traduce a respuestas HTTP con mensajes para el usuario."""


class ErrorDominio(Exception):
    """Regla de negocio incumplida por datos del usuario."""


class DatosInvalidos(ErrorDominio):
    pass


class SaldoInsuficiente(ErrorDominio):
    pass


class NoEncontrado(ErrorDominio):
    pass
