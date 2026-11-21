"""Load and preprocess the SNAP ca-GrQc collaboration network."""

from __future__ import annotations

import argparse
from pathlib import Path

import networkx as nx


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "CA-GrQc.txt"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"


def load_graphs(input_path: Path) -> tuple[nx.Graph, nx.Graph, dict[str, int]]:
    """Read the edge list as a simple undirected graph and return its LCC."""
    graph = nx.Graph()
    input_rows = 0
    self_loops = 0

    with input_path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            endpoints = stripped.split()
            if len(endpoints) != 2:
                raise ValueError(
                    f"Expected two node IDs at {input_path}:{line_number}, "
                    f"found {len(endpoints)}."
                )
            try:
                left, right = map(int, endpoints)
            except ValueError as error:
                raise ValueError(
                    f"Invalid integer node ID at {input_path}:{line_number}."
                ) from error
            input_rows += 1
            graph.add_nodes_from((left, right))
            if left == right:
                self_loops += 1
                continue
            graph.add_edge(left, right)

    if graph.number_of_nodes() == 0:
        raise ValueError(f"No non-self-loop edges found in {input_path}.")

    components = list(nx.connected_components(graph))
    lcc_nodes = min(components, key=lambda nodes: (-len(nodes), min(nodes)))
    lcc = graph.subgraph(lcc_nodes).copy()
    stats = {
        "input_rows": input_rows,
        "self_loops_removed": self_loops,
        "duplicate_or_reciprocal_rows_removed": (
            input_rows - self_loops - graph.number_of_edges()
        ),
    }
    return graph, lcc, stats


def save_graphs(
    graph: nx.Graph, lcc: nx.Graph, output_dir: Path
) -> tuple[Path, Path]:
    """Write stable, header-free edge lists for the full graph and its LCC."""
    output_dir.mkdir(parents=True, exist_ok=True)
    full_path = output_dir / "grqc_full.edgelist"
    lcc_path = output_dir / "grqc_lcc.edgelist"
    nx.write_edgelist(graph, full_path, data=False)
    nx.write_edgelist(lcc, lcc_path, data=False)
    return full_path, lcc_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    graph, lcc, stats = load_graphs(args.input)
    full_path, lcc_path = save_graphs(graph, lcc, args.output_dir)
    print(
        f"Read {stats['input_rows']:,} edge rows; removed "
        f"{stats['self_loops_removed']:,} self-loops and "
        f"{stats['duplicate_or_reciprocal_rows_removed']:,} duplicate/"
        "reciprocal rows."
    )
    print(
        f"Full graph: {graph.number_of_nodes():,} nodes, "
        f"{graph.number_of_edges():,} edges -> {full_path}"
    )
    print(
        f"LCC: {lcc.number_of_nodes():,} nodes, {lcc.number_of_edges():,} "
        f"edges -> {lcc_path}"
    )


if __name__ == "__main__":
    main()
