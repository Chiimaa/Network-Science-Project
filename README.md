# ca-GrQc Collaboration Network

## Research question

How robust is the GR-QC collaboration network to losing its most connected authors, and do hubs and degree correlations explain that robustness?

## Team

- Person A: Ilyes REZGUI
- Person B: Chaima Mehemmed

## Dataset

This project uses SNAP's ca-GrQc arXiv General Relativity co-authorship network. The supplied edge list is under `data/raw/`; nodes are author IDs and undirected edges represent co-authorship. The source and preprocessing decisions are documented in `report/sections/A_dataset_network_preprocessing.md`.

## Project structure

- `data/raw/`: source edge list
- `data/processed/`: cleaned full-graph and LCC edge lists
- `src/`: data loader and analysis scripts
- `notebooks/A_network_analysis.ipynb`: Person A analysis runner and output viewer
- `figures/A/`: Person A figures
- `tables/A/`: Person A CSV results
- `report/sections/`: Person A report sections; Person B and shared sections are to be added

## Reproduce Person A's analysis

From the project root, install the dependencies and run:

```powershell
python -m pip install -r requirements.txt
python src\analyze_person_a.py
```

The analysis uses seed 42 and three ER and WS realizations by default. It writes processed edge lists, CSV tables, figures, and `report/sections/A_summary.md`. To run the focused loader tests:

```powershell
python -m unittest discover -s tests -v
```

`src/load_data.py` can also be run on its own to build the full and LCC edge lists.

