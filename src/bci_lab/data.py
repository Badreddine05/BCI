"""Read the original BNCI2014-001 MAT files without merging recording sessions.

The official archive stores microvolts, 1-based trial starts, 22 EEG channels
followed by 3 EOG channels. Epochs cover [2, 6) seconds from trial onset.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from scipy.io import loadmat

CHANNELS = ("Fz", "FC3", "FC1", "FCz", "FC2", "FC4", "C5", "C3", "C1", "Cz", "C2", "C4", "C6", "CP3", "CP1", "CPz", "CP2", "CP4", "P1", "Pz", "P2", "POz")
CLASSES = ("left_hand", "right_hand", "feet", "tongue")
SOURCE = "https://lampx.tugraz.at/~bci/database/001-2014/"


@dataclass(frozen=True)
class Epochs:
    samples: np.ndarray
    labels: np.ndarray
    runs: np.ndarray
    subject: int
    session: str
    sampling_rate: int
    flagged_trials: int
    source_sha256: str


def validate_identity(subject: int, session: str) -> None:
    if isinstance(subject, bool) or not isinstance(subject, int) or subject not in range(1, 10):
        raise ValueError("subject must be an integer between 1 and 9")
    if session not in ("T", "E"):
        raise ValueError("session must be T (training day) or E (evaluation day)")


def file_hash(path: Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_session(subject: int, session: str, directory: Path, expected_hash: str | None = None) -> Path:
    """Download one original file atomically; never silently accept a changed hash."""
    validate_identity(subject, session)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"A{subject:02d}{session}.mat"
    if target.exists():
        if expected_hash and file_hash(target) != expected_hash:
            raise ValueError(f"Cached source checksum mismatch: {target.name}")
        return target
    temporary = target.with_suffix(".mat.part")
    try:
        request = Request(SOURCE + target.name, headers={"User-Agent": "BCI-NeuroLab/1.0 (research portfolio)"})
        with urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            for block in iter(lambda: response.read(1024 * 1024), b""):
                output.write(block)
        if temporary.stat().st_size < 1000:
            raise ValueError("The downloaded file is unexpectedly small")
        if expected_hash and file_hash(temporary) != expected_hash:
            raise ValueError(f"Downloaded source checksum mismatch: {target.name}")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def load_session(path: Path, subject: int, session: str) -> Epochs:
    validate_identity(subject, session)
    data = loadmat(path, struct_as_record=False, squeeze_me=True)
    if "data" not in data:
        raise ValueError("MAT file must contain the original data structure")
    samples, labels, groups = [], [], []
    flagged = 0
    for run_id, run in enumerate(np.atleast_1d(data["data"])):
        original_starts = np.atleast_1d(run.trial).reshape(-1)
        original_targets = np.atleast_1d(run.y).reshape(-1)
        if not np.isfinite(original_starts).all() or not np.isfinite(original_targets).all():
            raise ValueError("Trial indices and class labels must be finite")
        if not np.equal(original_starts, np.floor(original_starts)).all() or not np.equal(original_targets, np.floor(original_targets)).all():
            raise ValueError("Trial indices and class labels must be integers")
        starts = original_starts.astype(int)
        targets = original_targets.astype(int)
        if np.any(starts < 1):
            raise ValueError("Trial starts must be positive 1-based indices")
        if starts.size == 0:  # Calibration/EOG recordings are not trials.
            continue
        rate = np.asarray(run.fs).item()
        values = np.asarray(run.X, dtype=float)
        if rate != 250 or values.ndim != 2 or values.shape[1] != 25:
            raise ValueError("Expected 250 Hz recordings with 22 EEG and 3 EOG channels")
        # MATLAB may store an integral sampling rate as a double.
        rate = int(rate)
        if len(starts) != len(targets) or not np.isin(targets, [1, 2, 3, 4]).all():
            raise ValueError("Trial starts and four-class labels are inconsistent")
        artifacts = np.atleast_1d(getattr(run, "artifacts", np.zeros(len(starts)))).reshape(-1)
        if len(artifacts) != len(starts):
            raise ValueError("Artifact flags do not match the trial count")
        if not np.isin(artifacts, [0, 1]).all():
            raise ValueError("Artifact flags must be zero or one")
        for start, label, artifact in zip(starts, targets, artifacts, strict=True):
            first = int(start) - 1 + 2 * rate
            last = first + 4 * rate
            if first < 0 or last > values.shape[0]:
                raise ValueError("Trial extends beyond its recording")
            epoch = values[first:last, :22].T.copy()
            if not np.isfinite(epoch).all():
                raise ValueError("Non-finite EEG sample in a selected trial")
            samples.append(epoch)
            labels.append(int(label) - 1)
            groups.append(run_id)
            flagged += int(bool(artifact))
    if not samples:
        raise ValueError("No usable motor-imagery trials")
    return Epochs(np.stack(samples), np.asarray(labels), np.asarray(groups), subject, session, 250, flagged, file_hash(Path(path)))
