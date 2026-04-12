from __future__ import annotations

import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pygame

from env.gridworld import WALL, START, GOAL, ROAD, MUD, WATER

State = tuple[int, int]

#  Shared colour palette 
BG_DARK     = (10,  12,  18)
BG_PANEL    = (16,  20,  30)
BG_CARD     = (22,  28,  42)
BORDER_DIM  = (45,  55,  75)
BORDER_LIT  = (70,  90, 130)

TEXT_BRIGHT = (240, 245, 255)
TEXT_MID    = (170, 185, 210)
TEXT_DIM    = (100, 115, 140)

ACCENT_CYAN  = (  0, 210, 230)
ACCENT_PINK  = (255,  80, 160)
ACCENT_LIME  = ( 80, 255, 140)
ACCENT_AMBER = (255, 190,  40)
ACCENT_TEAL  = (  0, 170, 150)

WALL_COL   = ( 28,  32,  45)
FLOOR_COL  = (210, 220, 235)
START_COL  = (255,  70, 100)
GOAL_COL   = ( 50, 240, 130)
TERRAIN_R  = (230, 220, 180)
TERRAIN_M  = (160, 110,  70)
TERRAIN_W  = ( 60, 130, 220)

# Per-algo overlay colours (RGBA)
EXP1_NORMAL  = (100, 130, 255,  90)
EXP1_RECENT  = (150, 180, 255, 200)
EXP1_CURRENT = (200, 220, 255)
EXP2_NORMAL  = (255, 160,  60,  90)
EXP2_RECENT  = (255, 200, 100, 200)
EXP2_CURRENT = (255, 240, 160)
PATH_OVERLAY   = (120, 255, 170, 70)
PATH_LINE      = (70, 255, 150)
PATH_LINE_GLOW = (20, 120, 70)

TRAIL_LEN = 8

FRONTIER1_COL = (255, 255, 80, 70)
FRONTIER2_COL = (255, 255, 80, 70)


# Helpers 

