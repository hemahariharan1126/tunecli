"""
K-Means Clustering — Groups songs into mood clusters to optimize recommendation search.
Includes a lightweight NumPy-only fallback for Termux / resource-constrained environments.
"""

import numpy as np
from config import N_CLUSTERS


class _NumPyKMeans:
    """Lightweight, vectorized K-Means fallback when scikit-learn is unavailable."""
    def __init__(self, n_clusters: int, random_state: int = 42, max_iter: int = 50):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.max_iter = max_iter
        self.cluster_centers_ = None
        self.labels_ = None

    def fit(self, X: np.ndarray):
        n_samples = X.shape[0]
        k = min(self.n_clusters, n_samples)
        rng = np.random.RandomState(self.random_state)
        init_idx = rng.choice(n_samples, size=k, replace=False)
        self.cluster_centers_ = X[init_idx].astype(float).copy()

        for _ in range(self.max_iter):
            # Distance from each point to each centroid: (n_samples, k)
            distances = np.linalg.norm(X[:, np.newaxis] - self.cluster_centers_, axis=2)
            labels = np.argmin(distances, axis=1)

            new_centers = np.array([
                X[labels == i].mean(axis=0) if np.any(labels == i) else self.cluster_centers_[i]
                for i in range(k)
            ])

            if np.allclose(self.cluster_centers_, new_centers, atol=1e-4):
                break
            self.cluster_centers_ = new_centers

        self.labels_ = labels
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        distances = np.linalg.norm(X[:, np.newaxis] - self.cluster_centers_, axis=2)
        return np.argmin(distances, axis=1)


class SongClusterer:
    def __init__(self):
        self._model = None
        self._fitted = False

    def fit(self, feature_matrix: np.ndarray):
        """Fit K-Means on a 2D array of shape (n_songs, n_features)."""
        if self._model is None:
            try:
                from sklearn.cluster import KMeans
                self._model = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init="auto")
            except ImportError:
                # Use pure NumPy implementation on Termux / systems without scikit-learn
                self._model = _NumPyKMeans(n_clusters=N_CLUSTERS, random_state=42)

        self._model.fit(feature_matrix)
        self._fitted = True

    def predict_cluster(self, feature_vector: np.ndarray) -> int:
        """Return cluster ID for a given feature vector."""
        if not self._fitted:
            raise RuntimeError("Clusterer is not fitted. Call fit() first.")
        return int(self._model.predict(np.array([feature_vector]))[0])

    def get_cluster_indices(self, cluster_id: int) -> np.ndarray:
        """Return indices of all songs belonging to a cluster."""
        if not self._fitted:
            raise RuntimeError("Clusterer is not fitted. Call fit() first.")
        return np.where(self._model.labels_ == cluster_id)[0]
