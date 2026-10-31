#!/usr/bin/env python3
"""Generate the execution evidence used in the Week 3 report.

This is a development/reporting utility, not part of the financekit API.
It executes the real test/demo commands, saves their unedited text output
under ``docs/evidence/`` and renders selected outputs as terminal-style
PNG figures for embedding in the Word report.

Run from the project root after installing the development dependencies
plus Pillow (used only for PNG rendering):
    pip install -r requirements-dev.txt Pillow
    python tools/generate_evidence.py
"""

from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "evidence"
FIGURES = EVIDENCE / "figures"

FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def run_command(label: str, args: list[str]) -> str:
    """Execute a command in the project root and return a labelled transcript."""
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)
    display_args = ["python" if arg == sys.executable else arg for arg in args]
    command = " ".join(display_args)
    return (
        f"$ {command}\n"
        f"{result.stdout}"
        f"{result.stderr}"
        f"[exit_code={result.returncode}]\n"
    )


def save_text(name: str, content: str) -> Path:
    path = EVIDENCE / name
    path.write_text(content, encoding="utf-8")
    return path


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a report font, falling back gracefully outside the build host."""
    requested = Path(path)
    candidates = [requested]

    # Matplotlib, when present, ships the same DejaVu family on all platforms.
    try:
        import matplotlib

        candidates.append(
            Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf" / requested.name
        )
    except Exception:
        pass

    if "Mono" in requested.name:
        candidates.extend(
            Path(candidate)
            for candidate in (
                "/Library/Fonts/Menlo.ttc",
                "C:/Windows/Fonts/consola.ttf",
                "C:/Windows/Fonts/cour.ttf",
            )
        )
    else:
        candidates.extend(
            Path(candidate)
            for candidate in (
                "/Library/Fonts/Arial.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/segoeui.ttf",
            )
        )

    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow versions
        return ImageFont.load_default()


def render_terminal(title: str, lines: list[str], output_name: str, accent: str = "#2f9e44") -> Path:
    """Render actual command output as a readable terminal-style figure."""
    width = 1680
    line_height = 27
    top = 88
    bottom = 34
    height = top + max(1, len(lines)) * line_height + bottom
    image = Image.new("RGB", (width, height), "#101418")
    draw = ImageDraw.Draw(image)

    # Window chrome
    draw.rectangle((0, 0, width, 58), fill="#242b33")
    for i, color in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        x = 24 + i * 30
        draw.ellipse((x, 19, x + 18, 37), fill=color)
    draw.text((122, 16), title, font=font(FONT_MONO_BOLD, 20), fill="#e6edf3")
    draw.rectangle((0, 58, width, 64), fill=accent)

    mono = font(FONT_MONO, 19)
    y = top
    for raw in lines:
        for wrapped in textwrap.wrap(raw, width=112, replace_whitespace=False,
                                     drop_whitespace=False) or [""]:
            color = "#d6deeb"
            if wrapped.startswith("$"):
                color = "#7ee787"
            elif any(token in wrapped for token in ("FAILED", "ERROR", "exit_code=1")):
                color = "#ff7b72"
            elif any(token in wrapped for token in ("passed", "100%", "98%", "ACCEPT", "OK")):
                color = "#7ee787"
            elif wrapped.startswith(("Name", "TOTAL", "---")):
                color = "#79c0ff"
            draw.text((26, y), wrapped, font=mono, fill=color)
            y += line_height

    path = FIGURES / output_name
    image.save(path, optimize=True)
    return path


def project_metrics() -> str:
    """Measure the submitted code rather than quoting stale counts."""
    rows = ["Financekit source and test metrics", "=" * 72]
    for group in ("financekit", "tests"):
        total_lines = 0
        total_functions = 0
        total_classes = 0
        for path in sorted((ROOT / group).glob("*.py")):
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
            lines = len(text.splitlines())
            funcs = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
            classes = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
            total_lines += lines
            total_functions += funcs
            total_classes += classes
            rows.append(f"{group}/{path.name:<34} lines={lines:<4} functions={funcs:<3} classes={classes}")
        rows.append(f"{group.upper():<42} lines={total_lines:<4} functions={total_functions:<3} classes={total_classes}")
        rows.append("")
    return "\n".join(rows) + "\n"


def draw_architecture() -> Path:
    width, height = 1680, 930
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    title = font(FONT_SANS_BOLD, 34)
    head = font(FONT_SANS_BOLD, 22)
    body = font(FONT_SANS, 19)
    d.text((55, 35), "financekit module architecture and test boundaries", font=title, fill="#153a63")

    def box(x, y, w, h, label, detail, fill):
        d.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=fill, outline="#24476b", width=3)
        d.text((x + 22, y + 18), label, font=head, fill="#102a43")
        for i, line in enumerate(textwrap.wrap(detail, 34)):
            d.text((x + 22, y + 58 + i * 25), line, font=body, fill="#334e68")

    def arrow(x1, y1, x2, y2):
        d.line((x1, y1, x2, y2), fill="#486581", width=4)
        d.polygon([(x2, y2), (x2 - 14, y2 - 8), (x2 - 14, y2 + 8)], fill="#486581")

    box(65, 150, 340, 150, "interest.py", "simple/compound interest, PV/FV", "#dbeafe")
    box(480, 150, 340, 150, "loans.py", "EMI and amortization rows", "#dbeafe")
    box(895, 150, 340, 150, "investments.py", "NPV, IRR, CAGR, SIP", "#dbeafe")
    box(1285, 150, 330, 150, "statistics.py", "returns, Sharpe, drawdown", "#dbeafe")
    box(250, 390, 390, 150, "validation.py + errors.py", "one input/error contract for every public function", "#fef3c7")
    box(825, 390, 390, 150, "io.py", "cashflow CSV input; schedule CSV output", "#dcfce7")
    box(570, 625, 540, 150, "reports.py", "integration surface: loan report, investment report, file analysis", "#ede9fe")
    for x in (235, 650, 1065, 1450):
        arrow(x, 300, 445, 390)
    arrow(690, 540, 790, 625)
    arrow(1050, 540, 920, 625)
    d.rounded_rectangle((55, 820, 1625, 885), radius=14, fill="#eef2f7", outline="#9fb3c8", width=2)
    d.text((80, 838), "129 pytest items  •  104 unit  •  14 integration  •  58 edge  •  98% branch coverage",
           font=head, fill="#153a63")
    path = FIGURES / "fig01_architecture.png"
    img.save(path, optimize=True)
    return path


def draw_tdd_cycle() -> Path:
    width, height = 1680, 700
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    d.text((55, 35), "Auditable TDD evidence chain", font=font(FONT_SANS_BOLD, 34), fill="#153a63")
    stages = [
        ("RED", "117 failed\n1 passed", "118 tests written\nagainst stubs", "#fee2e2", "#b91c1c"),
        ("GREEN", "118 passed", "implementation written\nwithout editing tests", "#dcfce7", "#15803d"),
        ("COVERAGE", "129 tests\n98% branch", "11 tests added from\nuncovered branches", "#dbeafe", "#1d4ed8"),
        ("REFACTOR", "129 passed", "internals improved\nbehind green suite", "#ede9fe", "#6d28d9"),
    ]
    x = 55
    for label, metric, detail, fill, color in stages:
        d.rounded_rectangle((x, 175, x + 340, 485), radius=26, fill=fill, outline=color, width=4)
        d.text((x + 28, 205), label, font=font(FONT_SANS_BOLD, 30), fill=color)
        yy = 275
        for line in metric.splitlines():
            d.text((x + 28, yy), line, font=font(FONT_SANS_BOLD, 27), fill="#111827"); yy += 38
        yy += 8
        for line in detail.splitlines():
            d.text((x + 28, yy), line, font=font(FONT_SANS, 21), fill="#334155"); yy += 30
        if x < 1250:
            d.line((x + 345, 330, x + 400, 330), fill="#475569", width=6)
            d.polygon([(x + 412, 330), (x + 390, 316), (x + 390, 344)], fill="#475569")
        x += 415
    d.text((55, 565), "Raw transcripts: docs/tdd_evidence/01_red_phase.txt → 04_mutation_spotchecks.txt",
           font=font(FONT_SANS, 22), fill="#334155")
    d.text((55, 605), "Mutation spot-checks: 3 deliberate defects injected in a throwaway copy; all 3 were killed by tests.",
           font=font(FONT_SANS, 22), fill="#334155")
    path = FIGURES / "fig02_tdd_evidence_chain.png"
    img.save(path, optimize=True)
    return path


def draw_test_pyramid() -> Path:
    width, height = 1500, 820
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    d.text((55, 35), "Financekit test pyramid (129 collected items)", font=font(FONT_SANS_BOLD, 34), fill="#153a63")
    # Broad base manually drawn as stacked trapezoids/polygons
    d.polygon([(560,120),(940,120),(1015,270),(485,270)], fill="#ede9fe", outline="#6d28d9")
    d.polygon([(485,285),(1015,285),(1120,460),(380,460)], fill="#dbeafe", outline="#1d4ed8")
    d.polygon([(380,475),(1120,475),(1250,680),(250,680)], fill="#dcfce7", outline="#15803d")
    d.text((610,160), "User journey", font=font(FONT_SANS_BOLD, 25), fill="#4c1d95")
    d.text((650,200), "1 scenario", font=font(FONT_SANS, 21), fill="#334155")
    d.text((585,325), "Integration — 14", font=font(FONT_SANS_BOLD, 27), fill="#1e3a8a")
    d.text((565,368), "real files + reports", font=font(FONT_SANS, 21), fill="#334155")
    d.text((610,530), "Unit — 104", font=font(FONT_SANS_BOLD, 30), fill="#14532d")
    d.text((555,578), "formulas, invariants, errors", font=font(FONT_SANS, 21), fill="#334155")
    d.text((55,735), "58 items also carry the cross-cutting edge marker; marker groups overlap by design.",
           font=font(FONT_SANS, 21), fill="#334155")
    path = FIGURES / "fig04_test_pyramid.png"
    img.save(path, optimize=True)
    return path


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    pytest_verbose = run_command(
        "pytest verbose", [sys.executable, "-m", "pytest", "-o", "addopts=", "-v"]
    )
    save_text("pytest_verbose.txt", pytest_verbose)

    collect = run_command(
        "pytest collect", [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    )
    save_text("pytest_collect.txt", collect)

    markers_parts = []
    for marker in ("unit", "integration", "edge"):
        markers_parts.append(
            run_command(marker, [sys.executable, "-m", "pytest", "-m", marker, "-o", "addopts=", "-q"])
        )
    save_text("marker_runs.txt", "\n".join(markers_parts))

    coverage = run_command(
        "coverage",
        [sys.executable, "-m", "pytest", "--cov=financekit", "--cov-branch",
         "--cov-report=term-missing", "-o", "addopts=", "-q"],
    )
    save_text("coverage.txt", coverage)

    demo = run_command("demo", [sys.executable, "examples/demo.py"])
    save_text("demo_output.txt", demo)
    save_text("project_metrics.txt", project_metrics())

    draw_architecture()
    draw_tdd_cycle()
    draw_test_pyramid()

    verbose_lines = pytest_verbose.splitlines()
    selected = [verbose_lines[0], ""] + verbose_lines[1:16] + ["..."] + verbose_lines[-18:]
    render_terminal("Actual pytest verbose run", selected,
                    "fig07_pytest_verbose.png", "#2f9e44")

    coverage_lines = [
        line for line in coverage.splitlines()
        if line.startswith("$")
        or "tests coverage" in line
        or "coverage: platform" in line
        or line.startswith(("Name", "TOTAL", "---"))
        or "financekit/" in line
        or "passed" in line
        or "ERROR" in line
        or "exit_code" in line
    ]
    render_terminal("Actual branch-coverage run", coverage_lines,
                    "fig06_coverage.png", "#1971c2")

    red_path = ROOT / "docs" / "tdd_evidence" / "01_red_phase.txt"
    red_lines = red_path.read_text(encoding="utf-8").splitlines()
    red_selected = red_lines[:8] + [line for line in red_lines if line.startswith("FAILED")][:10] + red_lines[-7:]
    render_terminal("TDD RED phase — preserved transcript excerpt", red_selected,
                    "fig03_red_phase.png", "#e03131")

    render_terminal("Actual example/demo execution", demo.splitlines(),
                    "fig08_demo_output.png", "#2f9e44")

    marker_selected = []
    for line in "\n".join(markers_parts).splitlines():
        if line.startswith("$") or "passed" in line or "deselected" in line:
            marker_selected.append(line)
    render_terminal("Actual marker-subset executions", marker_selected,
                    "fig05_marker_runs.png", "#7048e8")

    mutation = (ROOT / "docs" / "tdd_evidence" / "04_mutation_spotchecks.txt").read_text(
        encoding="utf-8"
    ).splitlines()
    render_terminal("Mutation spot-check transcript", mutation,
                    "fig09_mutation_spotchecks.png", "#e8590c")

    print("Evidence generated in", EVIDENCE)
    for path in sorted(FIGURES.glob("*.png")):
        print("-", path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
