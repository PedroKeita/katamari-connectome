"""

Detecta se o jogo está pausado ou em menu.

Duas estratégias combinadas:

1. ESCURECIMENTO GERAL — quando o jogo pausa, sobrepõe um
   overlay escuro na tela. A luminosidade média cai bastante.

2. UNIFORMIDADE — tela de jogo tem muito ruído visual (objetos,
   texturas). Menu pausado tem áreas grandes e uniformes.
   Medida: desvio padrão do frame em escala de cinza.
   Jogo ativo → stddev alto (~40-60)
   Menu pausado → stddev mais baixo OU muito alto (tela branca)

3. ESTABILIDADE — se o frame quase não muda por N frames
   consecutivos, provavelmente está pausado/em menu.

Usa os três juntos com votação para ser robusto.
"""

import cv2
import numpy as np


class PauseDetector:

    def __init__(
        self,
        # Luminosidade média abaixo desse valor → suspeita de pausa
        dark_threshold: float = 60.0,
        # Diferença média entre frames abaixo disso → frame congelado
        freeze_threshold: float = 2.0,
        # Frames consecutivos congelados para confirmar pausa
        freeze_frames: int = 8,
        # Região de amostragem (proporção) — centro da tela
        # evita bordas com HUD fixo
        roi: tuple = (0.15, 0.15, 0.85, 0.75),
    ):
        self.dark_threshold   = dark_threshold
        self.freeze_threshold = freeze_threshold
        self.freeze_frames    = freeze_frames
        self.roi              = roi

        self._prev_gray     = None
        self._frozen_count  = 0
        self.is_paused      = False

    def check(self, frame: np.ndarray) -> bool:
        """
        Retorna True se o jogo parece pausado ou em menu.
        Atualiza self.is_paused.
        """
        h, w = frame.shape[:2]
        x1 = int(w * self.roi[0]); y1 = int(h * self.roi[1])
        x2 = int(w * self.roi[2]); y2 = int(h * self.roi[3])

        roi = frame[y1:y2, x1:x2]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        votes_paused = 0

        # --------------------------------------------------
        # 1. ESCURECIMENTO
        # --------------------------------------------------
        mean_brightness = float(gray.mean())
        if mean_brightness < self.dark_threshold:
            votes_paused += 1

        # --------------------------------------------------
        # 2. CONGELAMENTO — frame quase idêntico ao anterior
        # --------------------------------------------------
        if self._prev_gray is not None:
            diff = cv2.absdiff(gray, self._prev_gray)
            mean_diff = float(diff.mean())

            if mean_diff < self.freeze_threshold:
                self._frozen_count += 1
            else:
                self._frozen_count = 0

            if self._frozen_count >= self.freeze_frames:
                votes_paused += 2   # peso maior — muito confiável

        self._prev_gray = gray.copy()

        # --------------------------------------------------
        # 3. DECISÃO
        # --------------------------------------------------
        # 1 voto (só escuro) = incerto
        # 2+ votos = pausado
        self.is_paused = votes_paused >= 2

        return self.is_paused

    def reset(self):
        self._prev_gray    = None
        self._frozen_count = 0
        self.is_paused     = False