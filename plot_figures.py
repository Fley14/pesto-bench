#!/usr/bin/env python3
"""
Generate benchmark figures from CSV results.

Figures produced (SVG, in figures/YYYY-MM-DD_HH-MM-SS/):
  1. speedup.svg           — speedup with error bars (STD Dev)
  2. efficiency.svg        — efficiency (speedup / NUM_CORES) with error bars
  3. overhead.svg          — parallelisation overhead (par_time×cores − seq_time)
  4. ratio_sta_dyn.svg     — static / dynamic speedup ratio
  5. cv_stability.svg      — coefficient of variation (STD Dev %) per variant
  6. worstcase_speedup.svg — best-case vs worst-case speedup

Expected directory structure:
  results_valide/results_csv/
    sequential/   *.csv
    static/       *.csv
    dynamic/      *.csv

Each CSV: T0[,T1,...], score, Trimmed Mean, STD Dev, STD Dev %
"""

import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MultipleLocator

matplotlib.use("Agg")

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_DIR   = Path("results_valide/results_csv")
SEQ_DIR    = BASE_DIR / "sequential"
STATIC_DIR = BASE_DIR / "static"
DYN_DIR    = BASE_DIR / "dynamic"
NUM_CORES  = 64

# Timestamped output folder  →  figures/2025-06-12_14-30-00/
_TS     = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
FIG_DIR = Path("figures") / _TS

# Colours
BLUE   = "#4472C4"
ORANGE = "#ED7D31"
GREEN  = "#70AD47"
RED    = "#FF0000"
GREY   = "#A9A9A9"


# ── CSV helpers ───────────────────────────────────────────────────────────────

def stem_key(filename: str) -> str:
    """heat-2d-static.csv  →  'heat-2d'"""
    name = Path(filename).stem
    return re.sub(r"[-_](static|dynamic)$", "", name, flags=re.IGNORECASE)


def _find_col(df: pd.DataFrame, *candidates: str) -> str | None:
    normalised = {c.lower().replace(" ", ""): c for c in df.columns}
    for cand in candidates:
        if cand.lower().replace(" ", "") in normalised:
            return normalised[cand.lower().replace(" ", "")]
    return None


def read_stats(csv_path: Path) -> dict:
    """
    Return:
      best_time  – min(Trimmed Mean)   [fastest run / tile config]
      worst_time – max(Trimmed Mean)   [slowest run / tile config]
      std_dev    – mean(STD Dev)       across tile configs
      cv         – mean(STD Dev %)
    """
    empty = dict(best_time=np.nan, worst_time=np.nan, std_dev=np.nan, cv=np.nan)
    try:
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        tm_col  = _find_col(df, "Trimmed Mean", "score")
        std_col = _find_col(df, "STD Dev")
        cv_col  = _find_col(df, "STD Dev %")
        if tm_col is None:
            print(f"  [WARN] No timing column in {csv_path}", file=sys.stderr)
            return empty
        return dict(
            best_time  = float(df[tm_col].min()),
            worst_time = float(df[tm_col].max()),
            std_dev    = float(df[std_col].mean()) if std_col else np.nan,
            cv         = float(df[cv_col].mean())  if cv_col  else np.nan,
        )
    except Exception as exc:
        print(f"  [WARN] Could not read {csv_path}: {exc}", file=sys.stderr)
        return empty


def collect_files(directory: Path) -> dict[str, Path]:
    if not directory.exists():
        return {}
    return {stem_key(p.name): p for p in directory.glob("*.csv")}


# ── Build master table ────────────────────────────────────────────────────────

