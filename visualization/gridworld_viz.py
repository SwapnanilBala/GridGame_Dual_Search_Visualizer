# The File Reponsible for the Visualization of the Gridworld and the Comparison of Search Algorithm Results

from __future__ import annotations

from pathlib import Path

from datetime import datetime


def build_comparison_figure(
    algo1: str,
    algo1_res,
    algo2: str,
    algo2_res,
    map_name: str,
):
    
    """  Build and return a matplotlib Figure with bar charts + results table.  """

    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    from matplotlib.transforms import Bbox

    # ── Palette ──────────────────────────────────────────────────────────────
    BG       = "black"
    TEXT_COL = "whitesmoke"
    DIM_COL  = "slategray"
    COL1     = "royalblue"        # algo 1
    COL2     = "orange"           # algo 2
    COL_WIN  = "limegreen"        # winner highlight
    COL_FAIL = "tomato"           # not found
    BORDER_COL    = "darkslategray"
    GRID_LINE_COL = "dimgray"
    ROW_BG        = "midnightblue"
    HEADER_BG     = "darkslateblue"
    HEADER_BORDER = "slateblue"
    CELL_BG       = "black"

    # ── Data ─────────────────────────────────────────────────────────────────
    def _val(result, attr):
        if not result.found and attr in ("cost", "path_len"):
            return None
        if attr == "path_len":
            return len(result.path)
        return getattr(result, attr)

    metrics = [
        ("Nodes\nExpanded",  "expanded"),
        ("Max Nodes\nWaiting\nTo Explore", "maximum_nodes_waiting_to_be_explored"),
        ("Path\nCost",       "cost"),
        ("Path\nLength",     "path_len"),
    ]

    v1 = [_val(algo1_res, m[1]) for m in metrics]
    v2 = [_val(algo2_res, m[1]) for m in metrics]

    # ── Figure ───────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(12, 6), facecolor=BG)
    gs  = gridspec.GridSpec(2, 4, figure=fig, hspace=0.55, wspace=0.45,
                            top=0.88, bottom=0.12, left=0.06, right=0.97)

    fig.suptitle(
        f"Algorithm Comparison  —  {map_name}",
        color=TEXT_COL, fontsize=14, fontweight="bold", y=0.97,
    )

    # ── Bar charts (top row) ─────────────────────────────────────────────────
    for col_idx, (label, attr) in enumerate(metrics):
        ax = fig.add_subplot(gs[0, col_idx])
        ax.set_facecolor(BG)
        ax.spines[:].set_color(BORDER_COL)
        ax.tick_params(colors=DIM_COL, labelsize=8)
        ax.yaxis.label.set_color(DIM_COL)

        a1 = v1[col_idx]
        a2 = v2[col_idx]

        bars_x  = [0.35, 1.15]
        heights = [a1 if a1 is not None else 0,
                   a2 if a2 is not None else 0]
        colors  = [COL1, COL2]

        bars = ax.bar(bars_x, heights, width=0.55, color=colors,
                      edgecolor="none", zorder=3)
        ax.set_xticks(bars_x)
        ax.set_xticklabels(
            [algo1.upper(), algo2.upper()],
            fontsize=7, color=TEXT_COL,
        )
        ax.set_title(label, color=TEXT_COL, fontsize=8.5, pad=4)
        ax.set_xlim(-0.1, 1.65)
        ax.yaxis.set_tick_params(labelsize=7)
        ax.grid(axis="y", color=GRID_LINE_COL, linewidth=0.6, zorder=0)

        for bar, val, is_none in zip(bars, [a1, a2], [a1 is None, a2 is None]):
            if is_none:
                ax.text(bar.get_x() + bar.get_width() / 2, 0.5,
                        "N/A", ha="center", va="bottom",
                        fontsize=6, color=COL_FAIL, fontweight="bold")
            else:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() * 1.02,
                        f"{val:.1f}" if isinstance(val, float) and val != int(val) else str(int(val)) if val is not None else "N/A",
                        ha="center", va="bottom",
                        fontsize=6, color=TEXT_COL, fontweight="bold")

    # ── Table (bottom row, full width) ───────────────────────────────────────
    ax_tbl = fig.add_subplot(gs[1, :])
    ax_tbl.set_facecolor(BG)
    ax_tbl.axis("off")

    def _fmt(val, attr):
        if val is None:
            return "—"
        if attr == "cost":
            return f"{val:.2f}"
        return str(int(val))

    def _winner_char(v1, v2):
        """Return (w1_wins, w2_wins) bool tuple. Lower is better for all metrics."""
        if v1 is None and v2 is None:
            return False, False
        if v1 is None:
            return False, True
        if v2 is None:
            return True, False
        return v1 < v2, v2 < v1

    row_labels  = ["Found", "Path Cost", "Path Length",
                   "Nodes Expanded", "Max Nodes Waiting To Explore", "Winner (↓ better)"]
    row_attrs   = ["found", "cost", "path_len", "expanded", "maximum_nodes_waiting_to_be_explored", "__winner__"]

    # Count wins (lower is better for numerical metrics)
    num_metrics = ["cost", "path_len", "expanded", "maximum_nodes_waiting_to_be_explored"]
    w1_total, w2_total = 0, 0
    for attr in num_metrics:
        a, b = _winner_char(_val(algo1_res, attr), _val(algo2_res, attr))
        if a: w1_total += 1
        if b: w2_total += 1

    table_data  = []
    cell_colors = []
    for label, attr in zip(row_labels, row_attrs):
        if attr == "found":
            c1 = "Yes" if algo1_res.found else "No"
            c2 = "Yes" if algo2_res.found else "No"
            cc1 = COL_WIN if algo1_res.found else COL_FAIL
            cc2 = COL_WIN if algo2_res.found else COL_FAIL
        elif attr == "__winner__":
            c1 = f"{w1_total} / {len(num_metrics)}"
            c2 = f"{w2_total} / {len(num_metrics)}"
            cc1 = COL_WIN if w1_total > w2_total else (DIM_COL if w1_total == w2_total else COL_FAIL)
            cc2 = COL_WIN if w2_total > w1_total else (DIM_COL if w1_total == w2_total else COL_FAIL)
        else:
            c1 = _fmt(_val(algo1_res, attr), attr)
            c2 = _fmt(_val(algo2_res, attr), attr)
            a, b = _winner_char(_val(algo1_res, attr), _val(algo2_res, attr))
            cc1 = COL_WIN if a else TEXT_COL
            cc2 = COL_WIN if b else TEXT_COL

        table_data.append([label, c1, c2])
        cell_colors.append([ROW_BG, cc1, cc2])

    col_headers = ["Metric", algo1.upper(), algo2.upper()]
    tbl = ax_tbl.table(
        cellText=table_data,
        colLabels=col_headers,
        cellLoc="center",
        loc="center",
        bbox=Bbox.from_extents(0.0, -0.15, 1.0, 1.15),
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)

    # Style header row
    for col_idx, header in enumerate(col_headers):
        cell = tbl[0, col_idx]
        cell.set_facecolor(HEADER_BG)
        cell.set_text_props(color=TEXT_COL, fontweight="bold")
        cell.set_edgecolor(HEADER_BORDER)

    # Style data rows
    for row_idx, (row_data, row_cc) in enumerate(zip(table_data, cell_colors)):
        for col_idx in range(3):
            cell = tbl[row_idx + 1, col_idx]
            cell.set_facecolor(row_cc[col_idx] if col_idx == 0 else CELL_BG)
            cell.set_text_props(
                color=row_cc[col_idx] if col_idx > 0 else DIM_COL,
                fontweight="bold" if col_idx > 0 else "normal",
            )
            cell.set_edgecolor(GRID_LINE_COL)

    return fig


def save_comparison_jpg(
    algo1: str,
    algo1_res,
    algo2: str,
    algo2_res,
    map_name: str,
    out_path: "str | Path",
) -> None:
    
    """
        Build a comparison figure using the results of two search algorithms on a given map
    and save the resulting figure as a JPEG image to the specified output path.
    
    """

    import matplotlib.pyplot as plt

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig = build_comparison_figure(algo1, algo1_res, algo2, algo2_res, map_name)
    fig.savefig(out_path, format="jpeg", dpi=150,
                bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
