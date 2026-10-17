#!/usr/bin/env python3
"""Сборка документации по базе: docs/DATABASE.md -> docs/DATABASE.docx.

Запуск из корня проекта: python docs/make_docs.py
Нужны python-docx и matplotlib (pip install python-docx matplotlib).

Источник один — DATABASE.md. Скрипт рисует ER-диаграмму (docs/er_diagram.png),
вставляет ее вместо блока mermaid и переносит в Word заголовки, абзацы, списки,
таблицы и примеры кода.
"""

import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from docx import Document  # noqa: E402
from docx.enum.section import WD_ORIENT  # noqa: E402,F401
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402

DOCS = Path(__file__).resolve().parent
SOURCE = DOCS / "DATABASE.md"
TARGET = DOCS / "DATABASE.docx"
ER_PNG = DOCS / "er_diagram.png"

ACCENT = RGBColor(0x1F, 0x4E, 0x79)
HEADER_FILL = "DCE6F1"
CODE_FILL = "F2F2F2"

# ---------------------------------------------------------------- ER-диаграмма

ENTITIES = {
    # имя: (x, y, [(поле, тип, ключ)])
    "ТАКСОПАРКИ": (0.4, 3.8, [("код", "serial", "PK"), ("название", "varchar(100)", "UK")]),
    "ВОДИТЕЛИ": (0.4, 8.2, [("код", "serial", "PK"), ("taxi_id", "varchar(16)", "UK")]),
    "КЛИЕНТЫ": (0.4, 6.1, [("код", "serial", "PK"), ("тип", "varchar(30)", "UK"),
                          ("описание", "varchar(50)", "")]),
    "ПОЕЗДКИ": (5.0, 8.4, [("код_поездки", "serial", "PK"), ("trip_id", "varchar(16)", "UK"),
                          ("дата", "timestamp", ""), ("окончание", "timestamp", ""),
                          ("водитель", "integer", "FK"), ("клиент", "integer", "FK"),
                          ("таксопарк", "integer", "FK"), ("откуда", "integer", "FK"),
                          ("куда", "integer", "FK"), ("расстояние_км", "numeric(8,2)", ""),
                          ("время_мин", "integer", ""), ("стоимость", "numeric(10,2)", ""),
                          ("чаевые", "numeric(10,2)", ""), ("сборы", "numeric(10,2)", "")]),
    "РАЙОНЫ": (10.0, 5.46, [("код", "integer", "PK"), ("название", "varchar(50)", "UK"),
                          ("широта", "numeric(9,6)", ""), ("долгота", "numeric(9,6)", "")]),
    "СЕЗОН": (10.0, 7.56, [("месяц", "integer", "PK"), ("сезон", "varchar(10)", ""),
                         ("порядок", "integer", "")]),
}
LINKS = [  # (таблица, поле, справочник, поле, пунктир, x поворота линии)
    ("ПОЕЗДКИ", "водитель", "ВОДИТЕЛИ", "код", False, 4.6),
    ("ПОЕЗДКИ", "клиент", "КЛИЕНТЫ", "код", False, 4.5),
    ("ПОЕЗДКИ", "таксопарк", "ТАКСОПАРКИ", "код", False, 4.4),
    ("ПОЕЗДКИ", "откуда", "РАЙОНЫ", "код", False, 9.3),
    ("ПОЕЗДКИ", "куда", "РАЙОНЫ", "код", False, 9.3),
    ("ПОЕЗДКИ", "дата", "СЕЗОН", "месяц", True, 9.3),
]
BOX_W, ROW_H, HEAD_H = 3.6, 0.42, 0.55


