import TarjetaNodo from './TarjetaNodo.jsx'

/**
 * Topología del sistema: el coordinador arriba, los cajeros que solicitan
 * el retiro a la izquierda y los servidores regionales que reciben la
 * replicación a la derecha.
 */
export default function PanelNodos({ nodos, saldos, ultimoEventoPorNodo, saldoInicial }) {
  const coordinador = nodos.find((n) => n.rol === 'coordinador')
  const cajeros = nodos.filter((n) => n.rol === 'cajero')
  const replicas = nodos.filter((n) => n.rol === 'replica')

  const saldoDe = (nodo) => {
    if (!saldos) return nodo.rol === 'cajero' ? null : saldoInicial
    if (nodo.rol === 'coordinador') return saldos.coordinador
    if (nodo.rol === 'replica') return saldos.replicas?.[nodo.nombre] ?? saldoInicial
    return null
  }

  return (
    <section className="panel panel-nodos">
      <header className="panel-cabecera">
        <h2>Nodos del sistema</h2>
        <p>Saldo de cada nodo, actualizado en vivo mientras corre el escenario.</p>
      </header>

      <div className="topologia">
        <div className="columna columna-cajeros">
          <span className="columna-titulo">Cajeros (clientes)</span>
          {cajeros.map((nodo) => (
            <TarjetaNodo
              key={nodo.nombre}
              nodo={nodo}
              saldo={saldoDe(nodo)}
              ultimoEvento={ultimoEventoPorNodo[nodo.nombre]}
            />
          ))}
        </div>

        <div className="columna columna-centro">
          <span className="columna-titulo">Nodo maestro</span>
          {coordinador && (
            <TarjetaNodo
              nodo={coordinador}
              saldo={saldoDe(coordinador)}
              ultimoEvento={ultimoEventoPorNodo[coordinador.nombre]}
              destacado
            />
          )}
        </div>

        <div className="columna columna-replicas">
          <span className="columna-titulo">Réplicas (servidores regionales)</span>
          {replicas.map((nodo) => (
            <TarjetaNodo
              key={nodo.nombre}
              nodo={nodo}
              saldo={saldoDe(nodo)}
              ultimoEvento={ultimoEventoPorNodo[nodo.nombre]}
            />
          ))}
        </div>
      </div>
    </section>
  )
}
