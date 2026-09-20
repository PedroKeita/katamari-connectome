"""

WebSocket server que transmite dados de spike em tempo real para o
visualizador Three.js no browser.

Roda em thread separada junto com o main.py.
O browser conecta em ws://localhost:8765 e recebe JSON a cada frame.

Formato do payload:
{
  "fw_bias": -0.23,
  "left": 0.82,
  "center": 0.61,
  "right": 0.05,
  "mag": 0.94,
  "collected": 9,
  "reward_spikes": 0.042,   # taxa média de spike dos PAMs
  "escape_active": false,
  "circuits": {
    "reward":  {"active": 1840, "total": 22667, "rate": 0.042},
    "escape":  {"active": 212,  "total": 212,   "rate": 0.200},
    "orient":  {"active": 12,   "total": 265,   "rate": 0.004}
  }
}
"""

import asyncio
import json
import threading
import logging

logger = logging.getLogger(__name__)


class NeuralServer:
    """
    Servidor WebSocket leve para streaming de dados neurais.

    Uso:
        server = NeuralServer(port=8765)
        server.start()               # inicia thread em background
        server.push(data_dict)       # atualiza dados (thread-safe)
        server.stop()
    """

    def __init__(self, port: int = 8765):
        self.port     = port
        self._data    = {}
        self._lock    = threading.Lock()
        self._clients = set()
        self._thread  = None
        self._loop    = None
        self._running = False

    def push(self, data: dict):
        """Atualiza os dados mais recentes (chamado pelo loop principal)."""
        with self._lock:
            self._data = data.copy()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"[NeuralServer] ws://localhost:{self.port}")

    def stop(self):
        self._running = False

    def _run(self):
        try:
            import websockets

            async def handler(ws):
                self._clients.add(ws)
                logger.info(f"[NeuralServer] cliente conectado ({len(self._clients)})")
                try:
                    async for _ in ws:
                        pass   # ignora mensagens do cliente
                except Exception:
                    pass
                finally:
                    self._clients.discard(ws)

            async def broadcast():
                while self._running:
                    if self._clients:
                        with self._lock:
                            payload = json.dumps(self._data)
                        dead = set()
                        for ws in list(self._clients):
                            try:
                                await ws.send(payload)
                            except Exception:
                                dead.add(ws)
                        self._clients -= dead
                    await asyncio.sleep(1/30)   # 30 Hz

            async def main():
                async with websockets.serve(handler, "localhost", self.port):
                    await broadcast()

            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(main())

        except ImportError:
            logger.warning("[NeuralServer] 'websockets' não instalado — visualizador desativado")
            logger.warning("  pip install websockets")
        except Exception as e:
            logger.error(f"[NeuralServer] erro: {e}")