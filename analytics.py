"""Математическое ядро сезонного анализа (без matplotlib).

Единая точка расчёта доходности месяца — month_stats(); на ней строятся
и сводные таблицы, и детальные графики, поэтому формулы в разных частях
отчёта не могут разойтись.
"""

import pandas as pd


def month_stats(df, ticker, year, month):
    """Статистика одного календарного месяца или None, если данных нет.

    Базой служит последнее закрытие предыдущего месяца; если данных за
    предыдущий месяц нет (самый первый месяц загрузки), берётся первая
    свеча самого месяца. Возвращает словарь с ключами:
        base  — базовая цена (закрытие предыдущего месяца);
        end   — последнее закрытие месяца;
        money — изменение в валюте инструмента;
        pct   — изменение в процентах (None при нулевой базовой цене —
                защита от деления на ноль, актуально для фьючерсов).
    """
    month_start = pd.Timestamp(year=year, month=month, day=1)
    month_data = df[(df.index.year == year) & (df.index.month == month)]
    if month_data.empty:
        return None

    prev_month_data = df[df.index < month_start]
    if not prev_month_data.empty:
        base_price = prev_month_data[ticker].iloc[-1]
    else:
        base_price = month_data[ticker].iloc[0]

    end_price = month_data[ticker].iloc[-1]
    money_diff = end_price - base_price
    pct_diff = (money_diff / base_price) * 100 if base_price != 0 else None
    return {
        'base': base_price,
        'end': end_price,
        'money': money_diff,
        'pct': pct_diff,
    }


def fmt_pct(value):
    """Форматирует процент со знаком: '+1.23%', '-0.40%', '+0.00%'."""
    return f"{value:+.2f}%"


def build_table_rows(datasets, tickers_config, months_to_analyze, target_years):
    """Строки сводной таблицы и словари средних по тикерам.

    Возвращает кортеж (rows, avg_values, trimmed_values):
        rows           — строки [тикер, месяц, ячейки по годам, среднее, усеч. среднее];
        avg_values     — {тикер: {название месяца: среднее, %}};
        trimmed_values — {тикер: {название месяца: усечённое среднее, %}}.

    В средние включаются все месяцы с данными, включая текущий незавершённый.
    """
    rows = []
    avg_values = {item['ticker']: {} for item in tickers_config}
    trimmed_values = {item['ticker']: {} for item in tickers_config}

    for item in tickers_config:
        t_code = item['ticker']
        if t_code not in datasets:
            continue
        df_data = datasets[t_code]

        for m_info in months_to_analyze:
            m_num = m_info['number']
            m_name = m_info['name']
            row_cells = [t_code, m_name]
            pct_values = []

            for year in target_years:
                stats = month_stats(df_data, t_code, year, m_num)
                if stats is None or stats['pct'] is None:
                    row_cells.append("—")
                else:
                    row_cells.append(fmt_pct(stats['pct']))
                    pct_values.append(stats['pct'])

            # Среднее по всем месяцам с данными (включая незавершённые)
            if pct_values:
                avg_pct = sum(pct_values) / len(pct_values)
                row_cells.append(fmt_pct(avg_pct))
                avg_values[t_code][m_name] = avg_pct
            else:
                row_cells.append("—")

            # Усечённое среднее: с 3+ значений отбрасываются min и max,
            # при меньшем числе — обычное среднее
            if len(pct_values) >= 3:
                trimmed_list = sorted(pct_values)[1:-1]
                trimmed_pct = sum(trimmed_list) / len(trimmed_list)
            elif pct_values:
                trimmed_pct = sum(pct_values) / len(pct_values)
            else:
                trimmed_pct = None

            if trimmed_pct is not None:
                row_cells.append(fmt_pct(trimmed_pct))
                trimmed_values[t_code][m_name] = trimmed_pct
            else:
                row_cells.append("—")

            rows.append(row_cells)

    return rows, avg_values, trimmed_values


def find_extremes(avg_values, trimmed_values):
    """Лучшие и худшие месяцы (экстремумы) для каждого инструмента."""
    extremes = {}
    for t_code, avg_data in avg_values.items():
        item = {'max_avg': None, 'min_avg': None, 'max_trim': None, 'min_trim': None}
        if avg_data:
            item['max_avg'] = max(avg_data, key=avg_data.get)
            item['min_avg'] = min(avg_data, key=avg_data.get)
        trim_data = trimmed_values.get(t_code, {})
        if trim_data:
            item['max_trim'] = max(trim_data, key=trim_data.get)
            item['min_trim'] = min(trim_data, key=trim_data.get)
        extremes[t_code] = item
    return extremes
