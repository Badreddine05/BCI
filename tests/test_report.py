import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def test_published_metrics_reconcile_with_recorded_confusions():
    report = json.loads((ROOT / "web/data/benchmark.json").read_text("utf-8"))
    assert report["subjects"] == list(range(1, 10))
    assert len(report["sources"]) == 18
    assert len(report["records"]) == 27
    assert report["protocol"]["train_session"] != report["protocol"]["test_session"]
    for record in report["records"]:
        matrix = np.array(record["confusion"])
        assert matrix.shape == (4, 4)
        assert (matrix >= 0).all()
        assert matrix.sum() == record["test_trials"] == 288
        np.testing.assert_array_equal(matrix.sum(axis=1), [72]*4)
        np.testing.assert_allclose(np.trace(matrix)/matrix.sum(), record["accuracy"])
        np.testing.assert_allclose(np.mean(matrix.diagonal()/matrix.sum(axis=1)), record["balanced_accuracy"])
    for summary in report["summary"]:
        records = [r for r in report["records"] if r["model"] == summary["model"]]
        np.testing.assert_allclose(np.mean([r["balanced_accuracy"] for r in records]), summary["balanced_accuracy"])
        np.testing.assert_array_equal(np.sum([r["confusion"] for r in records], axis=0), summary["confusion"])
    sources = json.loads((ROOT / "data/sources.json").read_text("utf-8"))["files"]
    assert {r["sha256"] for r in sources} == {r["sha256"] for r in report["sources"]}
