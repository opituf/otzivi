from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import init_db, add_review, get_all_reviews, format_review
from config import BOT_TOKEN, ADMIN_PANEL_PASSWORD


init_db()


# Состояния для опроса
FOOD, STAFF, INTERIOR, COMMENT, FINISH = range(5)

# Главное меню
main_menu = InlineKeyboardMarkup([
    [InlineKeyboardButton("Посмотреть отзывы", callback_data="login")],
    [InlineKeyboardButton("Написать отзыв", callback_data="write_review")]
])


# Клавиатура для оценок
def rating_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(str(i), callback_data=f"rate_{i}") for i in range(1, 6)]
    ])


# Финальное меню
def finish_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Отправить отзыв", callback_data="submit_review")],
        [InlineKeyboardButton("✏️ Изменить оценки", callback_data="change_ratings")],
        [InlineKeyboardButton("📝 Добавить комментарий", callback_data="add_comment")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_review")]
    ])


async def start(update, context):
    await update.message.reply_text(
        "Я бот для написания отзывов, чем могу помочь?",
        reply_markup=main_menu
    )


async def help(update, context):
    await update.message.reply_text("Я бот книга для отзывов.")


async def login(update, context):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Введите пароль от панели администратора")
    return 1


async def check_password(update, context):
    password = update.message.text
    if password == ADMIN_PANEL_PASSWORD:
        await update.message.reply_text("Вы успешно вошли в панель администратора!")
        return await see_reviews(update, context)
    else:
        await update.message.reply_text("❌ Неверный пароль. Попробуйте ещё раз.")
        return 1


async def see_reviews(update, context):
    reviews = get_all_reviews()
    if not reviews:
        await update.message.reply_text("Пока нет отзывов.")
    else:
        for review in reviews:
            await update.message.reply_text(format_review(review))
    await update.message.reply_text("Что вы хотите сделать дальше?", reply_markup=main_menu)
    return ConversationHandler.END


async def write_review(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data['review'] = {}
    await query.edit_message_text(
        "Пожалуйста, оцените качество еды:",
        reply_markup=rating_keyboard()
    )
    return FOOD


async def rate_food(update, context):
    query = update.callback_query
    await query.answer()
    rating = int(query.data.split('_')[1])
    context.user_data['review']['food'] = rating
    await query.edit_message_text(
        "Теперь оцените персонал:",
        reply_markup=rating_keyboard()
    )
    return STAFF


async def rate_staff(update, context):
    query = update.callback_query
    await query.answer()
    rating = int(query.data.split('_')[1])
    context.user_data['review']['staff'] = rating
    await query.edit_message_text(
        "Теперь оцените интерьер:",
        reply_markup=rating_keyboard()
    )
    return INTERIOR


async def rate_interior(update, context):
    query = update.callback_query
    await query.answer()
    rating = int(query.data.split('_')[1])
    context.user_data['review']['interior'] = rating

    review = context.user_data['review']
    text = (
        "Ваши текущие оценки:\n"
        f"🍽 Еда: {review.get('food', 'не оценено')}/5\n"
        f"👨‍🍳 Персонал: {review.get('staff', 'не оценено')}/5\n"
        f"🏠 Интерьер: {rating}/5\n\n"
        "Что вы хотите сделать дальше?"
    )

    await query.edit_message_text(
        text,
        reply_markup=finish_keyboard()
    )
    return FINISH


async def add_comment(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Пожалуйста, напишите ваш комментарий:")
    return COMMENT


async def handle_comment(update, context):
    comment = update.message.text
    context.user_data['review']['comment'] = comment

    review = context.user_data['review']
    text = (
        "Ваш отзыв:\n"
        f"🍽 Еда: {review.get('food', 'не оценено')}/5\n"
        f"👨‍🍳 Персонал: {review.get('staff', 'не оценено')}/5\n"
        f"🏠 Интерьер: {review.get('interior', 'не оценено')}/5\n"
        f"📝 Комментарий: {comment}\n\n"
        "Подтвердите отправку:"
    )

    await update.message.reply_text(
        text,
        reply_markup=finish_keyboard()
    )
    return FINISH


async def submit_review(update, context):
    query = update.callback_query
    await query.answer()

    review = context.user_data['review']
    add_review(
        food=review.get('food', 0),
        staff=review.get('staff', 0),
        interior=review.get('interior', 0),
        comment=review.get('comment')
    )

    await query.edit_message_text(
        "Спасибо за ваш отзыв! Он был успешно отправлен.",
        reply_markup=main_menu
    )
    context.user_data.clear()
    return ConversationHandler.END


async def change_ratings(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Пожалуйста, оцените качество еды:",
        reply_markup=rating_keyboard()
    )
    return FOOD


async def cancel_review(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Написание отзыва отменено.",
        reply_markup=main_menu
    )
    context.user_data.clear()
    return ConversationHandler.END


async def stop(update, context):
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


def main():
    # Обработчик для админской панели
    admin_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(login, pattern="^login$")
        ],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)],
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    # Обработчик для написания отзыва
    review_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(write_review, pattern="^write_review$")],
        states={
            FOOD: [CallbackQueryHandler(rate_food, pattern="^rate_[1-5]$")],
            STAFF: [CallbackQueryHandler(rate_staff, pattern="^rate_[1-5]$")],
            INTERIOR: [CallbackQueryHandler(rate_interior, pattern="^rate_[1-5]$")],
            FINISH: [
                CallbackQueryHandler(submit_review, pattern="^submit_review$"),
                CallbackQueryHandler(change_ratings, pattern="^change_ratings$"),
                CallbackQueryHandler(add_comment, pattern="^add_comment$"),
                CallbackQueryHandler(cancel_review, pattern="^cancel_review$")
            ],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_comment)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(admin_conv_handler)
    application.add_handler(review_conv_handler)
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("stop", stop))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()