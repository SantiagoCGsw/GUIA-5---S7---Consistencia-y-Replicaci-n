"""
api.py
======
Servidor HTTP/WebSocket que expone la emulación del sistema bancario
distribuido (paquete `banco_distribuido`) para que pueda ser consumida
por la interfaz gráfica en React.

Arquitectura
------------
    React (navegador)  <--WebSocket-->  FastAPI  -->  banco_distribuido
         Cliente                         Servidor        Núcleo de la
                                                         simulación

La lógica de consistencia y replicación NO se reimplementa aquí: este
módulo únicamente orquesta el paquete original y retransmite, evento por
evento, lo que va ocurriendo dentro del sistema distribuido simulado.

Cómo se capturan los eventos
-----------------------------
`banco_distribuido.utils.log` admite suscriptores. Al iniciar una
simulación, este servidor registra un suscriptor que empuja cada línea
de log a una cola thread-safe (la simulación corre en varios hilos).
Un bucle asíncrono vacía esa cola y envía cada evento por el WebSocket
junto con una FOTOGRAFÍA del estado de todos los nodos en ese instante,
que es lo que permite ver los saldos cambiar en vivo en la interfaz.

Ejecutar
--------
    uvicorn backend.api:app --reload --port 8000
"""

import asyncio
import queue
import sys
import threading
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Permite importar el paquete desde src/ sin necesidad de `pip install -e .`
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from banco_distribuido import (  # noqa: E402
    agregar_suscriptor,
    analizar_resultado,
    construir_escenario,
    ejecutar_retiros,
    ordenar_cajeros,
    quitar_suscriptor,
)
from banco_distribuido.simulacion import (  # noqa: E402
    CAJEROS_POR_DEFECTO,
    ETIQUETAS_MODO,
    MODOS_VALIDOS,
    MONTO_RETIRO,
    REPLICAS_POR_DEFECTO,
    SALDO_INICIAL,
)

app = FastAPI(
    title="API — Sistema Bancario Distribuido",
    description="Expone la emulación de consistencia y replicación de la Guía 5.",
    version="1.0.0",
)

# El frontend de desarrollo (Vite) corre en otro puerto, así que necesita CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Solo se permite una simulación a la vez: los suscriptores de log son
# globales al proceso y dos escenarios en paralelo mezclarían sus eventos.
_candado_simulacion = asyncio.Lock()


# ----------------------------------------------------------------------
# Modelos de entrada/salida
# ----------------------------------------------------------------------
class ConfiguracionSimulacion(BaseModel):
    """Parámetros con los que se arma el escenario a ejecutar."""

    modo: str = Field(default="fuerte", description="'fuerte' o 'sin_lock'")
    saldo_inicial: float = Field(default=SALDO_INICIAL, gt=0)
    monto_retiro: float = Field(default=MONTO_RETIRO, gt=0)
    primero: Optional[str] = Field(
        default=None,
        description="Cajero que llega primero: 'Cajero-NY', 'Cajero-Madrid' o 'simultaneo'.",
    )


# ----------------------------------------------------------------------
# Clasificación de eventos (para colorear la consola en el frontend)
# ----------------------------------------------------------------------
def clasificar_evento(nodo: str, mensaje: str) -> str:
    """
    Deduce el tipo de un evento a partir de su texto, para que la
    interfaz pueda darle un color y un icono coherentes.

    Returns
    -------
    str
        Uno de: 'exito', 'error', 'bloqueo', 'replicacion', 'riesgo', 'info'.
    """
    texto = mensaje.lower()
    if "cancelada" in texto or "cancelado" in texto or "insuficiente" in texto:
        return "error"
    if "posible inconsistencia" in texto or "sin sincronizar" in texto:
        return "riesgo"
    if "sin bloqueo" in texto:
        # Solicitud emitida en el modo demostrativo: no es un evento de bloqueo.
        return "info"
    if "bloqueo" in texto:
        return "bloqueo"
    if "réplica actualizada" in texto:
        return "replicacion"
    if "confirmado" in texto or "actualizado" in texto:
        return "exito"
    return "info"


def rol_de_nodo(nombre: str) -> str:
    """Clasifica un nodo como 'coordinador', 'cajero' o 'replica'."""
    if nombre.startswith("Cajero"):
        return "cajero"
    if nombre.startswith("Réplica"):
        return "replica"
    return "coordinador"


