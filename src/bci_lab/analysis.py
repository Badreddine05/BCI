"""Corrected, reusable versions of the notebook's exploratory algorithms.

These utilities are tested independently; they are not additional tuned models
in the fixed three-model motor-imagery benchmark.
"""
import numpy as np
from scipy.fft import idct
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import linprog
from scipy.special import logsumexp
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_is_fitted


class RegularizedQDA(ClassifierMixin, BaseEstimator):
    """Gaussian discriminant classifier with stable log probabilities.

    Return the original labels, including strings/nonconsecutive integers.
    Covariance shrinkage and a diagonal floor handle singular small samples.
    """
    def __init__(self, regularization=0.1, variance_floor=1e-8):
        self.regularization = regularization
        self.variance_floor = variance_floor

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y)
        if X.ndim != 2 or X.shape[1] == 0 or y.shape != (len(X),) or not np.isfinite(X).all():
            raise ValueError("Expected finite feature rows and one label per row")
        if not 0 <= self.regularization <= 1 or self.variance_floor <= 0:
            raise ValueError("Invalid covariance regularization")
        self.classes_ = np.unique(y)
        if len(self.classes_) < 2:
            raise ValueError("At least two classes are required")
        self.n_features_in_ = X.shape[1]
        self.parameters_ = []
        for label in self.classes_:
            selected = X[y == label]
            if len(selected) < 2:
                raise ValueError("Each class requires two observations")
            covariance = np.atleast_2d(np.cov(selected, rowvar=False, ddof=1))
            scale = max(float(np.trace(covariance) / X.shape[1]), self.variance_floor)
            covariance = (1-self.regularization)*covariance + (self.regularization*scale+self.variance_floor)*np.eye(X.shape[1])
            factor = cho_factor(covariance, lower=True)
            log_determinant = 2*np.log(np.diag(factor[0])).sum()
            self.parameters_.append((selected.mean(axis=0), factor, log_determinant, np.log(len(selected)/len(X))))
        return self

    def _scores(self, X):
        check_is_fitted(self, "parameters_")
        X = np.asarray(X, dtype=float)
        if X.ndim != 2 or X.shape[1] != self.n_features_in_ or not np.isfinite(X).all():
            raise ValueError("Feature dimensions must match the fitted finite input")
        scores = []
        for mean, factor, determinant, prior in self.parameters_:
            centered = X - mean
            distance = np.sum(centered * cho_solve(factor, centered.T).T, axis=1)
            scores.append(prior - 0.5*(determinant + distance + self.n_features_in_*np.log(2*np.pi)))
        return np.stack(scores, axis=1)

    def predict(self, X):
        scores = self._scores(X)
        return self.classes_[np.argmax(scores, axis=1)]

    def predict_proba(self, X):
        scores = self._scores(X)
        return np.exp(scores - logsumexp(scores, axis=1, keepdims=True))


def sliding_correlations(signals, window, step):
    """Return complete-window Pearson matrices and center sample indices.

    Undefined correlations involving a constant channel remain NaN. They must
    be displayed as unavailable, never as evidence of zero connectivity.
    """
    values = np.asarray(signals, dtype=float)
    if values.ndim != 2 or values.shape[0] < 2 or not np.isfinite(values).all():
        raise ValueError("Expected finite [channels, time] signals")
    if isinstance(window, bool) or isinstance(step, bool) or not isinstance(window, int) or not isinstance(step, int):
        raise ValueError("Window and step must be integers")
    if not 2 <= window <= values.shape[1] or step < 1:
        raise ValueError("Invalid correlation window or step")
    starts = np.arange(0, values.shape[1]-window+1, step)
    matrices = []
    for start in starts:
        section = values[:, start:start+window]
        centered = section - section.mean(axis=1, keepdims=True)
        cross = centered @ centered.T
        norm = np.sqrt(np.diag(cross))
        denominator = norm[:, None]*norm[None, :]
        correlation = np.full(cross.shape, np.nan)
        np.divide(cross, denominator, out=correlation, where=denominator > 0)
        matrices.append(np.clip(correlation, -1, 1))
    return starts + (window-1)/2, np.stack(matrices)


def reconstruct_sparse_dct(length, indices, measurements):
    """Basis pursuit on a DCT basis; useful for controlled synthetic experiments.

    Sparsity is an assumption, not an assurance that EEG can be reconstructed
    from any fraction of its samples. No raw dataset is redistributed.
    """
    if isinstance(length, bool) or not isinstance(length, int) or not 2 <= length <= 2048:
        raise ValueError("Reconstruction length must be an integer from 2 to 2048")
    positions = np.asarray(indices)
    samples = np.asarray(measurements, dtype=float)
    if positions.ndim != 1 or positions.dtype.kind not in "iu" or len(positions) < 1:
        raise ValueError("Provide integer sampling positions")
    if len(np.unique(positions)) != len(positions) or np.any(positions < 0) or np.any(positions >= length):
        raise ValueError("Sampling positions must be unique and inside the signal")
    if samples.shape != positions.shape or not np.isfinite(samples).all():
        raise ValueError("Provide one finite measurement per position")
    basis = idct(np.eye(length), norm="ortho", axis=0)
    observed = basis[positions]
    result = linprog(np.ones(2*length), A_eq=np.concatenate([observed, -observed], axis=1), b_eq=samples, bounds=(0, None), method="highs")
    if not result.success:
        raise RuntimeError(f"DCT reconstruction failed: {result.message}")
    coefficients = result.x[:length] - result.x[length:]
    reconstruction = basis @ coefficients
    if not np.allclose(reconstruction[positions], samples, rtol=1e-5, atol=1e-7):
        raise RuntimeError("Reconstruction violates the measurement constraints")
    return reconstruction
