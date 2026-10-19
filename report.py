import matplotlib

# Гарантирует PDF-бэкенд даже при прямом запуске модуля (main.py задаёт его раньше).
matplotlib.use('pdf')

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from analytics import month_stats
from logging_utils import write_to_log

# Лимит строк сводной таблицы на одном листе
TABLE_ROWS_PER_PAGE = 24
ROW_HEIGHT_FACTOR = 0.034

TABLE_FOOTNOTE = (
    "Примечание. Правило расчета усеченного среднего: отбрасывается одно минимальное "
    "и одно максимальное значение, по оставшимся считается среднее."
)

# Заглушка для тикеров без рассчитанных экстремумов
EMPTY_EXTREMES = {'max_avg': None, 'min_avg': None, 'max_trim': None, 'min_trim': None}


def apply_render_defaults():
    """Параметры экспорта шрифтов (TrueType-текст) и приоритет шрифтов с кириллицей."""
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']


# ----------------------------------------------------------------------
# ЭТАП 2: сводные статистические таблицы
# ----------------------------------------------------------------------

def render_summary_tables(pdf, rows, extremes, tickers_config, target_years, current_moment_str):
    """Постранично рисует сводную таблицу доходностей в открытый PdfPages."""
    write_to_log("📑 ЭТАП 2: Построение сводных аналитических таблиц в PDF...", print_to_console=True)

    ticker_colors_map = {item['ticker']: item['color'] for item in tickers_config}
    ticker_list_ordered = [item['ticker'] for item in tickers_config]
    headers = ["Тикер", "Месяц"] + [f"{y} год" for y in target_years] + ["Среднее", "Усеч. среднее"]
    col_widths = [0.09, 0.09] + [0.10] * len(target_years) + [0.11, 0.11]

    total_rows = len(rows)
    chunk_start = 0
    is_first_page = True

    while chunk_start < total_rows:
        chunk_end = min(chunk_start + TABLE_ROWS_PER_PAGE, total_rows)
        chunk = rows[chunk_start:chunk_end]

        fig_table, ax_table = plt.subplots(figsize=(14, 11))
        ax_table.axis('off')
        computed_height = (len(chunk) + 1) * ROW_HEIGHT_FACTOR

        # Шапка документа — только на первой странице таблицы
        if is_first_page:
            fig_table.text(0.5, 0.95, "Сезонность по месяцам", fontsize=20, color='darkblue',
                           ha='center', fontweight='bold')
            fig_table.text(0.5, 0.91, f"Анализ исторических данных за {len(target_years)} лет от {current_moment_str}",
                           fontsize=11, color='gray', ha='center')
            table_location = [0.03, 0.88 - computed_height, 0.94, computed_height]
            is_first_page = False
        else:
            table_location = [0.03, 0.94 - computed_height, 0.94, computed_height]

        summary_table = ax_table.table(
            cellText=chunk,
            colLabels=headers,
            loc='upper center',
            cellLoc='center',
            colWidths=col_widths,
            bbox=table_location,
        )
        summary_table.set_fontsize(9)
        summary_table.auto_set_font_size(False)
        _style_summary_cells(summary_table, chunk, headers, ticker_colors_map, ticker_list_ordered, extremes)

        # Примечание о методике — только на последней странице таблицы
        if chunk_end == total_rows:
            fig_table.text(0.03, 0.03, TABLE_FOOTNOTE, fontsize=9, color='gray',
                           ha='left', va='bottom', style='italic')

        pdf.savefig(fig_table)
        plt.close(fig_table)
        chunk_start = chunk_end


