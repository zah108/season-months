
from datetime import date

# ----------------------------------------------------------------------
# Период анализа
# ----------------------------------------------------------------------

# Точка отсчёта анализируемого периода. Данные реально загружаются на месяц
# раньше (см. loader.load_start), чтобы у первого анализируемого месяца
# базой было закрытие предыдущего месяца, а не первая свеча самого месяца.
START_FETCH_DATE = "2021-01-01"

# Набор анализируемых исторических лет для построения графиков и таблиц
TARGET_YEARS = [2021, 2022, 2023, 2024, 2025, 2026]

# ----------------------------------------------------------------------
# Реестр конфигураций исследуемых биржевых инструментов
# ----------------------------------------------------------------------

TICKERS_CONFIG = [
    {
        'ticker': 'SBER',
        'market': 'TQBR',
        'name': 'Акции Сбербанка (SBER)',
        'unit': '₽',
        'color': 'seagreen',
        'plot_charts': True
    },
    {
        'ticker': 'GOLD',
        'market': 'TQBR',
        'name': 'Фонд ВИМ Золото (GOLD)',
        'unit': '₽',
        'color': 'darkorange',
        'plot_charts': False
    },
    {
        'ticker': 'MOEX',
        'market': 'TQBR',
        'name': 'Акции Московской биржи (MOEX)',
        'unit': '₽',
        'color': 'darkblue',
        'plot_charts': False
    },
    {
        'ticker': 'MTSS',
        'market': 'TQBR',
        'name': 'Акции МТС (MTSS)',
        'unit': '₽',
        'color': 'DarkTurquoise',
        'plot_charts': False
    },
    {
        'ticker': 'Si',
        'market': 'FORTS',
        'name': 'Фьючерс Доллар-Рубль (Si)',
        'unit': '₽',
        'color': 'darkgreen',
        'plot_charts': False
    },
    {
        'ticker': 'CR',
        'market': 'FORTS',
        'name': 'Фьючерс Юань-Рубль (CR)',
        'unit': '₽',
        'color': 'darkgreen',
        'plot_charts': True
    },
    {
        'ticker': 'GD',
        'market': 'FORTS',
        'name': 'Фьючерс Золото (GD)',
        'unit': '$',
        'color': 'darkorange',
        'plot_charts': False
    },
    {
        'ticker': 'SV',
        'market': 'FORTS',
        'name': 'Фьючерс Серебро (SV)',
        'unit': '$',
        'color': 'slategray',
        'plot_charts': True
    },
    {
        'ticker': 'PT',
        'market': 'FORTS',
        'name': 'Фьючерс Платина (PT)',
        'unit': '$',
        'color': 'chocolate',
        'plot_charts': True
    },
    {
        'ticker': 'NG',
        'market': 'FORTS',
        'name': 'Фьючерс Природный газ (NG)',
        'unit': '$',
        'color': 'DarkTurquoise',
        'plot_charts': True
    },
]

# ----------------------------------------------------------------------
# Календарь месяцев
# ----------------------------------------------------------------------

# Текстовые названия месяцев для подписей и таблиц
MONTHS_RU = {
    1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
    5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
    9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь',
}


def months_order(start_month=None):
    """Порядок месяцев, начиная с текущего календарного (по умолчанию)."""
    start = start_month if start_month is not None else date.today().month
    return [(start - 1 + i) % 12 + 1 for i in range(12)]


def build_months_to_analyze(start_month=None):
    """Список [{'number': 10, 'name': 'Октябрь'}, ...] в порядке анализа."""
    return [{'number': m, 'name': MONTHS_RU[m]} for m in months_order(start_month)]
