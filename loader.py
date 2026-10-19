"""Этап 1: чтение локальных котировок из txt/ в датафреймы.

Файлы ищутся в двух вариантах имени: "<тикер>-all-d.txt" и "<тикер>-d-5y.txt".
Разделитель определяется по первой строке файла (tab, ';' или запятая).
"""

import os

import pandas as pd

from logging_utils import write_to_log


def load_start(start_fetch_date):
    """Реальная дата начала загрузки: на месяц раньше точки отсчёта.

    Смещение нужно, чтобы у первого анализируемого месяца (январь 2021)
    базой служило закрытие предыдущего месяца (декабрь 2020), а не первая
    свеча самого января — иначе доходность января первого года искажалась.
    """
    return pd.Timestamp(start_fetch_date) - pd.DateOffset(months=1)


def detect_separator(path):
    """Определяет разделитель по первой строке файла: tab, ';' или запятая."""
    with open(path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
    if '\t' in first_line:
        return '\t'
    if ';' in first_line:
        return ';'
    return ','


def load_dataset(path, ticker, start_date):
    """Читает один файл: DataFrame с индексом-датой и колонкой с именем тикера.

    Дата парсится ПОСЛЕ нормализации имён колонок — при обратном порядке
    файлы с заголовками в другом регистре ('date', 'DATE') отбрасывались
    с ложной ошибкой «Ошибка чтения файла». Возвращает None, если в файле
    нет подходящей колонки с ценой.
    """
    sep_char = detect_separator(path)
    df = pd.read_csv(path, sep=sep_char)
    df.columns = [str(c).strip().capitalize() for c in df.columns]

    if 'Date' not in df.columns:
        return None
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date').sort_index()

    close_col = None
    for col in df.columns:
        if col in ('Close', ticker, ticker.lower(), ticker.capitalize()):
            close_col = col
            break
    if close_col is None:
        return None

    df = df[[close_col]].rename(columns={close_col: ticker})
    return df[df.index >= start_date]


def load_datasets(tickers_config, txt_dir, start_date):
    """Загружает все доступные инструменты. Возвращает {тикер: DataFrame}."""
    loaded = {}
    for item in tickers_config:
        t_code = item['ticker']
        possible_paths = [
            os.path.join(txt_dir, f"{t_code}-all-d.txt"),
            os.path.join(txt_dir, f"{t_code}-d-5y.txt"),
        ]

        df_file = None
        for txt_input_path in possible_paths:
            if not os.path.exists(txt_input_path):
                continue
            try:
                df_file = load_dataset(txt_input_path, t_code, start_date)
            except Exception as e:
                write_to_log(f"⚠️ Ошибка чтения файла {txt_input_path}: {e}", print_to_console=True)
                continue
            if df_file is not None:
                write_to_log(
                    f"📖 Успешно загружен локальный файл: {os.path.basename(txt_input_path)}",
                    print_to_console=True,
                )
                break

        if df_file is not None:
            loaded[t_code] = df_file
        else:
            write_to_log(
                f"⚠️ Ошибка: Локальные данные для {t_code} не найдены в папке {txt_dir}/. Пропуск.",
                print_to_console=True,
            )
    return loaded
