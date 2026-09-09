import { formatearDinero } from '../utilidades/formato.js'

/**
 * Fila de indicadores del estado actual de la cuenta distribuida.
 */
export default function ResumenSuperior({ saldos, saldoInicial, historial, corriendo, etiquetaModo }) {
  const saldoMaestro = saldos?.coordinador ?? saldoInicial
  const valoresReplicas = Object.values(saldos?.replicas ?? {})
  const sincronizadas =
    valoresReplicas.length > 0 && valoresReplicas.every((valor) => valor === saldoMaestro)
  const aprobadas = historial.filter((op) => op.estado.startsWith('APROBADO')).length

  const indicadores = [
    {
      titulo: 'Saldo maestro',
      valor: formatearDinero(saldoMaestro),
      detalle: `Saldo de apertura: ${formatearDinero(saldoInicial)}`,
      tono: saldoMaestro < 0 ? 'malo' : 'neutro',
    },
    {
      titulo: 'Retiros aprobados',
      valor: String(aprobadas),
      detalle: aprobadas > 1 ? 'Double-spending' : 'Dentro de lo esperado',
      tono: aprobadas > 1 ? 'malo' : 'bueno',
    },
    {
      titulo: 'Réplicas',
      valor: sincronizadas ? 'Sincronizadas' : 'Propagando',
      detalle: valoresReplicas.map((valor) => formatearDinero(valor)).join('  ·  ') || '—',
      tono: sincronizadas ? 'bueno' : 'aviso',
    },
    {
      titulo: 'Estado del sistema',
      valor: corriendo ? 'Ejecutando' : 'En reposo',
      detalle: etiquetaModo ?? 'Sin escenario ejecutado',
      tono: corriendo ? 'aviso' : 'neutro',
    },
  ]

  return (
    <div className="indicadores">
      {indicadores.map((indicador) => (
        <article key={indicador.titulo} className={`indicador-tarjeta tono-${indicador.tono}`}>
          <span className="indicador-titulo">{indicador.titulo}</span>
          <strong className="indicador-valor">{indicador.valor}</strong>
          <span className="indicador-detalle">{indicador.detalle}</span>
        </article>
      ))}
    </div>
  )
}
