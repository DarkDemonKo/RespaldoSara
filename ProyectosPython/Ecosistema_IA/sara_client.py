import asyncio
import json
import logging
import websockets
from websockets.exceptions import ConnectionClosed

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [SaraDesktop] - %(levelname)s - %(message)s")
logger = logging.getLogger("SaraDesktop")

SERVER_URI = "ws://127.0.0.1:8000/ws"

async def connection_loop():
    """Conexión WebSocket para el cliente de escritorio Sara."""
    backoff = 1
    max_backoff = 60

    while True:
        try:
            logger.info(f"Conectando a {SERVER_URI}...")
            async with websockets.connect(SERVER_URI) as websocket:
                logger.info("Conexión establecida con el enrutador central.")
                backoff = 1
                
                async def receive_messages():
                    while True:
                        response = await websocket.recv()
                        data = json.loads(response)
                        logger.info(f"Output Central: {data.get('respuesta')}")
                        
                receive_task = asyncio.create_task(receive_messages())
                
                async def mock_send():
                    for msg in ["Estado del sistema.", "Verifica los logs del servidor.", "Actualiza los repositorios."]:
                        await asyncio.sleep(4)
                        payload = {
                            "origen": "sara_desktop",
                            "mensaje": msg
                        }
                        logger.info(f"Transmitiendo: {msg}")
                        await websocket.send(json.dumps(payload))
                        
                send_task = asyncio.create_task(mock_send())
                
                await asyncio.gather(receive_task, send_task)
                
        except ConnectionClosed:
            logger.warning("Conexión cerrada.")
        except Exception as e:
            logger.error(f"Error de red: {e}")
        
        logger.info(f"Reintentando enlace en {backoff} segundos...")
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, max_backoff)

if __name__ == "__main__":
    asyncio.run(connection_loop())