def fotografia_estado(banco) -> Dict:
    """
    Devuelve el estado del sistema en este instante: saldo de cada nodo y
    operaciones registradas hasta el momento. Es lo que permite que la
    interfaz muestre los saldos y el historial cambiando en vivo.
    """
    return {
        "coordinador": banco.saldo,
        "replicas": {r.nombre: r.saldo for r in banco.replicas},
        "operaciones": len(banco.historial),
        "historial": [
            {
                "nodo_origen": op.nodo_origen,
                "monto": op.monto,
                "estado": op.estado.value,
                "marca_tiempo": op.marca_tiempo.strftime("%H:%M:%S.%f")[:-3],
            }
            for op in list(banco.historial)
        ],
    }


def descripcion_nodos(config: ConfiguracionSimulacion) -> List[Dict]:
    """Lista de los nodos que participan en el escenario, para la interfaz."""
    nodos = [
        {
            "nombre": "COORDINADOR",
            "rol": "coordinador",
            "etiqueta": "Nodo coordinador",
            "region": "Banco Central",
            "saldo": config.saldo_inicial,
        }
    ]
    regiones_cajeros = {"Cajero-NY": "Nueva York", "Cajero-Madrid": "Madrid"}
    for cajero in CAJEROS_POR_DEFECTO:
        nodos.append(
            {
                "nombre": cajero,
                "rol": "cajero",
                "etiqueta": "Cajero automático",
                "region": regiones_cajeros.get(cajero, cajero),
                "saldo": None,
            }
        )
    regiones_replicas = {"Réplica-Bogotá": "Bogotá", "Réplica-Tokio": "Tokio"}
    for replica in REPLICAS_POR_DEFECTO:
        nodos.append(
            {
                "nombre": replica,
                "rol": "replica",
                "etiqueta": "Servidor regional",
                "region": regiones_replicas.get(replica, replica),
                "saldo": config.saldo_inicial,
            }
        )
    return nodos


# ----------------------------------------------------------------------
# Endpoints REST
# ----------------------------------------------------------------------
@app.get("/api/salud")
def salud() -> Dict:
    """Comprobación rápida de que el backend está arriba."""
    return {"estado": "ok", "servicio": "banco-distribuido"}


@app.get("/api/configuracion")
def configuracion() -> Dict:
    """Valores por defecto y modos disponibles, que la interfaz muestra al cargar."""
    return {
        "modos": [
            {
                "id": modo,
                "etiqueta": ETIQUETAS_MODO[modo],
                "nombre_corto": "Consistencia fuerte" if modo == "fuerte" else "Sin bloqueo",
            }
            for modo in MODOS_VALIDOS
        ],
        "ordenes": [
            {"id": "simultaneo", "etiqueta": "Simultáneo", "detalle": "Lo decide el sistema"},
            {"id": "Cajero-NY", "etiqueta": "Nueva York primero", "detalle": "NY pide antes"},
            {"id": "Cajero-Madrid", "etiqueta": "Madrid primero", "detalle": "Madrid pide antes"},
        ],
        "saldo_inicial": SALDO_INICIAL,
        "monto_retiro": MONTO_RETIRO,
        "cajeros": list(CAJEROS_POR_DEFECTO),
        "replicas": list(REPLICAS_POR_DEFECTO),
        "nodos": descripcion_nodos(ConfiguracionSimulacion()),
    }


@app.post("/api/simulacion")
async def simulacion_completa(config: ConfiguracionSimulacion) -> Dict:
    """
    Ejecuta el escenario completo y devuelve el resultado final de una
    sola vez (sin streaming). Útil para pruebas o para consumir la API
    desde herramientas como curl o Postman.
    """
    if config.modo not in MODOS_VALIDOS:
        return {"error": f"Modo inválido: {config.modo}"}

    try:
        ordenar_cajeros(CAJEROS_POR_DEFECTO, config.primero)
    except ValueError as error:
        return {"error": str(error)}

    async with _candado_simulacion:
        banco = await asyncio.to_thread(_correr_escenario_sincrono, config)

    return {
        "modo": config.modo,
        "etiqueta_modo": ETIQUETAS_MODO[config.modo],
        "primero": config.primero,
        "resumen": analizar_resultado(banco, config.monto_retiro, config.saldo_inicial),
    }


def _correr_escenario_sincrono(config: ConfiguracionSimulacion):
    """Arma y ejecuta el escenario en un hilo aparte (bloqueante)."""
    banco = construir_escenario(config.saldo_inicial)
    ejecutar_retiros(banco, config.modo, config.monto_retiro, primero=config.primero)
    return banco


