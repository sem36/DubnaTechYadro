import logging
import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Путь к базе данных
DB_PATH = r'E:\Projects\DubnaTechYadro-Dima-A\animals_ads.db'

def init_db():
    """Инициализация базы данных."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo BLOB,
            description TEXT,
            location TEXT,
            breed TEXT,
            user_telegram_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_ad_to_db(description, photo_path, location, breed, user_telegram_id):
    """Сохранение объявления в базу данных."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    with open(photo_path, 'rb') as file:
        photo_data = file.read()
    cursor.execute('INSERT INTO ads (description, photo, location, breed, user_telegram_id) VALUES (?, ?, ?, ?, ?)', 
                   (description, photo_data, location, breed, user_telegram_id))
    conn.commit()
    conn.close()

def get_all_ads(breed=None):
    """Получение всех объявлений из базы данных, с фильтром по породе."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if breed:
        cursor.execute('SELECT id, description, photo, location, breed, user_telegram_id FROM ads WHERE breed = ?', (breed,))
    else:
        cursor.execute('SELECT id, description, photo, location, breed, user_telegram_id FROM ads')
    ads = cursor.fetchall()
    conn.close()
    return ads

def get_breeds():
    """Получение всех уникальных пород из базы данных."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT breed FROM ads')
    breeds = [row[0] for row in cursor.fetchall() if row[0]]  # Исключаем None и пустые строки
    conn.close()
    return breeds


# Главное меню
def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("➕ Добавить объявление")],
        [KeyboardButton("👀 Посмотреть объявления")],
        [KeyboardButton("🫶 Благотворительность")],
        [KeyboardButton("ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Привет! Выберите действие из меню ниже:',
        reply_markup=main_menu_keyboard()
    )

# Добавление объявления
async def handle_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления объявления."""
    context.user_data['current_announcement'] = {'description': None, 'photo': None, 'location': None, 'breed': None}
    await update.message.reply_text("Вы выбрали: Добавить объявление.\nПожалуйста, отправьте текстовое описание животного.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстового описания для объявления."""
    current_announcement = context.user_data.get('current_announcement')
    if current_announcement and current_announcement['description'] is None:
        current_announcement['description'] = update.message.text
        await update.message.reply_text("Описание сохранено. Теперь отправьте фото животного.")
    else:
        await update.message.reply_text("Сначала выберите 'Добавить объявление'.", reply_markup=main_menu_keyboard())

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение фото и завершение объявления."""
    current_announcement = context.user_data.get('current_announcement')
    if current_announcement and current_announcement['description'] is not None:
        photo_file = await update.message.photo[-1].get_file()
        photo_path = f'photos/{photo_file.file_id}.jpg'
        os.makedirs('photos', exist_ok=True)
        await photo_file.download_to_drive(photo_path)
        current_announcement['photo'] = photo_path

        # Сохранение данных в базу
        user_telegram_id = update.message.from_user.id
        save_ad_to_db(
            current_announcement['description'],
            photo_path,
            current_announcement.get('location'),
            current_announcement.get('breed'),
            user_telegram_id
        )
        del context.user_data['current_announcement']
        await update.message.reply_text("Объявление успешно сохранено!", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("Сначала отправьте описание животного.", reply_markup=main_menu_keyboard())

async def handle_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    breeds = get_breeds()
    if not breeds:
        await update.message.reply_text("Нет доступных пород для фильтрации.", reply_markup=main_menu_keyboard())
        return

    print(f"Список пород: {breeds}")  # Отладочный вывод

    keyboard = [
        [
            InlineKeyboardButton(text=breeds[i], callback_data=f"view_{breeds[i]}"),
            InlineKeyboardButton(text=breeds[i+1], callback_data=f"view_{breeds[i+1]}")
        ]
        for i in range(0, len(breeds) - 1, 2)
    ]

    if len(breeds) % 2 != 0:
        keyboard.append([InlineKeyboardButton(text=breeds[-1], callback_data=f"view_{breeds[-1]}")])
    
    keyboard.append([InlineKeyboardButton(text="Все породы", callback_data="view_all")])

    print(f"Клавиатура: {keyboard}")  # Отладочный вывод

    await update.message.reply_text(
        "Выберите породу для фильтрации или просмотрите все объявления:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_breed_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Фильтрует объявления по выбранной породе или показывает все."""
    query = update.callback_query
    breed = query.data.split('_')[1] if query.data != "view_all" else None
    
    # Получаем объявления из базы данных
    ads = get_all_ads(breed)
    
    if not ads:
        await query.message.reply_text("Нет объявлений для отображения по выбранной породе.", reply_markup=main_menu_keyboard())
        await query.answer()
        return
    
    # Сохраняем объявления и текущий индекс в контексте
    context.user_data['ads'] = ads
    context.user_data['current_index'] = 0
    
    # Отображаем первое объявление
    await show_ad(update, context)
    await query.answer()


async def show_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущее объявление с кнопками навигации."""
    current_index = context.user_data.get('current_index', 0)
    ads = context.user_data.get('ads', [])

    if not ads:
        await update.message.reply_text("Нет доступных объявлений.", reply_markup=main_menu_keyboard())
        return

    # Получаем данные текущего объявления
    ad_id, description, photo_data, location, breed, user_telegram_id = ads[current_index]
    breed_text = f"Порода: {breed}" if breed else "Порода: не указана"
    location_text = f"Местоположение: {location}" if location else "Местоположение: не указано"
    
    # Временный файл для фото
    temp_photo_path = f'temp_photos/ad_{current_index}.jpg'
    os.makedirs('temp_photos', exist_ok=True)
    with open(temp_photo_path, 'wb') as temp_file:
        temp_file.write(photo_data)
    
    navigation_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data='prev_ad'), InlineKeyboardButton("Вперед ➡️", callback_data='next_ad')],
        [InlineKeyboardButton("Забрать животное", callback_data=f'take_{user_telegram_id}')]
    ])
    
    query = update.callback_query
    if query:
        await query.message.delete()
        await query.message.reply_photo(
            photo=open(temp_photo_path, 'rb'),
            caption=f"{breed_text}\nОписание: {description}\n{location_text}",
            reply_markup=navigation_keyboard
        )
    else:
        await update.message.reply_photo(
            photo=open(temp_photo_path, 'rb'),
            caption=f"{breed_text}\nОписание: {description}\n{location_text}",
            reply_markup=navigation_keyboard
        )

async def navigate_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок навигации."""
    query = update.callback_query
    await query.answer()
    ads = context.user_data['ads']
    current_index = context.user_data['current_index']
    if query.data == 'next_ad':
        current_index = (current_index + 1) % len(ads)
    elif query.data == 'prev_ad':
        current_index = (current_index - 1) % len(ads)
    context.user_data['current_index'] = current_index
    await show_ad(update, context)

async def handle_take_animal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Забрать животное'."""
    query = update.callback_query
    user_telegram_id = query.data.split('_')[1]
    
    try:
        user = await context.bot.get_chat(user_telegram_id)
        username = user.username
        
        if username:
            user_contact = f"@{username}"
        else:
            user_contact = "Владелец не указал username."
        
        await query.message.reply_text(f"Свяжитесь с владельцем объявления: {user_contact}", reply_markup=main_menu_keyboard())
    except Exception as e:
        logger.error(f"Ошибка получения данных пользователя: {e}")
        await query.message.reply_text("Не удалось получить контакт владельца.", reply_markup=main_menu_keyboard())
    
    await query.answer()

# Благотворительность
async def donations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🙏 **Поддержите нашу миссию по поиску животных!**\n\n"
        "Для перевода используйте следующие реквизиты:\n\n"
        "`0000 0000 0000 0000`\n\n"
        "Просто нажмите на номер карты, чтобы скопировать!"
    )
    
    await update.message.reply_text(
        help_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='Markdown'
    )