def draw_er(path):
    fig, ax = plt.subplots(figsize=(13.6, 8.6), dpi=170)
    ax.set_xlim(0, 13.9)
    ax.set_ylim(1.5, 8.7)
    ax.axis("off")
    rows = {}
    for name, (x, y, fields) in ENTITIES.items():
        h = HEAD_H + ROW_H * len(fields)
        ax.add_patch(FancyBboxPatch((x, y - h), BOX_W, h, boxstyle="round,pad=0,rounding_size=0.08",
                                    fc="white", ec="#1F4E79", lw=1.4, zorder=2))
        ax.add_patch(FancyBboxPatch((x, y - HEAD_H), BOX_W, HEAD_H, boxstyle="round,pad=0,rounding_size=0.08",
                                    fc="#1F4E79", ec="#1F4E79", lw=1.4, zorder=3))
        ax.text(x + BOX_W / 2, y - HEAD_H / 2, name, ha="center", va="center", color="white",
                fontsize=11, fontweight="bold", zorder=4)
        for i, (field, ftype, key) in enumerate(fields):
            cy = y - HEAD_H - ROW_H * (i + 0.5)
            rows[(name, field)] = (x, cy)
            if i % 2:
                ax.add_patch(plt.Rectangle((x, cy - ROW_H / 2), BOX_W, ROW_H, fc="#EEF3F8", ec="none", zorder=2.5))
            ax.text(x + 0.12, cy, key, ha="left", va="center", fontsize=7.5, color="#C00000" if key == "PK"
                    else "#1F4E79", fontweight="bold", zorder=4)
            ax.text(x + 0.55, cy, field, ha="left", va="center", fontsize=9,
                    fontweight="bold" if key == "PK" else "normal", zorder=4)
            ax.text(x + BOX_W - 0.1, cy, ftype, ha="right", va="center", fontsize=7.5, color="#595959", zorder=4)
    for child, cfield, parent, pfield, dashed, mid in LINKS:
        cx, cy = rows[(child, cfield)]
        px, py = rows[(parent, pfield)]
        if px < cx:   # справочник слева
            x1, x2 = cx, px + BOX_W
        else:         # справочник справа
            x1, x2 = cx + BOX_W, px
        style = (0, (4, 3)) if dashed else "solid"
        ax.plot([x1, mid, mid, x2], [cy, cy, py, py], color="#404040", lw=1.1, ls=style, zorder=1)
        # «много» у поездок, «один» у справочника
        step = 0.18 if x2 > x1 else -0.18
        ax.plot([x1, x1 + step], [cy + 0.12, cy], color="#404040", lw=1.1, zorder=1)
        ax.plot([x1, x1 + step], [cy - 0.12, cy], color="#404040", lw=1.1, zorder=1)
        ax.plot([x2 - step * 0.8] * 2, [py - 0.12, py + 0.12], color="#404040", lw=1.1, zorder=1)
    ax.text(10.0, 2.85, "PK — первичный ключ, UK — уникальное поле, FK — внешний ключ\n"
            "сплошная линия — внешний ключ (одна запись справочника — много поездок)\n"
            "пунктир — связь по месяцу даты, без внешнего ключа",
            fontsize=8, color="#404040", va="top")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- Word

def shade(cell_or_par, fill):
    """Заливка ячейки таблицы или абзаца."""
    el = cell_or_par._tc if hasattr(cell_or_par, "_tc") else cell_or_par._p
    props = el.get_or_add_tcPr() if hasattr(cell_or_par, "_tc") else el.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    props.append(shd)


def add_inline(par, text, size=None):
    """Markdown внутри строки: **жирный**, `код`, [текст](ссылка)."""
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("**"):
            run = par.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("`"):
            run = par.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt((size or 11) - 1.5)
            run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
        else:
            run = par.add_run(part)
        if size and not part.startswith("`"):
            run.font.size = Pt(size)


