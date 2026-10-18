"""Convert a simple PRD markdown file (headings, paragraphs, lists, tables) to PDF.

Usage: python tools/md_to_pdf.py 01_PRD/GuardianBand_PRD.md
Writes the PDF next to the .md file. Re-run after editing pins or thresholds.
"""
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Arial covers ±, Ω, ≥, ² and arrows; the built-in Helvetica does not.
FONT_DIR = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Body", str(FONT_DIR / "arial.ttf")))
pdfmetrics.registerFont(TTFont("Body-Bold", str(FONT_DIR / "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Mono", str(FONT_DIR / "consola.ttf")))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold")

base = getSampleStyleSheet()
STYLES = {
    "h1": ParagraphStyle("h1", parent=base["Title"], fontName="Body-Bold", fontSize=16),
    "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Body-Bold", fontSize=12.5, spaceBefore=8),
    "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName="Body-Bold", fontSize=11, spaceBefore=6),
    "p": ParagraphStyle("p", parent=base["BodyText"], fontName="Body", fontSize=9.5, leading=13),
    "cell": ParagraphStyle("cell", parent=base["BodyText"], fontName="Body", fontSize=8.5, leading=11),
}


def inline(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"`(.+?)`", r'<font name="Mono">\1</font>', text)


def build_table(rows):
    cells = [[Paragraph(inline(c.strip()), STYLES["cell"]) for c in r.strip().strip("|").split("|")] for r in rows]
    t = Table(cells, repeatRows=1, hAlign="LEFT", colWidths=[None] * len(cells[0]))
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def convert(md_path):
    lines = md_path.read_text(encoding="utf-8").splitlines()
    story, table_rows = [], []
    for line in lines + [""]:
        if line.startswith("|"):
            if not re.match(r"^\|[\s\-|:]+\|$", line):
                table_rows.append(line)
            continue
        if table_rows:
            story += [build_table(table_rows), Spacer(1, 4)]
            table_rows = []
        s = line.strip()
        if not s:
            continue
        if s.startswith("### "):
            story.append(Paragraph(inline(s[4:]), STYLES["h3"]))
        elif s.startswith("## "):
            story.append(Paragraph(inline(s[3:]), STYLES["h2"]))
        elif s.startswith("# "):
            story.append(Paragraph(inline(s[2:]), STYLES["h1"]))
        elif re.match(r"^\d+\.\s", s):
            num, rest = s.split(" ", 1)
            story.append(Paragraph(f"{num} {inline(rest)}", STYLES["p"]))
        elif s.startswith("- "):
            story.append(Paragraph("• " + inline(s[2:]), STYLES["p"]))
        else:
            story.append(Paragraph(inline(s), STYLES["p"]))
    out = md_path.with_suffix(".pdf")
    SimpleDocTemplate(str(out), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=15 * mm, bottomMargin=15 * mm, title=md_path.stem).build(story)
    print("wrote", out)


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        convert(Path(arg))
