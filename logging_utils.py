"""
Все папки создаются рядом с проектом (по пути каталога скрипта, а не текущего
каталога запуска), логи накапливаются помесячно без ротации.
"""

import os
from datetime import date, datetime

FOLDER_NAMES = ('txt', 'logs', 'reports')

_log_file = None


def setup_folders(base_dir):
    """Создаёт при необходимости служебные папки и возвращает словарь путей.

    Пути привязываются к каталогу проекта, поэтому запуск возможен из любого
    текущего каталога — папки не «раскидываются» по месту запуска.
    """
    paths = {name: os.path.join(base_dir, name) for name in FOLDER_NAMES}
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
    return paths


def init_logging(logs_dir):
    """Фиксирует файл лога на месяц запуска (ротация отключена: файлы копятся помесячно)."""
    global _log_file
    log_date_str = date.today().strftime('%Y-%m')
    _log_file = os.path.join(logs_dir, f"{log_date_str}-season-months.log")


def write_to_log(message, print_to_console=False):
    """Добавляет строку с меткой времени в текущий лог-файл и, при необходимости, в консоль."""
    if _log_file is None:
        raise RuntimeError("Логирование не инициализировано: сначала вызовите init_logging().")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(_log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    if print_to_console:
        print(message)
