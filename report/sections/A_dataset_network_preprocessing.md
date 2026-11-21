# Dataset, network definition, and preprocessing

The analysis uses SNAP's `ca-GrQc` General Relativity collaboration network. Each node is an author identifier and an undirected edge indicates that two authors co-authored at least one paper in the arXiv General Relativity category. The supplied edge list contains integer author IDs and may list a collaboration in both directions; no author-name mapping is included, so results refer to IDs rather than inferred names.

The network is treated as unweighted and undirected. Self-loops are excluded and repeated or reciprocal edge rows are collapsed by constructing a simple NetworkX graph. Both the full graph and its largest connected component (LCC) are retained as edge lists under `data/processed/`. The full graph is used for whole-network structural summaries and the LCC for analyses that require connectivity, including path length, diameter, centrality comparisons, community detection, and the model comparison. `tables/A/structural_metrics.csv` and `report/sections/A_summary.md` report the measured size of the LCC and the nodes and edges omitted by restricting the analysis to it.

Dataset source: [Stanford Large Network Dataset Collection, ca-GrQc](https://snap.stanford.edu/data/ca-GrQc.html).