def build_table() -> pd.DataFrame:
    seq_files = collect_files(SEQ_DIR)
    sta_files = collect_files(STATIC_DIR)
    dyn_files = collect_files(DYN_DIR)

    all_programs = (set(sta_files) | set(dyn_files)) & set(seq_files)
    if not all_programs:
        return pd.DataFrame()

    _nan = dict(best_time=np.nan, worst_time=np.nan, std_dev=np.nan, cv=np.nan)

    rows = []
    for prog in sorted(all_programs):
        seq = read_stats(seq_files[prog])
        sta = read_stats(sta_files[prog]) if prog in sta_files else _nan.copy()
        dyn = read_stats(dyn_files[prog]) if prog in dyn_files else _nan.copy()

        seq_best  = seq["best_time"]
        seq_worst = seq["worst_time"]

        # ── Best-case speedup
        speedup_sta = seq_best / sta["best_time"]  if sta["best_time"]  > 0 else np.nan
        speedup_dyn = seq_best / dyn["best_time"]  if dyn["best_time"]  > 0 else np.nan

        # ── Worst-case speedup  (worst seq / worst par)
        wc_sta = seq_worst / sta["worst_time"] if sta["worst_time"] > 0 else np.nan
        wc_dyn = seq_worst / dyn["worst_time"] if dyn["worst_time"] > 0 else np.nan

        # ── Error bar on speedup via propagation:
        #   Δ(speedup) ≈ speedup × sqrt( (σ_seq/t_seq)² + (σ_par/t_par)² )
        def _err(sp, t_seq, sig_seq, t_par, sig_par):
            if any(np.isnan(v) for v in (sp, t_seq, sig_seq, t_par, sig_par)):
                return np.nan
            if t_seq == 0 or t_par == 0:
                return np.nan
            return sp * np.sqrt((sig_seq / t_seq) ** 2 + (sig_par / t_par) ** 2)

        err_sta = _err(speedup_sta, seq_best, seq["std_dev"], sta["best_time"], sta["std_dev"])
        err_dyn = _err(speedup_dyn, seq_best, seq["std_dev"], dyn["best_time"], dyn["std_dev"])

        # ── Parallel overhead  (par_time × cores) − seq_time
        overhead_sta = sta["best_time"] * NUM_CORES - seq_best if not np.isnan(sta["best_time"]) else np.nan
        overhead_dyn = dyn["best_time"] * NUM_CORES - seq_best if not np.isnan(dyn["best_time"]) else np.nan

        rows.append(dict(
            program      = prog,
            speedup_sta  = speedup_sta,
            speedup_dyn  = speedup_dyn,
            err_sta      = err_sta,
            err_dyn      = err_dyn,
            wc_sta       = wc_sta,
            wc_dyn       = wc_dyn,
            overhead_sta = overhead_sta,
            overhead_dyn = overhead_dyn,
            cv_seq       = seq["cv"],
            cv_sta       = sta["cv"],
            cv_dyn       = dyn["cv"],
        ))

    df = pd.DataFrame(rows)

    # Average row
    num_cols = df.select_dtypes(include="number").columns
    avg = df[num_cols].mean(skipna=True).to_dict()
    avg["program"] = "Average"
    df = pd.concat([df, pd.DataFrame([avg])], ignore_index=True)
    return df


# ── Generic plotting helpers ──────────────────────────────────────────────────

def pretty(name: str) -> str:
    return name.replace("-", "\u2011")   # non-breaking hyphen


