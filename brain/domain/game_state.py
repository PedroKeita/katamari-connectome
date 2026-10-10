"""
brain/game_state.py — Estado do loop principal

Centraliza todas as variáveis mutáveis do loop:
  - dopamina e foco
  - escape circuit (frames, stagnation)
  - detector de freeze L/C/R
  - contadores de frame e FPS
"""


class GameState:
    """Mutable domain state for one Katamari control session."""
    # Constantes biológicas
    ESCAPE_HOLD_FRAMES = 12   # ~400ms a 30fps
    STAGNATION_LIMIT   = 180  # frames sem coleta → escape (~6s a 30fps)
    LCR_FREEZE_LIMIT   = 60   # frames com L/C/R idênticos → jogo congelado (2s)
    PATIENCE_LIMIT     = 90   # frames focando no mesmo item antes de pular

    def __init__(self, base_dopamine: float = 1.0) -> None:
        # Dopamina
        self.base_dopamine        = base_dopamine
        self.dopamine             = base_dopamine

        # Foco / skip
        self.focus_patience       = 0
        self.skip_focus           = 0

        # Coleta
        self.total_collected      = 0
        self.last_collection_frame = -999

        # Escape
        self.escape_active        = False
        self.escape_frames        = 0
        self.frames_since_col     = 0

        # Freeze detector (L/C/R)
        self.last_lcr             = (0.0, 0.0, 0.0)
        self.lcr_freeze_count     = 0

        # FlyWire bias (lido da thread)
        self.fw_bias              = 0.0

        # Frame / FPS
        self.frame_n              = 0
        self.fps_disp             = 0.0
        self.paused_ui            = False

    # ------------------------------------------------------------------
    # Helpers de coleta
    # ------------------------------------------------------------------

    def on_collected(self) -> None:
        """Chamado quando um item é coletado."""
        self.total_collected      += 1
        self.focus_patience        = 0
        self.skip_focus            = 0
        self.last_collection_frame = self.frame_n
        self.frames_since_col      = 0
        self.dopamine              = min(self.base_dopamine * 1.6, 2.0)

    def decay_dopamine(self) -> None:
        """Decai dopamina gradualmente após coleta."""
        if self.dopamine > self.base_dopamine:
            self.dopamine = max(self.dopamine - 0.04, self.base_dopamine)

    # ------------------------------------------------------------------
    # Helpers de foco
    # ------------------------------------------------------------------

    def update_focus(self, has_items: bool, n_items: int) -> bool:
        """
        Atualiza paciência de foco. Retorna True se deve pular para
        o próximo candidato.
        """
        if has_items:
            self.focus_patience += 1
            if self.focus_patience >= self.PATIENCE_LIMIT:
                self.focus_patience = 0
                self.skip_focus = min(self.skip_focus + 1, n_items - 1)
                return True
        else:
            self.focus_patience = 0
            self.skip_focus = 0
        return False

    # ------------------------------------------------------------------
    # Helpers de freeze detector
    # ------------------------------------------------------------------

    def check_freeze(self, left: float, center: float, right: float) -> bool:
        """Retorna True se L/C/R estão congelados (jogo pausado/travado)."""
        lcr_now = (round(left, 3), round(center, 3), round(right, 3))
        if lcr_now == self.last_lcr and lcr_now != (0.0, 0.0, 0.0):
            self.lcr_freeze_count += 1
        else:
            self.lcr_freeze_count = 0
            self.last_lcr = lcr_now
        return self.lcr_freeze_count >= self.LCR_FREEZE_LIMIT

    # ------------------------------------------------------------------
    # Helpers de escape
    # ------------------------------------------------------------------

    def tick_escape(self) -> bool:
        """
        Decrementa o contador de escape ativo.
        Retorna True se o escape acabou de terminar.
        """
        if not self.escape_active:
            return False
        self.escape_frames -= 1
        if self.escape_frames <= 0:
            self.escape_active    = False
            self.frames_since_col = 0
            return True
        return False

    def trigger_escape(self):
        self.escape_active = True
        self.escape_frames = self.ESCAPE_HOLD_FRAMES

    def tick_stagnation(self, just_collected: bool) -> None:
        if just_collected:
            self.frames_since_col = 0
        else:
            self.frames_since_col += 1

    @property
    def stagnation_threat(self) -> bool:
        return self.frames_since_col >= self.STAGNATION_LIMIT