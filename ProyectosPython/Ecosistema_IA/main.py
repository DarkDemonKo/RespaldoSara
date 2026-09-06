import asyncio
import json
import logging
import websockets
from websockets.exceptions import ConnectionClosed

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [YunaClient] - %(levelname)s - %(message)s")
logger = logging.getLogger("YunaMobile")

SERVER_URI = "ws://127.0.0.1:8000/ws"

def start_foreground_service():
    """
    Inicia un Foreground Service en Android usando pyjnius para evadir Doze Mode.
    Esto funcionará si el entorno es Kivy/Buildozer.
    """
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        Intent = autoclass('android.content.Intent')
        
        activity = PythonActivity.mActivity
        # Asumiendo que el servicio en buildozer.spec se llama 'YunaService'
        service_intent = Intent()
        service_intent.setClassName(activity.getPackageName(), f"{activity.getPackageName()}.ServiceYunaService")
        activity.startForegroundService(service_intent)
        logger.info("Foreground service (Notificación persistente) iniciado para evadir Doze Mode.")
    except ImportError:
        logger.warning("Pyjnius no detectado o entorno no-Android. Omitiendo Foreground Service.")
    except Exception as e:
        logger.error(f"Error al iniciar Foreground Service: {e}")

async def audio_capture_loop():
    """Hilo secundario de bajo consumo esperando la wake word (simulado)."""
    logger.info("Módulo de escucha activado en bajo consumo. Esperando wake word...")
    while True:
        await asyncio.sleep(5)  # En producción, usar pyaudio/speech_recognition en un hilo separado
        # logger.debug("Escuchando...")

async def connection_loop():
    """Conexión WebSocket con lógica de reconexión y exponential backoff."""
    backoff = 1
    max_backoff = 60

    while True:
        try:
            logger.info(f"Conectando a {SERVER_URI}...")
            async with websockets.connect(SERVER_URI) as websocket:
                logger.info("Conexión establecida.")
                backoff = 1  # Resetear backoff
                
                # Bucle de recepción de mensajes
                async def receive_messages():
                    while True:
                        response = await websocket.recv()
                        data = json.loads(response)
                        logger.info(f"Respuesta del Servidor: {data.get('respuesta')}")
                        
                receive_task = asyncio.create_task(receive_messages())
                
                # Simular enviar peticiones de voz
                async def mock_send():
                    for msg in ["Hola, soy Yuna", "¿Qué hacemos hoy, papá?", "Apaga las luces de la sala."]:
                        await asyncio.sleep(3)
                        payload = {
                            "origen": "yuna_mobile",
                            "mensaje": msg
                        }
                        logger.info(f"Enviando: {msg}")
                        await websocket.send(json.dumps(payload))
                
                send_task = asyncio.create_task(mock_send())
                
                await asyncio.gather(receive_task, send_task)
                
        except ConnectionClosed:
            logger.warning("Conexión cerrada por el servidor.")
        except Exception as e:
            logger.error(f"Error de conexión: {e}")
        
        logger.info(f"Reconectando en {backoff} segundos...")
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, max_backoff)

async def main():
    start_foreground_service()
    
    # Ejecutar escucha de audio y conexión de red de forma asíncrona
    await asyncio.gather(
        audio_capture_loop(),
        connection_loop()
    )

if __name__ == "__main__":
    asyncio.run(main())