# Помощь
async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🔍 **Ответы на часто задаваемые вопросы**\n\n"
        "1. **Каким должно быть фото?**\n"
        "- Фото животного должно быть четким и хорошо освещенным.\n\n"
        "2. **Что нужно указать в описании?**\n"
        "- Укажите **тип** животного (кошка, собака и т.д.).\n"
        "- Укажите **породу** (если известна).\n"
        "- Опишите **цвет** и **особые приметы** (пятна, шрамы и т.д.).\n"
        "- Укажите **возраст** и **пол** животного.\n\n"
        "Эти данные помогут быстрее найти или вернуть животное!"
    )
    await update.message.reply_text(help_text, reply_markup=main_menu_keyboard(), parse_mode='Markdown')

def main():
    init_db()
    token = "7764937203:AAH9kBEQTlWg6QWXp4NkyaUMtk29tD0QTdY"  # Вставьте ваш токен
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("➕ Добавить объявление"), handle_add))
    application.add_handler(MessageHandler(filters.Regex("👀 Посмотреть объявления"), handle_view))
    application.add_handler(MessageHandler(filters.Regex("🫶 Благотворительность"), donations))
    application.add_handler(MessageHandler(filters.Regex("ℹ️ Помощь"), handle_help))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(handle_breed_selection, pattern="^view_"))
    application.add_handler(CallbackQueryHandler(navigate_ads, pattern='^(prev_ad|next_ad)$'))
    application.add_handler(CallbackQueryHandler(handle_take_animal, pattern='^take_'))

    application.run_polling()

if __name__ == '__main__':
    main()
