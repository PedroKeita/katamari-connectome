"""
Usa pynput para simular teclas WASD no Katamari Damacy REROLL.

Mapeamento:
    ControlOutput.x < -dead   → A  (esquerda)
    ControlOutput.x >  dead   → D  (direita)
    ControlOutput.y < 0       → W  (frente) — o fly sempre vai para frente
    magnitude == 0            → solta tudo

O Katamari não tem velocidade analógica via teclado, então a magnitude
é usada para controlar duty-cycle: com magnitude baixa, alterna
press/release em ciclos curtos para simular movimento mais lento.

dry_run=True → não pressiona nada, só loga.
"""

import logging
import time
import threading

logger = logging.getLogger(__name__)

# Limiar para considerar virada (0.0–1.0)
TURN_DEAD_ZONE = 0.25

# Stick esquerdo
KEY_FORWARD = 'w'
KEY_BACK    = 's'
KEY_LEFT    = 'a'
KEY_RIGHT   = 'd'

# Stick direito (Katamari precisa dos dois sticks para rolar)
KEY_FORWARD2 = 'i'
KEY_BACK2    = 'k'
KEY_LEFT2    = 'j'
KEY_RIGHT2   = 'l'


class GamepadController:
    """
    Envia teclas WASD com base num ControlOutput.

    Mantém o estado das teclas pressionadas para evitar
    spam de press/release a cada frame.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run  = dry_run
        self._pressed     = set()   # teclas atualmente seguradas
        self._escape_held = False   # SHIFT+CTRL pressionados
        self._kb      = None

        if not dry_run:
            try:
                from pynput.keyboard import Controller
                self._kb = Controller()
                logger.info("[Keyboard] pynput Controller pronto.")
            except Exception as e:
                logger.error(f"[Keyboard] Falha ao iniciar pynput: {e}")
                logger.error("  Instale: pip install pynput")
                raise
        else:
            logger.info("[Keyboard] Modo dry-run — nenhuma tecla será pressionada.")

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def send(self, output) -> None:
        """Recebe ControlOutput e ajusta as teclas pressionadas."""

        if output.magnitude < 0.01:
            # Sem estímulo — solta tudo
            self._release_all()
            return

        desired = set()

        # Stick esquerdo
        if output.y <= 0:
            desired.add(KEY_FORWARD)
            desired.add(KEY_FORWARD2)
        else:
            desired.add(KEY_BACK)
            desired.add(KEY_BACK2)

        # Virada lateral — ambos os sticks viram juntos
        if output.x < -TURN_DEAD_ZONE:
            desired.add(KEY_LEFT)
            desired.add(KEY_LEFT2)
        elif output.x > TURN_DEAD_ZONE:
            desired.add(KEY_RIGHT)
            desired.add(KEY_RIGHT2)

        self._apply(desired)

        if self.dry_run:
            logger.debug(
                f"[dry-run] teclas={sorted(desired)}"
                f"  x={output.x:+.2f}  mag={output.magnitude:.2f}"
            )

    def reset(self) -> None:
        """Solta todas as teclas."""
        if self._escape_held:
            self.release_escape()
        self._release_all()

    def close(self) -> None:
        self.reset()

    def trigger_escape(self) -> None:
        """
        Giant Fiber disparou — executa quick turn via SHIFT+CTRL.

        No Katamari Damacy REROLL, SHIFT+CTRL realiza um giro rápido
        de 180°, exatamente como a mosca real faz ao detectar looming.
        """
        if self.dry_run:
            return
        if not self._kb:
            return
        try:
            from pynput.keyboard import Key
            self._kb.press(Key.shift)
            self._kb.press(Key.ctrl)
            self._escape_held = True
        except Exception as e:
            logger.debug(f"trigger_escape erro: {e}")

    def release_escape(self) -> None:
        """Solta SHIFT+CTRL após o quick turn."""
        if self.dry_run:
            return
        if not self._kb:
            return
        try:
            from pynput.keyboard import Key
            self._kb.release(Key.ctrl)
            self._kb.release(Key.shift)
            self._escape_held = False
        except Exception as e:
            logger.debug(f"release_escape erro: {e}")

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _press(self, key: str):
        if key in self._pressed:
            return
        self._pressed.add(key)
        if not self.dry_run and self._kb:
            self._kb.press(key)

    def _release(self, key: str):
        if key not in self._pressed:
            return
        self._pressed.discard(key)
        if not self.dry_run and self._kb:
            self._kb.release(key)

    def _apply(self, desired: set):
        """Pressiona as teclas desejadas e solta as que não estão mais."""
        # Solta o que não é mais necessário
        for key in list(self._pressed):
            if key not in desired:
                self._release(key)
        # Pressiona o que falta
        for key in desired:
            self._press(key)

    def _release_all(self):
        for key in list(self._pressed):
            self._release(key)