# Methodology

All graph construction and analysis use NetworkX. The data loader ignores comment lines, validates that every data row contains two integer IDs, removes self-loops, and relies on an undirected simple graph to collapse duplicate and reciprocal rows. The analysis uses a fixed random seed (42 by default).

For both the full graph and LCC, the workflow reports node and edge counts, density, average degree, clustering, transitivity, and the connected-component size distribution. Degree frequencies are tabulated and plotted on linear and log-log axes for both graph versions. Average shortest-path length and diameter are computed exactly on the connected LCC only; they are undefined for a disconnected graph as a whole.

Centralities are computed on the LCC: degree, closeness, PageRank, and normalized betweenness estimaAted from 500 sampled source nodes. The top ten authors for each measure are exported, and Spearman correlations are computed over the full LCC rankings. The node identifiers are retained because the source file does not provide author names.

Communities are detected on the LCC with Louvain and greedy modularity. For each method, the workflow reports modularity, community sizes, mean degree, and the five highest-degree author IDs per community. The one-hop ego network of the three highest-degree LCC authors is visualized with spring and Kamada-Kawai layouts; node size reflects degree, labels mark the three hubs, and node color reflects Louvain assignment.