def _save(fig: plt.Figure, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {path}")


def _base_fig(n: int):
    fig, ax = plt.subplots(figsize=(max(10, n * 0.9), 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, color="#dddddd", zorder=0)
    return fig, ax


def _xticks(ax, programs):
    x = np.arange(len(programs))
    ax.set_xticks(x)
    ax.set_xticklabels([pretty(p) for p in programs], rotation=40, ha="right", fontsize=9)
    return x


def _avg_separator(ax, programs):
    if "Average" in programs:
        idx = programs.index("Average")
        ax.axvline(idx - 0.55, color="#cccccc", linewidth=0.8, linestyle="--", zorder=2)


def _bar_labels(ax, bars, fmt="{:.2f}"):
    for bar in bars:
        h = bar.get_height()
        if np.isnan(h):
            continue
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + max(abs(h) * 0.01, 0.005),
            fmt.format(h),
            ha="center", va="bottom", fontsize=7.5,
        )


def _legend(ax, labels_colors, **kw):
    ax.legend(
        handles=[mpatches.Patch(color=c, label=l) for l, c in labels_colors],
        fontsize=9, framealpha=0.9, edgecolor="#cccccc", **kw,
    )


# ── Figure 1 : Speedup  (with error bars) ────────────────────────────────────

def plot_speedup(df: pd.DataFrame, out_dir: Path):
    programs = df["program"].tolist()
    n = len(programs)
    x = np.arange(n)
    w = 0.35

    val_sta = df["speedup_sta"].to_numpy(dtype=float)
    val_dyn = df["speedup_dyn"].to_numpy(dtype=float)
    err_sta = df["err_sta"].to_numpy(dtype=float)
    err_dyn = df["err_dyn"].to_numpy(dtype=float)

    fig, ax = _base_fig(n)
    kw_err = dict(capsize=3, capthick=1, elinewidth=1, error_kw={"zorder": 5})
    b1 = ax.bar(x - w/2, val_sta, w, color=BLUE,   zorder=3, yerr=err_sta, **kw_err)
    b2 = ax.bar(x + w/2, val_dyn, w, color=ORANGE, zorder=3, yerr=err_dyn, **kw_err)
    _bar_labels(ax, b1)
    _bar_labels(ax, b2)
    ax.axhline(1.0, color=RED, linewidth=1.4, zorder=4)
    _avg_separator(ax, programs)
    _xticks(ax, programs)
    ax.set_ylabel("Speedup  (seq / par)", fontsize=11)
    ax.set_title("Speedup — Pesto vs Pluto",
                 fontsize=13, fontweight="bold", fontfamily="serif", pad=10)
    ax.yaxis.set_minor_locator(MultipleLocator(0.1))
    ax.set_xlim(-0.6, n - 0.4)
    _legend(ax, [("Static", BLUE), ("Dynamic", ORANGE)])
    _save(fig, out_dir / "speedup.svg")


# ── Figure 2 : Efficiency  (with error bars) ─────────────────────────────────

def plot_efficiency(df: pd.DataFrame, out_dir: Path):
    programs = df["program"].tolist()
    n = len(programs)
    x = np.arange(n)
    w = 0.35

    val_sta = df["speedup_sta"].to_numpy(dtype=float) / NUM_CORES
    val_dyn = df["speedup_dyn"].to_numpy(dtype=float) / NUM_CORES
    err_sta = df["err_sta"].to_numpy(dtype=float)     / NUM_CORES
    err_dyn = df["err_dyn"].to_numpy(dtype=float)     / NUM_CORES

    fig, ax = _base_fig(n)
    kw_err = dict(capsize=3, capthick=1, elinewidth=1, error_kw={"zorder": 5})
    b1 = ax.bar(x - w/2, val_sta, w, color=BLUE,   zorder=3, yerr=err_sta, **kw_err)
    b2 = ax.bar(x + w/2, val_dyn, w, color=ORANGE, zorder=3, yerr=err_dyn, **kw_err)
    _bar_labels(ax, b1, fmt="{:.3f}")
    _bar_labels(ax, b2, fmt="{:.3f}")
    ax.axhline(1 / NUM_CORES, color=RED, linewidth=1.4, zorder=4,
               label=f"Ideal  (1/{NUM_CORES} = {1/NUM_CORES:.4f})")
    _avg_separator(ax, programs)
    _xticks(ax, programs)
    ax.set_ylabel(f"Efficiency  (speedup / {NUM_CORES} cores)", fontsize=11)
    ax.set_title(f"Efficiency — Pesto vs Pluto  ({NUM_CORES} cores)",
                 fontsize=13, fontweight="bold", fontfamily="serif", pad=10)
    ax.yaxis.set_minor_locator(MultipleLocator(0.005))
    ax.set_xlim(-0.6, n - 0.4)
    _legend(ax, [("Static", BLUE), ("Dynamic", ORANGE)])
    _save(fig, out_dir / "efficiency.svg")


# ── Figure 3 : Parallel overhead ─────────────────────────────────────────────

def plot_overhead(df: pd.DataFrame, out_dir: Path):
    """
    Overhead = par_time × NUM_CORES − seq_time
    Positive → more CPU-time consumed than sequential (synchronisation cost).
    Negative → impossible in theory but may indicate measurement noise.
    """
    programs = df["program"].tolist()
    n = len(programs)
    x = np.arange(n)
    w = 0.35

    val_sta = df["overhead_sta"].to_numpy(dtype=float)
    val_dyn = df["overhead_dyn"].to_numpy(dtype=float)

    fig, ax = _base_fig(n)
    b1 = ax.bar(x - w/2, val_sta, w, color=BLUE,   zorder=3)
    b2 = ax.bar(x + w/2, val_dyn, w, color=ORANGE, zorder=3)
    _bar_labels(ax, b1, fmt="{:.3f}")
    _bar_labels(ax, b2, fmt="{:.3f}")
    ax.axhline(0, color=RED, linewidth=1.2, zorder=4)
    _avg_separator(ax, programs)
    _xticks(ax, programs)
    ax.set_ylabel("Overhead  (par × cores − seq)  [time units]", fontsize=10)
    ax.set_title("Parallelisation Overhead — Pesto vs Pluto",
                 fontsize=13, fontweight="bold", fontfamily="serif", pad=10)
    ax.set_xlim(-0.6, n - 0.4)
    _legend(ax, [("Static", BLUE), ("Dynamic", ORANGE)])
    _save(fig, out_dir / "overhead.svg")


# ── Figure 4 : Static / Dynamic ratio ────────────────────────────────────────

def plot_ratio(df: pd.DataFrame, out_dir: Path):
    """ratio > 1 → static wins;  ratio < 1 → dynamic wins"""
    programs = df["program"].tolist()
    n = len(programs)
    x = np.arange(n)
    w = 0.5

    ratio  = (df["speedup_sta"] / df["speedup_dyn"]).to_numpy(dtype=float)
    colors = [BLUE if (np.isnan(r) or r >= 1) else ORANGE for r in ratio]

    fig, ax = _base_fig(n)
    bars = ax.bar(x, ratio, w, color=colors, zorder=3)
    _bar_labels(ax, bars)
    ax.axhline(1.0, color=RED, linewidth=1.4, zorder=4)
    _avg_separator(ax, programs)
    _xticks(ax, programs)
    ax.set_ylabel("Speedup ratio  (static / dynamic)", fontsize=11)
    ax.set_title("Static vs Dynamic Scheduling — Speedup Ratio",
                 fontsize=13, fontweight="bold", fontfamily="serif", pad=10)
    ax.set_xlim(-0.6, n - 0.4)
    _legend(ax, [("Static wins  (ratio ≥ 1)", BLUE),
                 ("Dynamic wins (ratio < 1)", ORANGE)])
    _save(fig, out_dir / "ratio_sta_dyn.svg")


# ── Figure 5 : Coefficient of Variation ──────────────────────────────────────

def plot_cv(df: pd.DataFrame, out_dir: Path):
    """Lower CV = more stable / reproducible runs."""
    programs = df["program"].tolist()
    n = len(programs)
    x = np.arange(n)
    w = 0.25

    cv_seq = df["cv_seq"].to_numpy(dtype=float)
    cv_sta = df["cv_sta"].to_numpy(dtype=float)
    cv_dyn = df["cv_dyn"].to_numpy(dtype=float)

    fig, ax = _base_fig(n)
    b0 = ax.bar(x - w, cv_seq, w, color=GREY,   zorder=3)
    b1 = ax.bar(x,     cv_sta, w, color=BLUE,   zorder=3)
    b2 = ax.bar(x + w, cv_dyn, w, color=ORANGE, zorder=3)
    for bars in (b0, b1, b2):
        _bar_labels(ax, bars, fmt="{:.1f}")
    _avg_separator(ax, programs)
    _xticks(ax, programs)
    ax.set_ylabel("Coefficient of Variation  (STD Dev %)", fontsize=11)
    ax.set_title("Run Stability — Coefficient of Variation  (lower = more stable)",
                 fontsize=13, fontweight="bold", fontfamily="serif", pad=10)
    ax.set_xlim(-0.6, n - 0.4)
    _legend(ax, [("Sequential", GREY), ("Static", BLUE), ("Dynamic", ORANGE)])
    _save(fig, out_dir / "cv_stability.svg")


# ── Figure 6 : Best-case vs Worst-case speedup ───────────────────────────────

def plot_worstcase(df: pd.DataFrame, out_dir: Path):
    programs = df["program"].tolist()
    n = len(programs)
    x = np.arange(n)
    w = 0.35

    bc_sta = df["speedup_sta"].to_numpy(dtype=float)
    bc_dyn = df["speedup_dyn"].to_numpy(dtype=float)
    wc_sta = df["wc_sta"].to_numpy(dtype=float)
    wc_dyn = df["wc_dyn"].to_numpy(dtype=float)

    fig, ax = _base_fig(n)
    # Filled bars = best case
    ax.bar(x - w/2, bc_sta, w, color=BLUE,   zorder=3, alpha=0.9)
    ax.bar(x + w/2, bc_dyn, w, color=ORANGE, zorder=3, alpha=0.9)
    # Hatched outline = worst case
    ax.bar(x - w/2, wc_sta, w, color="none", zorder=4,
           edgecolor=BLUE,   linewidth=1.5, hatch="///")
    ax.bar(x + w/2, wc_dyn, w, color="none", zorder=4,
           edgecolor=ORANGE, linewidth=1.5, hatch="\\\\\\")

    ax.axhline(1.0, color=RED, linewidth=1.4, zorder=5)
    _avg_separator(ax, programs)
    _xticks(ax, programs)
    ax.set_ylabel("Speedup", fontsize=11)
    ax.set_title("Best-case vs Worst-case Speedup",
                 fontsize=13, fontweight="bold", fontfamily="serif", pad=10)
    ax.set_xlim(-0.6, n - 0.4)
    ax.legend(handles=[
        mpatches.Patch(color=BLUE,                    label="Static — best"),
        mpatches.Patch(color="none", ec=BLUE,
                       hatch="///",                   label="Static — worst"),
        mpatches.Patch(color=ORANGE,                  label="Dynamic — best"),
        mpatches.Patch(color="none", ec=ORANGE,
                       hatch="\\\\\\",                label="Dynamic — worst"),
    ], fontsize=8.5, framealpha=0.9, edgecolor="#cccccc", ncol=2)
    _save(fig, out_dir / "worstcase_speedup.svg")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Output folder : {FIG_DIR}\n")
    print("Loading CSV data …")
    df = build_table()

    if df.empty or len(df) <= 1:
        print("ERROR: no data found — check BASE_DIR and CSV layout.")
        sys.exit(1)

    print(df.to_string(index=False))
    print()

    FIG_DIR.mkdir(parents=True, exist_ok=True)

    print("1/6  Speedup (with error bars) …")
    plot_speedup(df, FIG_DIR)

    print("2/6  Efficiency (with error bars) …")
    plot_efficiency(df, FIG_DIR)

    print("3/6  Parallelisation overhead …")
    plot_overhead(df, FIG_DIR)

    print("4/6  Static / Dynamic ratio …")
    plot_ratio(df, FIG_DIR)

    print("5/6  Coefficient of variation (stability) …")
    plot_cv(df, FIG_DIR)

    print("6/6  Worst-case vs best-case speedup …")
    plot_worstcase(df, FIG_DIR)

    svg_count = len(list(FIG_DIR.glob("*.svg")))
    print(f"\nDone — {svg_count} SVG figures written to {FIG_DIR.resolve()}")


if __name__ == "__main__":
    main()