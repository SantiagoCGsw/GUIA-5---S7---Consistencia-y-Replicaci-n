import { useEffect, useMemo, useState } from 'react'
import ConsolaEventos from './componentes/ConsolaEventos.jsx'
import HistorialOperaciones from './componentes/HistorialOperaciones.jsx'
import PanelNodos from './componentes/PanelNodos.jsx'
import ResumenSuperior from './componentes/ResumenSuperior.jsx'
import SelectorModo from './componentes/SelectorModo.jsx'
import Veredicto from './componentes/Veredicto.jsx'
import { useSimulacion } from './hooks/useSimulacion.js'

export default function App() {
  const {
    conectado,
    corriendo,
    error,
    nodos,
    eventos,
    historial,
    saldos,
    resumen,
    etiquetaModo,
    iniciar,
    limpiar,
  } = useSimulacion()

  const [modo, setModo] = useState('fuerte')
  const [primero, setPrimero] = useState('simultaneo')
  const [configuracion, setConfiguracion] = useState({
    saldo_inicial: 100,
    monto_retiro: 100,
    nodos: [],
  })

  // Al cargar, se piden al backend los valores por defecto del escenario.
  useEffect(() => {
    fetch('/api/configuracion')
      .then((respuesta) => respuesta.json())
      .then((datos) => setConfiguracion(datos))
      .catch(() => {
        /* El aviso de conexión ya lo muestra el hook del WebSocket. */
      })
  }, [])

  // Último evento de cada nodo, para mostrarlo dentro de su tarjeta.
  const ultimoEventoPorNodo = useMemo(() => {
    const mapa = {}
    for (const evento of eventos) {
      mapa[evento.nodo] = evento
    }
    return mapa
  }, [eventos])

  const listaNodos = nodos.length > 0 ? nodos : configuracion.nodos ?? []

  return (
    <div className="aplicacion">
      <header className="barra-superior">
        <div className="marca">
          <span className="marca-logo" aria-hidden="true">
            BD
          </span>
          <div>
            <h1>Banco Distribuido</h1>
            <p>Consistencia y replicación — Guía 5 · S7</p>
          </div>
        </div>

        <div className="barra-derecha">
          <div className="cuenta">
            <span className="cuenta-titulo">Cuenta monitoreada</span>
            <span className="cuenta-numero">**** 4417 · Retiro simultáneo NY / Madrid</span>
          </div>
          <span className={`conexion ${conectado ? 'conexion-ok' : 'conexion-caida'}`}>
            <span className="punto" aria-hidden="true" />
            {conectado ? 'Backend conectado' : 'Sin conexión'}
          </span>
        </div>
      </header>

      <main className="contenido">
        {error && <div className="alerta">{error}</div>}

        <ResumenSuperior
          saldos={saldos}
          saldoInicial={configuracion.saldo_inicial}
          historial={historial}
          corriendo={corriendo}
          etiquetaModo={etiquetaModo}
        />

        <SelectorModo
          modo={modo}
          onCambiarModo={setModo}
          primero={primero}
          onCambiarPrimero={setPrimero}
          onEjecutar={() =>
            iniciar({
              modo,
              primero,
              saldo_inicial: configuracion.saldo_inicial,
              monto_retiro: configuracion.monto_retiro,
            })
          }
          onLimpiar={limpiar}
          corriendo={corriendo}
          conectado={conectado}
        />

        <PanelNodos
          nodos={listaNodos}
          saldos={saldos}
          ultimoEventoPorNodo={ultimoEventoPorNodo}
          saldoInicial={configuracion.saldo_inicial}
        />

        <div className="rejilla-inferior">
          <ConsolaEventos eventos={eventos} corriendo={corriendo} />
          <HistorialOperaciones historial={historial} />
        </div>

        <Veredicto resumen={resumen} />
      </main>

      <footer className="pie">
        Interfaz React sobre la emulación en Python <code>banco_distribuido</code> · los eventos
        llegan por WebSocket desde el backend FastAPI.
      </footer>
    </div>
  )
}