# Sistema Bancario Distribuido — Consistencia y Replicación

Emulación de un sistema bancario distribuido donde dos cajeros
(Nueva York y Madrid) intentan retirar $100 **al mismo tiempo** de una
cuenta que solo tiene $100, mientras dos servidores regionales
(Bogotá y Tokio) reciben el saldo actualizado.

El proyecto se puede usar de dos formas: por **consola** (como
originalmente) o a través de una **interfaz gráfica web en React** que
muestra en vivo lo que ocurre dentro del sistema distribuido.

## Cómo funciona

El programa se puede correr en dos modos:

- **`fuerte`** — Antes de aprobar un retiro, el sistema bloquea la
  cuenta para todos los demás nodos, valida el saldo y solo entonces
  confirma y replica el cambio a Bogotá y Tokio. Resultado: **solo se
  aprueba un retiro**, el saldo nunca queda negativo y las réplicas
  quedan sincronizadas.

- **`sin_lock`** — No usa ningún bloqueo. Ambos cajeros pueden leer el
  saldo de $100 antes de que el otro lo actualice, así que **los dos
  retiros pueden aprobarse** (double-spending) y las réplicas pueden
  quedar con valores distintos entre sí. Este modo existe solo para
  evidenciar el problema que la consistencia fuerte evita.

## Estructura del proyecto

```
main.py                     Punto de entrada por consola
interfaz.py                 Atajo para levantar la interfaz web
src/banco_distribuido/      Núcleo de la emulación (Python puro)
    coordinador.py          Nodo central: bloqueo distribuido y replicación
    replica.py              Servidor regional que guarda una copia del saldo
    estado.py               Operacion / EstadoOperacion
    simulacion.py           Escenario del retiro simultáneo
    utils.py                Log con marca de tiempo + suscriptores de eventos
backend/                    API FastAPI que expone la emulación por HTTP/WebSocket
frontend/                   Interfaz gráfica en React (Vite)
tests/                      Pruebas unitarias con pytest
docs/diagramas/             Diagramas de clases, componentes, despliegue y caso de uso
```

La lógica de consistencia y replicación vive **solo** en
`src/banco_distribuido/`. Ni el backend ni el frontend la reimplementan:
el backend orquesta el paquete y retransmite sus eventos, y el frontend
únicamente los dibuja.

## Cómo hacerlo funcionar

### Opción A — Consola (no requiere instalar nada)

Requiere Python 3.8 o superior.

```bash
python main.py fuerte
python main.py sin_lock
```

### Opción B — Interfaz gráfica en React

Requiere además Node.js 18+ (para compilar el frontend).

```bash
# 1. Dependencias del backend
pip install -r backend/requirements.txt

# 2. Compilar la interfaz
cd frontend
npm install
npm run build
cd ..

# 3. Levantar todo (API + interfaz) en un solo servidor
python interfaz.py
```

Luego abre **http://127.0.0.1:8000**, elige la estrategia
(*Consistencia fuerte* o *Sin bloqueo*) y presiona **Ejecutar simulación**.

#### Modo desarrollo (con recarga automática)

Si vas a modificar el frontend, es más cómodo usar dos terminales:

```bash
# Terminal 1 — backend
python -m uvicorn backend.api:app --reload --port 8000

# Terminal 2 — frontend (Vite, en http://127.0.0.1:5173)
cd frontend
npm run dev
```

Vite redirige automáticamente `/api` y `/ws` hacia el backend, así que
no hay que configurar nada más.

## Qué muestra la interfaz

- **Indicadores superiores**: saldo maestro, retiros aprobados, estado de
  las réplicas y estado del sistema.
- **Nodos del sistema**: una tarjeta por nodo (cajeros, coordinador y
  réplicas) con su saldo, que se resalta cada vez que cambia. Así se ve
  cómo la actualización llega primero al coordinador y después se
  propaga a Bogotá y Tokio.
- **Registro de eventos**: el mismo log de la consola, recibido en vivo
  por WebSocket y coloreado según el tipo de evento (bloqueo,
  replicación, confirmación, cancelación o riesgo).
- **Historial de operaciones**: lo que queda registrado en
  `banco.historial`, con su estado (APROBADO, APROBADO-RIESGOSO o
  CANCELADO).
- **Veredicto final**: si el sistema quedó consistente o qué fallo se
  produjo (double-spending, réplicas divergentes o saldo negativo).

## Cómo se comunican las partes

```
   Navegador (React)  ──WebSocket──▶  FastAPI  ──▶  banco_distribuido
        Cliente          /ws/simulacion   Servidor      Simulación en hilos
```

`banco_distribuido.utils.log` admite **suscriptores**. Cuando el backend
inicia un escenario, registra uno que empuja cada mensaje a una cola
thread-safe; un bucle asíncrono la vacía y envía cada evento al
navegador junto con una fotografía del saldo de todos los nodos en ese
instante. Por eso los saldos de la interfaz cambian al mismo ritmo que
los mensajes del log.

### Endpoints disponibles

| Método | Ruta                | Descripción                                       |
|--------|---------------------|---------------------------------------------------|
| GET    | `/api/salud`        | Comprobación de que el backend responde           |
| GET    | `/api/configuracion`| Modos disponibles, montos por defecto y nodos     |
| POST   | `/api/simulacion`   | Ejecuta un escenario y devuelve el resultado final|
| WS     | `/ws/simulacion`    | Transmite los eventos del escenario en tiempo real|

Ejemplo sin interfaz gráfica:

```bash
curl -X POST http://127.0.0.1:8000/api/simulacion \
     -H "Content-Type: application/json" \
     -d '{"modo":"sin_lock"}'
```

### Ejecutar las pruebas (opcional)

```bash
pip install -r requirements.txt
pytest -v
```
