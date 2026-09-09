"""
estado.py
=========
Modelos de datos relacionados con el estado de una operación bancaria.

Corresponde a las clases `Operacion` y `EstadoOperacion` del diagrama
de clases (docs/diagramas/01_clases.png).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EstadoOperacion(str, Enum):
    """Posibles estados de una operación de retiro sobre la cuenta."""

    APROBADO = "APROBADO"
    APROBADO_RIESGOSO = "APROBADO-RIESGOSO"  # aprobado sin bloqueo (modo demostrativo)
    CANCELADO = "CANCELADO"
    PENDIENTE = "PENDIENTE"


@dataclass
class Operacion:
    """
    Representa una operación de retiro registrada en el historial
    del coordinador bancario.

    Attributes
    ----------
    nodo_origen : str
        Nodo/cajero que solicitó la operación (p. ej. "Cajero-NY").
    monto : float
        Monto solicitado para el retiro.
    estado : EstadoOperacion
        Resultado final de la operación.
    marca_tiempo : datetime
        Momento en que se registró la operación.
    """

    nodo_origen: str
    monto: float
    estado: EstadoOperacion = EstadoOperacion.PENDIENTE
    marca_tiempo: datetime = field(default_factory=datetime.now)

    def confirmar(self) -> None:
        """Marca la operación como aprobada."""
        self.estado = EstadoOperacion.APROBADO

    def cancelar(self) -> None:
        """Marca la operación como cancelada."""
        self.estado = EstadoOperacion.CANCELADO
