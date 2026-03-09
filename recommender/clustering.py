"""
K-Means Clustering — Groups songs into mood clusters to optimize recommendation search.
"""

import numpy as np
from sklearn.cluster import KMeans
from config import N_CLUSTERS


class SongClusterer:
    def __init__(self):
        self._model = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init="auto")
        self._fitted = False

    def fit(self, feature_matrix: np.ndarray):
        """Fit K-Means on a 2D array of shape (n_songs, n_features)."""
        self._model.fit(feature_matrix)
        self._fitted = True

    def predict_cluster(self, feature_vector: np.ndarray) -> int:
        """Return cluster ID for a given feature vector."""
        if not self._fitted:
            raise RuntimeError("Clusterer is not fitted. Call fit() first.")
        return int(self._model.predict([feature_vector])[0])

    def get_cluster_indices(self, cluster_id: int) -> np.ndarray:
        """Return indices of all songs belonging to a cluster."""
        if not self._fitted:
            raise RuntimeError("Clusterer is not fitted. Call fit() first.")
        return np.where(self._model.labels_ == cluster_id)[0]
