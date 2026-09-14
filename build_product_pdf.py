from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Preformatted, KeepTogether,
)

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "docs" / "知源产品文档.md"
OUT = ROOT / "output" / "pdf" / "知源产品文档.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

FONT = r"C:\Windows\Fonts\Deng.ttf"
FONT_BOLD = r"C:\Windows\Fonts\Dengb.ttf"
pdfmetrics.registerFont(TTFont("Deng", FONT))
pdfmetrics.registerFont(TTFont("Deng-Bold", FONT_BOLD))

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="DocTitle", parent=styles["Title"], fontName="Deng-Bold", fontSize=24, leading=32, alignment=TA_CENTER, textColor=colors.HexColor("#173B63"), spaceAfter=10))
styles.add(ParagraphStyle(name="Subtitle", parent=styles["Normal"], fontName="Deng", fontSize=11, leading=18, alignment=TA_CENTER, textColor=colors.HexColor("#66788A"), spaceAfter=18))
styles.add(ParagraphStyle(name="H1cn", parent=styles["Heading1"], fontName="Deng-Bold", fontSize=19, leading=27, textColor=colors.HexColor("#173B63"), spaceBefore=17, spaceAfter=10))
styles.add(ParagraphStyle(name="H2cn", parent=styles["Heading2"], fontName="Deng-Bold", fontSize=15.5, leading=23, textColor=colors.HexColor("#245B8D"), spaceBefore=13, spaceAfter=7))
styles.add(ParagraphStyle(name="H3cn", parent=styles["Heading3"], fontName="Deng-Bold", fontSize=13.5, leading=21, textColor=colors.HexColor("#38739F"), spaceBefore=10, spaceAfter=5))
# 小四号正文：12 pt；列表和表格也保持可读字号。
styles.add(ParagraphStyle(name="BodyCN", parent=styles["BodyText"], fontName="Deng", fontSize=12, leading=20, textColor=colors.HexColor("#263746"), spaceAfter=8))
styles.add(ParagraphStyle(name="BulletCN", parent=styles["BodyText"], fontName="Deng", fontSize=11.5, leading=18, leftIndent=15, firstLineIndent=-10, bulletIndent=3, spaceAfter=4))
styles.add(ParagraphStyle(name="SmallCN", parent=styles["BodyText"], fontName="Deng", fontSize=10.5, leading=16, textColor=colors.HexColor("#526677")))
styles.add(ParagraphStyle(name="CodeCN", parent=styles["Code"], fontName="Deng", fontSize=9.5, leading=14, leftIndent=8, rightIndent=8, backColor=colors.HexColor("#F3F7FA"), borderColor=colors.HexColor("#D7E3EC"), borderWidth=.5, borderPadding=7))

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<font name='Deng-Bold'>\1</font>", s)
    return s

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D9E4EC"))
    canvas.line(18*mm, 14*mm, 192*mm, 14*mm)
    canvas.setFont("Deng", 8)
    canvas.setFillColor(colors.HexColor("#7B8A97"))
    canvas.drawString(18*mm, 8*mm, "知源（isoLogic）产品文档")
    canvas.drawRightString(192*mm, 8*mm, f"第 {doc.page} 页")
    canvas.restoreState()

class ProductDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=17*mm, bottomMargin=20*mm, title="知源（isoLogic）产品文档", author="Logic-Coloc")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal")
        self.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=footer)])

def parse_md(text):
    story = []
    lines = text.splitlines()
    i = 0
    first = True
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip() in {"---", "***"}:
            i += 1; continue
        if line.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            i += 1
            story += [Preformatted("\n".join(code), styles["CodeCN"]), Spacer(1, 5)]
            continue
        m = re.match(r"^(#{1,4})\s+(.+)$", line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            if first:
                story += [Paragraph(inline(title), styles["DocTitle"]), Paragraph("基于当前项目代码、产品说明、PRD/SPEC 与前端页面整理", styles["Subtitle"])]
                first = False
            else:
                story.append(Paragraph(inline(title), {1: styles["H1cn"], 2: styles["H2cn"], 3: styles["H3cn"], 4: styles["H3cn"]}[level]))
            i += 1; continue
        if line.startswith("- ") or line.startswith("* ") or re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and (lines[i].startswith("- ") or lines[i].startswith("* ") or re.match(r"^\d+\.\s+", lines[i])):
                current = lines[i]
                marker = re.match(r"^(\d+\.\s+|[-*]\s+)", current)
                prefix = marker.group(1).strip() if marker else "•"
                content = current[marker.end():].strip() if marker else current
                items.append([Paragraph(f"{prefix} " + inline(content), styles["BulletCN"])])
                i += 1
            story.append(Table(items, colWidths=[174*mm], style=TableStyle([("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 0), ("TOPPADDING", (0,0), (-1,-1), 1), ("BOTTOMPADDING", (0,0), (-1,-1), 1)])))
            continue
        if "|" in line and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-+", lines[i+1]):
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                if re.match(r"^\s*\|?\s*:?-+", lines[i]): i += 1; continue
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append([Paragraph(inline(c), styles["SmallCN"]) for c in cells]); i += 1
            col_count = max(len(r) for r in rows)
            for r in rows: r.extend([Paragraph("", styles["SmallCN"])] * (col_count-len(r)))
            tbl = Table(rows, colWidths=[174*mm/col_count]*col_count, repeatRows=1)
            tbl.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EAF3F9")), ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#173B63")), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#C8D8E3")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)]))
            story += [tbl, Spacer(1, 6)]; continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4})\s|^[-*]\s|^\d+\.\s+|^```", lines[i]) and "|" not in lines[i]:
            para.append(lines[i].strip()); i += 1
        story.append(Paragraph(inline(" ".join(para)), styles["BodyCN"]))
    return story

doc = ProductDoc(str(OUT))
doc.build(parse_md(SOURCE.read_text(encoding="utf-8")))
print(OUT)
