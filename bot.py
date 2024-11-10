from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from fastapi_integration import get_breed_from_image
from db import save_ad_to_db, get_all_ads, get_breeds, init_db,update_ad_with_telegram
import os

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

async def handle_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['current_announcement'] = {'description': None, 'photo': None, 'location': None}
    await update.message.reply_text("Вы выбрали: Добавить объявление.\nПожалуйста, отправьте текстовое описание.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_announcement = context.user_data.get('current_announcement')
    if current_announcement and current_announcement['description'] is None:
        current_announcement['description'] = update.message.text
        await update.message.reply_text("Описание сохранено. Теперь отправьте фото животного.")
    else:
        await update.message.reply_text("Выберите 'Добавить объявление' перед отправкой данных.", reply_markup=main_menu_keyboard())

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_announcement = context.user_data.get('current_announcement')
    if current_announcement and current_announcement['description'] is not None:
        photo_file = await update.message.photo[-1].get_file()
        photo_path = f'photos/{photo_file.file_id}.jpg'
        os.makedirs('photos', exist_ok=True)
        await photo_file.download_to_drive(photo_path)
        current_announcement['photo'] = photo_path
        
        breed = get_breed_from_image(photo_path)
        if breed:
            user_telegram_id = update.message.from_user.id
            save_ad_to_db(current_announcement['description'], photo_path, current_announcement.get('location'), breed, user_telegram_id)
            del context.user_data['current_announcement']
            await update.message.reply_text(f"Объявление успешно сохранено! Порода: {breed}", reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text("Произошла ошибка при обработке изображения.", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("Сначала отправьте описание животного.", reply_markup=main_menu_keyboard())








async def handle_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    breeds = get_breeds()
<<<<<<< HEAD
    
    filtered_breeds = [breed for breed in breeds if breed.isalpha() and breed.isascii()]
    if not filtered_breeds:
        filtered_breeds = breeds
    breeds = filtered_breeds
    
=======
>>>>>>> main
    keyboard = [[InlineKeyboardButton(breeds[i], callback_data=f"view_{breeds[i]}"),
                 InlineKeyboardButton(breeds[i+1], callback_data=f"view_{breeds[i+1]}")]
                for i in range(0, len(breeds) - 1, 2)]

    if len(breeds) % 2 != 0:
        keyboard.append([InlineKeyboardButton(breeds[-1], callback_data=f"view_{breeds[-1]}")])
    keyboard.append([InlineKeyboardButton("Все породы", callback_data="view_all")])
    
    await update.message.reply_text(
        "Выберите породу для фильтрации:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


<<<<<<< HEAD
=======

>>>>>>> main
async def handle_breed_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    breed = query.data.split('_')[1] if query.data != "view_all" else None
    ads = get_all_ads()
    
    if breed:
<<<<<<< HEAD
        ads = [ad for ad in ads if ad[4].lower() == breed.lower() or breed.lower() in ad[4].lower()]
=======
        ads = [ad for ad in ads if ad[4] == breed]
>>>>>>> main
    
    if not ads:
        await query.message.reply_text("Нет объявлений для отображения по выбранной породе.", reply_markup=main_menu_keyboard())
        return

    context.user_data['ads'] = ads
    context.user_data['current_index'] = 0

    await show_ad(update, context)



<<<<<<< HEAD









=======
>>>>>>> main
async def show_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_index = context.user_data['current_index']
    ads = context.user_data['ads']
    
    ad_id, description, photo_data, location, breed, user_telegram_id = ads[current_index]
    
    breed_text = f"Порода: {breed}" if breed else "Порода: не указана"
    location_text = f"Местоположение: {location}" if location else "Местоположение: не указано"

    temp_photo_path = f'temp_photos/ad_{ad_id}.jpg'
    os.makedirs('temp_photos', exist_ok=True)
    with open(temp_photo_path, 'wb') as temp_file:
        temp_file.write(photo_data)

    navigation_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️ Назад", callback_data='prev_ad'),
            InlineKeyboardButton("Вперед ➡️", callback_data='next_ad')
        ],
        [
            InlineKeyboardButton("Забрать питомца", callback_data='adopt_pet')
        ]
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


async def handle_adopt_pet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    current_index = context.user_data.get('current_index', None)

    if current_index is None:
        await query.message.reply_text("Не удалось получить данные об объявлении. Попробуйте снова.", reply_markup=main_menu_keyboard())
        return

    ads = context.user_data['ads']
    ad = ads[current_index]
    owner_telegram_id = ad[5]

    try:
        owner_user = await context.bot.get_chat(owner_telegram_id)
        username = f"@{owner_user.username}" if owner_user.username else "Пользователь не имеет username"
    except telegram.error.BadRequest:
        username = "Пользователь не начал чат с ботом или недоступен"

    await query.answer()
    await query.message.reply_text(
<<<<<<< HEAD
        f"Чтобы забрать питомца, напишите владельцу: {username}",
=======
        f"Чтобы забрать питомца, напишите: {username}",
>>>>>>> main
        reply_markup=main_menu_keyboard()
    )

async def donations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🙏 **Поддержите нашу миссию по поиску животных!**\n\n"
        "Реквизиты питомника:\n\n"
        "`0000 0000 0000 0000`\n\n"
        "Просто нажмите на номер карты, чтобы скопировать!"
    )
    
    await update.message.reply_text(
        help_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='Markdown'
    )


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

async def navigate_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    ads = context.user_data.get('ads', [])
    current_index = context.user_data.get('current_index', 0)
    
    if query.data == 'next_ad':
        current_index = (current_index + 1) % len(ads)
    elif query.data == 'prev_ad':
        current_index = (current_index - 1) % len(ads)
    
    context.user_data['current_index'] = current_index
    await show_ad(update, context)


def main():
    from telegram.ext import Application
    init_db()
    token = "7951976644:AAHhdZsL1sCoSQtOgvm1W5nKJJOCuFvRGsw"
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
    application.add_handler(CallbackQueryHandler(handle_adopt_pet, pattern='^adopt_pet$'))
    

    application.run_polling()

if __name__ == '__main__':
    main()
