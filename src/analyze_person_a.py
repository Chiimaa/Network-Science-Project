"""Run Person A's structural, community, and small-world analyses."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from statistics import mean, stdev

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from load_data import DEFAULT_INPUT, load_graphs, save_graphs


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE_DIR = PROJECT_ROOT / "tables" / "A"
DEFAULT_FIGURE_DIR = PROJECT_ROOT / "figures" / "A"
DEFAULT_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SEED = 42
BETWEENNESS_SAMPLES = 500
MODEL_REPEATS = 3


def graph_metrics(graph: nx.Graph) -> dict[str, float | int | str]:
    """Return structural metrics, computing path metrics only for connected graphs."""
    component_sizes = [len(component) for component in nx.connected_components(graph)]
    connected = len(component_sizes) == 1
    metrics: dict[str, float | int | str] = {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "average_degree": 2 * graph.number_of_edges() / graph.number_of_nodes(),
        "components": len(component_sizes),
        "lcc_nodes": max(component_sizes),
        "lcc_fraction": max(component_sizes) / graph.number_of_nodes(),
        "average_clustering": nx.average_clustering(graph),
        "transitivity": nx.transitivity(graph),
        "average_path_length": (
            nx.average_shortest_path_length(graph) if connected else math.nan
        ),
        "diameter": nx.diameter(graph) if connected else math.nan,
    }
    return metrics


def write_degree_outputs(
    full: nx.Graph, lcc: nx.Graph, table_dir: Path, figure_dir: Path
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    rows = []
    for label, graph, color in (
        ("full", full, "#4472C4"),
        ("lcc", lcc, "#ED7D31"),
    ):
        counts: dict[int, int] = {}
        for _, degree in graph.degree():
            counts[degree] = counts.get(degree, 0) + 1
        distribution = pd.DataFrame(
            [
                {
                    "graph": label,
                    "degree": degree,
                    "node_count": count,
                    "probability": count / graph.number_of_nodes(),
                }
                for degree, count in sorted(counts.items())
            ]
        )
        rows.extend(distribution.to_dict("records"))
        axes[0].plot(
            distribution["degree"],
            distribution["node_count"],
            marker="o",
            markersize=3,
            linewidth=1,
            color=color,
            label=label.upper(),
        )
        positive = distribution[distribution["degree"] > 0]
        axes[1].scatter(
            positive["degree"],
            positive["probability"],
            s=18,
            alpha=0.7,
            color=color,
            label=label.upper(),
        )
    pd.DataFrame(rows).to_csv(table_dir / "degree_distribution.csv", index=False)
    axes[0].set(xlabel="Degree", ylabel="Number of authors", title="Degree distribution")
    axes[0].legend()
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set(
        xlabel="Degree (log scale)",
        ylabel="Probability (log scale)",
        title="Degree distribution (log-log)",
    )
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "A_degree_distribution.png", dpi=300)
    plt.close(fig)


def write_component_outputs(graph: nx.Graph, table_dir: Path) -> None:
    component_sizes = sorted(
        (len(component) for component in nx.connected_components(graph)),
        reverse=True,
    )
    counts: dict[int, int] = {}
    for size in component_sizes:
        counts[size] = counts.get(size, 0) + 1
    pd.DataFrame(
        [
            {"component_size": size, "component_count": count}
            for size, count in sorted(counts.items(), reverse=True)
        ]
    ).to_csv(table_dir / "component_size_distribution.csv", index=False)


def centrality_outputs(
    graph: nx.Graph, table_dir: Path, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sample_count = min(BETWEENNESS_SAMPLES, graph.number_of_nodes())
    values = {
        "degree": dict(graph.degree()),
        "betweenness_approx": nx.betweenness_centrality(
            graph, k=sample_count, normalized=True, seed=seed
        ),
        "closeness": nx.closeness_centrality(graph),
        "pagerank": nx.pagerank(graph, alpha=0.85),
    }
    scores = pd.DataFrame(values).rename_axis("author_id")
    ranks = scores.rank(method="min", ascending=False).astype(int)
    rows = []
    for measure in scores.columns:
        top = scores[measure].nlargest(10)
        for position, (node, score) in enumerate(top.items(), start=1):
            rows.append(
                {
                    "measure": measure,
                    "rank": position,
                    "author_id": node,
                    "score": score,
                    "degree": int(scores.at[node, "degree"]),
                }
            )
    top_authors = pd.DataFrame(rows)
    top_authors.to_csv(table_dir / "centrality_top10.csv", index=False)
    ranks.corr(method="spearman").to_csv(table_dir / "centrality_spearman.csv")
    return scores, ranks


def detect_communities(
    graph: nx.Graph, table_dir: Path, seed: int
) -> tuple[dict[str, dict[int, int]], dict[str, float]]:
    partitions = {
        "louvain": nx.community.louvain_communities(graph, seed=seed),
        "greedy_modularity": list(nx.community.greedy_modularity_communities(graph)),
    }
    assignments: dict[str, dict[int, int]] = {}
    modularities: dict[str, float] = {}
    rows = []
    for algorithm, communities in partitions.items():
        modularities[algorithm] = nx.community.modularity(graph, communities)
        assignments[algorithm] = {
            node: community_id
            for community_id, community in enumerate(
                sorted(communities, key=lambda nodes: (-len(nodes), min(nodes)))
            )
            for node in community
        }
        for community_id, community in enumerate(
            sorted(communities, key=lambda nodes: (-len(nodes), min(nodes)))
        ):
            ranked_nodes = sorted(
                community, key=lambda node: (-graph.degree(node), node)
            )
            rows.append(
                {
                    "algorithm": algorithm,
                    "community_id": community_id,
                    "size": len(community),
                    "modularity": modularities[algorithm],
                    "mean_degree": mean(graph.degree(node) for node in community),
                    "top_degree_authors": ";".join(
                        str(node) for node in ranked_nodes[:5]
                    ),
                }
            )
    pd.DataFrame(rows).to_csv(table_dir / "community_size_distribution.csv", index=False)
    return assignments, modularities


def draw_hub_subgraph(
    graph: nx.Graph,
    community_ids: dict[int, int],
    figure_dir: Path,
    seed: int,
) -> None:
    hubs = [
        node
        for node, _ in sorted(graph.degree, key=lambda item: (-item[1], item[0]))[:3]
    ]
    selected = set(hubs)
    for hub in hubs:
        selected.update(graph.neighbors(hub))
    subgraph = graph.subgraph(selected).copy()
    palette = plt.get_cmap("tab20")
    colors = [palette(community_ids[node] % 20) for node in subgraph]
    sizes = [22 + min(graph.degree(node), 80) * 2.5 for node in subgraph]
    top_labels = {node: str(node) for node in hubs}
    layouts = {
        "spring": nx.spring_layout(subgraph, seed=seed, iterations=75),
        "kamada_kawai": nx.kamada_kawai_layout(subgraph),
    }
    for name, positions in layouts.items():
        fig, axis = plt.subplots(figsize=(10, 8))
        nx.draw_networkx_edges(subgraph, positions, ax=axis, alpha=0.2, width=0.5)
        nx.draw_networkx_nodes(
            subgraph, positions, ax=axis, node_color=colors, node_size=sizes, linewidths=0
        )
        nx.draw_networkx_labels(
            subgraph,
            positions,
            labels=top_labels,
            ax=axis,
            font_size=8,
            font_color="black",
        )
        axis.set_title(
            f"One-hop ego network of top 3 hubs ({len(subgraph)} nodes): {name}"
        )
        axis.set_axis_off()
        fig.tight_layout()
        fig.savefig(figure_dir / f"A_top_hubs_{name}.png", dpi=300)
        plt.close(fig)


def model_metrics(graph: nx.Graph) -> tuple[float, float, int]:
    component = max(nx.connected_components(graph), key=len)
    giant_component = graph.subgraph(component)
    return (
        nx.average_clustering(graph),
        nx.average_shortest_path_length(giant_component),
        len(component),
    )


def compare_models(
    lcc: nx.Graph, table_dir: Path, seed: int, repeats: int
) -> dict[str, float]:
    node_count = lcc.number_of_nodes()
    edge_count = lcc.number_of_edges()
    average_degree = 2 * edge_count / node_count
    ws_k = min(node_count - 1, max(2, round(average_degree)))
    if ws_k % 2:
        ws_k += 1 if ws_k + 1 < node_count else -1

    real_clustering = nx.average_clustering(lcc)
    real_path_length = nx.average_shortest_path_length(lcc)
    records: dict[str, list[tuple[float, float, int, int]]] = {
        "erdos_renyi": [],
        "watts_strogatz": [],
    }
    for repeat in range(repeats):
        er = nx.gnm_random_graph(node_count, edge_count, seed=seed + repeat)
        ws = nx.watts_strogatz_graph(
            node_count, ws_k, 0.1, seed=seed + 10_000 + repeat
        )
        for name, model in (("erdos_renyi", er), ("watts_strogatz", ws)):
            clustering, path_length, giant_size = model_metrics(model)
            records[name].append(
                (clustering, path_length, giant_size, model.number_of_edges())
            )

    rows = [
        {
            "model": "empirical_lcc",
            "nodes": node_count,
            "edges_mean": edge_count,
            "ws_k": "",
            "clustering_mean": real_clustering,
            "clustering_sd": 0.0,
            "path_length_lcc_mean": real_path_length,
            "path_length_lcc_sd": 0.0,
            "giant_component_fraction_mean": 1.0,
        }
    ]
    averages = {}
    for name, results in records.items():
        clustering_values = [result[0] for result in results]
        path_values = [result[1] for result in results]
        giant_fractions = [result[2] / node_count for result in results]
        edge_values = [result[3] for result in results]
        averages[name] = (
            mean(clustering_values),
            mean(path_values),
        )
        rows.append(
            {
                "model": name,
                "nodes": node_count,
                "edges_mean": mean(edge_values),
                "ws_k": ws_k if name == "watts_strogatz" else "",
                "clustering_mean": mean(clustering_values),
                "clustering_sd": stdev(clustering_values) if repeats > 1 else 0.0,
                "path_length_lcc_mean": mean(path_values),
                "path_length_lcc_sd": stdev(path_values) if repeats > 1 else 0.0,
                "giant_component_fraction_mean": mean(giant_fractions),
            }
        )
    er_clustering, er_path_length = averages["erdos_renyi"]
    sigma = (real_clustering / er_clustering) / (
        real_path_length / er_path_length
    )
    rows[0]["small_world_sigma_vs_er"] = sigma
    pd.DataFrame(rows).to_csv(table_dir / "small_world_model_comparison.csv", index=False)
    return {
        "sigma": sigma,
        "ws_k": ws_k,
        "er_clustering": er_clustering,
        "er_path_length": er_path_length,
        "ws_clustering": averages["watts_strogatz"][0],
        "ws_path_length": averages["watts_strogatz"][1],
    }


def plot_model_comparison(
    table_dir: Path, figure_dir: Path
) -> None:
    models = pd.read_csv(table_dir / "small_world_model_comparison.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    labels = models["model"].str.replace("_", " ")
    axes[0].bar(labels, models["clustering_mean"], color="#4472C4")
    axes[0].set_ylabel("Average clustering")
    axes[0].tick_params(axis="x", rotation=20)
    axes[1].bar(labels, models["path_length_lcc_mean"], color="#70AD47")
    axes[1].set_ylabel("Average shortest-path length (model LCC)")
    axes[1].tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(figure_dir / "A_small_world_model_comparison.png", dpi=300)
    plt.close(fig)


def write_summary(
    full_metrics: dict[str, float | int | str],
    lcc_metrics: dict[str, float | int | str],
    stats: dict[str, int],
    modularities: dict[str, float],
    model_results: dict[str, float],
    table_dir: Path,
    output_path: Path,
) -> None:
    top = pd.read_csv(table_dir / "centrality_top10.csv")
    degree_top = top[(top["measure"] == "degree")].head(5)
    communities = pd.read_csv(table_dir / "community_size_distribution.csv")
    largest_communities = communities.groupby("algorithm", sort=False).first()
    community_counts = communities.groupby("algorithm").size()
    lines = [
        "# Person A analysis summary",
        "",
        "## Data and preprocessing",
        "",
        f"- Input edge rows: {stats['input_rows']:,}.",
        f"- Self-loops removed: {stats['self_loops_removed']:,}.",
        f"- Duplicate/reciprocal rows collapsed: "
        f"{stats['duplicate_or_reciprocal_rows_removed']:,}.",
        "- The graph is treated as an undirected, unweighted simple graph.",
        f"- Restricting to the LCC excludes "
        f"{int(full_metrics['nodes']) - int(lcc_metrics['nodes']):,} nodes and "
        f"{int(full_metrics['edges']) - int(lcc_metrics['edges']):,} edges "
        f"({1 - float(full_metrics['lcc_fraction']):.1%} of full-graph nodes).",
        "",
        "## Structural metrics",
        "",
        "| Graph | Nodes | Edges | Density | Average degree | Components | LCC fraction | "
        "Average clustering | Transitivity | Average path length | Diameter |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, metrics in (("Full", full_metrics), ("LCC", lcc_metrics)):
        path_length = (
            f"{metrics['average_path_length']:.4f}"
            if not math.isnan(float(metrics["average_path_length"]))
            else "not defined"
        )
        diameter = (
            str(metrics["diameter"])
            if not math.isnan(float(metrics["diameter"]))
            else "not defined"
        )
        lines.append(
            f"| {label} | {metrics['nodes']:,} | {metrics['edges']:,} | "
            f"{metrics['density']:.6g} | {metrics['average_degree']:.3f} | "
            f"{metrics['components']:,} | {metrics['lcc_fraction']:.3f} | "
            f"{metrics['average_clustering']:.4f} | {metrics['transitivity']:.4f} | "
            f"{path_length} | {diameter} |"
        )
    lines.extend(
        [
            "",
            "The full graph is disconnected, so its global average path length and "
            "diameter are undefined; these are reported only for the LCC.",
            "",
            "## Centrality and communities",
            "",
            "Top five authors by degree:",
            "",
            "| Rank | Author ID | Degree |",
            "|---:|---:|---:|",
        ]
    )
    for _, row in degree_top.iterrows():
        lines.append(
            f"| {int(row['rank'])} | {int(row['author_id'])} | {int(row['degree'])} |"
        )
    lines.extend(
        [
            "",
            "| Community method | Communities | Modularity | Largest community size | "
            "Top-degree authors in largest community |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for algorithm in modularities:
        lines.append(
            f"| {algorithm} | {community_counts[algorithm]:,} | "
            f"{modularities[algorithm]:.4f} | "
            f"{int(largest_communities.loc[algorithm, 'size']):,} | "
            f"{largest_communities.loc[algorithm, 'top_degree_authors']} |"
        )
    rank_correlations = pd.read_csv(
        table_dir / "centrality_spearman.csv", index_col=0
    )
    lines.extend(
        [
            "",
            f"Degree and PageRank rankings are strongly aligned "
            f"(Spearman rho = {rank_correlations.loc['degree', 'pagerank']:.3f}); "
            f"degree and closeness align less closely "
            f"(rho = {rank_correlations.loc['degree', 'closeness']:.3f}). "
            "This is consistent with local connectivity and shortest-path position "
            "capturing different aspects of author importance.",
            "",
            f"Louvain returns {community_counts['louvain']} communities with a largest "
            f"community of {int(largest_communities.loc['louvain', 'size'])} authors; "
            f"greedy modularity returns {community_counts['greedy_modularity']} "
            f"communities, but its largest has "
            f"{int(largest_communities.loc['greedy_modularity', 'size'])} authors. "
            "Louvain has the higher modularity, while the larger greedy community "
            "illustrates that the partition depends on the detection method.",
            "",
            "In the Louvain partition, the five highest-degree authors occur together "
            "in one community, while the largest community is led by a different set "
            "of hubs.",
        ]
    )
    lines.extend(
        [
            "",
            "Centrality rankings and rank correlations are in "
            "`tables/A/centrality_top10.csv` and "
            "`tables/A/centrality_spearman.csv`. Community sizes and the leading "
            "authors of each community are in `tables/A/community_size_distribution.csv`.",
            "",
            "## Small-world comparison",
            "",
            f"- Watts–Strogatz matched degree parameter: k = {int(model_results['ws_k'])}.",
            f"- Small-world coefficient sigma (empirical LCC vs. ER): "
            f"{model_results['sigma']:.3f}.",
            f"- ER mean clustering/path length: "
            f"{model_results['er_clustering']:.4f} / "
            f"{model_results['er_path_length']:.4f}.",
            f"- WS mean clustering/path length: "
            f"{model_results['ws_clustering']:.4f} / "
            f"{model_results['ws_path_length']:.4f}.",
            "",
            "Model means and standard deviations are in "
            "`tables/A/small_world_model_comparison.csv`; visual outputs are in "
            "`figures/A/`.",
            "",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run_analysis(
    input_path: Path,
    processed_dir: Path,
    table_dir: Path,
    figure_dir: Path,
    seed: int = SEED,
    repeats: int = MODEL_REPEATS,
) -> None:
    for directory in (processed_dir, table_dir, figure_dir):
        directory.mkdir(parents=True, exist_ok=True)
    full, lcc, stats = load_graphs(input_path)
    save_graphs(full, lcc, processed_dir)

    full_metrics = graph_metrics(full)
    lcc_metrics = graph_metrics(lcc)
    pd.DataFrame(
        [{"graph": "full", **full_metrics}, {"graph": "lcc", **lcc_metrics}]
    ).to_csv(table_dir / "structural_metrics.csv", index=False)
    write_degree_outputs(full, lcc, table_dir, figure_dir)
    write_component_outputs(full, table_dir)

    centrality_scores, _ = centrality_outputs(lcc, table_dir, seed)
    community_assignments, modularities = detect_communities(lcc, table_dir, seed)
    draw_hub_subgraph(
        lcc, community_assignments["louvain"], figure_dir, seed
    )
    model_results = compare_models(lcc, table_dir, seed, repeats)
    plot_model_comparison(table_dir, figure_dir)
    write_summary(
        full_metrics,
        lcc_metrics,
        stats,
        modularities,
        model_results,
        table_dir,
        PROJECT_ROOT / "report" / "sections" / "A_summary.md",
    )
    print(
        f"Person A analysis complete: {len(centrality_scores):,} authors ranked; "
        f"outputs saved to {table_dir}, {figure_dir}, and report/sections/A_summary.md."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED_DIR)
    parser.add_argument("--table-dir", type=Path, default=DEFAULT_TABLE_DIR)
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--model-repeats", type=int, default=MODEL_REPEATS)
    args = parser.parse_args()
    if args.model_repeats < 1:
        parser.error("--model-repeats must be at least 1")
    run_analysis(
        args.input,
        args.processed_dir,
        args.table_dir,
        args.figure_dir,
        args.seed,
        args.model_repeats,
    )


if __name__ == "__main__":
    main()
