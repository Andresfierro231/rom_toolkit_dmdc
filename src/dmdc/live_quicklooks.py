"""Live Phase-6.3 quicklook plots for long-running archives.

Quicklooks are intentionally small static images.  They are not meant to replace
the Streamlit dashboard; they are meant to make days or months of archives easy
to skim in a file browser, a report, or an email.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json

import matplotlib.pyplot as plt
import pandas as pd

from .provenance import write_provenance


@dataclass
class QuicklookConfig:
    archive_root: str = "live_archive"
    summaries_dir: str | None = None
    outdir: str | None = None
    window_label: str = "60s"


@dataclass
class QuicklookResult:
    archive_root: str
    outdir: str
    n_plots: int
    plots: list[str]


def make_archive_quicklooks(config: QuicklookConfig, *, config_path: str | Path | None = None) -> QuicklookResult:
    summaries = Path(config.summaries_dir or Path(config.archive_root) / "summaries")
    outdir = Path(config.outdir or Path(config.archive_root) / "quicklooks")
    outdir.mkdir(parents=True, exist_ok=True)
    plots: list[str] = []

    candidates = [
        (summaries / f"trust_summary_{config.window_label}.csv", _plot_trust, outdir / f"trust_summary_{config.window_label}.png"),
        (summaries / f"residual_summary_{config.window_label}.csv", _plot_residuals, outdir / f"residual_summary_{config.window_label}.png"),
        (summaries / f"bias_summary_{config.window_label}.csv", _plot_bias, outdir / f"bias_summary_{config.window_label}.png"),
        (summaries / f"state_summary_{config.window_label}.csv", _plot_state_overview, outdir / f"state_summary_{config.window_label}.png"),
    ]
    for path, func, out in candidates:
        if path.exists() and path.stat().st_size > 0:
            try:
                df = pd.read_csv(path)
                if not df.empty:
                    func(df, out)
                    plots.append(str(out))
            except Exception:
                continue
    result = QuicklookResult(config.archive_root, str(outdir), len(plots), plots)
    (outdir / "quicklook_manifest.json").write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    write_provenance(outdir, config_path=config_path, extra={"command": "archive-quicklook", "result": asdict(result)})
    return result


def _plot_trust(df: pd.DataFrame, out: Path) -> None:
    plt.figure(figsize=(8, 4.5))
    x = df.get("window_start", range(len(df)))
    if "mean" in df:
        plt.plot(x, df["mean"], label="mean trust")
    if "min" in df:
        plt.plot(x, df["min"], label="min trust")
    plt.ylim(0, 1.05)
    plt.xlabel("time window start [s]")
    plt.ylabel("trust score")
    plt.title("Live model trust score quicklook")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out)
    plt.close()


def _plot_residuals(df: pd.DataFrame, out: Path) -> None:
    plt.figure(figsize=(9, 5))
    state_col = "state" if "state" in df.columns else None
    if state_col:
        for state, g in df.groupby(state_col):
            plt.plot(g["window_start"], g.get("mae", g.get("rmse")), label=str(state))
    else:
        plt.plot(df.get("window_start", range(len(df))), df.get("mae", df.get("rmse")))
    plt.xlabel("time window start [s]")
    plt.ylabel("residual magnitude")
    plt.title("Forecast residual quicklook")
    if state_col:
        plt.legend(ncol=2, fontsize=8)
    plt.tight_layout()
    plt.savefig(out)
    plt.close()


def _plot_bias(df: pd.DataFrame, out: Path) -> None:
    plt.figure(figsize=(9, 5))
    if "state" in df.columns:
        for state, g in df.groupby("state"):
            plt.plot(g["window_start"], g.get("last_bias", g.get("mean_bias")), label=str(state))
        plt.legend(ncol=2, fontsize=8)
    else:
        plt.plot(df.get("window_start", range(len(df))), df.get("last_bias", df.get("mean_bias")))
    plt.xlabel("time window start [s]")
    plt.ylabel("bias correction")
    plt.title("Bias correction drift quicklook")
    plt.tight_layout()
    plt.savefig(out)
    plt.close()


def _plot_state_overview(df: pd.DataFrame, out: Path) -> None:
    plt.figure(figsize=(9, 5))
    state_col = "state" if "state" in df.columns else "variable" if "variable" in df.columns else None
    if state_col:
        for state, g in df.groupby(state_col):
            plt.plot(g["window_start"], g.get("mean"), label=str(state))
        plt.legend(ncol=2, fontsize=8)
    else:
        plt.plot(df.get("window_start", range(len(df))), df.get("mean"))
    plt.xlabel("time window start [s]")
    plt.ylabel("mean value")
    plt.title("Cleaned stream state overview")
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
