#!/usr/bin/env python3
"""
Generate speedup and efficiency bar charts from benchmark CSV results.

Expected directory structure:
  results_valide/results_csv/
    sequential/   *.csv
    static/       *.csv
    dynamic/      *.csv

Each CSV has columns: T0[,T1,...,Tn], score, Trimmed Mean, STD Dev, STD Dev %
The script matches files across folders by their common stem prefix.
Figures are saved as SVG in the figures/ directory.
"""

import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MultipleLocator

matplotlib.use("Agg")

# ── Configuration ────────────────────────────────────────────────────────────
BASE_DIR   = Path("results_valide/results_csv")
SEQ_DIR    = BASE_DIR / "sequential"
STATIC_DIR = BASE_DIR / "static"
DYN_DIR    = BASE_DIR / "dynamic"
FIG_DIR    = Path("figures")
NUM_CORES  = 64          # number of cores used for parallel runs

# Colour palette (close to the reference image)
BLUE   = "#4472C4"
ORANGE = "#ED7D31"
RED    = "#FF0000"

# ── Helpers ──────────────────────────────────────────────────────────────────

def stem_key(filename: str) -> str:
    """
    Derive a canonical program name from a filename so that:
      heat-2d.csv / heat-2d-static.csv / heat-2d-dynamic.csv  →  'heat-2d'
      game-of-life.csv / game-of-life-static.csv              →  'game-of-life'
    """
    name = Path(filename).stem          # strip .csv
    name = re.sub(r'[-_](static|dynamic)$', '', name, flags=re.IGNORECASE)
    return name


def best_trimmed_mean(csv_path: Path) -> float | None:
    """Return the minimum Trimmed Mean found in a CSV (best = fastest run)."""
    try:
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        col = next((c for c in df.columns if c.lower().replace(' ', '') == 'trimmedmean'), None)
        if col is None:
            # fall back to 'score'
            col = next((c for c in df.columns if c.lower() == 'score'), None)
        if col is None:
            print(f"  [WARN] No timing column found in {csv_path}", file=sys.stderr)
            return None
        return float(df[col].min())
    except Exception as exc:
        print(f"  [WARN] Could not read {csv_path}: {exc}", file=sys.stderr)
        return None


def collect_files(directory: Path) -> dict[str, Path]:
    """Return {stem_key: path} for every CSV in directory."""
    result = {}
    if not directory.exists():
        return result
    for p in directory.glob("*.csv"):
        result[stem_key(p.name)] = p
    return result


# ── Data loading ─────────────────────────────────────────────────────────────

def build_speedup_table() -> pd.DataFrame:
    """
    Build a DataFrame with columns [program, speedup_static, speedup_dynamic].
    speedup = sequential_time / parallel_time
    """
    seq_files = collect_files(SEQ_DIR)
    sta_files = collect_files(STATIC_DIR)
    dyn_files = collect_files(DYN_DIR)

    # All programs that have at least one parallel variant AND a sequential reference
    all_programs = (set(sta_files) | set(dyn_files)) & set(seq_files)

    rows = []
    for prog in sorted(all_programs):
        seq_time = best_trimmed_mean(seq_files[prog])
        if seq_time is None:
            continue

        sta_time = best_trimmed_mean(sta_files[prog]) if prog in sta_files else None
        dyn_time = best_trimmed_mean(dyn_files[prog]) if prog in dyn_files else None

        speedup_sta = (seq_time / sta_time) if sta_time else np.nan
        speedup_dyn = (seq_time / dyn_time) if dyn_time else np.nan

        rows.append({
            "program":        prog,
            "speedup_static":  speedup_sta,
            "speedup_dynamic": speedup_dyn,
        })

    df = pd.DataFrame(rows)

    # Append an Average row
    avg_sta = df["speedup_static"].mean(skipna=True)
    avg_dyn = df["speedup_dynamic"].mean(skipna=True)
    df = pd.concat([df, pd.DataFrame([{
        "program": "Average",
        "speedup_static":  avg_sta,
        "speedup_dynamic": avg_dyn,
    }])], ignore_index=True)

    return df


# ── Plotting ─────────────────────────────────────────────────────────────────