def add_table(doc, lines):
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in lines]
    header, align_row, body = rows[0], rows[1], rows[2:]
    right = [c.endswith(":") and not c.startswith(":") for c in align_row]
    table = doc.add_table(rows=1 + len(body), cols=len(header))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r, cells in enumerate([header] + body):
        no_split = OxmlElement("w:cantSplit")  # строка не рвется между страницами
        table.rows[r]._tr.get_or_add_trPr().append(no_split)
        for c, value in enumerate(cells):
            cell = table.cell(r, c)
            par = cell.paragraphs[0]
            par.paragraph_format.space_after = Pt(0)
            if right[c]:
                par.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            add_inline(par, value, size=9.5)
            if r == 0:
                shade(cell, HEADER_FILL)
                if c == 0:  # шапка повторяется на каждой странице
                    tr_pr = table.rows[0]._tr.get_or_add_trPr()
                    tr_pr.append(OxmlElement("w:tblHeader"))
                for run in par.runs:
                    run.bold = True
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_code(doc, code):
    for i, line in enumerate(code.rstrip("\n").split("\n")):
        par = doc.add_paragraph()
        fmt = par.paragraph_format
        fmt.space_before = Pt(4 if i == 0 else 0)
        fmt.space_after = Pt(0)
        fmt.left_indent = Cm(0.4)
        shade(par, CODE_FILL)
        run = par.add_run(line or " ")
        run.font.name = "Consolas"
        run.font.size = Pt(9)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def page_number_footer(section):
    par = section.footer.paragraphs[0]
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = par.add_run()
    for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)


def setup_styles(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    normal.paragraph_format.space_after = Pt(6)
    for level, size in ((1, 16), (2, 13), (3, 11.5)):
        style = doc.styles[f"Heading {level}"]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.color.rgb = ACCENT
        style.paragraph_format.space_before = Pt(14 if level == 1 else 10)
        style.paragraph_format.space_after = Pt(4)
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.left_margin = section.right_margin = Cm(2)
    section.top_margin = section.bottom_margin = Cm(2)
    page_number_footer(section)


def build_docx(md, path):
    doc = Document()
    setup_styles(doc)
    lines = md.split("\n")
    title = lines[0].lstrip("# ").strip()
    headings = [line[3:] for line in lines if line.startswith("## ")]

    # титульный блок и оглавление
    par = doc.add_paragraph()
    run = par.add_run(title)
    run.bold = True
    run.font.size = Pt(24)
    run.font.color.rgb = ACCENT
    sub = doc.add_paragraph()
    add_inline(sub, "Поездки такси Чикаго · PostgreSQL · github.com/DarkSwordman999/TAXI-db", size=10)
    intro = lines[2].strip()  # абзац под заголовком документа — перед оглавлением
    add_inline(doc.add_paragraph(), intro)
    doc.add_heading("Содержание", level=1)
    for h in headings:
        p = doc.add_paragraph(h)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.left_indent = Cm(0.4)

    i = 1
    paragraph = []

    def flush():
        if paragraph:
            add_inline(doc.add_paragraph(), " ".join(paragraph))
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            lang = stripped[3:]
            block = []
            i += 1
            while not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            if lang == "mermaid":
                doc.add_picture(str(ER_PNG), width=Cm(17))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                add_code(doc, "\n".join(block))
        elif stripped.startswith("|"):
            flush()
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            add_table(doc, block)
            continue
        elif m := re.match(r"^(#{2,4}) (.*)", line):
            flush()
            level = len(m.group(1)) - 1
            if level == 1 and m.group(2) == headings[0]:  # после оглавления
                doc.add_page_break()
            doc.add_heading(m.group(2), level=level)
        elif m := re.match(r"^(\s*)(- |\d+\. )(.*)", line):
            flush()
            nested = len(m.group(1)) > 0
            style = "List Number" if m.group(2)[0].isdigit() else "List Bullet"
            if nested:
                style = "List Bullet 2"
            item = m.group(3)
            while i + 1 < len(lines) and lines[i + 1].startswith("   ") and not re.match(
                    r"^\s*(- |\d+\. )", lines[i + 1]):
                i += 1
                item += " " + lines[i].strip()
            par = doc.add_paragraph(style=style)
            par.paragraph_format.space_after = Pt(2)
            add_inline(par, item)
        elif not stripped:
            flush()
        elif stripped == intro:
            pass
        elif stripped.startswith("Версия Word:"):
            pass  # ссылка на сам docx нужна только в Markdown
        else:
            paragraph.append(stripped)
        i += 1
    flush()
    doc.core_properties.title = title
    doc.core_properties.author = "DarkSwordman999"
    doc.save(path)


def main():
    md = SOURCE.read_text(encoding="utf-8")
    draw_er(ER_PNG)
    build_docx(md, TARGET)
    print(f"Готово: {ER_PNG.name}, {TARGET.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
