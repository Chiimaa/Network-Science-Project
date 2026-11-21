# Person A analysis summary

## Data and preprocessing

- Input edge rows: 28,980.
- Self-loops removed: 12.
- Duplicate/reciprocal rows collapsed: 14,484.
- The graph is treated as an undirected, unweighted simple graph.
- Restricting to the LCC excludes 1,084 nodes and 1,062 edges (20.7% of full-graph nodes).

## Structural metrics

| Graph | Nodes | Edges | Density | Average degree | Components | LCC fraction | Average clustering | Transitivity | Average path length | Diameter |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Full | 5,242 | 14,484 | 0.0010544 | 5.526 | 355 | 0.793 | 0.5296 | 0.6298 | not defined | not defined |
| LCC | 4,158 | 13,422 | 0.00155304 | 6.456 | 1 | 1.000 | 0.5569 | 0.6289 | 6.0494 | 17.0 |

The full graph is disconnected, so its global average path length and diameter are undefined; these are reported only for the LCC.

## Centrality and communities

Top five authors by degree:

| Rank | Author ID | Degree |
|---:|---:|---:|
| 1 | 21012 | 81 |
| 2 | 21281 | 79 |
| 3 | 22691 | 77 |
| 4 | 12365 | 77 |
| 5 | 6610 | 68 |

| Community method | Communities | Modularity | Largest community size | Top-degree authors in largest community |
|---|---:|---:|---:|---|
| greedy_modularity | 62 | 0.7993 | 930 | 15244;13801;13929;9572;2710 |
| louvain | 40 | 0.8480 | 275 | 9572;7689;10762;7007;10711 |

Degree and PageRank rankings are strongly aligned (Spearman rho = 0.913); degree and closeness align less closely (rho = 0.498). This is consistent with local connectivity and shortest-path position capturing different aspects of author importance.

Louvain returns 40 communities with a largest community of 275 authors; greedy modularity returns 62 communities, but its largest has 930 authors. Louvain has the higher modularity, while the larger greedy community illustrates that the partition depends on the detection method.

In the Louvain partition, the five highest-degree authors occur together in one community, while the largest community is led by a different set of hubs.

Centrality rankings and rank correlations are in `tables/A/centrality_top10.csv` and `tables/A/centrality_spearman.csv`. Community sizes and the leading authors of each community are in `tables/A/community_size_distribution.csv`.

## Small-world comparison

- Watts–Strogatz matched degree parameter: k = 6.
- Small-world coefficient sigma (empirical LCC vs. ER): 279.285.
- ER mean clustering/path length: 0.0015 / 4.6782.
- WS mean clustering/path length: 0.4378 / 7.6231.

Model means and standard deviations are in `tables/A/small_world_model_comparison.csv`; visual outputs are in `figures/A/`.
