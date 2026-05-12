"""Case-aware train/test splitting utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .data import TimeSeriesDataset


@dataclass
class DatasetSplit:
    """Container for train/test trajectory splits."""

    train: list[TimeSeriesDataset]
    test: list[TimeSeriesDataset]
    strategy: str

    @property
    def train_case_ids(self) -> list[object]:
        return [ds.case_id for ds in self.train]

    @property
    def test_case_ids(self) -> list[object]:
        return [ds.case_id for ds in self.test]


def split_by_case_ids(
    datasets: Sequence[TimeSeriesDataset],
    *,
    train_cases: Sequence[object],
    test_cases: Sequence[object],
) -> DatasetSplit:
    """Split loaded trajectories using explicit train and test case IDs."""

    train_set = set(str(x) for x in train_cases)
    test_set = set(str(x) for x in test_cases)
    train = [ds for ds in datasets if str(ds.case_id) in train_set]
    test = [ds for ds in datasets if str(ds.case_id) in test_set]
    missing_train = sorted(train_set - {str(ds.case_id) for ds in train})
    missing_test = sorted(test_set - {str(ds.case_id) for ds in test})
    if missing_train or missing_test:
        raise ValueError(f"Unknown case ids. missing_train={missing_train}, missing_test={missing_test}")
    if not train:
        raise ValueError("Train split is empty.")
    if not test:
        raise ValueError("Test split is empty.")
    return DatasetSplit(train=train, test=test, strategy="explicit_case_lists")


def split_by_fraction(datasets: Sequence[TimeSeriesDataset], train_fraction: float = 0.7) -> DatasetSplit:
    """Deterministically split cases by fraction, preserving sorted load order."""

    if not (0.0 < train_fraction < 1.0):
        raise ValueError("train_fraction must be in (0, 1).")
    n_train = max(1, int(round(len(datasets) * train_fraction)))
    n_train = min(n_train, len(datasets) - 1)
    return DatasetSplit(train=list(datasets[:n_train]), test=list(datasets[n_train:]), strategy="by_case_fraction")


def leave_one_case_out_splits(datasets: Sequence[TimeSeriesDataset]) -> list[DatasetSplit]:
    """Return one split per held-out case."""

    if len(datasets) < 2:
        raise ValueError("Leave-one-case-out validation requires at least two cases.")
    splits = []
    for i, ds in enumerate(datasets):
        splits.append(DatasetSplit(train=[d for j, d in enumerate(datasets) if j != i], test=[ds], strategy="leave_one_case_out"))
    return splits


def make_split(datasets: Sequence[TimeSeriesDataset], config: dict | None = None) -> DatasetSplit:
    """Create a single train/test split from a config dictionary."""

    cfg = config or {}
    strategy = cfg.get("strategy", "by_case_fraction")
    if strategy == "explicit_case_lists":
        return split_by_case_ids(datasets, train_cases=cfg.get("train_cases", []), test_cases=cfg.get("test_cases", []))
    if strategy in {"by_case", "by_case_fraction"}:
        return split_by_fraction(datasets, train_fraction=float(cfg.get("train_fraction", 0.7)))
    if strategy == "leave_one_case_out":
        # Use the first LOO split for single-split workflows; validate can iterate all later.
        return leave_one_case_out_splits(datasets)[0]
    raise ValueError(f"Unsupported split strategy: {strategy}")
