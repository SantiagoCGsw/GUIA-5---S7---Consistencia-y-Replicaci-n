import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Construye la URL del WebSocket a partir del origen actual.
 * En desarrollo, Vite hace de proxy hacia el backend en el puerto 8000.
 */
function urlWebSocket() {
  const protocolo = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocolo}//${window.location.host}/ws/simulacion`
}

const ESTADO_INICIAL = {
  eventos: [],
  historial: [],
  saldos: null,
  resumen: null,
  modo: null,
  etiquetaModo: null,
}

/**
 * Hook que gestiona el canal en vivo con el backend FastAPI.
 *
 * Mantiene la conexión WebSocket abierta, envía la petición de una nueva
 * simulación y va acumulando los eventos que el sistema distribuido emite
 * mientras se ejecuta: cada evento trae consigo el saldo de todos los
 * nodos en ese instante, que es lo que hace que el panel se actualice
 * en tiempo real.
 */
export function useSimulacion() {
  const socketRef = useRef(null)
  const [conectado, setConectado] = useState(false)
  const [corriendo, setCorriendo] = useState(false)
  const [error, setError] = useState(null)
  const [datos, setDatos] = useState(ESTADO_INICIAL)
  const [nodos, setNodos] = useState([])

  useEffect(() => {
    let cerrado = false
    let reintento = null

    function conectar() {
      const socket = new WebSocket(urlWebSocket())
      socketRef.current = socket

      socket.onopen = () => {
        setConectado(true)
        setError(null)
      }

      socket.onclose = () => {
        setConectado(false)
        setCorriendo(false)
        if (!cerrado) {
          // Reintento suave: el backend puede estar reiniciándose.
          reintento = setTimeout(conectar, 2000)
        }
      }

      socket.onerror = () => {
        setError('No se pudo contactar el servidor. ¿Está corriendo el backend en el puerto 8000?')
      }

      socket.onmessage = (evento) => {
        const mensaje = JSON.parse(evento.data)

        if (mensaje.tipo === 'inicio') {
          setNodos(mensaje.nodos)
          setDatos({
            eventos: [],
            historial: [],
            saldos: {
              coordinador: mensaje.saldo_inicial,
              replicas: Object.fromEntries(
                mensaje.nodos
                  .filter((n) => n.rol === 'replica')
                  .map((n) => [n.nombre, mensaje.saldo_inicial]),
              ),
            },
            resumen: null,
            modo: mensaje.modo,
            etiquetaModo: mensaje.etiqueta_modo,
          })
          setCorriendo(true)
          return
        }

        if (mensaje.tipo === 'evento') {
          setDatos((previo) => ({
            ...previo,
            eventos: [...previo.eventos, mensaje],
            saldos: mensaje.estado
              ? { coordinador: mensaje.estado.coordinador, replicas: mensaje.estado.replicas }
              : previo.saldos,
            historial: mensaje.estado?.historial ?? previo.historial,
          }))
          return
        }

        if (mensaje.tipo === 'fin') {
          setDatos((previo) => ({
            ...previo,
            resumen: mensaje.resumen,
            historial: mensaje.resumen.historial,
          }))
          setCorriendo(false)
          return
        }

        if (mensaje.tipo === 'error') {
          setError(mensaje.mensaje)
          setCorriendo(false)
        }
      }
    }

    conectar()

    return () => {
      cerrado = true
      if (reintento) clearTimeout(reintento)
      socketRef.current?.close()
    }
  }, [])

  /** Pide al backend ejecutar un nuevo escenario. */
  const iniciar = useCallback((configuracion) => {
    const socket = socketRef.current
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setError('Sin conexión con el servidor.')
      return
    }
    setError(null)
    setCorriendo(true)
    socket.send(JSON.stringify(configuracion))
  }, [])

  /** Limpia la pantalla sin tocar la conexión. */
  const limpiar = useCallback(() => {
    setDatos(ESTADO_INICIAL)
    setError(null)
  }, [])

  return { conectado, corriendo, error, nodos, ...datos, iniciar, limpiar }
}
