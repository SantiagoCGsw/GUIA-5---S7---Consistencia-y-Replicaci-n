"""
utils.py
========
Funciones auxiliares compartidas por el resto del paquete.

Además del log por consola (usado por el modo de línea de comandos),
este módulo expone un mecanismo de SUSCRIPTORES que permite a otros
programas —por ejemplo el backend FastAPI que alimenta la interfaz
gráfica en React— recibir cada evento del sistema distribuido en el
mismo instante en que ocurre, sin modificar la lógica del coordinador
ni de las réplicas.
"""

import threading
from datetime import datetime
from typing import Callable, List

# ----------------------------------------------------------------------
# Suscriptores de eventos
# ----------------------------------------------------------------------
# Cada suscriptor es una función que recibe (marca_tiempo, nodo, mensaje).
# El sistema simulado corre en varios hilos, por lo que la lista se
# protege con su propio lock.
Suscriptor = Callable[[str, str, str], None]

_suscriptores: List[Suscriptor] = []
_lock_suscriptores = threading.Lock()

# Permite silenciar la salida por consola cuando el consumidor es la
# interfaz gráfica (evita ensuciar los logs del servidor).
_imprimir_en_consola: bool = True


def agregar_suscriptor(funcion: Suscriptor) -> None:
    """Registra una función que será notificada en cada evento de log."""
    with _lock_suscriptores:
        _suscriptores.append(funcion)


def quitar_suscriptor(funcion: Suscriptor) -> None:
    """Elimina un suscriptor previamente registrado (si existe)."""
    with _lock_suscriptores:
        if funcion in _suscriptores:
            _suscriptores.remove(funcion)


def configurar_consola(activa: bool) -> None:
    """Activa o desactiva la impresión de los logs por consola."""
    global _imprimir_en_consola
    _imprimir_en_consola = activa


def log(nodo: str, mensaje: str) -> None:
    """
    Imprime un mensaje de log con marca de tiempo y el nombre del nodo
    que lo origina, para poder seguir en consola el orden real en que
    ocurren los eventos en el sistema distribuido simulado.

    Adicionalmente notifica a todos los suscriptores registrados con
    `agregar_suscriptor`, que es como la interfaz gráfica recibe los
    eventos en tiempo real.

    Parameters
    ----------
    nodo : str
        Nombre del nodo/actor que emite el mensaje (p. ej. "Cajero-NY").
    mensaje : str
        Contenido del mensaje a mostrar.
    """
    marca_tiempo = datetime.now().strftime("%H:%M:%S.%f")[:-3]

    if _imprimir_en_consola:
        print(f"[{marca_tiempo}] [{nodo:^12}] {mensaje}")

    with _lock_suscriptores:
        destinatarios = list(_suscriptores)

    for funcion in destinatarios:
        try:
            funcion(marca_tiempo, nodo, mensaje)
        except Exception:  # noqa: BLE001
            # Un suscriptor defectuoso (p. ej. un WebSocket que se cerró)
            # nunca debe interrumpir la simulación en curso.
            pass
