"""Fix non-rectangular maps by padding/truncating rows to the most common width."""
from collections import Counter
from pathlib import Path

MAPS_DIR = Path(__file__).resolve().parents[1] / "assets" / "maps"


def _load_lines(path: Path) -> list[str]:
    return [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _target_width(widths: list[int]) -> int:
    counts = Counter(widths)
    return max(counts, key=lambda width: (counts[width], width))


def fix_one(path: Path) -> None:
    """Pad short rows / truncate long rows so every row has the same width."""
    lines = _load_lines(path)
    if not lines:
        print(f"[SKIP] {path.name}: empty")
        return

    widths = [len(line) for line in lines]
    target = _target_width(widths)
    bad = [(index, width, line) for index, (width, line) in enumerate(zip(widths, lines)) if width != target]

    if not bad:
        print(f"[OK]  {path.name} ({target} cols, {len(lines)} rows)")
        return

    print(f"[BAD] {path.name}: target={target}, widths={sorted(set(widths))}")
    for index, width, row in bad[:8]:
        print(f"  line {index + 1}: len={width} row={row!r}")

    fixed = [line[:target].ljust(target, "F") for line in lines]
    path.write_text("\n".join(fixed) + "\n", encoding="utf-8")
    print(f"      -> fixed {path.name}\n")


def main() -> None:
    if not MAPS_DIR.exists():
        raise FileNotFoundError(f"Maps dir not found: {MAPS_DIR}")
    for path in sorted(MAPS_DIR.glob("*.txt")):
        fix_one(path)


if __name__ == "__main__":
    main()
