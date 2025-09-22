from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import calendar

import pytz

def get_admin_panel_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Тексты✏️", callback_data="admin_texts"),
            InlineKeyboardButton(text="Пользователи📗", callback_data="admin_users"),
            InlineKeyboardButton(text="Уведомления🔔", callback_data="admin_notifications")
        ]
    ])
    return keyboard

def get_back_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Назад", callback_data="back_to_menu")
        ]
    ])
    return keyboard

def get_answer_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Ответить", callback_data="answer"),
            InlineKeyboardButton(text="Отключить уведомления", callback_data="disable_notifications")
        ]
    ])
    return keyboard

def get_only_answer_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Ответить", callback_data="answer")
        ]
    ])
    return keyboard

def get_text_navigation_keyboard(page, total_pages, text_fields):
    start_idx = (page - 1) * 3
    end_idx = start_idx + 3
    keyboard_buttons = [
        InlineKeyboardButton(text=field, callback_data=f"text_{field}_{page}") for field in text_fields[start_idx:end_idx]
    ]

    rows = [keyboard_buttons[i:i + 3] for i in range(0, len(keyboard_buttons), 3)]

    navigation_row = [
        InlineKeyboardButton(text="<<", callback_data=f"prev_page_{page}") if page > 1 else InlineKeyboardButton(text=" ", callback_data="ignore"),
        InlineKeyboardButton(text="Назад", callback_data="back_to_menu"),
        InlineKeyboardButton(text=">>", callback_data=f"next_page_{page}") if page < total_pages else InlineKeyboardButton(text=" ", callback_data="ignore")
    ]
    
    rows.append(navigation_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_user_navigation_keyboard(page, total_pages):
    navigation_row = [
        InlineKeyboardButton(text="<<", callback_data=f"prev_page_{page}") if page > 1 else InlineKeyboardButton(text=" ", callback_data="ignore"),
        InlineKeyboardButton(text="Назад", callback_data="back_to_menu"),
        InlineKeyboardButton(text=">>", callback_data=f"next_page_{page}") if page < total_pages else InlineKeyboardButton(text=" ", callback_data="ignore")
    ]

    search_row = [
        InlineKeyboardButton(text="Поиск 🔎", callback_data="search_user"),
        InlineKeyboardButton(text="ZIP 📁", callback_data="download_zip")
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[navigation_row, search_row])
    return keyboard

def get_user_search_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Поиск 🔎", callback_data="search_user")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
    ])

def get_admin_notification_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Выкл 🟥", callback_data="disable_admin_notification"),
            InlineKeyboardButton(text="Назад", callback_data="back_to_menu"),
            InlineKeyboardButton(text="Вкл 🟩", callback_data="enable_admin_notification")
        ]
    ])
    return keyboard

def get_admin_notify_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="24 часа", callback_data="notify_24"),
            InlineKeyboardButton(text="Завтра", callback_data="notify_tomorrow"),
            InlineKeyboardButton(text="Дата", callback_data="notify_data")
        ]
    ])
    return keyboard

# Функция для создания календаря
def create_calendar(year: int, month: int, user_id: int):
    # Названия месяцев на русском
    month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    
    # Дни недели
    week_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    
    # Короткий формат года (например, 2024 -> 24)
    short_year = year % 100
    
    # Создаем список списков кнопок
    inline_kb = []
    
    # Шапка календаря с названием месяца и кнопками навигации
    header_buttons = [
        InlineKeyboardButton(text='<', callback_data=f'prev_{year}_{month}_{user_id}'),
        InlineKeyboardButton(text=f'{month_names[month - 1]} {short_year}', callback_data='ignore'),
        InlineKeyboardButton(text='>', callback_data=f'next_{year}_{month}_{user_id}')
    ]
    inline_kb.append(header_buttons)
    
    # Дни недели
    week_day_buttons = [InlineKeyboardButton(text=day, callback_data='ignore') for day in week_days]
    inline_kb.append(week_day_buttons)
    
    # Дни месяца
    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                # Пустые кнопки для выравнивания календаря
                row.append(InlineKeyboardButton(text=' ', callback_data='ignore'))
            else:
                # Кнопки для дней месяца
                row.append(InlineKeyboardButton(text=str(day), callback_data=f'day_{year}_{month}_{day}_{user_id}'))
        inline_kb.append(row)
    
    moscow_tz = pytz.timezone('Europe/Moscow')
    today = datetime.now(moscow_tz)
    today_day = today.day

    today_button = [InlineKeyboardButton(text=f"Сегодня ({today_day})", callback_data=f'day_{year}_{month}_{today_day}_{user_id}')]
    inline_kb.append(today_button)

    # Добавляем кнопку "Назад" на отдельной строке
    back_button = [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
    inline_kb.append(back_button)
    
    # Создаем объект InlineKeyboardMarkup
    markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    return markup

def user_change_kb(tg_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Удалить", callback_data=f"delete_user_{tg_id}"),
            InlineKeyboardButton(text="Изменить ФИО", callback_data=f"change_username_{tg_id}")
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data="admin_users"),
            InlineKeyboardButton(text="Рестарт", callback_data="back_to_menu")
        ]
    ])
    return keyboard

def edit_messages_kb(tg_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Удалить все", callback_data=f"delete_all_messages_{tg_id}"),
            InlineKeyboardButton(text="Удалить", callback_data=f"delete_message")
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data="admin_users"),
            InlineKeyboardButton(text="Рестарт", callback_data="back_to_menu")
        ]
    ])
    return keyboard

def all_good(tg_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Всё хорошо", callback_data=f"all_good_{tg_id}")
        ]
    ])
    return keyboard