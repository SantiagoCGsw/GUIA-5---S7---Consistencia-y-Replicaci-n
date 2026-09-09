"""
replica.py
==========
Modelo del nodo Réplica: un servidor regional que guarda una copia
del saldo maestro y la actualiza cuando el coordinador se lo indica
(replicación síncrona).

Corresponde a la clase `Replica` del diagrama de clases
(docs/diagramas/01_clases.png).
"""

import time
from dataclasses import dataclass

from .utils import log


@dataclass
class Replica:
    """
    Representa un nodo/servidor regional que guarda una copia del saldo.

    Attributes
    ----------
    nombre : str
        Nombre identificador del nodo (p. ej. "Réplica-Bogotá").
    saldo : float
        Copia local del saldo de la cuenta.
    """

    nombre: str
    saldo: float

    def actualizar(self, nuevo_saldo: float, retardo_red: float = 0.0) -> None:
        """
        Aplica una actualización de saldo replicada desde el coordinador.

        Simula la latencia de red mediante `retardo_red` antes de
        confirmar la actualización, para poder observar en los logs
        el efecto de la replicación síncrona sobre varios nodos.

        Parameters
        ----------
        nuevo_saldo : float
            Nuevo valor de saldo a aplicar en esta réplica.
        retardo_red : float, optional
            Segundos de latencia simulada de red (por defecto 0.0).
        """
        time.sleep(retardo_red)
        self.saldo = nuevo_saldo
        log(self.nombre, f"Réplica actualizada -> saldo = ${self.saldo:.2f}")

    def obtener_saldo(self) -> float:
        """Devuelve el saldo actualmente almacenado en esta réplica."""
        return self.saldo
