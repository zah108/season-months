#!/usr/bin/env python3
"""Точка входа и сборка отчёта season-months.

Запуск: python3 main.py из папки проекта либо по полному пути из любого каталога.

Модули проекта:
    config.py        — период анализа, реестр активов, календарь месяцев;
    logging_utils.py — служебные папки и помесячный лог;
    loader.py        — этап 1: чтение котировок из txt/;
    analytics.py     — расчёт доходностей, средних и экстремумов;
    report.py        — этапы 2–3: отрисовка PDF (таблицы и графики).

Тяжёлые библиотеки (matplotlib, pandas) импортируются внутри main() после
первых сообщений в консоли — чтобы между запуском и откликом не было тишины.
"""

import os
import sys
from datetime import datetime

# Кэш байт-кода (.pyc) специально не отключаем: без него каждый запуск заново
# компилирует pandas/matplotlib — это лишние секунды на старте.
#
# Папка проекта — там же, где лежит этот файл: она же путь поиска модулей
# и место служебных папок txt/, logs/, reports/.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Наверху — только стандартная библиотека; matplotlib и pandas грузятся
# внутри main() после первых сообщений.
from logging_utils import init_logging, setup_folders, write_to_log


def main():
    # Первые сообщения — сразу, до загрузки тяжёлых библиотек.
    paths = setup_folders(PROJECT_DIR)
    init_logging(paths['logs'])

    # Момент запуска: попадает в заголовок отчёта (дата и время) и в имя файла
    now = datetime.now()
    write_to_log("🚀 Запуск системы сезонного анализа рынка season-months.", print_to_console=True)

    # Тяжёлые импорты: pandas нужен этапу 1, pyplot — этапам 2–3.
    import matplotlib

    # PDF-бэкенд задаётся строго до импорта pyplot внутри report.
    matplotlib.use('pdf')

    import analytics
    import config
    import loader
    import report
    from matplotlib.backends.backend_pdf import PdfPages

    write_to_log("📊 ЭТАП 1: Чтение локальных файлов и анализ доходностей...", print_to_console=True)

    # Данные грузим на месяц раньше точки отсчёта: у января 2021 года базой
    # должно быть закрытие декабря 2020, а не первая свеча самого января.
    load_from = loader.load_start(config.START_FETCH_DATE)
    datasets = loader.load_datasets(config.TICKERS_CONFIG, paths['txt'], load_from)

    if not datasets:
        write_to_log("❌ Критическая ошибка: Нет данных для анализа. Убедитесь, что файлы лежат в папке txt/", print_to_console=True)
        sys.exit(1)

    months_to_analyze = config.build_months_to_analyze(now.month)
    rows, avg_values, trimmed_values = analytics.build_table_rows(
        datasets, config.TICKERS_CONFIG, months_to_analyze, config.TARGET_YEARS
    )
    extremes = analytics.find_extremes(avg_values, trimmed_values)
    write_to_log("📊 Матрицы доходностей по месяцам и годам рассчитаны.", print_to_console=True)

    output_pdf_path = os.path.join(paths['reports'], f"{now.strftime('%Y-%m-%d')}-Season-months.pdf")

    report.apply_render_defaults()

    # Контекстный менеджер закрывает PDF даже при ошибке отрисовки
    with PdfPages(output_pdf_path) as pdf:
        report.render_summary_tables(
            pdf, rows, extremes, config.TICKERS_CONFIG, config.TARGET_YEARS,
            now.strftime('%d.%m.%Y %H:%M')
        )
        report.render_detail_pages(
            pdf, datasets, config.TICKERS_CONFIG, months_to_analyze, config.TARGET_YEARS
        )

    write_to_log(f"✅ Сезонный помесячный анализ завершен успешно! Файл: {output_pdf_path}", print_to_console=True)


if __name__ == '__main__':
    main()
