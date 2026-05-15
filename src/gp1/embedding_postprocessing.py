import numpy as np
from sklearn.decomposition import PCA

def remove_common_components(X, n_components=1, center=True):
    """
    Remove top principal components from embedding matrix.

    Args:
        X: np.ndarray of shape (N, D)
        n_components: number of dominant components to remove
        center: whether to mean-center before PCA

    Returns:
        X_clean: np.ndarray of shape (N, D)
    """
    X_proc = X.copy()

    if center:
        mean = X_proc.mean(axis=0, keepdims=True)
        X_proc = X_proc - mean

    pca = PCA(n_components=n_components)
    pca.fit(X_proc)

    components = pca.components_

    for comp in components:
        X_proc -= (X_proc @ comp[:, None]) * comp[None, :]

    return X_proc
