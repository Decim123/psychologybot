import asyncio
from asyncio.log import logger
import tempfile
from aiogram import Router, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.types.input_file import FSInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.services import *
from keyboards.keyboard import *
router = Router()
user_states = {}
notification_states = {}
VALID_KEYS = {"ao_GKaI3f"}

import asyncio
from datetime import datetime, timedelta
import pytz

async def send_reminder(bot: Bot, user_id: int, delay: int, message_text: str, retries_left: int):
    await asyncio.sleep(delay)
    if notification_states.get(user_id, True):
        await bot.send_message(user_id, message_text, reply_markup=get_answer_keyboard())
        add_message(user_id, '🔔', 'Уведомление получено')

    else:
        logger.info(f"Уведомление пользователю {user_id} не отправлено: статус {user_states.get(user_id)}")

    if retries_left > 0:
        next_delay = 172800 if retries_left == 2 else 432000
        next_message = str(answer('n1'))
        await send_reminder(bot, user_id, next_delay, next_message, retries_left - 1)
    else:
        logger.info(f"Все попытки уведомления исчерпаны для пользователя {user_id}")


async def notify_admins_about_answers(user_id: int, bot: Bot):
    admins = get_admins_with_notifications_enabled()  # Получаем список администраторов с включенными уведомлениями
    user_data = get_user_data(user_id)  # Получаем данные о пользователе

    # Формируем короткое сообщение с инлайн-кнопкой
    message_text = (
        f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\n"
        f"ответил на вопросы."
    )

    # Создаем инлайн-клавиатуру с кнопкой "Посмотреть"
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Посмотреть", callback_data=f"view_answers_{user_data['tg_id']}")
        ]
    ])

    for admin in admins:
        try:
            await bot.send_message(chat_id=admin['tg_id'], text=message_text, reply_markup=inline_kb)
            print(admin['tg_id'], 'получил уведомление')
        except:
            print(admin['tg_id'], 'не получил уведомление')

async def notify_admins_about_reg(user_id: int, bot: Bot):
    admins = get_admins_with_notifications_enabled()  # Получаем список администраторов с включенными уведомлениями
    user_data = get_user_data(user_id)  # Получаем данные о пользователе

    message_text = (
        f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\n"
        f"Зарегистрирован."
    )

    for admin in admins:
        try:
            await bot.send_message(chat_id=admin['tg_id'], text=message_text)
            print(admin['tg_id'], 'получил уведомление')
        except:
            print(admin['tg_id'], 'не получил уведомление')

@router.message(CommandStart())
async def process_start_command(message: Message, bot: Bot, command: CommandStart):
    key = command.args 
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    username = message.from_user.username
    if key in VALID_KEYS or user_exists(str(user_id)):
        add_user_if_not_exists(user_id, user_full_name, username)
        user_states[user_id] = 'start'
        formatted_message = format_answer('start', message.from_user.first_name)
        await message.answer(formatted_message, reply_markup=get_only_answer_keyboard())
        
        await notify_admins_about_reg(user_id, bot)
    
        notification_states[user_id] = True
        delay_in_seconds = 86400
        reminder_message = str(answer('n2'))
        await send_reminder(bot, user_id, delay_in_seconds, reminder_message, 2)
    else:
        await message.answer("У вас нет доступа.")

@router.message(Command(commands='admin'))
async def process_admin_command(message: Message):
    tg_id = message.from_user.id

    if is_admin(tg_id):
        await message.answer("🎛️ Панель управления", reply_markup=get_admin_panel_keyboard())
    else:
        user_states[tg_id] = 'admin_password_wait'
        await message.answer("Введите пароль:")

@router.message(Command(commands='questions'))
async def process_question_command(message: Message):
    tg_id = message.from_user.id
    try:
        del user_states[tg_id]
    except:
        pass

    user_states[tg_id] = 'q1'
    await message.answer(answer('q1'))