def _style_summary_cells(summary_table, chunk, headers, ticker_colors_map, ticker_list_ordered, extremes):
    """Пост-процессинг ячеек: чередование фона, цвета тикеров, экстремумы, знак доходности."""
    for (row, col), cell in summary_table.get_celld().items():
        if row == 0:
            cell.set_facecolor('#a0a0a0')
            cell.get_text().set_fontweight('bold')
            cell.get_text().set_color('black')
            cell.get_text().set_fontsize(9)
            continue

        row_ticker = chunk[row - 1][0]
        row_month = chunk[row - 1][1]

        # Чередование фона строк по порядку тикеров в реестре
        if row_ticker in ticker_list_ordered:
            ticker_index = ticker_list_ordered.index(row_ticker)
            cell.set_facecolor('#e0e0e0' if ticker_index % 2 == 1 else '#ffffff')

        if col == 0:
            cell.get_text().set_fontweight('normal')
            cell.get_text().set_fontsize(9)
            if row_ticker in ticker_colors_map:
                cell.get_text().set_color(ticker_colors_map[row_ticker])
        elif col >= 2:
            txt = cell.get_text().get_text().strip()
            item = extremes.get(row_ticker, EMPTY_EXTREMES)
            cell.get_text().set_fontsize(9)

            # Экстремумы выделяются жирным в колонке «Среднее»
            if col == len(headers) - 2:
                if row_month in (item['max_avg'], item['min_avg']):
                    cell.get_text().set_fontweight('bold')
                    cell.get_text().set_fontsize(10)
                else:
                    cell.get_text().set_fontweight('normal')
            # Экстремумы выделяются жирным в колонке «Усеч. среднее»
            elif col == len(headers) - 1:
                if row_month in (item['max_trim'], item['min_trim']):
                    cell.get_text().set_fontweight('bold')
                    cell.get_text().set_fontsize(10)
                else:
                    cell.get_text().set_fontweight('normal')
            else:
                cell.get_text().set_fontweight('medium')

            # Знак доходности: зелёный — рост, красный — падение
            if txt.startswith('+'):
                cell.get_text().set_color('forestgreen')
            elif txt.startswith('-'):
                cell.get_text().set_color('darkred')
            else:
                cell.get_text().set_color('black')


# ----------------------------------------------------------------------
# ЭТАП 3: детальные помесячные страницы по активам
# ----------------------------------------------------------------------

def _years_word(n):
    """Форма слова «год» для подписи среднего: 6 лет, 3 года, 1 год."""
    if n % 100 in (11, 12, 13, 14):
        return "лет"
    if n % 10 == 1:
        return "год"
    if n % 10 in (2, 3, 4):
        return "года"
    return "лет"


def render_detail_pages(pdf, datasets, tickers_config, months_to_analyze, target_years):
    """Рисует по одной странице на каждый месяц каждого активного инструмента."""
    write_to_log("📈 ЭТАП 3: Отрисовка поактивных детальных исторических графиков...", print_to_console=True)

    for col_info in tickers_config:
        t_code = col_info['ticker']
        if t_code not in datasets:
            continue
        if not col_info.get('plot_charts', True):
            continue
        df_data = datasets[t_code]

        for m_info in months_to_analyze:
            _render_month_page(pdf, df_data, col_info, m_info, target_years)


def _render_month_page(pdf, df_data, col_info, m_info, target_years):
    """Одна страница: заголовок, среднее за все годы с данными и сетка subplot'ов по годам."""
    t_code = col_info['ticker']
    m_num, m_name = m_info['number'], m_info['name']

    pct_values, money_values = [], []
    for year in target_years:
        stats = month_stats(df_data, t_code, year, m_num)
        if stats is not None and stats['pct'] is not None:
            pct_values.append(stats['pct'])
            money_values.append(stats['money'])

    if pct_values:
        n_years = len(pct_values)
        avg_percent = sum(pct_values) / n_years
        avg_money = sum(money_values) / n_years
        avg_sign = "+" if avg_percent >= 0 else ""
        avg_text = (f"Среднее значение за {n_years} {_years_word(n_years)}: "
                    f"{avg_sign}{avg_money:.2f} {col_info['unit']} ({avg_sign}{avg_percent:.2f}%)")
        avg_color = 'forestgreen' if avg_percent >= 0 else 'darkred'
    else:
        avg_text = "Среднее изменение: нет данных"
        avg_color = 'gray'

    n_cols = 2
    n_rows = (len(target_years) + n_cols - 1) // n_cols
    fig, axes_grid = plt.subplots(n_rows, n_cols, figsize=(14, 10))
    axes = list(axes_grid.flat)

    page_title = f"{m_name}. {col_info['name']}"
    fig.text(0.5, 0.97, page_title, fontsize=14, color='black', ha='center', fontweight='bold')
    fig.text(0.5, 0.94, avg_text, fontsize=11, color=avg_color, ha='center', fontweight='semibold')

    for idx, year in enumerate(target_years):
        _render_year_subplot(axes[idx], df_data, col_info, m_info, year)

    # Лишние ячейки сетки (при нечётном числе лет) скрываются
    for ax in axes[len(target_years):]:
        ax.axis('off')

    plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.91])
    pdf.savefig(fig)
    plt.close(fig)


