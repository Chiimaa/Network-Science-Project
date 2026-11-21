import tempfile
import unittest
from pathlib import Path

from src.load_data import load_graphs, save_graphs


class LoadGraphsTests(unittest.TestCase):
    def test_collapses_reciprocals_removes_loops_and_selects_lcc(self):
        contents = (
            "# sample graph\n"
            "1 1\n"
            "1 2\n"
            "2 1\n"
            "2 3\n"
            "7 7\n"
            "8 9\n"
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "sample.txt"
            input_path.write_text(contents, encoding="utf-8")

            full, lcc, stats = load_graphs(input_path)

            self.assertEqual(set(full.nodes), {1, 2, 3, 7, 8, 9})
            self.assertEqual(set(full.edges), {(1, 2), (2, 3), (8, 9)})
            self.assertEqual(set(lcc.nodes), {1, 2, 3})
            self.assertEqual(stats["input_rows"], 6)
            self.assertEqual(stats["self_loops_removed"], 2)
            self.assertEqual(stats["duplicate_or_reciprocal_rows_removed"], 1)

    def test_saves_plain_edge_lists(self):
        graph_contents = "10 11\n11 12\n"
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "sample.txt"
            input_path.write_text(graph_contents, encoding="utf-8")
            full, lcc, _ = load_graphs(input_path)

            full_path, lcc_path = save_graphs(
                full, lcc, Path(temporary_directory) / "processed"
            )

            self.assertEqual(full_path.read_text(encoding="utf-8").splitlines(), ["10 11", "11 12"])
            self.assertEqual(lcc_path.read_text(encoding="utf-8").splitlines(), ["10 11", "11 12"])


if __name__ == "__main__":
    unittest.main()
