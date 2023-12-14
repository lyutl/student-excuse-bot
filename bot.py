import json

from config import TOKEN
from collections import defaultdict
from dateutil.parser import parse
from telegram import (Update,
                      InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup)
from telegram.ext import (ApplicationBuilder,
                          CallbackQueryHandler,
                          CommandHandler,
                          ContextTypes,
                          ConversationHandler,
                          MessageHandler,
                          filters)
from template import (change_placeholder,
                      COLUMN_DICT,
                      END,
                      Option,
                      START,
                      Template)

# open json file
f = open('letter_parameters.json', encoding='utf-8')

data = json.load(f)
params = data['parameters'][0]

option = Option()
template = Template()


class Bot:
    """A class for the student excuse bot."""

    id2users = defaultdict(dict)
    choices = {}
    multiple_buttons = []

    def __init__(self, token):
        self.app = ApplicationBuilder().token(TOKEN).build()
        start_handler = CommandHandler('start', self.start)
        self.app.add_handler(start_handler)
        main_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.ALL, self.handle_message)],

            states={
                'receiver': [MessageHandler(filters.TEXT & (~filters.COMMAND), self.receiver)],
                'date': [MessageHandler(filters.TEXT & (~filters.COMMAND), self.date)],
                'class': [MessageHandler(filters.TEXT & (~filters.COMMAND), self.classes)],
                'postpone': [MessageHandler(filters.TEXT & (~filters.COMMAND), self.choose_postpone)],
                'reason': [CallbackQueryHandler(self.choose_reason)],
                'people': [CallbackQueryHandler(self.choose_people)],
                'summary': [CallbackQueryHandler(self.say_summary)]
            },

            fallbacks=[CommandHandler('stop', self.stop)]
        )
        self.app.add_handler(main_handler)

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send message on /start and ask user for code word."""

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Привет! Это бот, который составит письмо преподавателю вместо Вас! "
                                            "Чтобы начать, введите ПИСЬМО",
                                       reply_markup=ReplyKeyboardMarkup([[KeyboardButton('ПИСЬМО')]],
                                                                        resize_keyboard=True,
                                                                        one_time_keyboard=True))

    @staticmethod
    async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Send message on /stop and end the conversation."""

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Чтобы начать заново, наберите /start.')
        return ConversationHandler.END

    @staticmethod
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Continue the conversation after code word and ask user for name."""

        print("Received", update.message, '\n')

        if update.message.text.lower() == 'письмо':
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='Хорошо, давайте начнем! Как Вы хотите подписать письмо?')
            return 'receiver'

    async def receiver(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """"""

        name = update.message.text.title()

        self.choices['sender'] = name.title()

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Кому Вы хотите отправить письмо? Введите имя преподавателя:')
        return 'date'

    async def date(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """"""
        received_message = update.message.text.capitalize()

        self.choices['name'] = received_message.title()

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='На какую дату Вы хотите перенести?')
        return 'class'

    async def classes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """"""

        received_message = update.message.text.capitalize()

        # dt = parse(str(received_message))
        # self.choices['date'] = dt.strftime('%d-%m')
        self.choices['date'] = received_message.lower()

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Какое название у дисциплины?')
        return 'postpone'

    async def choose_postpone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Show buttons with postponement options."""

        buttons = []

        received_message = update.message.text.capitalize()

        self.choices['class'] = received_message.capitalize()

        for post in COLUMN_DICT['Postponement']:
            buttons.append([InlineKeyboardButton(params['post'][post],
                                                 callback_data=post)])

        markup = InlineKeyboardMarkup(buttons)

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Выберите тип переноса:',
                                       reply_markup=markup)
        return 'reason'

    async def choose_reason(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Show buttons with reason options."""

        buttons = []

        query = update.callback_query

        await query.answer()
        await query.edit_message_text(text=f"Ваш выбор: {params['post'][query.data.lower()]}")

        self.choices['postpone'] = query.data.lower()

        reason_options = option.get_reason_options(query.data.lower())

        for reason in reason_options:
            buttons.append([InlineKeyboardButton(params['reason'][reason], callback_data=reason)])

        markup = InlineKeyboardMarkup(buttons)

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Выберите причину для письма:',
                                       reply_markup=markup)
        return 'people'

    async def choose_people(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Show buttons with people options."""

        buttons = []

        query = update.callback_query

        await query.answer()
        await query.edit_message_text(text=f"Ваш выбор: {params['reason'][query.data.lower()]}")

        self.choices['reason'] = query.data.lower()

        people_options = option.get_ppl_options(self.choices.get('postpone'), query.data.lower())

        for ppl in people_options:
            buttons.append([InlineKeyboardButton(params['people'][ppl], callback_data=ppl)])

        markup = InlineKeyboardMarkup(buttons)

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Письмо личное или групповое?',
                                       reply_markup=markup)
        return 'summary'

    async def say_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display the chosen template and end the conversation."""

        self.multiple_buttons.clear()

        query = update.callback_query

        self.choices['people'] = query.data.lower()

        await query.answer()
        await query.edit_message_text(text=f"Ваш выбор: {params['people'][query.data.lower()]}")

        user_choices = list(self.choices.values())[2:]

        for choice in user_choices:
            for item in COLUMN_DICT.items():
                template.get_by_choice(choice, item)

        got_template = template.random_choice()

        chosen_template = ''
        template_parts = [START, got_template, END]
        for part in template_parts:
            chosen_template += change_placeholder(part, self.choices)

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f'{chosen_template}')
        return ConversationHandler.END


if __name__ == "__main__":
    print('Работаем!\n')
    bot = Bot('TOKEN')
    bot.app.run_polling()
