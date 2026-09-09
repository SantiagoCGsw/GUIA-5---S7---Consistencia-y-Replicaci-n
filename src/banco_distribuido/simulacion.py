"""
simulacion.py
=============
Escenario de demostración: dos cajeros (Nueva York y Madrid) intentan
retirar $100 SIMULTÁNEAMENTE de una cuenta que solo tiene $100,
mientras dos réplicas regionales (Bogotá y Tokio) reciben el saldo
actualizado.

Este módulo expone:

- `construir_escenario(...)`  -> arma el coordinador y sus réplicas.
- `ordenar_cajeros(...)`      -> decide qué cajero llega primero.
- `ejecutar_retiros(...)`     -> lanza los retiros concurrentes.
- `analizar_resultado(...)`   -> devuelve el veredicto de consistencia
                                 como diccionario (lo consume tanto la
                                 consola como la interfaz gráfica).
- `ejecutar_escenario(modo)`  -> la demostración completa por consola.
- `main()`                    -> punto de entrada de línea de comandos.

Uso desde consola
------------------
    python main.py fuerte              # ambos cajeros salen a la vez
    python main.py fuerte madrid       # Madrid llega primero
    python main.py sin_lock ny         # Nueva York llega primero
"""

import sys
import threading
import time
from typing import Dict, List, Optional, Sequence

from .coordinador import CoordinadorBancario
from .estado import EstadoOperacion
from .replica import Replica
from .utils import log

SALDO_INICIAL = 100.0
MONTO_RETIRO = 100.0
MODOS_VALIDOS = ("fuerte", "sin_lock")

CAJEROS_POR_DEFECTO = ("Cajero-NY", "Cajero-Madrid")
REPLICAS_POR_DEFECTO = ("Réplica-Bogotá", "Réplica-Tokio")

ETIQUETAS_MODO = {
    "fuerte": "CONSISTENCIA FUERTE (con bloqueo distribuido)",
    "sin_lock": "SIN BLOQUEO (condición de carrera)",
}

# Ventaja (en segundos) que se le da al cajero elegido para llegar primero.
# Es más pequeña que la ventana de carrera del modo sin bloqueo (0.05-0.15 s),
# así que sirve para decidir quién gana el bloqueo en el modo fuerte SIN
# eliminar la condición de carrera que el modo demostrativo debe evidenciar.
VENTAJA_LLEGADA = 0.03

ORDEN_SIMULTANEO = ("simultaneo", "simultáneo", "ninguno", "")


# ----------------------------------------------------------------------
# Piezas reutilizables (usadas por la consola y por el backend de la GUI)
# ----------------------------------------------------------------------
def construir_escenario(
    saldo_inicial: float = SALDO_INICIAL,
    nombres_replicas: tuple = REPLICAS_POR_DEFECTO,
) -> CoordinadorBancario:
    """
    Crea el coordinador bancario con sus réplicas regionales.

    Parameters
    ----------
    saldo_inicial : float
        Saldo con el que se abre la cuenta en todos los nodos.
    nombres_replicas : tuple
        Nombres de los servidores regionales a crear.

    Returns
    -------
    CoordinadorBancario
        Coordinador listo para procesar retiros.
    """
    replicas = [Replica(nombre, saldo_inicial) for nombre in nombres_replicas]
    banco = CoordinadorBancario(saldo_inicial, replicas)
    log("COORDINADOR", f"Cuenta creada con saldo = ${saldo_inicial:.2f}")
    return banco


def ordenar_cajeros(
    cajeros: Sequence[str] = CAJEROS_POR_DEFECTO,
    primero: Optional[str] = None,
) -> List[str]:
    """
    Reordena la lista de cajeros para que `primero` quede al frente.

    Acepta el nombre completo del nodo ("Cajero-Madrid") o solo la ciudad
    ("madrid", "ny"). Si `primero` es None o indica salida simultánea, se
    devuelve el orden original.

    Raises
    ------
    ValueError
        Si el cajero indicado no existe en el escenario.
    """
    if primero is None or primero.strip().lower() in ORDEN_SIMULTANEO:
        return list(cajeros)

    clave = primero.strip().lower().replace("cajero-", "")
    elegido = next((c for c in cajeros if clave in c.lower()), None)
    if elegido is None:
        raise ValueError(
            f"Cajero desconocido: {primero!r}. Disponibles: {', '.join(cajeros)}."
        )
    return [elegido] + [c for c in cajeros if c != elegido]


