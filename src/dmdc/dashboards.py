"""Portable dashboard tables for ROM studies."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


def dataframe_to_latex_table(df: pd.DataFrame, caption: str, label: str) -> str:
    """Convert a dataframe to a compact LaTeX table string."""

    if df.empty:
        return f"% {caption}: no rows available\n"
    return df.to_latex(index=False, escape=True, caption=caption, label=label, longtable=False)


def save_dashboard(df: pd.DataFrame, outdir: str | Path, name: str, *, caption: str | None = None) -> None:
    """Save a dashboard table as CSV, Markdown, and LaTeX."""

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / f"{name}.csv", index=False)
    try:
        md = df.to_markdown(index=False)
    except Exception:  # pragma: no cover - tabulate may be missing in minimal envs
        md = df.to_string(index=False)
    (out / f"{name}.md").write_text(md + "\n", encoding="utf-8")
    tex = dataframe_to_latex_table(df, caption or name.replace("_", " ").title(), f"tab:{name}")
    (out / f"{name}.tex").write_text(tex, encoding="utf-8")


def plot_model_comparison(df: pd.DataFrame, path: str | Path) -> None:
    """Plot train/test rollout RMSE by model."""

    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots()
    if df.empty:
        ax.text(0.5, 0.5, "No model comparison rows", ha="center")
    else:
        x = np.arange(len(df))
        width = 0.35
        ax.bar(x - width / 2, df["train_rollout_rmse"].to_numpy(), width, label="train")
        ax.bar(x + width / 2, df["test_rollout_rmse"].to_numpy(), width, label="test")
        ax.set_xticks(x)
        ax.set_xticklabels(df["model_name"].astype(str).tolist(), rotation=35, ha="right")
        ax.set_ylabel("Rollout RMSE")
        ax.set_title("Model comparison")
        ax.legend()
        ax.grid(True, axis="y")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
