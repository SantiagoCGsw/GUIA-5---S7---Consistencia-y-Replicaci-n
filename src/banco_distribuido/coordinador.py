"""
coordinador.py
===============
Núcleo de la emulación: el nodo COORDINADOR (banco central).

Mantiene el estado autoritativo (saldo maestro) de la cuenta y
orquesta la replicación síncrona hacia los nodos regionales.
Implementa dos estrategias de control de concurrencia para poder
comparar sus efectos:

1. `retirar_consistencia_fuerte` -> usa un bloqueo distribuido
   (equivalente simplificado a un Two-Phase Commit): antes de
   aprobar un retiro, bloquea la cuenta en todo el sistema, valida
   el saldo y solo entonces confirma. Garantiza CONSISTENCIA FUERTE.

2. `retirar_sin_lock` -> no usa ningún bloqueo. Se incluye únicamente
   con fines DIDÁCTICOS, para reproducir en clase la condición de
   carrera (race condition) que la consistencia fuerte evita.

Corresponde a la clase `CoordinadorBancario` del diagrama de clases
(docs/diagramas/01_clases.png).
"""

import random
import threading
import time
from typing import List

from .estado import EstadoOperacion, Operacion
from .replica import Replica
from .utils import log


class CoordinadorBancario:
    """
    Nodo coordinador (banco central) de la cuenta bancaria distribuida.

    Parameters
    ----------
    saldo_inicial : float
        Saldo con el que se abre la cuenta.
    replicas : List[Replica]
        Lista de nodos réplica que deben mantenerse sincronizados con
        el saldo maestro.
    """

    def __init__(self, saldo_inicial: float, replicas: List[Replica]):
        self.saldo: float = saldo_inicial
        self.replicas: List[Replica] = replicas
        self.lock: threading.Lock = threading.Lock()  # bloqueo distribuido simulado
        self.historial: List[Operacion] = []
        # Hilos de replicación ASÍNCRONA lanzados por `retirar_sin_lock`.
        # Se registran para poder esperarlos antes de leer el estado final
        # (de lo contrario el resumen mostraría réplicas que todavía no
        # han recibido la actualización y ocultaría la inconsistencia real).
        self.hilos_replicacion: List[threading.Thread] = []

    # ------------------------------------------------------------------
    # MODO 1: CONSISTENCIA FUERTE (bloqueo distribuido / 2PC simplificado)
    # ------------------------------------------------------------------
    def retirar_consistencia_fuerte(self, nodo_origen: str, monto: float) -> bool:
        """
        Procesa un retiro garantizando consistencia fuerte.

        Fase 1 (preparar): intenta adquirir el bloqueo distribuido sobre
        la cuenta. Si no lo logra a tiempo, cancela la operación.

        Fase 2 (confirmar): valida el saldo, actualiza el saldo maestro
        y replica el cambio de forma SÍNCRONA (espera confirmación de
        todas las réplicas) antes de dar la operación por completada.

        Parameters
        ----------
        nodo_origen : str
            Identificador del cajero que solicita el retiro.
        monto : float
            Monto a retirar.

        Returns
        -------
        bool
            True si el retiro fue aprobado, False si fue cancelado.
        """
        log(nodo_origen, f"Solicitud de retiro de ${monto:.2f}")

        adquirido = self.lock.acquire(timeout=2)
        if not adquirido:
            log(nodo_origen, "No se pudo bloquear la cuenta a tiempo -> "
                              "operación CANCELADA")
            self.historial.append(
                Operacion(nodo_origen, monto, EstadoOperacion.CANCELADO)
            )
            return False

        try:
            log(nodo_origen, "Bloqueo distribuido adquirido sobre la cuenta")
            time.sleep(random.uniform(0.05, 0.15))  # latencia de validación

            if self.saldo < monto:
                log(nodo_origen, f"Saldo insuficiente (disponible: ${self.saldo:.2f}) "
                                  "-> operación CANCELADA")
                self.historial.append(
                    Operacion(nodo_origen, monto, EstadoOperacion.CANCELADO)
                )
                return False

            nuevo_saldo = self.saldo - monto
            self.saldo = nuevo_saldo
            log("COORDINADOR", f"Saldo maestro actualizado -> ${self.saldo:.2f}")

            self._replicar_sincrono(nuevo_saldo)

            log(nodo_origen, f"Retiro de ${monto:.2f} CONFIRMADO en todos los nodos")
            self.historial.append(
                Operacion(nodo_origen, monto, EstadoOperacion.APROBADO)
            )
            return True
        finally:
            self.lock.release()
            log(nodo_origen, "Bloqueo liberado")

    # ------------------------------------------------------------------
    # MODO 2: SIN BLOQUEO (para evidenciar la condición de carrera)
    # ------------------------------------------------------------------
    def retirar_sin_lock(self, nodo_origen: str, monto: float) -> bool:
        """
        Procesa un retiro SIN ningún mecanismo de control de concurrencia.

        Se incluye únicamente con fines demostrativos: permite observar
        cómo, sin un bloqueo distribuido, dos nodos pueden leer el mismo
        saldo antes de que cualquiera de los dos lo actualice y ambos
        aprobar la operación (double-spending), además de dejar las
        réplicas con valores inconsistentes entre sí.

        Parameters
        ----------
        nodo_origen : str
            Identificador del cajero que solicita el retiro.
        monto : float
            Monto a retirar.

        Returns
        -------
        bool
            True si el retiro fue "aprobado" (posiblemente de forma
            incorrecta), False si fue rechazado por saldo insuficiente
            según la lectura local del nodo.
        """
        log(nodo_origen, f"Solicitud de retiro de ${monto:.2f} (SIN bloqueo)")
        saldo_leido = self.saldo
        log(nodo_origen, f"Lee saldo = ${saldo_leido:.2f}")

        time.sleep(random.uniform(0.05, 0.15))  # ventana de carrera

        if saldo_leido < monto:
            log(nodo_origen, "Saldo insuficiente (según lectura local) -> cancelado")
            self.historial.append(
                Operacion(nodo_origen, monto, EstadoOperacion.CANCELADO)
            )
            return False

        # Sin bloqueo, dos hilos pueden pasar esta validación al mismo tiempo.
        self.saldo = saldo_leido - monto
        log("COORDINADOR", f"Saldo maestro actualizado (sin sincronizar) -> ${self.saldo:.2f}")

        for replica in self.replicas:
            hilo = threading.Thread(
                target=replica.actualizar,
                args=(self.saldo, random.uniform(0.05, 0.2)),
            )
            self.hilos_replicacion.append(hilo)
            hilo.start()

        log(nodo_origen, f"Retiro de ${monto:.2f} 'confirmado' (posible inconsistencia)")
        self.historial.append(
            Operacion(nodo_origen, monto, EstadoOperacion.APROBADO_RIESGOSO)
        )
        return True

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    def esperar_replicacion_pendiente(self, timeout: float = 5.0) -> None:
        """
        Espera a que terminen las replicaciones ASÍNCRONAS que quedaron en
        vuelo (modo `sin_lock`).

        En replicación síncrona esto no hace nada, porque el coordinador ya
        esperó a todas las réplicas antes de confirmar. En el modo sin
        bloqueo, en cambio, las actualizaciones viajan "en segundo plano":
        sin esta espera, el resumen final leería el saldo de las réplicas
        ANTES de que la propagación llegara, mostrando un estado que no
        corresponde al reposo del sistema.
        """
        for hilo in list(self.hilos_replicacion):
            hilo.join(timeout=timeout)
        self.hilos_replicacion.clear()

    def _replicar_sincrono(self, nuevo_saldo: float) -> None:
        """
        Propaga `nuevo_saldo` a todas las réplicas de forma síncrona:
        lanza un hilo por réplica y espera (`join`) a que todas
        confirmen antes de continuar. Esto modela la replicación
        síncrona descrita en el marco conceptual de la guía.
        """
        hilos = []
        for replica in self.replicas:
            hilo = threading.Thread(
                target=replica.actualizar,
                args=(nuevo_saldo, random.uniform(0.05, 0.2)),
            )
            hilo.start()
            hilos.append(hilo)
        for hilo in hilos:
            hilo.join()