def ejecutar_retiros(
    banco: CoordinadorBancario,
    modo: str,
    monto: float = MONTO_RETIRO,
    cajeros: Sequence[str] = CAJEROS_POR_DEFECTO,
    primero: Optional[str] = None,
    ventaja: float = VENTAJA_LLEGADA,
) -> None:
    """
    Lanza un hilo por cajero para que intenten retirar `monto` de forma
    concurrente, usando la estrategia indicada por `modo`, y espera a que
    todos terminen.

    Parameters
    ----------
    banco : CoordinadorBancario
        Coordinador sobre el que se ejecutan los retiros.
    modo : str
        "fuerte" o "sin_lock".
    monto : float
        Monto que cada cajero intenta retirar.
    cajeros : Sequence[str]
        Nombres de los cajeros que participan en el escenario.
    primero : str, optional
        Cajero que debe llegar primero ("Cajero-NY", "madrid", …). Si es
        None o "simultaneo", todos los hilos arrancan a la vez y el orden
        lo decide el planificador del sistema operativo.
    ventaja : float
        Segundos de ventaja que se le dan al cajero elegido. Debe ser menor
        que la ventana de carrera del modo sin bloqueo para no alterar la
        demostración de esa condición de carrera.
    """
    if modo not in MODOS_VALIDOS:
        raise ValueError(f"Modo inválido: {modo!r}. Use uno de {MODOS_VALIDOS}.")

    orden = ordenar_cajeros(cajeros, primero)
    simultaneo = orden == list(cajeros) and (
        primero is None or primero.strip().lower() in ORDEN_SIMULTANEO
    )

    if simultaneo:
        log("COORDINADOR", "Los cajeros solicitan el retiro de forma simultánea")
    else:
        log(
            "COORDINADOR",
            f"Orden de llegada forzado: {' -> '.join(orden)} "
            f"(ventaja de {ventaja * 1000:.0f} ms)",
        )

    metodo = (banco.retirar_consistencia_fuerte
              if modo == "fuerte" else banco.retirar_sin_lock)

    hilos = [
        threading.Thread(target=metodo, args=(cajero, monto), name=cajero)
        for cajero in orden
    ]

    for indice, hilo in enumerate(hilos):
        # La ventaja se aplica ANTES de arrancar cada hilo posterior al
        # primero: así el cajero elegido alcanza a pedir el bloqueo antes.
        if indice > 0 and not simultaneo:
            time.sleep(ventaja)
        hilo.start()

    for hilo in hilos:
        hilo.join()

    # En el modo sin bloqueo la replicación viaja en segundo plano: hay que
    # esperar a que el sistema llegue a reposo antes de evaluar su estado.
    banco.esperar_replicacion_pendiente()


def analizar_resultado(
    banco: CoordinadorBancario,
    monto: float = MONTO_RETIRO,
    saldo_inicial: float = SALDO_INICIAL,
) -> Dict:
    """
    Evalúa el estado final del sistema y devuelve el veredicto de
    consistencia en forma de diccionario, para que pueda ser mostrado
    tanto en consola como en la interfaz gráfica.

    Returns
    -------
    dict
        Con las claves: `consistente`, `doble_gasto`, `replicas_inconsistentes`,
        `saldo_negativo`, `saldo_coordinador`, `replicas`, `aprobados`,
        `historial` y `mensajes`.
    """
    aprobados: List = [
        op for op in banco.historial
        if op.estado in (EstadoOperacion.APROBADO, EstadoOperacion.APROBADO_RIESGOSO)
    ]
    doble_gasto = len(aprobados) > 1
    saldos_replicas = {replica.saldo for replica in banco.replicas}
    replicas_inconsistentes = len(saldos_replicas) > 1
    saldo_negativo = banco.saldo < 0

    mensajes: List[str] = []
    if doble_gasto:
        mensajes.append(
            f"Se aprobaron {len(aprobados)} retiros de ${monto:.2f} sobre un saldo "
            f"inicial de ${saldo_inicial:.2f} (double-spending / sobreventa de fondos)."
        )
    if replicas_inconsistentes:
        detalle = ", ".join(f"{r.nombre}: ${r.saldo:.2f}" for r in banco.replicas)
        mensajes.append(f"Las réplicas quedaron con valores distintos entre sí ({detalle}).")
    if saldo_negativo:
        mensajes.append(f"El saldo maestro quedó en negativo (${banco.saldo:.2f}).")

    return {
        "consistente": not (doble_gasto or replicas_inconsistentes or saldo_negativo),
        "doble_gasto": doble_gasto,
        "replicas_inconsistentes": replicas_inconsistentes,
        "saldo_negativo": saldo_negativo,
        "saldo_coordinador": banco.saldo,
        "replicas": [
            {"nombre": r.nombre, "saldo": r.saldo} for r in banco.replicas
        ],
        "aprobados": len(aprobados),
        "historial": [
            {
                "nodo_origen": op.nodo_origen,
                "monto": op.monto,
                "estado": op.estado.value,
                "marca_tiempo": op.marca_tiempo.strftime("%H:%M:%S.%f")[:-3],
            }
            for op in banco.historial
        ],
        "mensajes": mensajes,
    }


