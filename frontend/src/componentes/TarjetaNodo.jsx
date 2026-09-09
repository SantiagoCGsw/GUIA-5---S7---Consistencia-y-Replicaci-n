import { useEffect, useRef, useState } from 'react'
import { formatearDinero } from '../utilidades/formato.js'

const ICONOS = {
  coordinador: '🏛',
  cajero: '🏧',
  replica: '🗄',
}

/**
 * Tarjeta de un nodo. Resalta brevemente cuando su saldo cambia, para que
 * se pueda seguir a simple vista cómo se propaga la actualización.
 */
export default function TarjetaNodo({ nodo, saldo, ultimoEvento, destacado = false }) {
  const [pulso, setPulso] = useState(false)
  const saldoPrevio = useRef(saldo)

  useEffect(() => {
    if (saldo !== saldoPrevio.current) {
      saldoPrevio.current = saldo
      setPulso(true)
      const temporizador = setTimeout(() => setPulso(false), 700)
      return () => clearTimeout(temporizador)
    }
  }, [saldo])

  const clases = [
    'nodo',
    `nodo-${nodo.rol}`,
    destacado ? 'nodo-destacado' : '',
    pulso ? 'nodo-pulso' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <article className={clases}>
      <div className="nodo-encabezado">
        <span className="nodo-icono" aria-hidden="true">
          {ICONOS[nodo.rol]}
        </span>
        <div>
          <h3>{nodo.region}</h3>
          <span className="nodo-etiqueta">{nodo.etiqueta}</span>
        </div>
      </div>

      <div className="nodo-saldo">
        {saldo === null || saldo === undefined ? (
          <span className="nodo-sin-saldo">Sin copia local</span>
        ) : (
          <>
            <span className="nodo-saldo-valor">{formatearDinero(saldo)}</span>
            <span className="nodo-saldo-titulo">saldo almacenado</span>
          </>
        )}
      </div>

      <footer className={`nodo-estado nodo-estado-${ultimoEvento?.evento ?? 'reposo'}`}>
        {ultimoEvento ? ultimoEvento.mensaje : 'En reposo'}
      </footer>
    </article>
  )
}
