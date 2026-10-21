#!/usr/bin/env python3
"""Сборка документации в Word по ГОСТ 7.32-2017: docs/*.md -> docs/*.docx.

Запуск из корня проекта: python docs/make_docs.py [--pdf папка]
Нужны python-docx и matplotlib (pip install -r requirements-dev.txt).

Источник — Markdown: DATABASE.md, USER_GUIDE.md, COMMANDS.md. Скрипт рисует ER-диаграмму
(docs/er_diagram.png), вставляет ее вместо блока mermaid и переносит в Word заголовки,
абзацы, списки, таблицы, рисунки и примеры кода. Подписи таблиц и рисунков берутся
из комментариев <!-- Таблица: ... --> и <!-- Рисунок: ... --> перед ними.
Если в Windows установлен Word, содержание с номерами страниц обновляется сразу;
--pdf дополнительно сохраняет PDF-копии в указанную папку.
"""

import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from docx import Document  # noqa: E402
from docx.enum.style import WD_STYLE_TYPE  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402

DOCS = Path(__file__).resolve().parent
ER_PNG = DOCS / "er_diagram.png"

# ---------------------------------------------------------------- ER-диаграмма

ENTITIES = {
    # имя: (x, y, [(поле, тип, ключ)])
    "ТАКСОПАРКИ": (0.4, 3.8, [("код", "serial", "PK"), ("название", "varchar(100)", "UK")]),
    "ВОДИТЕЛИ": (0.4, 8.2, [("код", "serial", "PK"), ("taxi_id", "varchar(16)", "UK")]),
    "ОПЛАТА": (0.4, 6.1, [("код", "serial", "PK"), ("тип", "varchar(30)", "UK"),
                          ("описание", "varchar(50)", "")]),
    "ПОЕЗДКИ": (5.0, 8.4, [("код_поездки", "serial", "PK"), ("trip_id", "varchar(16)", "UK"),
                          ("дата", "timestamp", ""), ("окончание", "timestamp", ""),
                          ("водитель", "integer", "FK"), ("оплата", "integer", "FK"),
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
    ("ПОЕЗДКИ", "оплата", "ОПЛАТА", "код", False, 4.5),
    ("ПОЕЗДКИ", "таксопарк", "ТАКСОПАРКИ", "код", False, 4.4),
    ("ПОЕЗДКИ", "откуда", "РАЙОНЫ", "код", False, 9.3),
    ("ПОЕЗДКИ", "куда", "РАЙОНЫ", "код", False, 9.3),
    ("ПОЕЗДКИ", "дата", "СЕЗОН", "месяц", True, 9.3),
]
BOX_W, ROW_H, HEAD_H = 3.6, 0.42, 0.55


ER_THEMES = {
    # светлая — для Word и светлой темы GitHub, темная — для темной темы GitHub
    "light": {"bg": "white", "box": "white", "head": "#1F4E79", "edge": "#1F4E79", "head_text": "white",
              "stripe": "#EEF3F8", "pk": "#C00000", "key": "#1F4E79", "field": "black", "type": "#595959",
              "line": "#404040"},
    "dark": {"bg": "none", "box": "#161b22", "head": "#1c5cab", "edge": "#2a78d6", "head_text": "white",
             "stripe": "#1c2430", "pk": "#e66767", "key": "#86b6ef", "field": "#f0efec", "type": "#8f8e86",
             "line": "#8b949e"},
}


def draw_er(path, theme="light"):
    t = ER_THEMES[theme]
    fig, ax = plt.subplots(figsize=(13.6, 8.6), dpi=170)
    ax.set_xlim(0, 13.9)
    ax.set_ylim(1.5, 8.7)
    ax.axis("off")
    rows = {}
    for name, (x, y, fields) in ENTITIES.items():
        h = HEAD_H + ROW_H * len(fields)
        ax.add_patch(FancyBboxPatch((x, y - h), BOX_W, h, boxstyle="round,pad=0,rounding_size=0.08",
                                    fc=t["box"], ec=t["edge"], lw=1.4, zorder=2))
        ax.add_patch(FancyBboxPatch((x, y - HEAD_H), BOX_W, HEAD_H, boxstyle="round,pad=0,rounding_size=0.08",
                                    fc=t["head"], ec=t["edge"], lw=1.4, zorder=3))
        ax.text(x + BOX_W / 2, y - HEAD_H / 2, name, ha="center", va="center", color=t["head_text"],
                fontsize=11, fontweight="bold", zorder=4)
        for i, (field, ftype, key) in enumerate(fields):
            cy = y - HEAD_H - ROW_H * (i + 0.5)
            rows[(name, field)] = (x, cy)
            if i % 2:
                ax.add_patch(plt.Rectangle((x, cy - ROW_H / 2), BOX_W, ROW_H, fc=t["stripe"], ec="none", zorder=2.5))
            ax.text(x + 0.12, cy, key, ha="left", va="center", fontsize=7.5, color=t["pk"] if key == "PK"
                    else t["key"], fontweight="bold", zorder=4)
            ax.text(x + 0.55, cy, field, ha="left", va="center", fontsize=9, color=t["field"],
                    fontweight="bold" if key == "PK" else "normal", zorder=4)
            ax.text(x + BOX_W - 0.1, cy, ftype, ha="right", va="center", fontsize=7.5, color=t["type"], zorder=4)
    for child, cfield, parent, pfield, dashed, mid in LINKS:
        cx, cy = rows[(child, cfield)]
        px, py = rows[(parent, pfield)]
        if px < cx:   # справочник слева
            x1, x2 = cx, px + BOX_W
        else:         # справочник справа
            x1, x2 = cx + BOX_W, px
        style = (0, (4, 3)) if dashed else "solid"
        ax.plot([x1, mid, mid, x2], [cy, cy, py, py], color=t["line"], lw=1.1, ls=style, zorder=1)
        # «много» у поездок, «один» у справочника
        step = 0.18 if x2 > x1 else -0.18
        ax.plot([x1, x1 + step], [cy + 0.12, cy], color=t["line"], lw=1.1, zorder=1)
        ax.plot([x1, x1 + step], [cy - 0.12, cy], color=t["line"], lw=1.1, zorder=1)
        ax.plot([x2 - step * 0.8] * 2, [py - 0.12, py + 0.12], color=t["line"], lw=1.1, zorder=1)
    ax.text(10.0, 2.85, "PK — первичный ключ, UK — уникальное поле, FK — внешний ключ\n"
            "сплошная линия — внешний ключ (одна запись справочника — много поездок)\n"
            "пунктир — связь по месяцу даты, без внешнего ключа",
            fontsize=8, color=t["line"], va="top")
    fig.savefig(path, bbox_inches="tight", facecolor=t["bg"], transparent=t["bg"] == "none")
    plt.close(fig)


# ---------------------------------------------------------------- Word по ГОСТ 7.32-2017
#
# Оформление как у отчетов и выпускных работ: A4, поля 30/15/20/20 мм, Times New Roman 14,
# интервал 1,5, абзацный отступ 1,25 см, выравнивание по ширине; титульный лист без номера,
# номера страниц внизу по центру; СОДЕРЖАНИЕ, ВВЕДЕНИЕ и СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ —
# прописными по центру; разделы с новой страницы, нумерация «1», «1.1» без точки в конце;
# «Таблица N – Название» над таблицей, «Рисунок N – Название» под рисунком.

FONT = "Times New Roman"
MONO = "Courier New"
TEXT_WIDTH = Cm(21 - 3 - 1.5)
INDENT = Cm(1.25)
DASH = "–"
ACCESS_DATE = "21.10.2026"  # дата обращения к электронным ресурсам в списке источников

# Markdown-документ -> Word: (исходник, результат, название на титульном листе, вид документа,
# каждый раздел с новой страницы). В справочнике команд разделы короткие — идут подряд.
DOCUMENTS = [
    ("DATABASE.md", "DATABASE.docx", "БАЗА ДАННЫХ TAXI", "Описание базы данных", True),
    ("USER_GUIDE.md", "USER_GUIDE.docx", "TAXI: ПОЕЗДКИ ТАКСИ ЧИКАГО", "Инструкция пользователя", True),
    ("COMMANDS.md", "COMMANDS.docx", "TAXI: ПОЕЗДКИ ТАКСИ ЧИКАГО", "Справочник команд", False),
]
# ссылки между документами: в Word вместо имени файла — название документа
DOC_NAMES = {
    "DATABASE.md": "«Описание базы данных»",
    "USER_GUIDE.md": "«Инструкция пользователя»",
    "COMMANDS.md": "«Справочник команд»",
    "../README.md": "README проекта",
}
# описания электронных ресурсов для списка источников (ГОСТ Р 7.0.100-2018)
SOURCES = {
    "https://data.cityofchicago.org/resource/ajtu-isnz.json":
        "Taxi Trips : набор открытых данных // City of Chicago Data Portal : [сайт]. – Chicago, 2025–2026",
    "https://www.postgresql.org/download/":
        "PostgreSQL Downloads : [сайт] / The PostgreSQL Global Development Group",
    "https://www.python.org/downloads/": "Download Python : [сайт] / Python Software Foundation",
    "https://git-scm.com/downloads": "Git – Downloads : [сайт]",
    "https://github.com/DarkSwordman999/TAXI-db/releases/latest":
        "TAXI-db. Releases : [репозиторий] / DarkSwordman999 // GitHub : [сайт]",
}


def set_fonts(el_rpr, name):
    """Шрифт для всех алфавитов; темы шаблона (asciiTheme и др.) иначе перекрывают имя шрифта."""
    fonts = el_rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        el_rpr.insert(0, fonts)
    for attr in list(fonts.attrib):
        if attr.endswith("Theme"):
            del fonts.attrib[attr]
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        fonts.set(qn(attr), name)


def run_font(run, name=FONT, size=None, bold=None):
    run.font.name = name
    set_fonts(run._r.get_or_add_rPr(), name)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)


def mono_size(size):
    """Код в тексте на 1 пт меньше основного шрифта, в таблицах (12 пт) — 10 пт."""
    return size - 1 if size >= 14 else size - 2


def text_width_cm(text, size=12):
    """Примерная ширина строки в ячейке: `код` — моноширинным шрифтом, остальное — Times New Roman."""
    width = 0
    for part in re.split(r"(`[^`]+`)", re.sub(r"\[([^\]]+)\]\([^)]+\)", r" [0]", text)):
        if part.startswith("`"):
            width += (len(part) - 2) * 0.6 * mono_size(size) * 0.0353   # Courier New: 0,6 кегля на знак
        else:
            width += len(part.replace("**", "")) * 0.5 * size * 0.0353  # Times: ~0,5 кегля
    return width


def column_widths(rows, padding=0.45):
    """Каждый столбец не уже самого длинного слова (слова не рвутся),
    оставшееся место — пропорционально длине текста; в сумме — ширина текста страницы."""
    total = TEXT_WIDTH.cm
    cols = range(len(rows[0]))
    tokens = [[t for row in rows for t in re.findall(r"`[^`]+`|\S+", row[c])] for c in cols]
    # шапка полужирная — ее слова шире на ~12 %
    head = [max((text_width_cm(t) * 1.12 for t in rows[0][c].split()), default=0) for c in cols]
    minw = []
    for c in cols:
        # код до 6 см не переносится; длинный может переноситься по пробелам внутри
        words = [text_width_cm(t) if not t.startswith("`") or text_width_cm(t) <= 6 else
                 max(text_width_cm(f"`{w}`") for w in t.strip("`").split()) for t in tokens[c]] or [0.5]
        minw.append(max(max(words), head[c]) + padding)
    natural = [max(text_width_cm(row[c]) for row in rows) + padding for c in cols]
    if sum(minw) >= total:
        widths = [w * total / sum(minw) for w in minw]
    else:
        extra = total - sum(minw)
        room = [n - m for n, m in zip(natural, minw)]
        if sum(room) <= extra:   # все помещается в одну строку — добавка пропорционально тексту
            widths = [n + (extra - sum(room)) * n / sum(natural) for n in natural]
        else:
            widths = [m + extra * r / sum(room) for m, r in zip(minw, room)]
    return [Cm(w) for w in widths]


def para_format(par, indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY, spacing=1.5, before=0, after=0):
    fmt = par.paragraph_format
    fmt.first_line_indent = INDENT if indent else Cm(0)
    fmt.left_indent = Cm(0)
    fmt.alignment = align
    fmt.line_spacing = spacing
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    return fmt


class GostDoc:
    def __init__(self, source_name, sections_new_page=True):
        self.doc = Document()
        self.sections_new_page = sections_new_page
        self.source_name = source_name
        self.tables = 0
        self.figures = 0
        self.sources = []          # URL в порядке первой ссылки
        self.numbers = [0, 0, 0]   # счетчики разделов
        self.setup(sections_new_page)

    # ---------- стили и страница
    def setup(self, sections_new_page):
        doc = self.doc
        normal = doc.styles["Normal"]
        normal.font.name = FONT
        normal.font.size = Pt(14)
        set_fonts(normal.element.get_or_add_rPr(), FONT)
        lang = OxmlElement("w:lang")
        lang.set(qn("w:val"), "ru-RU")
        lang.set(qn("w:eastAsia"), "ru-RU")
        normal.element.get_or_add_rPr().append(lang)
        fmt = normal.paragraph_format
        fmt.first_line_indent = INDENT
        fmt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        fmt.line_spacing = 1.5
        fmt.space_before = fmt.space_after = Pt(0)
        fmt.widow_control = True

        for level in (1, 2, 3):
            style = doc.styles[f"Heading {level}"]
            style.font.name = FONT
            set_fonts(style.element.get_or_add_rPr(), FONT)
            style.font.size = Pt(14)
            style.font.bold = True
            style.font.italic = False
            style.font.color.rgb = RGBColor(0, 0, 0)
            sf = style.paragraph_format
            sf.first_line_indent = INDENT
            sf.left_indent = Cm(0)
            sf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            sf.line_spacing = 1.5
            sf.space_before = Pt(0 if level == 1 else 12)
            sf.space_after = Pt(12)
            sf.keep_with_next = True
            sf.page_break_before = level == 1 and sections_new_page

        # стили строк содержания: точки до номера страницы у правого края
        for level, left in ((1, 0), (2, 0.5), (3, 1.0)):
            name = f"toc {level}"
            try:
                style = doc.styles[name]
            except KeyError:
                style = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            style.base_style = normal
            sf = style.paragraph_format
            sf.first_line_indent = Cm(0)
            sf.left_indent = Cm(left)
            sf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            sf.space_after = Pt(0)
            sf.tab_stops.add_tab_stop(TEXT_WIDTH, WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)

        section = doc.sections[0]
        section.page_width, section.page_height = Cm(21), Cm(29.7)
        section.left_margin, section.right_margin = Cm(3), Cm(1.5)
        section.top_margin = section.bottom_margin = Cm(2)
        section.footer_distance = Cm(1)
        section.different_first_page_header_footer = True  # на титульном листе номера нет
        par = section.footer.paragraphs[0]
        para_format(par, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1)
        self.field(par, "PAGE", size=12)

    def field(self, par, instr, placeholder="", size=None):
        """Поле Word (номер страницы, содержание); значение пересчитывает Word."""
        def add(tag=None, text=None):
            run = par.add_run()
            run_font(run, size=size)
            if tag:
                el = OxmlElement("w:fldChar")
                el.set(qn("w:fldCharType"), tag)
                run._r.append(el)
            else:
                el = OxmlElement("w:instrText")
                el.set(qn("xml:space"), "preserve")
                el.text = text
                run._r.append(el)
        add("begin")
        add(text=f" {instr} ")
        add("separate")
        if placeholder:
            run_font(par.add_run(placeholder), size=size)
        add("end")

    # ---------- текст со встроенной разметкой
    def inline(self, par, text, size=14, bold=None):
        """**жирный**, `код`, [текст](ссылка) внутри абзаца."""
        def link(m):
            label, target = m.group(1), m.group(2)
            if target.startswith("http"):
                if target not in self.sources:
                    self.sources.append(target)
                return f"{label} [{self.sources.index(target) + 1}]"
            name = DOC_NAMES.get(target.split("#")[0])
            if name and label.endswith(".md"):
                return name
            return label
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)
        for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
            if not part:
                continue
            if part.startswith("**"):
                run_font(par.add_run(part[2:-2]), size=size, bold=True)
            elif part.startswith("`"):
                run_font(par.add_run(part[1:-1]), name=MONO, size=mono_size(size), bold=bold)
            else:
                run_font(par.add_run(part), size=size, bold=bold)

    def paragraph(self, text):
        par = self.doc.add_paragraph()
        para_format(par)
        self.inline(par, text)

    def list_item(self, text, numbered, number, level):
        par = self.doc.add_paragraph()
        fmt = para_format(par)
        fmt.left_indent = INDENT * level
        mark = f"{number})" if numbered else DASH
        self.inline(par, f"{mark} {text}")

    # ---------- заголовки
    def structural(self, title, in_toc=True):
        """СОДЕРЖАНИЕ, ВВЕДЕНИЕ и т. п.: прописными, полужирным, по центру, с новой страницы."""
        par = self.doc.add_paragraph(style="Heading 1") if in_toc else self.doc.add_paragraph()
        para_format(par, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, after=12)
        par.paragraph_format.page_break_before = True
        par.paragraph_format.keep_with_next = True
        run_font(par.add_run(title.upper()), bold=True)

    def heading(self, title, level):
        self.numbers[level - 1] += 1
        for i in range(level, 3):
            self.numbers[i] = 0
        number = ".".join(str(n) for n in self.numbers[:level])
        par = self.doc.add_paragraph(style=f"Heading {level}")
        if level == 1 and not self.sections_new_page and self.numbers[0] > 1:
            par.paragraph_format.space_before = Pt(18)
        # заголовок без точки в конце; `код` в заголовке — обычным шрифтом заголовка
        self.inline(par, f"{number} {title.rstrip('.')}", bold=True)
        for run in par.runs:
            run.bold = True

    # ---------- таблицы, рисунки, код
    def caption_par(self, text, align, keep_next):
        par = self.doc.add_paragraph()
        fmt = para_format(par, indent=False, align=align)
        fmt.keep_with_next = keep_next
        self.inline(par, text)

    def table(self, lines, caption):
        rows = [[c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))] for line in lines]
        header, align_row, body = rows[0], rows[1], rows[2:]
        right = [c.endswith(":") and not c.startswith(":") for c in align_row]
        self.tables += 1
        self.caption_par(f"Таблица {self.tables} {DASH} {caption}", WD_ALIGN_PARAGRAPH.LEFT, True)

        table = self.doc.add_table(rows=1 + len(body), cols=len(header))
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        widths = column_widths([header] + body)
        table.autofit = False  # фиксированная разметка: Word не пересчитывает ширины по тексту
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        table._tbl.tblPr.append(layout)
        for c, col in enumerate(table.columns):
            col.width = widths[c]
        for r, cells in enumerate([header] + body):
            tr_pr = table.rows[r]._tr.get_or_add_trPr()
            tr_pr.append(OxmlElement("w:cantSplit"))  # строка не рвется между страницами
            if r == 0:
                tr_pr.append(OxmlElement("w:tblHeader"))  # шапка повторяется на каждой странице
            for c, value in enumerate(cells):
                cell = table.cell(r, c)
                cell.width = widths[c]
                par = cell.paragraphs[0]
                align = WD_ALIGN_PARAGRAPH.CENTER if r == 0 else (
                    WD_ALIGN_PARAGRAPH.RIGHT if right[c] else WD_ALIGN_PARAGRAPH.LEFT)
                para_format(par, indent=False, align=align, spacing=1)
                self.inline(par, value.replace("\\|", "|"), size=12, bold=True if r == 0 else None)
        self.spacer()

    def spacer(self):
        par = self.doc.add_paragraph()
        para_format(par, indent=False, spacing=1)

    def figure(self, path, caption):
        par = self.doc.add_paragraph()
        para_format(par, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1, before=6)
        par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(str(path), width=TEXT_WIDTH)
        self.figures += 1
        self.caption_par(f"Рисунок {self.figures} {DASH} {caption}", WD_ALIGN_PARAGRAPH.CENTER, False)
        self.spacer()

    def code(self, code):
        lines = code.rstrip("\n").split("\n")
        for i, line in enumerate(lines):
            par = self.doc.add_paragraph()
            fmt = para_format(par, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1,
                              before=6 if i == 0 else 0, after=6 if i == len(lines) - 1 else 0)
            fmt.left_indent = INDENT
            fmt.keep_with_next = i < len(lines) - 1
            fmt.keep_together = True
            run_font(par.add_run(line or " "), name=MONO, size=11)

    # ---------- титульный лист, содержание, источники
    def title_page(self, title, kind, intro_year):
        def line(text, size=14, bold=False, before=0, align=WD_ALIGN_PARAGRAPH.CENTER):
            par = self.doc.add_paragraph()
            para_format(par, indent=False, align=align, spacing=1.15, before=before)
            run_font(par.add_run(text), size=size, bold=bold)
            return par
        line("Проект TAXI-db")
        line("Поездки такси Чикаго в PostgreSQL")
        line(title, size=16, bold=True, before=200)
        line(kind, size=14, before=12)
        line("Разработчик: DarkSwordman999", before=150, align=WD_ALIGN_PARAGRAPH.RIGHT)
        line("github.com/DarkSwordman999/TAXI-db", align=WD_ALIGN_PARAGRAPH.RIGHT)
        last = line(intro_year, before=150)
        last.paragraph_format.keep_with_next = False

    def contents(self):
        self.structural("Содержание", in_toc=False)
        par = self.doc.add_paragraph()
        para_format(par, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT)
        self.field(par, 'TOC \\o "1-2" \\h \\z \\u',
                   placeholder="Содержание обновляется в Word: правый щелчок по нему → «Обновить поле».")

    def source_list(self):
        if not self.sources:
            return
        self.structural("Список использованных источников")
        for i, url in enumerate(self.sources, 1):
            name = SOURCES.get(url, url)
            par = self.doc.add_paragraph()
            para_format(par)
            run_font(par.add_run(f"{i} {name}. {DASH} URL: {url} (дата обращения: {ACCESS_DATE}). "
                                 f"{DASH} Текст : электронный."))

    def save(self, path, title):
        self.doc.core_properties.title = title
        self.doc.core_properties.author = "DarkSwordman999"
        self.doc.save(path)