@router.message()
async def process_user_message(message: Message, bot: Bot):
    tg_id = message.from_user.id
    if user_exists(str(tg_id)):
        pass
    else:
        await message.answer("У вас нет доступа.")
        return
    if tg_id in user_states:
        print(user_states[tg_id])
    if tg_id in user_states and user_states[tg_id] == 'search_user_input':
        search_query = message.text.lower()
        users_list = users()
        results = []
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[])

        # Флаг для отслеживания, нашли ли мы пользователя по ID
        user_found_by_id = False

        # Проходим по списку пользователей
        for user in users_list:
            # Проверяем, совпадает ли ID пользователя с введенным текстом
            if str(user['id']) == search_query:
                # Если нашли пользователя по ID, очищаем результаты и добавляем только его
                results = []
                inline_kb.inline_keyboard = []
                results.append(f"{user['id']}: {user['username']} (@{user['tg_username']}) [id: {user['id']}]")
                inline_kb.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=f"Ответы для {user['username']}",
                        callback_data=f"view_answers_{user['tg_id']}"
                    ),
                    InlineKeyboardButton(
                        text=f"Напоминание для {user['username']}",
                        callback_data=f"notify_user_{user['tg_id']}"
                    )
                ])
                inline_kb.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=f"Изменить {user['username']}",
                        callback_data=f"change_user_{user['tg_id']}"
                    )
                ])
                user_found_by_id = True
                break  # Прерываем цикл, так как нашли пользователя по ID
            elif not user_found_by_id:
                # Если пользователь не найден по ID, продолжаем поиск по другим параметрам
                if (user['username'] and search_query in user['username'].lower()) or \
                (user['tg_username'] and search_query in user['tg_username'].lower()):
                    results.append(f"{user['id']}: {user['username']} (@{user['tg_username']}) [id: {user['id']}]")
                    inline_kb.inline_keyboard.append([
                        InlineKeyboardButton(
                            text=f"📄 Ответы для {user['username']}",
                            callback_data=f"view_answers_{user['tg_id']}"
                        ),
                        InlineKeyboardButton(
                            text=f"🔔 Напоминание для {user['username']}",
                            callback_data=f"notify_user_{user['tg_id']}"
                        )
                    ])

        if results:
            inline_kb.inline_keyboard.append([
                InlineKeyboardButton(text="Назад", callback_data="admin_users"),
                InlineKeyboardButton(text="Рестарт", callback_data="back_to_menu")
            ])
            await message.answer("\n".join(results), reply_markup=inline_kb)
        else:
            await message.answer("🔴 Ничего не найдено.", reply_markup=get_back_keyboard())


        del user_states[tg_id]
    elif tg_id in user_states and user_states[tg_id].startswith("editing_"):
        field = user_states[tg_id].split("_")[1]
        new_text = message.text
        current_page = int(user_states[tg_id].split("_")[2])

        if new_text == "0":
            await message.answer(f"❌ Текст для ключа **{field}** не был изменен.", parse_mode="Markdown")
        else:
            write_answer(field, new_text)
            await message.answer(f"✅ Текст для ключа **{field}** был успешно обновлен.", parse_mode="Markdown")

        del user_states[tg_id]

        text_fields = ['start', 'q1', 'q2', 'q3', 'q4', 'q5', 'thx', 'n1', 'n2', 'n3', 'empty']
        texts_per_page = 3
        total_pages = (len(text_fields) + texts_per_page - 1) // texts_per_page
        start_idx = (current_page - 1) * texts_per_page
        end_idx = start_idx + texts_per_page
        formatted_texts = format_texts(text_fields[start_idx:end_idx])

        await message.answer(
            formatted_texts,
            reply_markup=get_text_navigation_keyboard(current_page, total_pages, text_fields),
            parse_mode="Markdown"
        )
    elif tg_id in user_states and user_states[tg_id] == 'admin_password_wait':
        password = message.text

        if add_admin_if_password_correct(tg_id, password):
            await message.answer("✅ Пароль верный.\n/admin откроет панель управления")
        else:
            await message.answer("🚫 Пароль неверный")

        del user_states[tg_id]
    
    elif tg_id in user_states and user_states[tg_id].startswith("wait_username_"):
        user_id = user_states[tg_id].split("_")[2]
        
        update_username(user_id, message.text)

        del user_states[tg_id]
        await message.answer("✅ Имя пользователя изменено", reply_markup=get_back_keyboard())
    elif tg_id in user_states and user_states[tg_id] == "delete_message":
        delete_message_by_id(message.text)
        del user_states[tg_id]
        await message.answer("✅ Сообщение удалено", reply_markup=get_back_keyboard())

    elif tg_id in user_states and user_states[tg_id] == 'q1':
        add_answer_to_user(tg_id, answer('q1'), message.text)
        user_states[tg_id] = 'q2'
        await message.answer(answer('q2'))

    elif tg_id in user_states and user_states[tg_id] == 'q2':
        add_answer_to_user(tg_id, answer('q2'), message.text)
        user_states[tg_id] = 'q3'
        await message.answer(answer('q3'))

    elif tg_id in user_states and user_states[tg_id] == 'q3':
        add_answer_to_user(tg_id, answer('q3'), message.text)
        user_states[tg_id] = 'thx'
        await message.answer(answer('q4'), reply_markup=all_good(tg_id))
    
    #elif tg_id in user_states and user_states[tg_id] == 'q4':
    #    add_answer_to_user(tg_id, answer('q4'), message.text)
    #    user_states[tg_id] = 'thx'
    #    await message.answer(answer('q5'))

    #elif tg_id in user_states and user_states[tg_id] == 'thx':
    #    add_answer_to_user(tg_id, answer('q4'), message.text)
    #    del user_states[tg_id]
    #    notification_states[tg_id] = False
    #    await message.answer(answer('thx'))
    #    await notify_admins_about_answers(tg_id, bot)
    
    # Если пользователь уже завершил все вопросы
    else:
        add_answer_to_user(tg_id, answer('empty'), message.text)
        await message.answer(answer('empty'))
        await notify_admins_about_answers(tg_id, bot)

