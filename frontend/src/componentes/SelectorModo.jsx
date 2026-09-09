const MODOS = [
  {
    id: 'fuerte',
    titulo: 'Consistencia fuerte',
    subtitulo: 'Con bloqueo distribuido (2PC simplificado)',
    detalle:
      'El coordinador bloquea la cuenta para todo el sistema, valida el saldo y replica de forma síncrona antes de confirmar.',
  },
  {
    id: 'sin_lock',
    titulo: 'Sin bloqueo',
    subtitulo: 'Condición de carrera (modo demostrativo)',
    detalle:
      'Los dos cajeros leen el saldo antes de que el otro lo actualice, así que ambos retiros pueden aprobarse (double-spending).',
  },
]

const ORDENES = [
  { id: 'simultaneo', etiqueta: 'Simultáneo', detalle: 'Lo decide el sistema operativo' },
  { id: 'Cajero-NY', etiqueta: 'Nueva York primero', detalle: 'NY pide el retiro antes' },
  { id: 'Cajero-Madrid', etiqueta: 'Madrid primero', detalle: 'Madrid pide el retiro antes' },
]

/**
 * Panel de control: elige la estrategia de concurrencia, el orden de
 * llegada de los cajeros y lanza el escenario.
 */
export default function SelectorModo({
  modo,
  onCambiarModo,
  primero,
  onCambiarPrimero,
  onEjecutar,
  onLimpiar,
  corriendo,
  conectado,
}) {
  return (
    <section className="panel panel-control">
      <header className="panel-cabecera">
        <h2>Estrategia de concurrencia</h2>
        <p>Dos cajeros intentan retirar $100 al mismo tiempo de una cuenta con $100.</p>
      </header>

      <div className="modos">
        {MODOS.map((opcion) => (
          <button
            key={opcion.id}
            type="button"
            className={`modo ${modo === opcion.id ? 'modo-activo' : ''} modo-${opcion.id}`}
            onClick={() => onCambiarModo(opcion.id)}
            disabled={corriendo}
          >
            <span className="modo-marca" aria-hidden="true" />
            <span className="modo-texto">
              <strong>{opcion.titulo}</strong>
              <em>{opcion.subtitulo}</em>
              <span>{opcion.detalle}</span>
            </span>
          </button>
        ))}
      </div>

      <div className="orden">
        <div className="orden-texto">
          <strong>Orden de llegada</strong>
          <span>
            Quién solicita el retiro primero. Con bloqueo distribuido gana el que llega antes; sin
            bloqueo el orden no evita el double-spending.
          </span>
        </div>

        <div className="orden-opciones" role="group" aria-label="Orden de llegada">
          {ORDENES.map((opcion) => (
            <button
              key={opcion.id}
              type="button"
              className={`orden-boton ${primero === opcion.id ? 'orden-activo' : ''}`}
              onClick={() => onCambiarPrimero(opcion.id)}
              disabled={corriendo}
              title={opcion.detalle}
            >
              {opcion.etiqueta}
            </button>
          ))}
        </div>
      </div>

      <div className="acciones">
        <button
          type="button"
          className="boton boton-primario"
          onClick={onEjecutar}
          disabled={corriendo || !conectado}
        >
          {corriendo ? 'Ejecutando…' : 'Ejecutar simulación'}
        </button>
        <button type="button" className="boton boton-secundario" onClick={onLimpiar} disabled={corriendo}>
          Limpiar
        </button>
      </div>
    </section>
  )
}