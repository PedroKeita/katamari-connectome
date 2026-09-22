"""
Logging científico por sessão.

Salva dois arquivos CSV por sessão em data/sessions/:

  session_YYYY-MM-DD_HH-MM-SS.csv        — dados por frame
  session_YYYY-MM-DD_HH-MM-SS_events.csv — eventos importantes

Uso:
    logger = SessionLogger()
    logger.log_frame(frame_n, fps, left, center, right, ...)
    logger.log_event(frame_n, "COLETADO", "#1")
    logger.close()  # salva e fecha
"""

import csv
import os
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Any


SESSIONS_DIR = os.path.join("data", "sessions")


class SessionLogger:
    """Persist frame and event telemetry for one control session."""

    FRAME_FIELDS = [
        "timestamp", "frame", "fps",
        "left", "center", "right",
        "x", "magnitude",
        "fw_bias", "visual_bias",
        "escape_active", "dopamine",
        "items", "skip_focus", "collected",
        "reward_rate", "escape_rate", "orient_rate",
    ]

    EVENT_FIELDS = [
        "timestamp", "frame", "event", "value"
    ]

    def __init__(
        self,
        session_id: str | None = None,
        sessions_dir: str = SESSIONS_DIR,
    ) -> None:
        os.makedirs(sessions_dir, exist_ok=True)

        if session_id is None:
            session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        self.session_id   = session_id
        self.start_time   = time.time()
        self.frame_count  = 0
        self.event_count  = 0

        frame_path = os.path.join(sessions_dir, f"session_{session_id}.csv")
        event_path = os.path.join(sessions_dir, f"session_{session_id}_events.csv")

        self._frame_f  = open(frame_path,  "w", newline="", encoding="utf-8")
        self._event_f  = open(event_path,  "w", newline="", encoding="utf-8")
        self._frame_w  = csv.DictWriter(self._frame_f, fieldnames=self.FRAME_FIELDS)
        self._event_w  = csv.DictWriter(self._event_f, fieldnames=self.EVENT_FIELDS)
        self._frame_w.writeheader()
        self._event_w.writeheader()

        # Buffer para não fazer I/O a cada frame
        self._frame_buf = []
        self._event_buf = []
        self.FLUSH_EVERY = 30   # flush a cada 30 frames (~1s)

        self.frame_path = frame_path
        self.event_path = event_path
        self._closed = False
        self._summary: dict[str, Any] | None = None

    def log_frame(
        self,
        frame:         int,
        fps:           float,
        left:          float,
        center:        float,
        right:         float,
        x:             float,
        magnitude:     float,
        fw_bias:       float,
        visual_bias:   float,
        escape_active: bool,
        dopamine:      float,
        items:         int,
        skip_focus:    int,
        collected:     int,
        reward_rate:   float = 0.0,
        escape_rate:   float = 0.0,
        orient_rate:   float = 0.0,
    ) -> None:
        """Buffer one frame of telemetry and flush periodically."""
        self.frame_count += 1
        row = {
            "timestamp":    round(time.time() - self.start_time, 3),
            "frame":        frame,
            "fps":          round(fps, 1),
            "left":         round(left, 4),
            "center":       round(center, 4),
            "right":        round(right, 4),
            "x":            round(x, 4),
            "magnitude":    round(magnitude, 4),
            "fw_bias":      round(fw_bias, 4),
            "visual_bias":  round(visual_bias, 4),
            "escape_active": int(escape_active),
            "dopamine":     round(dopamine, 3),
            "items":        items,
            "skip_focus":   skip_focus,
            "collected":    collected,
            "reward_rate":  round(reward_rate, 4),
            "escape_rate":  round(escape_rate, 4),
            "orient_rate":  round(orient_rate, 4),
        }
        self._frame_buf.append(row)

        if len(self._frame_buf) >= self.FLUSH_EVERY:
            self._flush()

    def log_event(self, frame: int, event: str, value: str = "") -> None:
        """Persist an event immediately so important events survive crashes."""
        self.event_count += 1
        row = {
            "timestamp": round(time.time() - self.start_time, 3),
            "frame":     frame,
            "event":     event,
            "value":     value,
        }
        self._event_buf.append(row)
        # Eventos sempre flush imediato
        self._event_w.writerows(self._event_buf)
        self._event_buf.clear()
        self._event_f.flush()

    def _flush(self) -> None:
        if self._frame_buf:
            self._frame_w.writerows(self._frame_buf)
            self._frame_buf.clear()
            self._frame_f.flush()

    def close(self) -> dict[str, Any]:
        """Fecha os arquivos e retorna um resumo da sessão."""
        if self._closed:
            return self._summary or {}

        self._flush()
        if self._event_buf:
            self._event_w.writerows(self._event_buf)
            self._event_buf.clear()

        self._frame_f.close()
        self._event_f.close()

        duration = time.time() - self.start_time
        self._summary = {
            "session_id":   self.session_id,
            "duration_s":   round(duration, 1),
            "frames":       self.frame_count,
            "events":       self.event_count,
            "frame_file":   self.frame_path,
            "event_file":   self.event_path,
        }
        self._closed = True
        return self._summary

    def __enter__(self) -> "SessionLogger":
        """Return this logger for use as a context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Flush and close the session when leaving a context manager."""
        self.close()