def _render_year_subplot(ax, df_data, col_info, m_info, year):
    """Отдельный subplot: линия цены за месяц конкретного года с базой прошлого месяца."""
    t_code = col_info['ticker']
    m_num, m_name = m_info['number'], m_info['name']
    month_start = pd.Timestamp(year=year, month=m_num, day=1)

    month_data = df_data[(df_data.index.year == year) & (df_data.index.month == m_num)]

    # Если в самом месяце данных нет — выводим заглушку без графика и без якоря
    if month_data.empty:
        ax.axis('off')
        ax.text(0.5, 0.5, f"Нет данных\n{m_name} {year} г.", ha='center', va='center',
                color='gray', fontsize=10)
        ax.set_title(f"{year} год", fontsize=11, fontweight='bold', pad=10)
        return

    # Якорь: последняя свеча предыдущего месяца — линия начинается с реального
    # закрытия прошлого месяца
    prev_month_data = df_data[df_data.index < month_start]
    has_prev = not prev_month_data.empty
    if has_prev:
        month_data = pd.concat([prev_month_data.iloc[[-1]], month_data])

    ax.plot(month_data.index, month_data[t_code], color=col_info['color'], linewidth=1.5, label=t_code)
    ax.set_title(f"{year} год", fontsize=11, fontweight='bold')

    ax.tick_params(axis='y', which='both', left=True, right=True, labelleft=False, labelright=True)
    ax.yaxis.set_label_position("right")
    ax.set_ylabel("Цена закрытия", fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.6)

    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax.tick_params(axis='x', labelsize=8)

    stats = month_stats(df_data, t_code, year, m_num)
    if stats is None:  # недостижимо после проверки month_data, защита на будущее
        return

    if stats['pct'] is not None:
        sign = "+" if stats['money'] >= 0 else ""
        change_label = "Изменение к прошл. месяцу" if has_prev else "Изменение за месяц (внутри)"
        result_text = f"{change_label}: {sign}{stats['money']:.2f} {col_info['unit']} ({sign}{stats['pct']:.2f}%)"
        text_color = 'forestgreen' if stats['money'] >= 0 else 'darkred'
    else:
        result_text = "Изменение: н/д (нулевая базовая цена)"
        text_color = 'gray'

    ax.axhline(stats['base'], color='#4a4a4a', linestyle='--', linewidth=0.8, alpha=0.75)
    ax.axhline(stats['end'], color='#4a4a4a', linestyle='--', linewidth=0.8, alpha=0.75)

    ax.text(0.015, stats['base'], f"{stats['base']:.2f}", transform=ax.get_yaxis_transform(),
            fontsize=8, color=text_color, ha='left', va='center', fontweight='normal')
    ax.text(0.015, stats['end'], f"{stats['end']:.2f}", transform=ax.get_yaxis_transform(),
            fontsize=8, color=text_color, ha='left', va='center', fontweight='normal')

    ax.set_xlabel(result_text, fontsize=9, fontweight='medium', color=text_color)
