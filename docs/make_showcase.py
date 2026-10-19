#!/usr/bin/env python3
"""Картинки для README: карта посадок, тепловая карта, средний чек по месяцам.

Каждая картинка строится в двух вариантах, для светлой и темной темы GitHub:
docs/showcase/<имя>-light.png и <имя>-dark.png.

    python docs/make_showcase.py
"""

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch
import psycopg2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from scripts.db_config import DB_CONFIG  # noqa: E402

OUT = ROOT / "docs" / "showcase"

# Палитра: один синий тон для величин, нейтральные чернила для текста и осей
THEMES = {
    "light": {
        "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#8a8984", "grid": "#e4e3df",
        "accent": "#2a78d6", "accent_soft": "#86b6ef", "route": "#eb6834",
        "ramp": ["#f2f7fd", "#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"],
    },
    "dark": {
        "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#8f8e86", "grid": "#30363d",
        "accent": "#3987e5", "accent_soft": "#256abf", "route": "#d95926",
        "ramp": ["#161b22", "#104281", "#1c5cab", "#2a78d6", "#5598e7", "#9ec5f4", "#cde2fb"],
    },
}

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MONTHS_GEN = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
              "сентября", "октября", "ноября", "декабря"]
MONTHS = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]


def fetch(cur, sql):
    cur.execute(sql)
    return cur.fetchall()


def load_data():
    with psycopg2.connect(**DB_CONFIG) as conn, conn.cursor() as cur:
        return {
            "areas": fetch(cur, """
                SELECT р.название, р.широта::float, р.долгота::float, count(п.*)
                FROM РАЙОНЫ р LEFT JOIN ПОЕЗДКИ п ON п.откуда = р.код
                GROUP BY р.код ORDER BY р.код"""),
            "routes": fetch(cur, """
                WITH пары AS (
                    SELECT least(откуда, куда) AS r1, greatest(откуда, куда) AS r2, count(*) AS n
                    FROM ПОЕЗДКИ WHERE откуда <> куда GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 8)
                SELECT a.широта::float, a.долгота::float, b.широта::float, b.долгота::float, п.n
                FROM пары п JOIN РАЙОНЫ a ON a.код = п.r1 JOIN РАЙОНЫ b ON b.код = п.r2
                ORDER BY п.n DESC"""),
            "heat": fetch(cur, """
                SELECT extract(isodow FROM дата)::int, extract(hour FROM дата)::int,
                       count(*)::float / count(DISTINCT дата::date)
                FROM ПОЕЗДКИ GROUP BY 1, 2"""),
            "months": fetch(cur, """
                SELECT date_trunc('month', дата)::date, count(*), sum(стоимость + чаевые + сборы)::float
                FROM ПОЕЗДКИ GROUP BY 1 ORDER BY 1"""),
        }


def style(t):
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 11,
        "text.color": t["ink"], "axes.labelcolor": t["ink2"],
        "xtick.color": t["ink2"], "ytick.color": t["ink2"],
        "axes.edgecolor": t["grid"], "axes.facecolor": "none", "figure.facecolor": "none",
    })


def title(fig, t, text, sub):
    fig.text(0.02, 0.97, text, fontsize=15, fontweight="bold", color=t["ink"], va="top")
    fig.text(0.02, 0.905, sub, fontsize=10.5, color=t["ink2"], va="top")


def clean_axes(ax, t, grid_axis="y"):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(t["grid"])
    ax.tick_params(length=0)
    if grid_axis:
        ax.grid(axis=grid_axis, color=t["grid"], linewidth=0.8)
    ax.set_axisbelow(True)