def build_docx(md, path, title, kind, sections_new_page=True):
    """Markdown-документ проекта -> Word по ГОСТ 7.32-2017."""
    lines = md.split("\n")
    g = GostDoc(path.name, sections_new_page)
    g.title_page(title, kind, "2026")
    g.contents()

    # все до первого раздела (кроме заголовка и ссылки на docx) — во ВВЕДЕНИЕ
    first = next(i for i, line in enumerate(lines) if line.startswith("## "))
    g.structural("Введение")
    for block in "\n".join(lines[1:first]).split("\n\n"):
        text = " ".join(block.split())
        if text and not text.startswith("Версия Word:"):
            g.paragraph(text)

    i = first
    paragraph = []
    caption = None
    heading_title = ""
    numbered = 0

    def flush():
        if paragraph:
            g.paragraph(" ".join(paragraph))
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if m := re.match(r"^<!-- (Таблица|Рисунок): (.*) -->$", stripped):
            flush()
            caption = m.group(2)
        elif stripped.startswith("```"):
            flush()
            lang = stripped[3:]
            block = []
            i += 1
            while not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            if lang == "mermaid":
                g.figure(ER_PNG, caption or heading_title)
            else:
                g.code("\n".join(block))
            caption = None
        elif m := re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped):
            flush()
            g.figure(DOCS / m.group(2), m.group(1))
        elif stripped.startswith("|"):
            flush()
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            g.table(block, caption or heading_title)
            caption = None
            continue
        elif m := re.match(r"^(#{2,4}) (.*)", line):
            flush()
            # номера из Markdown («3.1.») не переносятся: Word нумерует сам, по ГОСТ
            heading_title = re.sub(r"^\d+(\.\d+)*\.?\s+", "", m.group(2))
            g.heading(heading_title, len(m.group(1)) - 1)
            numbered = 0
        elif m := re.match(r"^(\s*)(- |\d+\. )(.*)", line):
            flush()
            is_numbered = m.group(2)[0].isdigit()
            numbered = numbered + 1 if is_numbered else numbered
            item = m.group(3)
            while i + 1 < len(lines) and lines[i + 1].startswith("   ") and not re.match(
                    r"^\s*(- |\d+\. )", lines[i + 1]):
                i += 1
                item += " " + lines[i].strip()
            g.list_item(item, is_numbered, numbered, 1 + len(m.group(1)) // 2)
        elif not stripped:
            flush()
        else:
            paragraph.append(stripped)
        i += 1
    flush()
    g.source_list()
    g.save(path, f"{title}. {kind}")


def update_in_word(paths, pdf_dir=None):
    """Пересчитывает содержание и номера страниц в установленном Word (только Windows).

    Без Word документ тоже правильный, только содержание нужно обновить вручную (F9)."""
    try:
        import win32com.client  # noqa: PLC0415
    except ImportError:
        return False
    try:
        word = win32com.client.DispatchEx("Word.Application")
    except Exception:  # noqa: BLE001 — Word не установлен
        return False
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        for path in paths:
            doc = word.Documents.Open(str(path.resolve()))
            for toc in doc.TablesOfContents:
                toc.Update()
            doc.Save()
            if pdf_dir:
                doc.ExportAsFixedFormat(str((Path(pdf_dir) / path.with_suffix(".pdf").name).resolve()), 17)
            doc.Close(False)
    finally:
        word.Quit()
    return True


def main():
    pdf_dir = sys.argv[sys.argv.index("--pdf") + 1] if "--pdf" in sys.argv else None
    draw_er(ER_PNG)
    built = []
    for source, target, title, kind, new_page in DOCUMENTS:
        md = (DOCS / source).read_text(encoding="utf-8")
        build_docx(md, DOCS / target, title, kind, new_page)
        built.append(DOCS / target)
    names = ", ".join(p.name for p in built)
    if update_in_word(built, pdf_dir):
        print(f"Готово: {ER_PNG.name}, {names}; содержание обновлено в Word")
    else:
        print(f"Готово: {ER_PNG.name}, {names}; откройте в Word и обновите содержание (F9)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
