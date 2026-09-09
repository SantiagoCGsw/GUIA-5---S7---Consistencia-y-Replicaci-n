"""
test_coordinador.py
====================
Pruebas unitarias para `CoordinadorBancario`.

Se enfocan en dos cosas:
1. El comportamiento funcional básico (retiro simple, saldo insuficiente).
2. El INVARIANTE de consistencia fuerte: bajo concurrencia, el saldo
   nunca debe quedar negativo ni aprobar más de un retiro cuando la
   suma de los montos excede el saldo disponible.

Ejecutar con:
    pytest -v
"""

import threading

from banco_distribuido import CoordinadorBancario, EstadoOperacion, Replica


def crear_banco(saldo_inicial: float = 100.0) -> CoordinadorBancario:
    replicas = [Replica("Réplica-Test-A", saldo_inicial),
                Replica("Réplica-Test-B", saldo_inicial)]
    return CoordinadorBancario(saldo_inicial, replicas)


def test_retiro_simple_consistencia_fuerte_se_aprueba():
    banco = crear_banco(100.0)
    resultado = banco.retirar_consistencia_fuerte("Cajero-Test", 40.0)

    assert resultado is True
    assert banco.saldo == 60.0
    assert all(r.saldo == 60.0 for r in banco.replicas)
    assert banco.historial[-1].estado == EstadoOperacion.APROBADO


def test_retiro_con_saldo_insuficiente_se_cancela():
    banco = crear_banco(50.0)
    resultado = banco.retirar_consistencia_fuerte("Cajero-Test", 100.0)

    assert resultado is False
    assert banco.saldo == 50.0  # el saldo no debe modificarse
    assert banco.historial[-1].estado == EstadoOperacion.CANCELADO


def test_consistencia_fuerte_evita_doble_retiro_concurrente():
    """
    Invariante central del caso bancario: si dos cajeros intentan
    retirar el saldo total al mismo tiempo, el sistema con bloqueo
    distribuido debe aprobar solo UNA operación y el saldo final
    nunca debe ser negativo.
    """
    banco = crear_banco(100.0)

    hilo_ny = threading.Thread(
        target=banco.retirar_consistencia_fuerte, args=("Cajero-NY", 100.0)
    )
    hilo_madrid = threading.Thread(
        target=banco.retirar_consistencia_fuerte, args=("Cajero-Madrid", 100.0)
    )

    hilo_ny.start()
    hilo_madrid.start()
    hilo_ny.join()
    hilo_madrid.join()

    aprobados = [op for op in banco.historial if op.estado == EstadoOperacion.APROBADO]

    assert banco.saldo >= 0
    assert len(aprobados) == 1
    assert all(r.saldo == banco.saldo for r in banco.replicas), (
        "Todas las réplicas deben quedar sincronizadas con el saldo maestro"
    )


def test_modo_sin_lock_puede_producir_doble_aprobacion():
    """
    Prueba de contraste (documenta el problema, no lo valida como
    correcto): repite el escenario sin bloqueo varias veces; se
    espera observar AL MENOS UNA vez una doble aprobación, evidenciando
    la condición de carrera que la consistencia fuerte evita.

    Nota: esta prueba es intencionalmente demostrativa/no determinista,
    por lo que se repite el experimento varias veces para aumentar la
    probabilidad de observar el fallo.
    """
    doble_aprobacion_observada = False

    for _ in range(15):
        banco = crear_banco(100.0)
        hilo_ny = threading.Thread(
            target=banco.retirar_sin_lock, args=("Cajero-NY", 100.0)
        )
        hilo_madrid = threading.Thread(
            target=banco.retirar_sin_lock, args=("Cajero-Madrid", 100.0)
        )
        hilo_ny.start()
        hilo_madrid.start()
        hilo_ny.join()
        hilo_madrid.join()

        aprobados = [
            op for op in banco.historial
            if op.estado == EstadoOperacion.APROBADO_RIESGOSO
        ]
        if len(aprobados) > 1:
            doble_aprobacion_observada = True
            break

    assert doble_aprobacion_observada, (
        "Se esperaba observar al menos una doble aprobación en modo "
        "sin bloqueo tras varios intentos; si esto falla de forma "
        "reproducible, revisar la ventana de carrera simulada."
    )
