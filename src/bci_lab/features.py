"""Deterministic offline filtering and fitted spatial features."""
import numpy as np
from scipy.linalg import eigh
from scipy.signal import butter, sosfiltfilt, welch
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted


def validate_epochs(samples):
    values = np.asarray(samples, dtype=float)
    if values.ndim != 3 or min(values.shape) < 1 or values.shape[2] < 64:
        raise ValueError("Expected nonempty [trials, channels, time] arrays with at least 64 samples")
    if not np.isfinite(values).all():
        raise ValueError("EEG data must be finite")
    return values


def bandpass(samples, sampling_rate=250, low=8.0, high=30.0):
    """Zero-phase Butterworth filtering per trial; this is an OFFLINE transform."""
    values = validate_epochs(samples)
    if not 0 < low < high < sampling_rate / 2:
        raise ValueError("Band must fall strictly inside the Nyquist interval")
    sos = butter(4, [low, high], btype="bandpass", fs=sampling_rate, output="sos")
    return sosfiltfilt(sos, values, axis=-1)


class LogBandPower(TransformerMixin, BaseEstimator):
    """Log absolute mu and beta power, estimated with Welch per EEG channel."""
    def __init__(self, sampling_rate=250, bands=((8.0, 12.0), (13.0, 30.0))):
        self.sampling_rate = sampling_rate
        self.bands = bands

    def fit(self, X, y=None):
        self.n_channels_in_ = validate_epochs(X).shape[1]
        return self

    def transform(self, X):
        check_is_fitted(self, "n_channels_in_")
        values = validate_epochs(X)
        if values.shape[1] != self.n_channels_in_:
            raise ValueError("EEG channel count changed after fitting")
        frequency, power = welch(values, fs=self.sampling_rate, nperseg=min(250, values.shape[-1]), axis=-1)
        features = []
        for low, high in self.bands:
            if not 0 <= low < high < self.sampling_rate / 2:
                raise ValueError("Invalid frequency band")
            selection = (frequency >= low) & (frequency <= high)
            if selection.sum() < 2:
                raise ValueError("Frequency resolution too low for this band")
            energy = np.trapezoid(power[..., selection], frequency[selection], axis=-1)
            features.append(np.log(np.maximum(energy, np.finfo(float).tiny)))
        return np.concatenate(features, axis=1)


class SpatialCSP(TransformerMixin, BaseEstimator):
    """Regularized one-versus-rest CSP, learnt only inside the training pipeline.

    Two spatial filters per class (opposite eigenvalue extremes). Their signs
    are fixed for deterministic output; log-variance is sign-invariant.
    """
    def __init__(self, regularization=0.1):
        self.regularization = regularization

    def fit(self, X, y):
        values = validate_epochs(X)
        labels = np.asarray(y)
        classes = np.unique(labels)
        if labels.shape != (len(values),) or len(classes) < 2 or values.shape[1] < 2:
            raise ValueError("CSP needs matching labels, two classes and two channels")
        if not 0 < self.regularization < 1:
            raise ValueError("CSP regularization must lie between zero and one")
        centered = values - values.mean(axis=-1, keepdims=True)
        covariance = centered @ centered.transpose(0, 2, 1)
        traces = np.trace(covariance, axis1=1, axis2=2)
        if np.any(traces <= np.finfo(float).tiny):
            raise ValueError("CSP cannot fit zero-variance trials")
        covariance /= traces[:, None, None]
        channels = values.shape[1]
        shrink = lambda matrix: (1-self.regularization)*matrix + self.regularization*np.eye(channels)/channels
        filters = []
        for label in classes:
            positive = shrink(covariance[labels == label].mean(axis=0))
            negative = shrink(covariance[labels != label].mean(axis=0))
            _, vectors = eigh(positive, positive + negative, check_finite=True)
            for index in (0, -1):
                vector = vectors[:, index]
                vector *= 1 if vector[np.argmax(np.abs(vector))] >= 0 else -1
                filters.append(vector)
        self.filters_ = np.stack(filters)
        self.n_channels_in_ = channels
        self.classes_ = classes
        return self

    def transform(self, X):
        check_is_fitted(self, "filters_")
        values = validate_epochs(X)
        if values.shape[1] != self.n_channels_in_:
            raise ValueError("EEG channel count changed after fitting")
        projected = np.einsum("kc,nct->nkt", self.filters_, values)
        variance = np.var(projected, axis=-1)
        return np.log(np.maximum(variance, np.finfo(float).tiny))
