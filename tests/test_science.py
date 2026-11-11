from dataclasses import replace
from pathlib import Path
import numpy as np
import pytest
from scipy.io import savemat
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline

from bci_lab.data import Epochs, load_session, validate_identity
from bci_lab.features import bandpass, LogBandPower, SpatialCSP
from bci_lab.evaluation import evaluate_pair, aggregate


@pytest.mark.parametrize("rate", [250, 250.0])
def test_loader_crops_from_cue_and_excludes_eog(tmp_path, rate):
    # A 1-based onset at sample 11: [2, 6) seconds starts at index 510.
    recording = np.arange(2000)[:, None] + np.arange(25)[None, :] * 10000
    run = {"X": recording, "trial": [11], "y": [4], "fs": rate, "artifacts": [1]}
    target = tmp_path / "fixture.mat"
    savemat(target, {"data": np.array([run], dtype=object)})
    data = load_session(target, 1, "T")
    assert data.samples.shape == (1, 22, 1000)
    assert data.samples[0, 0, 0] == 510
    assert data.samples[0, -1, -1] == 211509
    assert data.labels.tolist() == [3]
    assert data.flagged_trials == 1
    assert data.sampling_rate == 250


@pytest.mark.parametrize("onset", [0, -1, -499])
def test_loader_rejects_nonpositive_matlab_onsets(tmp_path, onset):
    target = tmp_path / "invalid-onset.mat"
    run = {"X": np.zeros((2000, 25)), "trial": [onset], "y": [1], "fs": 250, "artifacts": [0]}
    savemat(target, {"data": np.array([run], dtype=object)})
    with pytest.raises(ValueError, match="positive 1-based"):
        load_session(target, 1, "T")


def test_loader_rejects_fractional_class_labels(tmp_path):
    target = tmp_path / "invalid.mat"
    run = {"X": np.zeros((2000, 25)), "trial": [1], "y": [1.5], "fs": 250, "artifacts": [0]}
    savemat(target, {"data": np.array([run], dtype=object)})
    with pytest.raises(ValueError, match="integers"):
        load_session(target, 1, "T")


@pytest.mark.parametrize("subject,session", [(0, "T"), (10, "E"), (True, "T"), (1, "other")])
def test_invalid_download_identity_is_rejected(subject, session):
    with pytest.raises(ValueError):
        validate_identity(subject, session)


def test_offline_filter_retains_mu_and_suppresses_mains():
    time = np.arange(1000) / 250
    samples = (np.sin(2*np.pi*10*time)+np.sin(2*np.pi*50*time))[None, None, :]
    filtered = bandpass(samples)[0, 0, 100:-100]
    assert np.corrcoef(filtered, np.sin(2*np.pi*10*time[100:-100]))[0, 1] > 0.99


def test_bandpower_has_physical_frequency_separation():
    time = np.arange(1000)/250
    values = np.stack([np.sin(2*np.pi*10*time), np.sin(2*np.pi*22*time)])[None, :, :]
    features = LogBandPower().fit_transform(values)
    assert features.shape == (1, 4)
    assert features[0, 0] > features[0, 1] + 10
    assert features[0, 3] > features[0, 2] + 10


def test_csp_learns_spatial_variance_on_training_only():
    rng = np.random.default_rng(42)
    labels = np.tile([0, 1], 80)
    values = rng.normal(size=(len(labels), 4, 256))
    values[labels == 0, 0] *= 3
    values[labels == 1, 3] *= 3
    model = make_pipeline(SpatialCSP(), LinearDiscriminantAnalysis())
    model.fit(values[:100], labels[:100])
    before = model[0].filters_.copy()
    assert model.score(values[100:], labels[100:]) > 0.95
    model.predict(values[100:] * 100)
    np.testing.assert_array_equal(before, model[0].filters_)


def test_csp_rejects_degenerate_and_malformed_inputs():
    with pytest.raises(ValueError, match="zero-variance"):
        SpatialCSP().fit(np.zeros((4, 2, 100)), [0, 1, 0, 1])
    with pytest.raises(ValueError, match="finite"):
        bandpass(np.full((2, 2, 100), np.nan))


def test_session_evaluation_rejects_same_recording_or_subject():
    epoch = Epochs(np.ones((4, 22, 1000)), np.arange(4), np.arange(4), 1, "T", 250, 0, "a")
    for test in (epoch, replace(epoch, session="E"), replace(epoch, subject=2, session="E", source_sha256="b")):
        with pytest.raises(ValueError):
            evaluate_pair(epoch, test)


@pytest.mark.parametrize("side", ["train", "test"])
def test_session_evaluation_rejects_wrong_sampling_rate(side):
    train = Epochs(np.ones((8, 22, 1000)), np.tile(np.arange(4), 2), np.zeros(8), 1, "T", 250, 0, "a")
    test = replace(train, session="E", source_sha256="b")
    if side == "train":
        train = replace(train, sampling_rate=100)
    else:
        test = replace(test, sampling_rate=100)
    with pytest.raises(ValueError, match="250 Hz epochs"):
        evaluate_pair(train, test)


@pytest.mark.parametrize("changes", [
    {"samples": np.ones((8, 21, 1000))},
    {"samples": np.ones((8, 22, 999))},
    {"samples": np.ones((7, 22, 1000))},
    {"labels": np.tile(np.arange(4), 2).reshape(2, 4)},
    {"runs": np.zeros(7)},
    {"labels": np.tile(np.arange(4), 2) + 0.5},
])
def test_session_evaluation_rejects_inconsistent_epoch_contract(changes):
    train = Epochs(np.ones((8, 22, 1000)), np.tile(np.arange(4), 2), np.zeros(8), 1, "T", 250, 0, "a")
    test = replace(train, session="E", source_sha256="b", **changes)
    with pytest.raises(ValueError, match="requires|must contain"):
        evaluate_pair(train, test)


def test_aggregate_is_macro_average_and_confusion_conserves_counts():
    records = []
    for model in ("baseline", "bandpower", "csp"):
        for subject, accuracy, trials in [(1, .5, 10), (2, 1., 20)]:
            records.append({"model": model, "subject": subject, "accuracy": accuracy, "balanced_accuracy": accuracy, "kappa": accuracy, "confusion": (np.eye(4, dtype=int)*trials).tolist(), "train_trials": trials*4, "test_trials": trials*4})
    for result in aggregate(records):
        assert result["balanced_accuracy"] == .75
        assert result["subject_min"] == .5
        assert result["subject_max"] == 1
        assert sum(map(sum, result["confusion"])) == result["test_trials"] == 120
