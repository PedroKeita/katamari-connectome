"""
O teclado do Katamari simula os dois analógicos do controle.

Mapeamento padrão do jogo:

    Stick esquerdo:  W A S D
    Stick direito:   I J K L

Movimentos:

    Frente          -> W + I
    Trás            -> S + K
    Esquerda        -> A + J
    Direita         -> D + L

    Frente + direita -> W + I + D + L
    Frente + esquerda -> W + I + A + J

O controlador recebe um ControlOutput:

    output.x
        < -dead -> esquerda
        >  dead -> direita

    output.y
        <  0 -> frente
        >  0 -> trás

    magnitude
        próximo de 0 -> nenhuma tecla

dry_run=True:
    não pressiona teclas, apenas registra o comando.
"""

import logging

from pynput.keyboard import Controller

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

TURN_DEAD_ZONE = 0.25
MOVEMENT_DEAD_ZONE = 0.10


# ---------------------------------------------------------------------------
# Katamari — dois sticks
# ---------------------------------------------------------------------------

# Stick esquerdo
LEFT_FORWARD = "w"
LEFT_BACK = "s"
LEFT_LEFT = "a"
LEFT_RIGHT = "d"

# Stick direito
RIGHT_FORWARD = "i"
RIGHT_BACK = "k"
RIGHT_LEFT = "j"
RIGHT_RIGHT = "l"


class GamepadController:
    """
    Controlador de teclado para Katamari Damacy REROLL.

    O jogo espera que os dois conjuntos de teclas sejam usados
    simultaneamente para movimentar o Katamari.

    Exemplo:

        output.x = 0
        output.y = -1

    resulta em:

        W + I

    que faz o Katamari andar para frente.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

        # Teclas atualmente pressionadas
        self._pressed = set()

        self._kb = None

        if not dry_run:
            try:
                self._kb = Controller()

                logger.info(
                    "[Keyboard] Katamari keyboard controller pronto."
                )

            except Exception as e:
                logger.error(
                    f"[Keyboard] Falha ao iniciar pynput: {e}"
                )
                logger.error(
                    "Instale com: pip install pynput"
                )
                raise

        else:
            logger.info(
                "[Keyboard] Modo dry-run — nenhuma tecla será pressionada."
            )

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def send(self, output) -> None:
        """
        Converte ControlOutput em movimento do Katamari.

        x:
            negativo = esquerda
            positivo = direita

        y:
            negativo = frente
            positivo = trás
        """

        # --------------------------------------------------------------
        # Sem movimento
        # --------------------------------------------------------------

        if output.magnitude < 0.01:
            self._release_all()
            return

        desired = set()

        x = output.x
        y = output.y

        # --------------------------------------------------------------
        # Eixo vertical
        #
        # Os dois "sticks" precisam receber o mesmo comando.
        # --------------------------------------------------------------

        if y < -MOVEMENT_DEAD_ZONE:

            # Frente
            desired.add(LEFT_FORWARD)
            desired.add(RIGHT_FORWARD)

        elif y > MOVEMENT_DEAD_ZONE:

            # Trás
            desired.add(LEFT_BACK)
            desired.add(RIGHT_BACK)

        # --------------------------------------------------------------
        # Eixo horizontal
        # --------------------------------------------------------------

        if x < -TURN_DEAD_ZONE:

            # Esquerda
            desired.add(LEFT_LEFT)
            desired.add(RIGHT_LEFT)

        elif x > TURN_DEAD_ZONE:

            # Direita
            desired.add(LEFT_RIGHT)
            desired.add(RIGHT_RIGHT)

        # --------------------------------------------------------------
        # Aplica as teclas
        # --------------------------------------------------------------

        self._apply(desired)

        if self.dry_run:
            logger.debug(
                "[dry-run] "
                f"teclas={sorted(desired)} "
                f"x={x:+.2f} "
                f"y={y:+.2f} "
                f"mag={output.magnitude:.2f}"
            )

    # ------------------------------------------------------------------
    # Movimentos especiais
    # ------------------------------------------------------------------

    def quick_turn_right(self):
        """
        Faz o quick turn usando a combinação:

            W + K

        No Katamari, isso movimenta os dois sticks
        em direções opostas.
        """

        desired = {
            LEFT_FORWARD,
            RIGHT_BACK,
        }

        self._apply(desired)

    def quick_turn_left(self):
        """
        Faz o quick turn na direção oposta:

            S + I
        """

        desired = {
            LEFT_BACK,
            RIGHT_FORWARD,
        }

        self._apply(desired)

    def release(self):
        """Solta todas as teclas."""
        self._release_all()

    def reset(self) -> None:
        """Solta todas as teclas."""
        self._release_all()

    def close(self) -> None:
        self.reset()

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

        """
        Faz a transição entre o estado atual e o estado desejado.

        Exemplo:

            atual:
                W + I

            desejado:
                W + I + D + L

        Apenas D e L serão pressionadas.
        """

        # Solta teclas que não são mais necessárias
        for key in list(self._pressed):

            if key not in desired:
                self._release(key)

        # Pressiona novas teclas
        for key in desired:

            if key not in self._pressed:
                self._press(key)

    def _release_all(self):

        for key in list(self._pressed):
            self._release(key)