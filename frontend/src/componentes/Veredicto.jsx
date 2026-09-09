/**
 * Conclusión del escenario: indica si el sistema quedó consistente y, si
 * no, qué fallo concreto se produjo (double-spending, réplicas divergentes
 * o saldo negativo).
 */
export default function Veredicto({ resumen }) {
  if (!resumen) return null

  const consistente = resumen.consistente

  return (
    <section className={`veredicto ${consistente ? 'veredicto-ok' : 'veredicto-fallo'}`}>
      <div className="veredicto-icono" aria-hidden="true">
        {consistente ? '✓' : '!'}
      </div>

      <div className="veredicto-cuerpo">
        <h2>
          {consistente
            ? 'Sistema consistente: la integridad de la cuenta se mantuvo'
            : 'Fallo de consistencia detectado'}
        </h2>

        {consistente ? (
          <p>
            Solo se aprobó una operación y todas las réplicas quedaron sincronizadas en{' '}
            <strong>${resumen.saldo_coordinador.toFixed(2)}</strong>. El bloqueo distribuido evitó
            la doble entrega de dinero.
          </p>
        ) : (
          <>
            <ul>
              {resumen.mensajes.map((mensaje, indice) => (
                <li key={indice}>{mensaje}</li>
              ))}
            </ul>
            <p className="veredicto-nota">
              Esto demuestra por qué un sistema bancario con recursos críticos no puede operar con
              consistencia débil o eventual.
            </p>
          </>
        )}

        <div className="veredicto-chips">
          <span className="chip">
            Operaciones aprobadas: <strong>{resumen.aprobados}</strong>
          </span>
          <span className="chip">
            Saldo maestro final: <strong>${resumen.saldo_coordinador.toFixed(2)}</strong>
          </span>
          <span className="chip">
            Réplicas: <strong>{resumen.replicas_inconsistentes ? 'divergentes' : 'sincronizadas'}</strong>
          </span>
        </div>
      </div>
    </section>
  )
}