def pretty_label(name: str) -> str:
    """Make program names a bit nicer for display."""
    return name.replace("-", "\u2011")   # non-breaking hyphen keeps label tidy


def make_bar_chart(
    df: pd.DataFrame,
    col_static: str,
    col_dynamic: str,
    ylabel: str,
    title: str,
    out_path: Path,
    reference_line: float = 1.0,
):
    programs = df["program"].tolist()
    n = len(programs)
    x = np.arange(n)
    width = 0.35

    # Separate Average from the rest for a visual gap
    is_avg = [p == "Average" for p in programs]

    fig, ax = plt.subplots(figsize=(max(10, n * 0.85), 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    val_sta = df[col_static].to_numpy(dtype=float)
    val_dyn = df[col_dynamic].to_numpy(dtype=float)

    bars_sta = ax.bar(x - width / 2, val_sta, width, color=BLUE,   zorder=3, label="Pesto vs Pluto (static)")
    bars_dyn = ax.bar(x + width / 2, val_dyn, width, color=ORANGE, zorder=3, label="Pesto vs Pluto (dynamic)")

    # Value labels on bars
    for bar in bars_sta:
        h = bar.get_height()
        if np.isnan(h):
            continue
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01,
                f"{h:.2f}", ha="center", va="bottom", fontsize=7.5, color="black")
    for bar in bars_dyn:
        h = bar.get_height()
        if np.isnan(h):
            continue
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01,
                f"{h:.2f}", ha="center", va="bottom", fontsize=7.5, color="black")

    # Reference horizontal line
    ax.axhline(reference_line, color=RED, linewidth=1.4, zorder=4)

    # Vertical separator before Average
    if any(is_avg):
        avg_idx = programs.index("Average")
        ax.axvline(avg_idx - 0.55, color="#cccccc", linewidth=0.8, linestyle="--", zorder=2)

    # Axes styling
    ax.set_xticks(x)
    ax.set_xticklabels([pretty_label(p) for p in programs],
                       rotation=40, ha="right", fontsize=9)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10,
                 fontfamily="serif")
    ax.yaxis.set_minor_locator(MultipleLocator(0.1))
    ax.grid(axis="y", which="major", linestyle="--", linewidth=0.5,
            color="#dddddd", zorder=0)
    ax.set_xlim(-0.6, n - 0.4)

    # Legend
    patch_sta = mpatches.Patch(color=BLUE,   label="Pesto vs Pluto (static)")
    patch_dyn = mpatches.Patch(color=ORANGE, label="Pesto vs Pluto (dynamic)")
    ax.legend(handles=[patch_sta, patch_dyn], loc="upper right", fontsize=9,
              framealpha=0.9, edgecolor="#cccccc")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {out_path}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Building speedup table …")
    df = build_speedup_table()

    if df.empty:
        print("ERROR: no data found. Check that BASE_DIR is correct and CSVs exist.")
        sys.exit(1)

    print(df.to_string(index=False))
    print()

    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # ── Figure 1 : Speedup ────────────────────────────────────────────────
    print("Generating speedup chart …")
    make_bar_chart(
        df,
        col_static="speedup_static",
        col_dynamic="speedup_dynamic",
        ylabel="Speedup  (sequential / parallel)",
        title="Speedup — Pluto",
        out_path=FIG_DIR / "speedup.svg",
        reference_line=1.0,
    )

    # ── Figure 2 : Efficiency ─────────────────────────────────────────────
    df_eff = df.copy()
    df_eff["speedup_static"]  = df_eff["speedup_static"]  / NUM_CORES
    df_eff["speedup_dynamic"] = df_eff["speedup_dynamic"] / NUM_CORES

    print("Generating efficiency chart …")
    make_bar_chart(
        df_eff,
        col_static="speedup_static",
        col_dynamic="speedup_dynamic",
        ylabel=f"Efficiency  (speedup / {NUM_CORES} cores)",
        title=f"Efficiency — Pluto  ({NUM_CORES} cores)",
        out_path=FIG_DIR / "efficiency.svg",
        reference_line=1 / NUM_CORES,
    )

    print("\nDone. SVG figures written to:", FIG_DIR.resolve())


if __name__ == "__main__":
    main()