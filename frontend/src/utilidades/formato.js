/** Formatea un número como moneda en dólares. */
export function formatearDinero(valor) {
  if (valor === null || valor === undefined) return '—'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(valor)
}

/** Devuelve la clase CSS asociada al estado de una operación. */
export function claseEstadoOperacion(estado) {
  if (estado === 'APROBADO') return 'aprobado'
  if (estado === 'APROBADO-RIESGOSO') return 'riesgoso'
  if (estado === 'CANCELADO') return 'cancelado'
  return 'pendiente'
}
