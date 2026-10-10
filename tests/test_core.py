import unittest
from unittest.mock import patch

from brain.domain.game_state import GameState
from control.integrator import CircuitIntegrator


class GameStateTests(unittest.TestCase):
    def test_collection_resets_focus_and_boosts_dopamine(self):
        state = GameState(base_dopamine=1.0)
        state.frame_n = 12
        state.focus_patience = 8
        state.skip_focus = 2

        state.on_collected()

        self.assertEqual(state.total_collected, 1)
        self.assertEqual(state.last_collection_frame, 12)
        self.assertEqual(state.focus_patience, 0)
        self.assertEqual(state.skip_focus, 0)
        self.assertEqual(state.dopamine, 1.6)

    def test_focus_skips_after_patience_limit(self):
        state = GameState()

        skipped = [state.update_focus(True, 3) for _ in range(state.PATIENCE_LIMIT)]

        self.assertEqual(skipped.count(True), 1)
        self.assertEqual(state.skip_focus, 1)
        self.assertEqual(state.focus_patience, 0)

    def test_freeze_requires_repeated_nonzero_signal(self):
        state = GameState()
        self.assertFalse(state.check_freeze(0.2, 0.4, 0.1))

        for _ in range(state.LCR_FREEZE_LIMIT - 1):
            self.assertFalse(state.check_freeze(0.2, 0.4, 0.1))

        self.assertTrue(state.check_freeze(0.2, 0.4, 0.1))


class CircuitIntegratorTests(unittest.TestCase):
    def test_no_stimulus_uses_exploration_command(self):
        output = CircuitIntegrator().integrate(0.0, 0.0, 0.0, {})

        self.assertEqual(output.x, 0.0)
        self.assertEqual(output.y, -1.0)
        self.assertEqual(output.magnitude, 0.3)

    def test_right_signal_produces_positive_turn(self):
        with patch("random.random", return_value=1.0):
            output = CircuitIntegrator().integrate(0.0, 0.5, 1.0, {})

        self.assertGreater(output.x, 0.0)
        self.assertEqual(output.y, -1.0)
        self.assertGreater(output.magnitude, 0.0)


if __name__ == "__main__":
    unittest.main()