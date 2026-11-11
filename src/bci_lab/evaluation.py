"""Evaluate each person on a different recording day, without test-set tuning."""
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path

import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, cohen_kappa_score, confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .data import CHANNELS, CLASSES, SOURCE, download_session, load_session, file_hash
from .features import bandpass, LogBandPower, SpatialCSP

MODEL_NAMES = {"baseline": "Classe majoritaire", "bandpower": "Puissance spectrale + LDA", "csp": "CSP + LDA"}
PROTOCOL = {
    "dataset": "BNCI2014-001 / BCI Competition IV 2a",
    "train_session": "T", "test_session": "E", "sampling_rate_hz": 250,
    "epoch_seconds": [2, 6], "epoch_end_exclusive": True,
    "eeg_channels": list(CHANNELS), "eog_channels_used": False,
    "classes": list(CLASSES), "bandpass_hz": [8, 30],
    "filter": "Butterworth order 4, zero phase per epoch (offline)",
    "artifact_policy": "All labelled trials retained, including provider-flagged trials; counts disclosed.",
    "csp": "One-versus-rest, two filters per class, covariance shrinkage 0.1",
    "tuning": "Fixed choices; no hyperparameter search, no model selection on session E.",
    "generalization": "New session of a known participant; not unseen-participant evaluation.",
}


def make_models():
    return {
        "baseline": make_pipeline(LogBandPower(), DummyClassifier(strategy="most_frequent")),
        "bandpower": make_pipeline(LogBandPower(), StandardScaler(), LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")),
        "csp": make_pipeline(SpatialCSP(regularization=0.1), StandardScaler(), LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")),
    }


def evaluate_pair(train, test):
    """Fail closed if a caller accidentally provides the same recording session."""
    if train.subject != test.subject or train.session != "T" or test.session != "E":
        raise ValueError("Evaluation requires T -> E for the same participant")
    if train.source_sha256 == test.source_sha256:
        raise ValueError("Training and evaluation must be distinct source files")
    expected_samples = (PROTOCOL["epoch_seconds"][1] - PROTOCOL["epoch_seconds"][0]) * PROTOCOL["sampling_rate_hz"]
    for recording in (train, test):
        if recording.sampling_rate != PROTOCOL["sampling_rate_hz"]:
            raise ValueError("Evaluation requires 250 Hz epochs; resampling is not implicit")
        samples = np.asarray(recording.samples)
        labels = np.asarray(recording.labels)
        runs = np.asarray(recording.runs)
        if labels.ndim != 1 or labels.size == 0 or runs.shape != labels.shape:
            raise ValueError("Each epoch requires one class label and one run identifier")
        if samples.shape != (labels.size, len(CHANNELS), expected_samples):
            raise ValueError("Evaluation requires matching [trials, 22 EEG channels, 1000 samples] arrays")
        if set(np.unique(labels)) != set(range(4)):
            raise ValueError("Both sessions must contain all four imagery classes")
    X_train, X_test = bandpass(train.samples), bandpass(test.samples)
    records = []
    for name, model in make_models().items():
        model.fit(X_train, train.labels)
        prediction = model.predict(X_test)
        records.append({
            "subject": train.subject, "model": name, "name": MODEL_NAMES[name],
            "train_trials": len(train.labels), "test_trials": len(test.labels),
            "accuracy": float(accuracy_score(test.labels, prediction)),
            "balanced_accuracy": float(balanced_accuracy_score(test.labels, prediction)),
            "kappa": float(cohen_kappa_score(test.labels, prediction)),
            "confusion": confusion_matrix(test.labels, prediction, labels=range(4)).tolist(),
        })
    return records


def aggregate(records):
    summary = []
    for model in MODEL_NAMES:
        selected = [r for r in records if r["model"] == model]
        if not selected:
            raise ValueError("Missing model results")
        accuracy = [r["balanced_accuracy"] for r in selected]
        summary.append({
            "model": model, "name": MODEL_NAMES[model], "subjects": len(selected),
            "balanced_accuracy": float(np.mean(accuracy)),
            "accuracy": float(np.mean([r["accuracy"] for r in selected])),
            "kappa": float(np.mean([r["kappa"] for r in selected])),
            "subject_min": min(accuracy), "subject_max": max(accuracy),
            "confusion": np.sum([r["confusion"] for r in selected], axis=0).tolist(),
            "train_trials": sum(r["train_trials"] for r in selected),
            "test_trials": sum(r["test_trials"] for r in selected),
        })
    return summary


def run_benchmark(subjects, raw_directory: Path, output: Path, sources_file: Path, download=False):
    subjects = list(subjects)
    if not subjects or len(set(subjects)) != len(subjects):
        raise ValueError("Provide unique participant numbers")
    known = json.loads(sources_file.read_text("utf-8"))["files"] if sources_file.exists() else []
    expected = {item["file"]: item["sha256"] for item in known}
    records, sources, quality = [], [], []
    for subject in sorted(subjects):
        sessions = []
        for session in ("T", "E"):
            name = f"A{subject:02d}{session}.mat"
            path = raw_directory / name
            if download:
                path = download_session(subject, session, raw_directory, expected.get(name))
            if not path.is_file():
                raise FileNotFoundError(f"Missing {name}; pass --download to fetch the original source")
            if name in expected and file_hash(path) != expected[name]:
                raise ValueError(f"Source differs from its recorded hash: {name}")
            data = load_session(path, subject, session)
            sessions.append(data)
            sources.append({"file": name, "url": SOURCE + name, "bytes": path.stat().st_size, "sha256": data.source_sha256})
            quality.append({"subject": subject, "session": session, "trials": len(data.labels), "runs": len(np.unique(data.runs)), "flagged_trials": data.flagged_trials, "class_counts": np.bincount(data.labels, minlength=4).tolist()})
        result = evaluate_pair(*sessions)
        records.extend(result)
        print(f"S{subject:02d}: " + ", ".join(f"{r['model']}={r['balanced_accuracy']:.3f}" for r in result), flush=True)
    report = {
        "schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
        "protocol": PROTOCOL, "subjects": sorted(subjects), "records": records,
        "summary": aggregate(records), "quality": quality, "sources": sources,
        "runtime": {name: version(name) for name in ("numpy", "scipy", "scikit-learn")},
        "data_license": "CC BY-ND 4.0; original recordings are downloaded from the licensor, not redistributed here.",
        "source_page": "https://bnci-horizon-2020.eu/database/data-sets",
        "publication": "https://doi.org/10.3389/fnins.2012.00055",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", "utf-8")
    # Keep previously pinned files when a smaller subset is evaluated later.
    merged = {item["file"]: item for item in known}
    merged.update({item["file"]: item for item in sources})
    sources_file.parent.mkdir(parents=True, exist_ok=True)
    sources_file.write_text(json.dumps({"files": sorted(merged.values(), key=lambda x: x["file"])}, indent=2) + "\n", "utf-8")
    return report