def chart_map(d, t):
    fig = plt.figure(figsize=(6.4, 7.6))
    title(fig, t, "Где садятся в такси", "посадки по 77 районам Чикаго и самые частые маршруты")
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.82])
    areas = [a for a in d["areas"] if a[1] is not None]
    top = max(a[3] for a in areas)
    total = sum(a[3] for a in areas)

    # маршруты: дуги между центрами районов, толщина по числу поездок
    rmax = d["routes"][0][4]
    for lat1, lon1, lat2, lon2, n in d["routes"]:
        ax.add_patch(FancyArrowPatch(
            (lon1, lat1), (lon2, lat2), arrowstyle="-", connectionstyle="arc3,rad=0.25",
            color=t["route"], linewidth=1 + 4 * n / rmax, alpha=0.75, zorder=2))

    ax.scatter([a[2] for a in areas], [a[1] for a in areas],
               s=[10 + 1300 * a[3] / top for a in areas],
               color=t["accent"], alpha=0.55, edgecolors=t["accent"], linewidths=1, zorder=3)

    # подписи крупных районов вынесены в сторону, к району ведет тонкая линия
    labels = {"Ohare": (-87.905, 41.94, "center"), "Lake View": (-87.575, 41.965, "left"),
              "Near North Side": (-87.575, 41.915, "left"), "Loop": (-87.575, 41.865, "left"),
              "Near West Side": (-87.735, 41.835, "right")}
    for name, lat, lon, n in areas:
        if name in labels:
            x, y, ha = labels[name]
            shown = "O'Hare" if name == "Ohare" else name
            ax.annotate(f"{shown}  {100 * n / total:.0f} %", (lon, lat), xytext=(x, y),
                        fontsize=10, color=t["ink"], ha=ha, va="center", zorder=4,
                        arrowprops=dict(arrowstyle="-", color=t["muted"], linewidth=0.8,
                                        shrinkA=3, shrinkB=4))

    ax.text(-87.53, 42.03, "озеро\nМичиган", color=t["muted"], fontsize=10, style="italic", ha="center")
    ax.scatter([], [], s=120, color=t["accent"], alpha=0.55, label="посадки в районе")
    ax.plot([], [], color=t["route"], linewidth=3, label="самые частые маршруты")
    ax.legend(loc="lower left", frameon=False, labelcolor=t["ink2"], fontsize=9.5)
    ax.set_xlim(-87.95, -87.43)
    ax.axis("off")
    return fig


def chart_heat(d, t):
    fig = plt.figure(figsize=(11, 3.9))
    title(fig, t, "Ритм города", "поездок в час в среднем за день: будничные пики в 8 и 17 часов, тишина в 4 утра")
    ax = fig.add_axes([0.05, 0.12, 0.86, 0.66])
    grid = [[0.0] * 24 for _ in range(7)]
    for dow, hour, n in d["heat"]:
        grid[dow - 1][hour] = n
    cmap = LinearSegmentedColormap.from_list("ramp", t["ramp"])
    im = ax.imshow(grid, cmap=cmap, aspect="auto", interpolation="nearest")
    ax.set_yticks(range(7), WEEKDAYS)
    ax.set_xticks(range(0, 24, 2), [f"{h}:00" for h in range(0, 24, 2)])
    ax.tick_params(length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    # тонкие разделители между клетками цветом фона GitHub
    sep = "#ffffff" if t is THEMES["light"] else "#0d1117"
    ax.set_xticks([x - 0.5 for x in range(1, 24)], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, 7)], minor=True)
    ax.grid(which="minor", color=sep, linewidth=1.5)
    ax.tick_params(which="minor", length=0)
    cax = fig.add_axes([0.925, 0.12, 0.015, 0.66])
    cb = fig.colorbar(im, cax=cax)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, labelsize=9)
    return fig


def chart_months(d, t):
    months = d["months"]
    checks = [m[2] / m[1] for m in months]
    lo = min(range(len(checks)), key=checks.__getitem__)
    growth = 100 * (checks[-1] / checks[lo] - 1)
    fig = plt.figure(figsize=(11, 3.9))
    title(fig, t, "Чек растет",
          f"средний чек с чаевыми и сборами по месяцам: с {MONTHS_GEN[months[lo][0].month - 1]} "
          f"по сентябрь +{growth:.0f} %")
    ax = fig.add_axes([0.06, 0.12, 0.92, 0.66])
    x = list(range(len(months)))
    ax.plot(x, checks, color=t["accent"], linewidth=2.2, zorder=3)
    ax.scatter(x, checks, s=36, color=t["accent"], zorder=4)
    ax.set_xticks(x, [f"{MONTHS[m[0].month - 1]}\n{m[0]:%Y}" if m[0].month in (1, 10) else MONTHS[m[0].month - 1]
                      for m in months])
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v:.0f}"))
    clean_axes(ax, t)
    for i in (lo, len(checks) - 1):
        ax.annotate(f"${checks[i]:.2f}".replace(".", ","), (i, checks[i]), xytext=(0, 12 if i == len(checks) - 1 else -22),
                    textcoords="offset points", ha="center", fontsize=10, color=t["ink"], fontweight="bold")
    ax.set_ylim(min(checks) - 3, max(checks) + 2)
    ax.set_xlim(-0.4, len(months) - 0.6)
    return fig


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = load_data()
    charts = {"map": chart_map, "rhythm": chart_heat, "check": chart_months}
    for mode, t in THEMES.items():
        style(t)
        for name, build in charts.items():
            fig = build(d, t)
            path = OUT / f"{name}-{mode}.png"
            fig.savefig(path, dpi=144, transparent=True)
            plt.close(fig)
            print(f"  {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
