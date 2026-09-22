import tempfile
import unittest
from pathlib import Path

from brain.runtime.session_logger import SessionLogger


class SessionLoggerTests(unittest.TestCase):
    def test_context_manager_flushes_and_close_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            with SessionLogger(session_id="test", sessions_dir=directory) as logger:
                logger.log_event(1, "TESTE", "ok")

            summary = logger.close()
            frame_path = Path(directory) / "session_test.csv"
            event_path = Path(directory) / "session_test_events.csv"

            self.assertEqual(summary["events"], 1)
            self.assertTrue(frame_path.exists())
            self.assertTrue(event_path.exists())
            self.assertIn("TESTE", event_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()