# ----------------------------------------------------------------------
# WebSocket: transmisión de eventos en tiempo real
# ----------------------------------------------------------------------
@app.websocket("/ws/simulacion")
async def websocket_simulacion(websocket: WebSocket) -> None:
    """
    Canal en vivo con la interfaz gráfica.

    Protocolo
    ---------
    El cliente envía  : {"modo": "fuerte", "primero": "Cajero-Madrid", ...}
    El servidor envía :
        {"tipo": "inicio",  "modo": ..., "nodos": [...]}
        {"tipo": "evento",  "ts": ..., "nodo": ..., "mensaje": ..., "estado": {...}}
        {"tipo": "fin",     "resumen": {...}}
        {"tipo": "error",   "mensaje": ...}
    """
    await websocket.accept()

    try:
        while True:
            peticion = await websocket.receive_json()
            try:
                config = ConfiguracionSimulacion(**peticion)
            except Exception as exc:  # noqa: BLE001
                await websocket.send_json({"tipo": "error", "mensaje": str(exc)})
                continue

            if config.modo not in MODOS_VALIDOS:
                await websocket.send_json(
                    {"tipo": "error", "mensaje": f"Modo inválido: {config.modo}"}
                )
                continue

            try:
                # Valida por adelantado el cajero elegido, para no lanzar la
                # simulación y que falle dentro de un hilo.
                ordenar_cajeros(CAJEROS_POR_DEFECTO, config.primero)
            except ValueError as error:
                await websocket.send_json({"tipo": "error", "mensaje": str(error)})
                continue

            if _candado_simulacion.locked():
                await websocket.send_json(
                    {"tipo": "error", "mensaje": "Ya hay una simulación en curso."}
                )
                continue

            async with _candado_simulacion:
                await _transmitir_escenario(websocket, config)

    except WebSocketDisconnect:
        return
    except Exception:  # noqa: BLE001
        # El cliente se fue o el canal se rompió: no hay nada que reportar.
        return


async def _transmitir_escenario(
    websocket: WebSocket, config: ConfiguracionSimulacion
) -> None:
    """
    Ejecuta un escenario y va enviando cada evento por el WebSocket a
    medida que ocurre, junto con el estado de los nodos en ese instante.
    """
    await websocket.send_json(
        {
            "tipo": "inicio",
            "modo": config.modo,
            "etiqueta_modo": ETIQUETAS_MODO[config.modo],
            "saldo_inicial": config.saldo_inicial,
            "monto_retiro": config.monto_retiro,
            "primero": config.primero,
            "nodos": descripcion_nodos(config),
        }
    )

    cola: "queue.Queue[Optional[Dict]]" = queue.Queue()
    banco = None

    def suscriptor(marca_tiempo: str, nodo: str, mensaje: str) -> None:
        """Se ejecuta dentro de los hilos de la simulación."""
        cola.put(
            {
                "tipo": "evento",
                "ts": marca_tiempo,
                "nodo": nodo,
                "rol": rol_de_nodo(nodo),
                "mensaje": mensaje,
                "evento": clasificar_evento(nodo, mensaje),
                "estado": fotografia_estado(banco) if banco is not None else None,
            }
        )

    def trabajo() -> None:
        """Corre la simulación completa y cierra la cola al terminar."""
        nonlocal banco
        try:
            banco = construir_escenario(config.saldo_inicial)
            ejecutar_retiros(
                banco, config.modo, config.monto_retiro, primero=config.primero
            )
        finally:
            cola.put(None)  # centinela de fin

    agregar_suscriptor(suscriptor)
    hilo = threading.Thread(target=trabajo, name="simulacion", daemon=True)
    hilo.start()

    try:
        while True:
            evento = await asyncio.to_thread(cola.get)
            if evento is None:
                break
            await websocket.send_json(evento)
    finally:
        quitar_suscriptor(suscriptor)
        await asyncio.to_thread(hilo.join)

    if banco is None:
        await websocket.send_json(
            {"tipo": "error", "mensaje": "La simulación no pudo iniciarse."}
        )
        return

    await websocket.send_json(
        {
            "tipo": "fin",
            "modo": config.modo,
            "resumen": analizar_resultado(banco, config.monto_retiro, config.saldo_inicial),
        }
    )


# ----------------------------------------------------------------------
# Frontend compilado (opcional)
# ----------------------------------------------------------------------
# Si se ejecutó `npm run build` en frontend/, este mismo servidor sirve la
# interfaz en http://127.0.0.1:8000, sin necesidad de levantar Vite aparte.
_DIST = RAIZ / "frontend" / "dist"
if _DIST.is_dir():
    from fastapi.staticfiles import StaticFiles  # noqa: E402

    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="frontend")