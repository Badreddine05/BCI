import numpy as np
import pytest
from scipy.fft import idct
from bci_lab.analysis import RegularizedQDA, sliding_correlations, reconstruct_sparse_dct


def test_qda_preserves_labels_and_avoids_pdf_underflow():
    X = np.array([[-2., -2.], [-1., -1.], [1., 1.], [2., 2.]])
    model = RegularizedQDA().fit(X, ["left", "left", "right", "right"])
    assert model.predict([[-3, -3], [3, 3]]).tolist() == ["left", "right"]
    probability = model.predict_proba([[1000, 1000], [-1000, -1000]])
    assert np.isfinite(probability).all()
    np.testing.assert_allclose(probability.sum(axis=1), [1, 1])


def test_correlations_include_last_complete_window_without_zero_padding():
    signal = np.arange(10, dtype=float)
    centers, matrices = sliding_correlations(np.stack([signal, -signal, np.ones(10)]), 4, 3)
    assert centers.tolist() == [1.5, 4.5, 7.5]
    assert matrices.shape == (3, 3, 3)
    np.testing.assert_allclose(matrices[:, 0, 1], -1)
    assert np.isnan(matrices[:, 2, :]).all()


def test_sparse_reconstruction_preserves_measured_values_and_known_signal():
    coefficients = np.zeros(32)
    coefficients[[0, 3]] = [2, 5]
    signal = idct(coefficients, norm="ortho")
    positions = np.sort(np.random.default_rng(4).choice(32, 22, replace=False))
    result = reconstruct_sparse_dct(32, positions, signal[positions])
    np.testing.assert_allclose(result, signal, atol=1e-7)


def test_reconstruction_rejects_duplicate_sampling_positions():
    with pytest.raises(ValueError, match="unique"):
        reconstruct_sparse_dct(8, [1, 1], [2, 2])
