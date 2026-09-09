import { useEffect, useRef } from 'react'

const ETIQUETAS_EVENTO = {
  bloqueo: 'BLOQUEO',
  replicacion: 'REPLICACIÓN',
  exito: 'OK',
  error: 'CANCELADO',
  riesgo: 'RIESGO',
  info: 'INFO',
}

/**
 * Consola de eventos: el mismo log que imprime el programa por consola,
 * pero recibido en vivo por WebSocket y coloreado según el tipo de evento.
 */
export default function ConsolaEventos({ eventos, corriendo }) {
  const finRef = useRef(null)

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [eventos.length])

  return (
    <section className="panel panel-consola">
      <header className="panel-cabecera panel-cabecera-consola">
        <div>
          <h2>Registro de eventos</h2>
          <p>Orden real en que ocurren los mensajes entre los nodos.</p>
        </div>
        <span className={`indicador ${corriendo ? 'indicador-activo' : ''}`}>
          {corriendo ? 'transmitiendo' : `${eventos.length} eventos`}
        </span>
      </header>

      <div className="consola">
        {eventos.length === 0 && (
          <p className="consola-vacia">
            Todavía no hay eventos. Elige una estrategia y ejecuta la simulación.
          </p>
        )}

        {eventos.map((evento, indice) => (
          <div key={`${evento.ts}-${indice}`} className={`linea linea-${evento.evento}`}>
            <span className="linea-hora">{evento.ts}</span>
            <span className={`linea-nodo linea-nodo-${evento.rol}`}>{evento.nodo}</span>
            <span className="linea-tipo">{ETIQUETAS_EVENTO[evento.evento]}</span>
            <span className="linea-mensaje">{evento.mensaje}</span>
          </div>
        ))}
        <div ref={finRef} />
      </div>
    </section>
  )
}
