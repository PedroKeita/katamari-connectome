import unittest
from types import SimpleNamespace

from main import CircuitLoaders, setup_circuits


class SetupCircuitsTests(unittest.TestCase):
    def test_no_flywire_does_not_load_any_circuit(self):
        calls = []

        def loader(name):
            def load(data_dir):
                calls.append((name, data_dir))
                return object()

            return load

        loaders = CircuitLoaders(
            flywire=loader("flywire"),
            ppl=loader("ppl"),
            pcb=loader("pcb"),
            cx=loader("cx"),
            visual=loader("visual"),
        )

        result = setup_circuits(
            SimpleNamespace(no_flywire=True, escape=True),
            data_dir="fake-data",
            loaders=loaders,
        )

        self.assertEqual(result, (None, None, None, None, None))
        self.assertEqual(calls, [])

    def test_loaders_receive_data_dir_and_visual_is_optional(self):
        calls = []

        def flywire(data_dir):
            calls.append(("flywire", data_dir))
            return None

        def loader(name):
            def load(data_dir):
                calls.append((name, data_dir))
                return None

            return load

        loaders = CircuitLoaders(
            flywire=flywire,
            ppl=loader("ppl"),
            pcb=loader("pcb"),
            cx=loader("cx"),
            visual=loader("visual"),
        )

        result = setup_circuits(
            SimpleNamespace(no_flywire=False, escape=False),
            data_dir="fake-data",
            loaders=loaders,
        )

        self.assertEqual(result, (None, None, None, None, None))
        self.assertEqual(
            calls,
            [("flywire", "fake-data"), ("ppl", "fake-data"),
             ("pcb", "fake-data"), ("cx", "fake-data")],
        )


if __name__ == "__main__":
    unittest.main()