# ----------------------------------------------------------------------
# Demostración completa por consola
# ----------------------------------------------------------------------
def ejecutar_escenario(modo: str, primero: Optional[str] = None) -> CoordinadorBancario:
    """
    Construye el escenario bancario y ejecuta el intento de retiro
    concurrente desde dos cajeros, usando la estrategia indicada.

    Parameters
    ----------
    modo : str
        "fuerte" para consistencia fuerte (bloqueo distribuido) o
        "sin_lock" para el modo demostrativo sin control de concurrencia.
    primero : str, optional
        Cajero que debe llegar primero ("ny" o "madrid"). Si se omite,
        ambos salen a la vez y el orden lo decide el sistema operativo.

    Returns
    -------
    CoordinadorBancario
        La instancia del coordinador ya con el escenario ejecutado,
        útil para inspeccionar `saldo`, `replicas` e `historial`
        (usado también por las pruebas unitarias).
    """
    if modo not in MODOS_VALIDOS:
        raise ValueError(f"Modo inválido: {modo!r}. Use uno de {MODOS_VALIDOS}.")

    print("=" * 70)
    print(" EMULACIÓN - CASO BANCARIO: RETIRO SIMULTÁNEO NUEVA YORK / MADRID")
    print(f" Modo: {ETIQUETAS_MODO[modo]}")
    orden = ordenar_cajeros(CAJEROS_POR_DEFECTO, primero)
    print(f" Orden de llegada: {' -> '.join(orden) if primero else 'simultáneo'}")
    print("=" * 70)

    banco = construir_escenario(SALDO_INICIAL)
    ejecutar_retiros(banco, modo, MONTO_RETIRO, primero=primero)

    _imprimir_resumen(banco)
    return banco


def _imprimir_resumen(banco: CoordinadorBancario) -> None:
    """Imprime en consola el estado final del escenario y su interpretación."""
    print("-" * 70)
    log("COORDINADOR", f"SALDO FINAL EN EL COORDINADOR: ${banco.saldo:.2f}")
    for replica in banco.replicas:
        log(replica.nombre, f"Saldo final en réplica: ${replica.saldo:.2f}")

    print("-" * 70)
    print("Historial de operaciones:")
    for operacion in banco.historial:
        print(f"   -> ({operacion.nodo_origen}, {operacion.monto}, {operacion.estado.value})")

    veredicto = analizar_resultado(banco, MONTO_RETIRO, SALDO_INICIAL)

    if not veredicto["consistente"]:
        print("\n[!] RESULTADO: Fallo de consistencia detectado.")
        for mensaje in veredicto["mensajes"]:
            print(f"    -> {mensaje}")
        print("    Esto demuestra por qué NO se puede usar una consistencia débil")
        print("    o eventual en un sistema bancario con recursos críticos.")
    else:
        print("\n[OK] RESULTADO: Solo se aprobó una operación y todas las réplicas")
        print("     quedan sincronizadas. La consistencia fuerte evitó la doble")
        print("     entrega de dinero.")
    print("=" * 70)


def main() -> None:
    """
    Punto de entrada de línea de comandos.

        python main.py fuerte              # ambos cajeros salen a la vez
        python main.py fuerte madrid       # Madrid llega primero
        python main.py sin_lock ny         # Nueva York llega primero
    """
    modo = sys.argv[1] if len(sys.argv) > 1 else "fuerte"
    primero = sys.argv[2] if len(sys.argv) > 2 else None

    if modo not in MODOS_VALIDOS:
        print(f"Uso: python main.py [{'|'.join(MODOS_VALIDOS)}] [ny|madrid]")
        sys.exit(1)

    try:
        ejecutar_escenario(modo, primero)
    except ValueError as error:
        print(error)
        print(f"Uso: python main.py [{'|'.join(MODOS_VALIDOS)}] [ny|madrid]")
        sys.exit(1)


if __name__ == "__main__":
    main()