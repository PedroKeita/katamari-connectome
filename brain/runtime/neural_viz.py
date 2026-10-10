"""
Visualizador neural desenhado em OpenCV.
Renderiza diretamente na janela de debug — sem browser, sem dependências extras.

Mostra:
  - Três nuvens de pontos (reward / escape / orientation)
  - Pontos acendem proporcionalmente à taxa de spike
  - Barra de fw_bias
  - Painel de stats (L/C/R, coletas, mag)
  - Flash verde ao coletar
"""

import cv2
import numpy as np
import math


class NeuralViz:
    """
    Desenha o estado neural num frame OpenCV.

    Uso:
        viz = NeuralViz(width=1280, height=720)
        frame = viz.render(state)   # state = dict com fw_bias, left, etc.
        cv2.imshow("...", frame)
    """

    def __init__(self, width: int = 1280, height: int = 720, n_points: int = 800):
        self.W = width
        self.H = height
        self.n_points = n_points
        self._t = 0.0
        self._flash = 0.0
        self._prev_collected = 0

        # Centros das três nuvens (coordenadas de tela normalizadas)
        cx, cy = width // 2, height // 2
        self._centers = {
            "reward":  (cx,          cy + 20),
            "escape":  (cx - 320,    cy - 80),
            "orient":  (cx + 320,    cy - 80),
        }
        self._radii = {
            "reward": 160,
            "escape": 60,
            "orient": 70,
        }
        self._colors_base = {
            "reward": (0, 220, 160),   # verde-azulado
            "escape": (60,  80, 255),  # vermelho
            "orient": (220, 120,  0),  # azul-laranja
        }
        self._labels = {
            "reward": "Mushroom Body",
            "escape": "Giant Fiber",
            "orient": "Descending N.",
        }

        # Gera posições fixas dos pontos (esfera achatada = elipse)
        self._pts = {}
        rng = np.random.default_rng(42)
        for name, (ocx, ocy) in self._centers.items():
            r = self._radii[name]
            angles  = rng.uniform(0, 2 * math.pi, n_points)
            radii_r = r * np.cbrt(rng.uniform(0, 1, n_points))
            xs = (ocx + radii_r * np.cos(angles)).astype(np.int32)
            ys = (ocy + radii_r * np.sin(angles) * 0.55).astype(np.int32)   # achatado
            # Profundidade para simular 3D (pontos mais ao centro = mais brilhantes)
            depth = 1.0 - (radii_r / r) * 0.6
            self._pts[name] = (xs, ys, depth)

    def render(self, state: dict, game_frame: np.ndarray | None = None) -> np.ndarray:
        """
        Renderiza o estado neural.

        state: {
            fw_bias, left, center, right, mag, collected,
            circuits: {
                reward: {rate: float},
                escape: {rate: float},
                orient: {rate: float},
            }
        }
        game_frame: frame do jogo (opcional) — mostrado em miniatura no canto
        """
        self._t += 0.04

        # Canvas preto
        canvas = np.zeros((self.H, self.W, 3), dtype=np.uint8)

        circuits = state.get("circuits", {})

        # ----------------------------------------------------------
        # 1. LINHAS DE CONEXÃO (sinapses estilizadas)
        # ----------------------------------------------------------
        self._draw_connection(canvas, "reward", "escape", (30, 60, 50))
        self._draw_connection(canvas, "reward", "orient", (30, 50, 70))

        # ----------------------------------------------------------
        # 2. NUVENS DE NEURÔNIOS
        # ----------------------------------------------------------
        for name in ["reward", "escape", "orient"]:
            rate = circuits.get(name, {}).get("rate", 0.0)
            self._draw_cloud(canvas, name, rate)

        # ----------------------------------------------------------
        # 3. BARRA DE FW_BIAS
        # ----------------------------------------------------------
        bias = state.get("fw_bias", 0.0)
        self._draw_bias_bar(canvas, bias)

        # ----------------------------------------------------------
        # 4. PAINEL DE STATS
        # ----------------------------------------------------------
        self._draw_stats(canvas, state)

        # ----------------------------------------------------------
        # 5. FLASH DE COLETA
        # ----------------------------------------------------------
        collected = state.get("collected", 0)
        if collected > self._prev_collected:
            self._flash = 1.5
            self._prev_collected = collected

        if self._flash > 0:
            self._flash -= 0.05
            alpha = min(self._flash, 1.0)
            overlay = canvas.copy()
            cv2.putText(overlay, f"COLETADO #{collected}",
                        (self.W//2 - 160, self.H//2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4,
                        (0, 255, 80), 3, cv2.LINE_AA)
            cv2.addWeighted(overlay, alpha, canvas, 1 - alpha * 0.3, 0, canvas)

        # ----------------------------------------------------------
        # 6. MINIATURA DO JOGO (canto inferior direito)
        # ----------------------------------------------------------
        if game_frame is not None:
            th, tw = 180, 320
            mini = cv2.resize(game_frame, (tw, th))
            x0 = self.W - tw - 12
            y0 = self.H - th - 12
            # Borda
            cv2.rectangle(canvas, (x0-2, y0-2), (x0+tw+2, y0+th+2), (40,40,40), 1)
            canvas[y0:y0+th, x0:x0+tw] = mini

        return canvas

    # ----------------------------------------------------------
    # Internos
    # ----------------------------------------------------------

    def _draw_cloud(self, canvas, name, rate):
        xs, ys, depth = self._pts[name]
        base = self._colors_base[name]
        cx, cy = self._centers[name]
        r = self._radii[name]

        # Fração de pontos ativos
        active_frac = min(rate * 4.0, 1.0)

        # Pulso suave sincronizado com a taxa
        pulse = 0.5 + 0.5 * math.sin(self._t * (1 + rate * 10))

        n = len(xs)
        # Determina quais pontos estão "acesos" neste frame
        rng = np.random.default_rng(int(self._t * 100) % 10000)
        active_mask = rng.random(n) < active_frac

        for i in range(n):
            x, y = int(xs[i]), int(ys[i])
            if x < 0 or x >= self.W or y < 0 or y >= self.H:
                continue

            d = float(depth[i])

            if active_mask[i]:
                bright = d * (0.6 + 0.4 * pulse)
                size   = 2 if d > 0.7 else 1
            else:
                bright = d * 0.06
                size   = 1

            color = (
                int(base[0] * bright),
                int(base[1] * bright),
                int(base[2] * bright),
            )

            if size == 1:
                canvas[y, x] = color
            else:
                cv2.circle(canvas, (x, y), size, color, -1)

        # Halo central quando taxa alta
        if rate > 0.05:
            halo_r = int(r * 0.3 * rate * 3)
            halo_r = min(halo_r, r // 2)
            alpha  = min(rate * 2, 0.4)
            overlay = canvas.copy()
            cv2.circle(overlay, (cx, cy), halo_r,
                       (base[0]//3, base[1]//3, base[2]//3), -1)
            cv2.addWeighted(overlay, alpha, canvas, 1-alpha, 0, canvas)

        # Label
        label = self._labels[name]
        total = {"reward": 22667, "escape": 212, "orient": 265}[name]
        active_n = int(total * active_frac)
        txt = f"{label}  {active_n:,}/{total:,}"
        cv2.putText(canvas, txt,
                    (cx - 80, cy + r + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                    (base[0]//2, base[1]//2, base[2]//2),
                    1, cv2.LINE_AA)

    def _draw_connection(self, canvas, a, b, color):
        x1, y1 = self._centers[a]
        x2, y2 = self._centers[b]
        # Linha tracejada
        pts = np.linspace(0, 1, 20)
        for i in range(0, len(pts)-1, 2):
            p0 = (int(x1 + (x2-x1)*pts[i]),   int(y1 + (y2-y1)*pts[i]))
            p1 = (int(x1 + (x2-x1)*pts[i+1]), int(y1 + (y2-y1)*pts[i+1]))
            cv2.line(canvas, p0, p1, color, 1, cv2.LINE_AA)

    def _draw_bias_bar(self, canvas, bias):
        bw = 400   # largura total da barra
        bh = 8
        bx = self.W//2 - bw//2
        by = self.H - 40

        # Fundo
        cv2.rectangle(canvas, (bx, by), (bx+bw, by+bh), (25, 25, 25), -1)
        # Centro
        cv2.line(canvas, (bx+bw//2, by-4), (bx+bw//2, by+bh+4), (60,60,60), 1)

        # Barra de bias
        fill_w = int(abs(bias) * bw // 2)
        if bias >= 0:
            x0 = bx + bw//2
            color = (0, 200, 140)
        else:
            x0 = bx + bw//2 - fill_w
            color = (60, 80, 220)
        cv2.rectangle(canvas, (x0, by), (x0+fill_w, by+bh), color, -1)

        # Labels
        cv2.putText(canvas, "ESQ",
                    (bx - 30, by + bh - 1),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (80,80,80), 1)
        cv2.putText(canvas, "DIR",
                    (bx + bw + 4, by + bh - 1),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (80,80,80), 1)
        cv2.putText(canvas, f"fw_bias  {bias:+.3f}",
                    (bx + bw//2 - 40, by - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (80,80,80), 1)

    def _draw_stats(self, canvas, state):
        x, y = 16, 24
        dy = 20

        def line(label, val, color=(160,160,160)):
            nonlocal y
            cv2.putText(canvas, f"{label}", (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (80,80,80), 1, cv2.LINE_AA)
            cv2.putText(canvas, f"{val}", (x+80, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1, cv2.LINE_AA)
            y += dy

        line("L / C / R",
             f"{state.get('left',0):.2f}  {state.get('center',0):.2f}  {state.get('right',0):.2f}")
        line("magnitude", f"{state.get('mag',0):.2f}")
        line("coletados", str(state.get("collected", 0)), (0, 200, 100))
        line("fw bias",   f"{state.get('fw_bias',0):+.3f}")