@router.callback_query()
async def process_callback(callback: CallbackQuery, bot: Bot):
    tg_id = callback.from_user.id

    if callback.data == "answer":
        user_states[tg_id] = 'q1'
        notification_states[tg_id] = True
        await bot.send_message(tg_id, answer('q1'))
        await callback.answer()

    elif callback.data == "disable_notifications":
        notification_states[tg_id] = False
        await bot.send_message(tg_id, str(answer('n3')))
        await callback.answer()


    if callback.data == "download_zip":
        zip_buffer = create_zip_for_users()
        zip_buffer.seek(0)

        if zip_buffer.getbuffer().nbytes == 0:
            await bot.edit_message_text("Архив пуст.", chat_id=tg_id, message_id=callback.message.message_id)
            await callback.answer()
            return

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(zip_buffer.read())  # Записываем буфер в файл
            temp_file_path = temp_file.name

        if os.stat(temp_file_path).st_size == 0:
            await bot.edit_message_text("Файл пуст.", chat_id=tg_id, message_id=callback.message.message_id)
            await callback.answer()
            return

        # Редактируем сообщение, добавляя текст, что архив готов
        await bot.edit_message_text(
            chat_id=tg_id,
            message_id=callback.message.message_id,
            text="✅ Архив с ответами пользователей готов. Вы можете скачать его ниже.",
            reply_markup=get_back_keyboard()
        )

        # Отправляем сам архив как отдельное сообщение
        document = FSInputFile(temp_file_path)
        await bot.send_document(
            chat_id=tg_id,
            document=document,
            caption="💾 Архив с ответами пользователей"
        )

        # Удаляем временный файл
        os.remove(temp_file_path)
        await callback.answer()

    text_fields = ['start', 'q1', 'q2', 'q3', 'q4', 'q5', 'thx', 'n1', 'n2', 'n3', 'empty']
    texts_per_page = 3
    total_pages = (len(text_fields) + texts_per_page - 1) // texts_per_page
    
    if callback.data == "admin_texts":
        page = 1
        start_idx = (page - 1) * texts_per_page
        end_idx = start_idx + texts_per_page
        formatted_texts = format_texts(text_fields[start_idx:end_idx])

        await bot.edit_message_text(
            formatted_texts,
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=get_text_navigation_keyboard(page, total_pages, text_fields),
            parse_mode="Markdown"
        )
        await callback.answer()

    # В функции обработки callback'а при выводе списка пользователей
    elif callback.data == "admin_users":
        users_list = users()
        total_users = len(users_list)
        formatted_users = "\n".join([
            f"{user['id']}: {user['username']} (@{user['tg_username']})\n--------"
            for user in users_list[:3000]
        ])
        formatted_users += f"\n🟢 количество пользователей: {total_users}"

        await bot.edit_message_text(
            f"📗 Пользователи:\n{formatted_users}\nНажмите 🔎 поиск, чтобы выбрать пользователя",
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=get_user_navigation_keyboard(1, total_users // 3000 + 1)
        )
        await callback.answer()


    elif callback.data == "admin_notifications":
        notification_status = 'Включены 🟩' if get_admin_notification_status(tg_id) == 1 else  'Выключены 🟥'
        await bot.edit_message_text(
            f"Уведомления: {notification_status}\n\n*это изменение касается только вас, другие администраторы продолжат получать уведомления",
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=get_admin_notification_keyboard()
        )
        await callback.answer()

    elif callback.data == "disable_admin_notification":
        disable_admin_notifications(tg_id)
        notification_status = 'Включены 🟩' if get_admin_notification_status(tg_id) == 1 else  'Выключены 🟥'
        await bot.edit_message_text(
            f"Уведомления: {notification_status}\n\n*это изменение касается только вас, другие администраторы продолжат получать уведомления",
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=get_admin_notification_keyboard()
        )
        await callback.answer()

    elif callback.data == "enable_admin_notification":
        enable_admin_notifications(tg_id)
        notification_status = 'Включены 🟩' if get_admin_notification_status(tg_id) == 1 else  'Выключены 🟥'
        await bot.edit_message_text(
            f"Уведомления: {notification_status}\n\n*это изменение касается только вас, другие администраторы продолжат получать уведомления",
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=get_admin_notification_keyboard()
        )
        await callback.answer()

    elif callback.data.startswith("prev_page_"):
        page = int(callback.data.split("_")[-1]) - 1
        start_idx = (page - 1) * texts_per_page
        end_idx = start_idx + texts_per_page
        formatted_texts = format_texts(text_fields[start_idx:end_idx])

        await bot.edit_message_text(
            formatted_texts,
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=get_text_navigation_keyboard(page, total_pages, text_fields),
            parse_mode="Markdown"
        )
        await callback.answer()

    elif callback.data.startswith("next_page_"):
        page = int(callback.data.split("_")[-1]) + 1
        start_idx = (page - 1) * texts_per_page
        end_idx = start_idx + texts_per_page
        formatted_texts = format_texts(text_fields[start_idx:end_idx])

        await bot.edit_message_text(
            formatted_texts,
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=get_text_navigation_keyboard(page, total_pages, text_fields),
            parse_mode="Markdown"
        )
        await callback.answer()

    elif callback.data.startswith("text_"):
        field, page = callback.data.split("_")[1], int(callback.data.split("_")[-1])
        current_text = answer(field)
        user_states[tg_id] = f"editing_{field}_{page}"
        await bot.send_message(
            tg_id, 
            f"Вы выбрали текст: **{field}**\n{current_text}\n\nВведите текст, который заменит этот. Если не хотите ничего менять, введите 0.",
            parse_mode="Markdown"
        )
        await callback.answer()

    elif callback.data == "back_to_menu":
        await bot.edit_message_text(
            "🎛️ Панель управления",
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=get_admin_panel_keyboard()
        )
        await callback.answer()

    elif callback.data == "ignore":
        await callback.answer()

    elif callback.data == "search_user":
        user_states[tg_id] = 'search_user_input'
        await bot.send_message(tg_id, f"🔎 Введите id или username или имя или фамилию для поиска.\n\nПояснение:\nid: имя фамилия (@username)\n\n*username без собачки\n*для поиска необязательно писать запрос полностью\n(если написать 'Al' будут выведенны все, чьё имя/фамилия/username начинаются с этих букв) ")
        await callback.answer()

    elif callback.data.startswith("view_answers_"):
        user_id = int(callback.data.split("_")[2])
        user_data = get_user_data(user_id)
        user_answers = get_user_answers(user_id)

        if not user_answers:
            user_answers = "Ответов пользователя не найдено."
        else:
            # Формируем строку с ответами пользователя
            answers_text = ""
            for user_answer in user_answers:
                answers_text += (
                    f"{user_answer['id']}|📅 {user_answer['data']}\n"
                    f"{user_answer['question']}\n"
                    f"{user_answer['text']}\n"
                    
                )

        # Формируем сообщение с ответами пользователя
        message_text = (
            f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\n"
            f"tg_id: {user_data['tg_id']}\n\n"
            f"📄 Ответы:\n{answers_text}"
        )

        # Разбиваем сообщение на части, если оно слишком длинное
        parts = split_message(message_text)

        # Если сообщение состоит из нескольких частей, отправляем их по очереди
        for part in parts:
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=part,
                reply_markup=edit_messages_kb(user_data['tg_id'])
            )

        # Отправляем ответ на callback, чтобы убрать индикатор ожидания
        await callback.answer()
    elif callback.data.startswith("all_good_"):
        user_id = int(callback.data.split("_")[2])
        add_answer_to_user(user_id, answer('q4'), 'Всё хорошо')
        notification_states[user_id] = False
        del user_states[user_id]
        await bot.edit_message_text(
            f"Всё хорошо",
            chat_id=tg_id,
            message_id=callback.message.message_id
        )
        await bot.send_message(user_id, text = answer('thx'))
        await notify_admins_about_answers(user_id, bot)
    elif callback.data.startswith("delete_all_messages_"):
        user_id = int(callback.data.split("_")[3])
        user_data = get_user_data(user_id)
        delete_messages_by_tg_id(user_id)
        await bot.edit_message_text(
            f"Все сообщения пользователя {user_data['username']} удалены",
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=get_back_keyboard()
        )
    elif callback.data == "delete_message":
        user_states[tg_id] = 'delete_message'
        await bot.send_message(tg_id, f"🔎 Введите номер сообщения , которое хотите удалить:")
        await callback.answer()
    elif callback.data.startswith("change_user_"):
        user_id = int(callback.data.split("_")[2])
        user_data = get_user_data(user_id)
        print(user_id)

        message_text = (
            f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\n"
        )

        await callback.answer()
        await bot.edit_message_text(
            message_text,
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=user_change_kb(user_id)
        )

    elif callback.data.startswith("delete_user_"):
        user_id = int(callback.data.split("_")[2])
        user_data = get_user_data(user_id)
        print(user_id)

        message_text = (
            f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\nУдален"
        )

        delete_user(user_id)

        await callback.answer()
        await bot.edit_message_text(
            message_text,
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=get_back_keyboard()
        )

    elif callback.data.startswith("change_username_"):
        user_id = int(callback.data.split("_")[2])
        user_data = get_user_data(user_id)
        print(tg_id)
        print(user_id)

        user_states[tg_id] = f'wait_username_{user_id}'
        
        message_text = (
            f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\nВведите новое имя пользователя:"
        )

        await callback.answer()
        await bot.edit_message_text(
            message_text,
            chat_id=tg_id,
            message_id=callback.message.message_id
        )
          
    elif callback.data.startswith("notify_user_"):
        user_id = int(callback.data.split("_")[2])
        user_data = get_user_data(user_id)
        message_text = (
            f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\n"
            f"-------\n\n"
            f"🕓 Выберите время для отправки напоминания"
        )

        def get_admin_notify_keyboard():
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="Сейчас", callback_data=f"notify_choose_24_{user_id}"),
                    InlineKeyboardButton(text="Завтра", callback_data=f"notify_choose_tomorrow_{user_id}"),
                    InlineKeyboardButton(text="Дата", callback_data=f"notify_choose_data_{user_id}")
                ],
                [
                    InlineKeyboardButton(text="Назад", callback_data="admin_users"),
                    InlineKeyboardButton(text="Рестарт", callback_data="back_to_menu")
                ]
            ])
            return keyboard
        
        await bot.edit_message_text(
            message_text,
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=get_admin_notify_keyboard()
        )

    elif callback.data.startswith("notify_choose"):
        user_id = int(callback.data.split("_")[3])
        notify_type = str(callback.data.split("_")[2])
        user_data = get_user_data(user_id)
        print(answer('n2'))
        reminder_message = str(answer('n2'))
        template_message_text = (
            f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\n"
            f"-------\n\n"
        )
        
        if notify_type == "24":
            delay_in_sec = 1
            message_text = template_message_text + "🔔 Уведомление доставлено"
            add_answer_to_user(user_id, 24, 0)
            await bot.edit_message_text(
                message_text,
                chat_id=tg_id,
                message_id=callback.message.message_id,
                reply_markup=get_back_keyboard()
            )
            await send_reminder(bot, user_id, delay_in_sec, reminder_message, retries_left=3)

        elif notify_type == "tomorrow":
            message_text = template_message_text + "🕓 Выберите время для отправки уведомления:"

            def hour_kb():
                buttons = [
                    [
                        InlineKeyboardButton(
                            text=f"{hour:02d}:00",
                            callback_data=f"calendar_hour_{user_id}_{hour}"
                        ) for hour in range(i, min(i + 4, 24))  # Убедимся, что не превышаем 24
                    ]
                    for i in range(0, 24, 4)
                ] + [
                    [
                        InlineKeyboardButton(
                            text="Назад",
                            callback_data="admin_users"
                        ),
                        InlineKeyboardButton(text="Рестарт", callback_data="back_to_menu")
                    ]
                ]
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                return keyboard

            await bot.edit_message_text(
                message_text,
                chat_id=tg_id,
                message_id=callback.message.message_id,
                reply_markup=hour_kb()
            )
        elif notify_type == "data":
            today = datetime.today()
            message_text = template_message_text + "📆 Выберите дату для отправки уведомления:"
            await bot.edit_message_text(
                message_text,
                chat_id=tg_id,
                message_id=callback.message.message_id,
                reply_markup=create_calendar(today.year, today.month, user_id)
            )
        else:
            pass

    elif callback.data.startswith('day_'):
        year = int(callback.data.split("_")[1])
        month = int(callback.data.split("_")[2])
        day = int(callback.data.split("_")[3])
        user_id = int(callback.data.split("_")[4])
        user_data = get_user_data(user_id)
        template_message_text = (
            f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\n"
            f"-------\n\n"
        )
        message_text = template_message_text + f"📆 Выбанная дата: {day}.{month}.{year}\n🕓 Выберите время для отправки уведомления:"
        def calendar_hour_kb():
            buttons = [
                [InlineKeyboardButton(text=f"{hour:02d}:00", callback_data=f"calendar_hour_{user_id}_{hour}_{year}_{month}_{day}") for hour in range(i, i + 4)]
                for i in range(0, 24, 4) 
            ] + [
                [
                    InlineKeyboardButton(
                        text="Назад",
                        callback_data="admin_users"
                    ),
                    InlineKeyboardButton(text="Рестарт", callback_data="back_to_menu")
                ]
            ]

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            return keyboard

        await bot.edit_message_text(
            message_text,
            chat_id=tg_id,
            message_id=callback.message.message_id,
            reply_markup=calendar_hour_kb()
        )

    elif callback.data.startswith('prev_'):
        # Обработка кнопки предыдущего месяца
        year = int(callback.data.split("_")[1])
        month = int(callback.data.split("_")[2])
        user_id = int(callback.data.split("_")[3])
        user_data = get_user_data(user_id)
        prev_month = month - 1 if month > 1 else 12
        prev_year = year - 1 if month == 1 else year
        template_message_text = (
            f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\n"
            f"-------\n\n"
        )
        message_text = template_message_text + "📆 Выберите дату для отправки уведомления:"
        await bot.edit_message_text(
            message_text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=create_calendar(prev_year, prev_month, user_id)
        )
        await callback.answer()

    elif callback.data.startswith('next_'):
        # Обработка кнопки следующего месяца
        year = int(callback.data.split("_")[1])
        month = int(callback.data.split("_")[2])
        user_id = int(callback.data.split("_")[3])
        user_data = get_user_data(user_id)
        next_month = month + 1 if month < 12 else 1
        next_year = year + 1 if month == 12 else year
        template_message_text = (
            f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\n"
            f"-------\n\n"
        )
        message_text = template_message_text + "📆 Выберите дату для отправки уведомления:"

        await bot.edit_message_text(
            message_text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=create_calendar(next_year, next_month,  user_id)
        )
        await callback.answer()

    elif callback.data.startswith('calendar_hour_'):
        user_id = int(callback.data.split("_")[2])
        user_data = get_user_data(user_id)
        hour =  int(callback.data.split("_")[3])
        moscow_tz = pytz.timezone("Europe/Moscow")
        now = datetime.now(moscow_tz)
        try:
            year = int(callback.data.split("_")[4])
            month = int(callback.data.split("_")[5])
            day = int(callback.data.split("_")[6])
        except:
            year, month, day = 0, 0, 0
        
        if  year == 0:
            message_text = (
                f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\n"
                f"-------\n\n"
                f"🔔 Уведомление будет доставленно завтра в {hour}:00"
            )
            send_time = now + timedelta(days=1)
            send_time = send_time.replace(hour=hour, minute=0, second=0, microsecond=0)
            add_answer_to_user(user_id, str(send_time), 0)
        else:
            message_text = (
                f"🟢 Пользователь: {user_data['username']} (@{user_data['tg_username']})\n"
                f"-------\n\n"
                f"🔔 Уведомление будет доставленно {day}.{month}.{year} в {hour}:00"
            )
            send_time = moscow_tz.localize(datetime(year, month, day, hour, 0, 0))
            add_answer_to_user(user_id, str(send_time), 0)
            
        if send_time < now:
            send_time += timedelta(days=1)

        delay_in_sec = (send_time - now).total_seconds()

        if delay_in_sec < 0:
            await bot.edit_message_text(
                "🔔 Уведомление не будет отправленно\n\n⚠ Ошибка: выбрано время в прошлом",
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=get_back_keyboard()
            )
        else:
            await bot.edit_message_text(
                message_text,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=get_back_keyboard()
            )
            await send_reminder(bot, user_id, delay_in_sec, str(answer('n2')), retries_left=3)
