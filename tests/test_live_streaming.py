from pathlib import Path

import pandas as pd

from dmdc import CSVReplayAdapter, CSVTailAdapter, RollingLiveBuffer, LiveIngestionConfig, run_live_ingestion
from dmdc.cli import main


def _write_stream_csv(path: Path, n: int = 5) -> None:
    pd.DataFrame(
        {
            "time": [0.0, 0.1, 0.23, 0.5, 0.9][:n],
            "case_id": ["run_001"] * n,
            "TP1": [600.0 + i for i in range(n)],
            "TP2": [590.0 + 0.5 * i for i in range(n)],
            "massFlowRate": [0.2] * n,
            "q_heater": [50.0] * n,
        }
    ).to_csv(path, index=False)


def test_csv_replay_adapter_chunks_rows(tmp_path: Path) -> None:
    data = tmp_path / "stream.csv"
    _write_stream_csv(data, n=5)
    adapter = CSVReplayAdapter(data, chunk_size=2, case_col="case_id", case_id="run_001", sort_by_time_col="time")
    first = adapter.read_new_samples()
    second = adapter.read_new_samples()
    third = adapter.read_new_samples()
    assert len(first) == 2
    assert len(second) == 2
    assert len(third) == 1
    assert adapter.read_new_samples() == []


def test_csv_tail_adapter_returns_only_new_rows(tmp_path: Path) -> None:
    data = tmp_path / "tail.csv"
    _write_stream_csv(data, n=2)
    adapter = CSVTailAdapter(data)
    assert len(adapter.read_new_samples()) == 2
    assert adapter.read_new_samples() == []
    frame = pd.read_csv(data)
    frame.loc[len(frame)] = {"time": 0.23, "case_id": "run_001", "TP1": 602.0, "TP2": 591.0, "massFlowRate": 0.2, "q_heater": 50.0}
    frame.to_csv(data, index=False)
    new = adapter.read_new_samples()
    assert len(new) == 1
    assert new[0].values["TP1"] == 602.0


def test_rolling_live_buffer_keeps_clean_samples_and_warns(tmp_path: Path) -> None:
    data = tmp_path / "stream.csv"
    _write_stream_csv(data, n=3)
    adapter = CSVReplayAdapter(data, chunk_size=10)
    samples = adapter.read_new_samples()
    buffer = RollingLiveBuffer(
        state_cols=["TP1", "TP2", "massFlowRate"],
        input_cols=["q_heater"],
        time_col="time",
        buffer_seconds=0.25,
    )
    warnings = buffer.append(samples)
    assert warnings == []
    X, U, t = buffer.matrices()
    # Buffer keeps only samples within 0.25 s of the latest time 0.23.
    assert X.shape[1] == 3
    assert U.shape[1] == 1
    assert t is not None
    assert buffer.summary()["nonuniform_time_assumed"] is True


def test_run_live_ingestion_replay_writes_logs(tmp_path: Path) -> None:
    data = tmp_path / "stream.csv"
    _write_stream_csv(data, n=5)
    out = tmp_path / "out"
    cfg = LiveIngestionConfig(
        stream_type="csv_replay",
        path=str(data),
        time_col="time",
        state_cols=["TP1", "TP2", "massFlowRate"],
        input_cols=["q_heater"],
        outdir=str(out),
        chunk_size=2,
        max_samples=4,
    )
    result = run_live_ingestion(cfg)
    assert result.n_samples_seen == 4
    assert (out / "raw_stream_log.csv").exists()
    assert (out / "cleaned_stream_log.csv").exists()
    assert (out / "live_ingestion_summary.json").exists()
    clean = pd.read_csv(out / "cleaned_stream_log.csv")
    assert len(clean) == 4


def test_live_replay_cli_and_config(tmp_path: Path) -> None:
    data = tmp_path / "stream.csv"
    _write_stream_csv(data, n=5)
    out = tmp_path / "live_cli"
    cfg = tmp_path / "live.toml"
    cfg.write_text(
        f'''
[stream]
type = "csv_replay"
path = "{data}"
chunk_size = 2

[data]
time_col = "time"
state_cols = ["TP1", "TP2", "massFlowRate"]
input_cols = ["q_heater"]

[live]
max_samples = 3
outdir = "{out}"
''',
        encoding="utf-8",
    )
    main(["live-replay", "--config", str(cfg)])
    assert (out / "cleaned_stream_log.csv").exists()
    assert len(pd.read_csv(out / "cleaned_stream_log.csv")) == 3
    assert (out / "provenance.json").exists()


def test_live_run_cli_tail_mode_limited_polls(tmp_path: Path) -> None:
    data = tmp_path / "tail.csv"
    _write_stream_csv(data, n=3)
    out = tmp_path / "tail_out"
    main(
        [
            "live-run",
            "--data",
            str(data),
            "--time-col",
            "time",
            "--state-cols",
            "TP1",
            "TP2",
            "massFlowRate",
            "--input-cols",
            "q_heater",
            "--max-polls",
            "1",
            "--outdir",
            str(out),
        ]
    )
    assert (out / "cleaned_stream_log.csv").exists()
    assert len(pd.read_csv(out / "cleaned_stream_log.csv")) == 3
