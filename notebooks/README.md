# Notebooks

Jupyter notebooks documenting the full ML pipeline — from raw data exploration through model
evaluation. Each notebook imports directly from the project's detection modules and runs against
the real dataset.

## Notebook Index

| # | Notebook | Description |
|---|----------|-------------|
| 01 | [EDA & Dataset](01_eda_and_dataset.ipynb) | Dataset quality, class distribution, missing-field analysis |
| 02 | [Feature Engineering](02_feature_engineering.ipynb) | Metadata, AST, and obfuscation feature extraction demos |
| 03 | [Embedding Clustering](03_embedding_clustering.ipynb) | t-SNE visualization of benign vs malicious in embedding space |
| 04 | [Model Training](04_model_training.ipynb) | XGBoost classifier training with imbalance handling, ROC curves |
| 05 | [Evaluation & Ablation](05_evaluation_ablation.ipynb) | Ablation study, false-positive analysis, weight sensitivity |
| 06 | [Graph Visualization](06_layer5_graph_visualization.ipynb) | Dependency graph + risk propagation visualization |

## Prerequisites

```bash
pip install pandas matplotlib scikit-learn xgboost sentence-transformers faiss-cpu scipy
```

For fast notebook execution, pre-compute the data cache first:

```bash
python notebooks/precompute_cache.py
```

Run from the `notebooks/` directory or the project root.
