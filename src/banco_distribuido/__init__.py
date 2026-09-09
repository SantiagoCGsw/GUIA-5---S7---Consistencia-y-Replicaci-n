"""
banco_distribuido
==================
Paquete que emula un sistema bancario distribuido para ilustrar los
conceptos de CONSISTENCIA y REPLICACIÓN estudiados en la Guía 5
(Módulo: Gestión de Recursos y Tolerancia a Fallos).

Caso emulado: dos cajeros automáticos (Nueva York y Madrid) intentan
retirar simultáneamente el saldo total de una misma cuenta, mientras
el saldo se replica de forma síncrona hacia servidores regionales.

Componentes principales
------------------------
- `CoordinadorBancario`: nodo central que mantiene el saldo maestro
  y aplica el bloqueo distribuido (consistencia fuerte).
- `Replica`: nodo regional que recibe copias del saldo.
- `Operacion` / `EstadoOperacion`: registro histórico de cada retiro.
- `ejecutar_escenario`: arma y corre la demostración completa.
- `ordenar_cajeros`: define qué cajero solicita el retiro primero.
"""

from .coordinador import CoordinadorBancario
from .estado import EstadoOperacion, Operacion
from .replica import Replica
from .simulacion import (
    analizar_resultado,
    construir_escenario,
    ejecutar_escenario,
    ejecutar_retiros,
    ordenar_cajeros,
)
from .utils import agregar_suscriptor, configurar_consola, quitar_suscriptor

__all__ = [
    "CoordinadorBancario",
    "Replica",
    "Operacion",
    "EstadoOperacion",
    "ejecutar_escenario",
    "construir_escenario",
    "ejecutar_retiros",
    "ordenar_cajeros",
    "analizar_resultado",
    "agregar_suscriptor",
    "quitar_suscriptor",
    "configurar_consola",
]

__version__ = "1.0.0"