def _lerp(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def _tile_base(ch: str) -> tuple:
    if ch == WALL:  return WALL_COL
    if ch == START: return START_COL
    if ch == GOAL:  return GOAL_COL
    return {
        ROAD:  TERRAIN_R,
        MUD:   TERRAIN_M,
        WATER: TERRAIN_W,
    }.get(ch, FLOOR_COL)


def _draw_path_line(
    screen: pygame.Surface,
    origin_x: int,
    origin_y: int,
    cell: int,
    path_states: list[State],
) -> None:
    if not path_states:
        return

    points = [
        (origin_x + c * cell + cell // 2, origin_y + r * cell + cell // 2)
        for r, c in path_states
    ]
    if len(points) == 1:
        pygame.draw.circle(screen, PATH_LINE, points[0], max(3, cell // 4))
        return

    glow_width = max(6, cell // 2)
    line_width = max(3, cell // 5)
    pygame.draw.lines(screen, PATH_LINE_GLOW, False, points, glow_width)
    pygame.draw.lines(screen, PATH_LINE, False, points, line_width)


def _draw_grid(
    screen: pygame.Surface,
    grid: list[list[str]],
    origin_x: int,
    origin_y: int,
    cell: int,
    expanded: set,
    expanded_order: list,
    trace_i: int,
    trace: list,
    path_states: list[State],
    exp_normal: tuple,
    exp_recent: tuple,
    exp_current: tuple,
    show_path: bool,
    frontier: set | None = None,
    frontier_col: tuple = (255, 255, 80, 70),
) -> None:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    radius = 0 if cell < 18 else max(3, cell // 6)
    trail_start = max(0, len(expanded_order) - TRAIL_LEN)
    recent_set  = set(expanded_order[trail_start:])
    shown_path = set(path_states) if show_path else set()
    overlay = pygame.Surface((cell, cell), pygame.SRCALPHA)

    for r in range(rows):
        for c in range(cols):
            ch = grid[r][c]
            x  = origin_x + c * cell
            y  = origin_y + r * cell
            rect = pygame.Rect(x, y, cell, cell)

            # Base tile
            pygame.draw.rect(screen, _tile_base(ch), rect, border_radius=radius)
            pygame.draw.rect(screen, (0, 0, 0, 20), rect, 1, border_radius=radius)

            state = (r, c)

            # Expanded overlay
            if state in expanded and ch != WALL:
                overlay.fill(exp_recent if state in recent_set else exp_normal)
                screen.blit(overlay, (x, y))

            # Frontier overlay (pulsing)
            if frontier and state in frontier and ch != WALL:
                pulse = 0.5 + 0.5 * math.sin(time.time() * 8)
                alpha = int(frontier_col[3] * (0.5 + 0.5 * pulse))
                overlay.fill((frontier_col[0], frontier_col[1], frontier_col[2], alpha))
                screen.blit(overlay, (x, y))

            # Current-node pulse
            if not show_path and trace_i > 0 and state == trace[trace_i - 1] and ch != WALL:
                pulse = 0.6 + 0.4 * math.sin(time.time() * 10)
                sz = max(4, int(cell * 0.42 * pulse))
                pygame.draw.circle(screen, exp_current, rect.center, sz)

            # Path overlay (after trace completes)
            if show_path and state in shown_path and ch not in (START, GOAL, WALL):
                overlay.fill(PATH_OVERLAY)
                screen.blit(overlay, (x, y))

            # Start / goal
            if ch == START:
                pygame.draw.rect(screen, START_COL, rect, border_radius=radius)
            elif ch == GOAL:
                pygame.draw.rect(screen, GOAL_COL, rect, border_radius=radius)

            # Terrain labels
            if ch in (MUD, WATER, ROAD) and cell >= 18:
                fnt = pygame.font.SysFont("", max(14, int(cell * 0.46)))
                lbl = fnt.render(ch, True, (20, 20, 20))
                screen.blit(lbl, (rect.right - lbl.get_width() - 4, rect.y + 3))

                # Step cost label (bottom-left)
                cost_map = {ROAD: 1, MUD: 5, WATER: 10}
                cost_lbl = fnt.render(str(cost_map[ch]), True, (100, 100, 100))
                screen.blit(cost_lbl, (rect.x + 3, rect.bottom - cost_lbl.get_height() - 2))

            # Grid line
            pygame.draw.rect(screen, (0, 0, 0, 25), rect, 1, border_radius=radius)

    if show_path:
        _draw_path_line(screen, origin_x, origin_y, cell, path_states)


#  run_trace_viewer (single-mode, backward compat) 

def run_trace_viewer(
    grid: list[list[str]],
    trace: list[State],
    path: list[State] | None,
    cell_size: int = 30,
    start_fps: int = 15,
    title_line1: str = "",
    title_line2: str = "",
) -> None:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if rows == 0 or cols == 0:
        raise ValueError("Grid is empty.")

    pygame.init()
    PAD   = max(8, cell_size // 5)
    HUD_H = max(82, cell_size + 52)
    screen_w = cols * cell_size + PAD * 2
    screen_h = rows * cell_size + PAD * 2 + HUD_H
    info = pygame.display.Info()
    os.environ["SDL_VIDEO_WINDOW_POS"] = (
        f"{(info.current_w - screen_w) // 2},{(info.current_h - screen_h) // 2}"
    )
    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("GridWorld Search Visualization")
    clock  = pygame.font.SysFont("", max(22, int(cell_size * 0.72)))
    clock_ = pygame.time.Clock()
    font   = pygame.font.SysFont("", max(22, int(cell_size * 0.72)))
    font_s = pygame.font.SysFont("", max(18, int(cell_size * 0.56)))

    i = 0
    paused = False
    fps = start_fps
    expanded: set[State] = set()
    expanded_order: list[State] = []
    path_list = list(path) if path else []

    running = True
    while running:
        clock_.tick(fps)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_UP:
                    fps = min(240, fps + 10)
                elif event.key == pygame.K_DOWN:
                    fps = max(5, fps - 10)
                elif event.key == pygame.K_r:
                    i = 0; expanded.clear(); expanded_order.clear()
                    paused = False

        if not paused and i < len(trace):
            expanded.add(trace[i]); expanded_order.append(trace[i]); i += 1

        show_path = i >= len(trace) and bool(path_list)
        shown_path = path_list if show_path else []

        screen.fill(BG_DARK)
        # HUD bar
        pygame.draw.rect(screen, BG_PANEL, (0, 0, screen_w, HUD_H))
        pygame.draw.line(screen, BORDER_DIM, (0, HUD_H - 1), (screen_w, HUD_H - 1), 2)
        y_txt = 10
        if title_line1:
            s = font.render(title_line1, True, TEXT_BRIGHT)
            screen.blit(s, (12, y_txt)); y_txt += s.get_height() + 2
        if title_line2:
            s = font_s.render(title_line2, True, TEXT_MID)
            screen.blit(s, (12, y_txt)); y_txt += s.get_height() + 2
        hud = font_s.render(
            f"step {i}/{len(trace)}  fps {fps}  {'PAUSED' if paused else 'RUNNING'}",
            True, TEXT_DIM,
        )
        screen.blit(hud, (12, y_txt))

        _draw_grid(
            screen, grid, PAD, HUD_H + PAD, cell_size,
            expanded, expanded_order, i, trace,
            shown_path,
            EXP1_NORMAL, EXP1_RECENT, EXP1_CURRENT, show_path,
        )
        pygame.display.flip()

    pygame.quit()


#  run_dual_viewer 

def run_dual_viewer(
    grid: list[list[str]],
    trace1: list[State],
    algo1_res: Any,
    trace2: list[State],
    algo2_res: Any,
    algo1: str,
    algo2: str,
    map_name: str,
    fps: int = 15,
    cell_size: int = 38,
    analysis_dir: Path | None = None,
) -> None:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if rows == 0 or cols == 0:
        raise ValueError("Grid is empty.")

    PAD      = 16
    DIVIDER  = 12
    HUD_H    = 130
    FOOTER_H = 66

    GRID_W  = cols * cell_size + PAD * 2
    GRID_H  = rows * cell_size + PAD * 2
    screen_w = GRID_W * 2 + DIVIDER
    screen_h = HUD_H + GRID_H + FOOTER_H

    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("GridWorld — Dual Search Viewer")
    clock = pygame.time.Clock()

    font_lg = pygame.font.SysFont("consolas", max(26, cell_size // 2 + 6), bold=True)
    font_md = pygame.font.SysFont("consolas", max(22, cell_size // 2), bold=True)
    font_sm = pygame.font.SysFont("consolas", max(18, cell_size // 3))

    #  Playback state 
    i1 = i2 = 0
    exp1: set[State] = set(); ord1: list[State] = []
    exp2: set[State] = set(); ord2: list[State] = []
    path1 = algo1_res.path if algo1_res.found else []
    path2 = algo2_res.path if algo2_res.found else []
    phase = "trace"    # "trace" | "done"
    popup_triggered = False
    paused = False
    start_time = time.time()
    elapsed = 0.0
    show_frontier = False

    ox_left  = 0
    ox_right = GRID_W + DIVIDER

    def _draw_hud():
        pygame.draw.rect(screen, BG_PANEL, (0, 0, screen_w, HUD_H))
        pygame.draw.line(screen, BORDER_DIM, (0, HUD_H - 1), (screen_w, HUD_H - 1), 2)

        # Row 1: map name
        title = font_lg.render(f"MAP:  {map_name}", True, ACCENT_CYAN)
        screen.blit(title, ((screen_w - title.get_width()) // 2, 10))

        # Row 2: algo names + steps
        a1_lbl = font_md.render(f"ALGO 1:  {algo1.upper()}", True, (150, 180, 255))
        a2_lbl = font_md.render(f"ALGO 2:  {algo2.upper()}", True, (255, 200, 100))
        screen.blit(a1_lbl, (16, 48))
        screen.blit(a2_lbl, (screen_w - a2_lbl.get_width() - 16, 48))
        step_txt = font_sm.render(
            f"L: {i1}/{len(trace1)}   R: {i2}/{len(trace2)}", True, TEXT_MID,
        )
        screen.blit(step_txt, ((screen_w - step_txt.get_width()) // 2, 52))

        # Row 3: expanded counts + timer + fps + phase
        e1 = font_sm.render(f"expanded: {len(exp1)}", True, (150, 180, 255))
        e2 = font_sm.render(f"expanded: {len(exp2)}", True, (255, 200, 100))
        time_mm = int(elapsed) // 60
        time_ss = elapsed % 60
        time_lbl = font_sm.render(f"{time_mm:02d}:{time_ss:04.1f}", True, ACCENT_AMBER)
        fps_lbl = font_sm.render(
            f"fps {fps}  {'PAUSED' if paused else phase.upper()}", True, TEXT_DIM,
        )
        screen.blit(e1, (16, 84))
        screen.blit(e2, (screen_w - e2.get_width() - 16, 84))
        center_x = (screen_w - time_lbl.get_width() - 16 - fps_lbl.get_width()) // 2
        screen.blit(time_lbl, (center_x, 84))
        screen.blit(fps_lbl, (center_x + time_lbl.get_width() + 16, 84))

        # Row 4: separator + hint
        pygame.draw.line(screen, BORDER_DIM, (0, 116), (screen_w, 116), 1)
        hint = font_sm.render("SPACE pause   R restart   F frontier   ESC/Q back", True, TEXT_DIM)
        screen.blit(hint, ((screen_w - hint.get_width()) // 2, 122))

    def _draw_footer():
        fy = HUD_H + GRID_H
        pygame.draw.rect(screen, BG_PANEL, (0, fy, screen_w, FOOTER_H))
        pygame.draw.line(screen, BORDER_DIM, (0, fy), (screen_w, fy), 1)

        # Progress bars (5px tall) at top of footer
        BAR_H = 5
        BAR_BG = (30, 35, 50)
        ALGO1_BAR = (100, 130, 255)
        ALGO2_BAR = (255, 160, 60)
        pygame.draw.rect(screen, BAR_BG, (0, fy, GRID_W, BAR_H))
        if len(trace1) > 0:
            fill_w = int(GRID_W * i1 / len(trace1))
            pygame.draw.rect(screen, ALGO1_BAR, (0, fy, fill_w, BAR_H))
        pygame.draw.rect(screen, BAR_BG, (GRID_W + DIVIDER, fy, GRID_W, BAR_H))
        if len(trace2) > 0:
            fill_w = int(GRID_W * i2 / len(trace2))
            pygame.draw.rect(screen, ALGO2_BAR, (GRID_W + DIVIDER, fy, fill_w, BAR_H))

        if algo1_res.found:
            r1 = font_md.render(
                f"{algo1.upper()}  cost={algo1_res.cost:.1f}  path={len(algo1_res.path)}  exp={algo1_res.expanded}",
                True, (150, 180, 255),
            )
            screen.blit(r1, (16, fy + 18))
        if algo2_res.found:
            r2 = font_md.render(
                f"{algo2.upper()}  cost={algo2_res.cost:.1f}  path={len(algo2_res.path)}  exp={algo2_res.expanded}",
                True, (255, 200, 100),
            )
            screen.blit(r2, (screen_w - r2.get_width() - 16, fy + 18))

    def _draw_divider():
        pygame.draw.rect(screen, ACCENT_TEAL, (GRID_W, HUD_H, DIVIDER, GRID_H))

    running = True
    while running:
        clock.tick(fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_f:
                    show_frontier = not show_frontier
                elif event.key == pygame.K_r:
                    i1 = i2 = 0
                    exp1.clear(); ord1.clear()
                    exp2.clear(); ord2.clear()
                    phase = "trace"
                    popup_triggered = False
                    paused = False
                    start_time = time.time()
                    elapsed = 0.0
                    show_frontier = False

        if not paused:
            if i1 < len(trace1):
                exp1.add(trace1[i1]); ord1.append(trace1[i1]); i1 += 1
            if i2 < len(trace2):
                exp2.add(trace2[i2]); ord2.append(trace2[i2]); i2 += 1
            if i1 >= len(trace1) and i2 >= len(trace2):
                phase = "done"

        # Update elapsed time
        if not paused and phase != "done":
            elapsed = time.time() - start_time

        # Trigger analysis popup once
        if phase == "done" and not popup_triggered:
            popup_triggered = True
            _trigger_analysis(
                algo1, algo1_res, algo2, algo2_res,
                map_name, analysis_dir,
            )

        #  Draw 
        screen.fill(BG_DARK)
        _draw_hud()
        _draw_divider()

        show_path1 = i1 >= len(trace1) and bool(path1)
        show_path2 = i2 >= len(trace2) and bool(path2)

        # Compute frontier if toggled on
        fr1 = set()
        fr2 = set()
        if show_frontier and phase == "trace":
            for s in exp1:
                r, c = s
                for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nb = (r+dr, c+dc)
                    nr, nc = nb
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != WALL and nb not in exp1:
                        fr1.add(nb)
            for s in exp2:
                r, c = s
                for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nb = (r+dr, c+dc)
                    nr, nc = nb
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != WALL and nb not in exp2:
                        fr2.add(nb)

        _draw_grid(
            screen, grid, ox_left + PAD, HUD_H + PAD, cell_size,
            exp1, ord1, i1, trace1, path1 if show_path1 else [],
            EXP1_NORMAL, EXP1_RECENT, EXP1_CURRENT, show_path1,
            frontier=fr1, frontier_col=FRONTIER1_COL,
        )
        _draw_grid(
            screen, grid, ox_right + PAD, HUD_H + PAD, cell_size,
            exp2, ord2, i2, trace2, path2 if show_path2 else [],
            EXP2_NORMAL, EXP2_RECENT, EXP2_CURRENT, show_path2,
            frontier=fr2, frontier_col=FRONTIER2_COL,
        )
        _draw_footer()
        pygame.display.flip()


def _trigger_analysis(
    algo1: str, algo1_res: Any,
    algo2: str, algo2_res: Any,
    map_name: str,
    analysis_dir: Path | None,
) -> None:
    """Save JPG then open interactive matplotlib popup."""
    if analysis_dir is not None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = map_name.replace(".txt", "")
        fname = f"{algo1}_vs_{algo2}__{stem}__{ts}.jpg"
        out_path = Path(analysis_dir) / fname
        try:
            from visualization.gridworld_viz import save_comparison_jpg
            save_comparison_jpg(
                algo1, algo1_res,
                algo2, algo2_res,
                map_name, out_path,
            )
            print(f"Analysis saved → {out_path}")
        except Exception as exc:
            print(f"[analysis] save failed: {exc}")

    # Interactive popup (blocks until closed; pygame window stays visible behind it)
    try:
        import matplotlib.pyplot as plt
        from visualization.gridworld_viz import build_comparison_figure

        fig = build_comparison_figure(
            algo1, algo1_res, algo2, algo2_res, map_name,
        )
        plt.show()
        plt.close(fig)

    except Exception as exc:
        print(f"[analysis] popup failed: {exc}")


#  run_launcher 

def run_launcher(
    maps: list[Path],
    algos: list[str],
    run_once: Callable[[Path, str], tuple[Any, Any, list[State]]],
    cell_size: int = 38,
    start_fps: int = 15,
    analysis_dir: Path | None = None,
) -> None:
    """Interactive launcher: pick two algos + map, then run dual viewer."""
    if not maps:
        raise ValueError("No maps found.")
    if not algos:
        raise ValueError("No algorithms provided.")

    W, H = 1280, 720
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("GridWorld — Dual Search Launcher")
    clock = pygame.time.Clock()

    ft = pygame.font.SysFont("consolas", 48, bold=True)
    fm = pygame.font.SysFont("consolas", 32, bold=True)
    fn = pygame.font.SysFont("consolas", 28)
    fh = pygame.font.SysFont("consolas", 21)

    map_i   = 0
    algo1_i = 0
    algo2_i = min(1, len(algos) - 1)
    fps     = max(5, min(120, start_fps))
    t0      = time.time()

    def _draw_launcher():
        t = time.time() - t0

        #  Gradient background 
        for y in range(H):
            col = _lerp((12, 14, 20), (22, 28, 44), y / H)
            pygame.draw.line(screen, col, (0, y), (W, y))

        #  Top animated accent stripe 
        sw2 = 200
        sx = int((math.sin(t * 0.8) * 0.5 + 0.5) * (W - sw2))
        ss = pygame.Surface((sw2, 4), pygame.SRCALPHA)
        ss.fill((*ACCENT_CYAN, 110))
        screen.blit(ss, (sx, 0))

        #  Title 
        glow = int(180 + 75 * math.sin(t * 2.2))
        title_col = (glow, glow, 255)
        title = ft.render("GRIDWORLD   DUAL   SEARCH", True, title_col)
        screen.blit(title, ((W - title.get_width()) // 2, 24))

        # Separator
        lny = 92
        pygame.draw.line(screen, ACCENT_CYAN, (60, lny), (W - 60, lny), 2)

        #  Helper: draw card 
        def card(x, y, w, h, label, label_col, value, idx, total, arrow_col):
            pygame.draw.rect(screen, BG_CARD, (x, y, w, h), border_radius=10)
            pygame.draw.rect(screen, BORDER_DIM, (x, y, w, h), 2, border_radius=10)
            lbl_surf = fm.render(label, True, label_col)
            screen.blit(lbl_surf, (x + 12, y + 8))
            font_center_render(fn, value, TEXT_BRIGHT, x, y, w, h, dx=0, dy=10)
            arr = fn.render("<", True, arrow_col)
            arr2 = fn.render(">", True, arrow_col)
            screen.blit(arr,  (x + 18, y + h // 2 + 4))
            screen.blit(arr2, (x + w - 18 - arr2.get_width(), y + h // 2 + 4))
            ctr_lbl = fh.render(f"{idx + 1} / {total}", True, TEXT_DIM)
            screen.blit(ctr_lbl, (x + w - ctr_lbl.get_width() - 12, y + 10))

        def font_center_render(font_obj, text, color, cx, cy, cw, ch, dx=0, dy=0):
            s = font_obj.render(text, True, color)
            bx = cx + (cw - s.get_width()) // 2 + dx
            by = cy + (ch - s.get_height()) // 2 + dy
            screen.blit(s, (bx, by))
            return s

        arr_col = _lerp(TEXT_DIM, TEXT_BRIGHT, 0.5 + 0.5 * math.sin(t * 3))

        #  MAP CARD 
        card(50, 108, W - 100, 104, "MAP", ACCENT_CYAN,
             maps[map_i].name, map_i, len(maps), arr_col)

        #  DUAL ALGO ROW 
        half = (W - 100 - 24) // 2
        arr2_col = _lerp(TEXT_DIM, TEXT_BRIGHT, 0.5 + 0.5 * math.sin(t * 3 + 1))

        card(50, 236, half, 124, "ALGO 1  (A / D)",
             (150, 180, 255), algos[algo1_i].upper(), algo1_i, len(algos), arr2_col)

        card(50 + half + 24, 236, half, 124, "ALGO 2  (J / L)",
             ACCENT_PINK, algos[algo2_i].upper(), algo2_i, len(algos), arr2_col)

        #  FPS CARD 
        fx, fy, fw, fh_ = 50, 384, W - 100, 90
        pygame.draw.rect(screen, BG_CARD, (fx, fy, fw, fh_), border_radius=12)
        pygame.draw.rect(screen, BORDER_DIM, (fx, fy, fw, fh_), 2, border_radius=12)
        fps_lbl = fm.render("ANIMATION FPS  (UP / DOWN)", True, ACCENT_AMBER)
        screen.blit(fps_lbl, (fx + 16, fy + 10))
        fps_val = ft.render(str(fps), True, ACCENT_AMBER)
        screen.blit(fps_val, (fx + (fw - fps_val.get_width()) // 2, fy + 30))
        rng = fh.render("5 — 120", True, TEXT_DIM)
        screen.blit(rng, (fx + fw - rng.get_width() - 16, fy + 12))

        #  RUN BUTTON 
        pulse = 0.5 + 0.5 * math.sin(t * 4)
        btn_col = _lerp((30, 120, 70), (70, 240, 130), pulse)
        bx = (W - 440) // 2; by = 498
        pygame.draw.rect(screen, btn_col, (bx, by, 440, 66), border_radius=18)
        btn_txt = fm.render("PRESS  ENTER  TO  RUN", True, (8, 8, 8))
        screen.blit(btn_txt, (bx + (440 - btn_txt.get_width()) // 2, by + 16))

        #  HINT BAR 
        hints = [
            ("LEFT/RIGHT", "map", ACCENT_CYAN),
            ("A/D", "algo 1", (150, 180, 255)),
            ("J/L", "algo 2", ACCENT_PINK),
            ("UP/DOWN", "fps", ACCENT_AMBER),
            ("ENTER", "run", ACCENT_LIME),
        ]
        hx = 50
        for key, desc, col in hints:
            k = fh.render(key, True, col)
            d = fh.render(f" {desc}  ", True, TEXT_DIM)
            screen.blit(k, (hx, H - 64))
            screen.blit(d, (hx + k.get_width(), H - 64))
            hx += k.get_width() + d.get_width()

        close_hint = fh.render("close window to exit", True, TEXT_DIM)
        screen.blit(close_hint, (W - close_hint.get_width() - 50, H - 64))

        #  Bottom accent stripe 
        sx2 = int((math.cos(t * 0.6) * 0.5 + 0.5) * (W - sw2))
        ss2 = pygame.Surface((sw2, 4), pygame.SRCALPHA)
        ss2.fill((*ACCENT_PINK, 90))
        screen.blit(ss2, (sx2, H - 4))

        pygame.display.flip()

    running = True
    while running:
        clock.tick(60)
        _draw_launcher()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                running = False
                return

            elif event.type == pygame.KEYDOWN:
                key = event.key

                if key in (pygame.K_ESCAPE, pygame.K_q):
                    pass  # intentionally ignored

                elif key == pygame.K_LEFT:
                    map_i = (map_i - 1) % len(maps)
                elif key == pygame.K_RIGHT:
                    map_i = (map_i + 1) % len(maps)

                elif key == pygame.K_a:
                    algo1_i = (algo1_i - 1) % len(algos)
                elif key == pygame.K_d:
                    algo1_i = (algo1_i + 1) % len(algos)

                elif key == pygame.K_j:
                    algo2_i = (algo2_i - 1) % len(algos)
                elif key == pygame.K_l:
                    algo2_i = (algo2_i + 1) % len(algos)

                elif key == pygame.K_UP:
                    fps = min(120, fps + 5)
                elif key == pygame.K_DOWN:
                    fps = max(5, fps - 5)

                elif key == pygame.K_RETURN:
                    env1, algo1_res, trace1 = run_once(maps[map_i], algos[algo1_i])
                    env2, algo2_res, trace2 = run_once(maps[map_i], algos[algo2_i])
                    run_dual_viewer(
                        grid=env1.grid,
                        trace1=trace1, algo1_res=algo1_res,
                        trace2=trace2, algo2_res=algo2_res,
                        algo1=algos[algo1_i],
                        algo2=algos[algo2_i],
                        map_name=maps[map_i].name,
                        fps=fps,
                        cell_size=cell_size,
                        analysis_dir=analysis_dir,
                    )
                    # Restore launcher window
                    screen = pygame.display.set_mode((1280, 720))
                    pygame.display.set_caption("GridWorld — Dual Search Launcher")
