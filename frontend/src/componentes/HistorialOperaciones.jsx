import { claseEstadoOperacion, formatearDinero } from '../utilidades/formato.js'

/**
 * Historial de operaciones registradas por el coordinador, tal como queda
 * en `banco.historial` al final del escenario.
 */
export default function HistorialOperaciones({ historial }) {
  return (
    <section className="panel panel-historial">
      <header className="panel-cabecera">
        <h2>Historial de operaciones</h2>
        <p>Registro que mantiene el coordinador bancario.</p>
      </header>

      {historial.length === 0 ? (
        <p className="tabla-vacia">Sin operaciones registradas.</p>
      ) : (
        <table className="tabla">
          <thead>
            <tr>
              <th>Hora</th>
              <th>Nodo origen</th>
              <th className="derecha">Monto</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {historial.map((operacion, indice) => (
              <tr key={`${operacion.marca_tiempo}-${indice}`}>
                <td className="mono">{operacion.marca_tiempo}</td>
                <td>{operacion.nodo_origen}</td>
                <td className="derecha mono">{formatearDinero(operacion.monto)}</td>
                <td>
                  <span className={`pastilla pastilla-${claseEstadoOperacion(operacion.estado)}`}>
                    {operacion.estado}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
