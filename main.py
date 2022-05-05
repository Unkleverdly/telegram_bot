import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import sqlite3
from time import sleep

con = sqlite3.connect('database', check_same_thread=False)
cursor = con.cursor()

chat = ''
subchat = ''

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)


def themes():
    answer = []
    answer_time = []
    count = 0
    list_topics = [i[1] for i in cursor.execute(f"""SELECT * FROM themes""").fetchall()]
    for i in range(len(list_topics)):
        count += 1
        answer_time.append(list_topics[i])
        if count == 2:
            count = 0
            answer.append(answer_time)
            answer_time = []
    if len(list_topics) % 2 == 0:
        return answer
    else:
        answer.append(list_topics[-1])
        return answer


def subtopics(topic):
    answer = []
    answer_time = []
    count = 0
    list_topics = [i[1] for i in cursor.execute(
        f"""SELECT * FROM subtopics WHERE id_topic = (SELECT id_topic FROM THEMES WHERE topic = '{topic}')""").fetchall()]
    for i in range(len(list_topics)):
        count += 1
        answer_time.append(list_topics[i])
        if count == 2:
            count = 0
            answer.append(answer_time)
            answer_time = []
    if len(list_topics) % 2 == 0:
        return answer
    else:
        answer.append(list_topics[-1])
        return answer


markup = ReplyKeyboardMarkup(themes() + [['⬅️', '➡️']], one_time_keyboard=True, resize_keyboard=True)

logger = logging.getLogger(__name__)

TOKEN = '5349950152:AAHdYch7YjjhXyro-CbbQwtHuIPCF5MM2-U'


def start(update, context):
    cursor.execute(
        f"""INSERT INTO users(user_name, user_id) VALUES('{update.message.from_user.username}', '{update.message.from_user.id}')""")
    con.commit()
    update.message.reply_text(f'Привет @{update.message.from_user.username}')
    sleep(0.5)
    update.message.reply_text(f'Чтобы выбрать чат напиши: /find_chat',
                              reply_markup=ReplyKeyboardMarkup([['/find_chat']], one_time_keyboard=True,
                                                               resize_keyboard=True))


def find_chat(update, contex):
    update.message.reply_text(f'Выбери интересующую тебя тему', reply_markup=markup)
    return 1


def find_chat2(update, contex):
    answer1 = update.message.text
    update.message.reply_text('Выбери интересный тебе чат',
                              reply_markup=ReplyKeyboardMarkup(subtopics(topic=answer1) + [['⬅️', '➡️']],
                                                               one_time_keyboard=True, resize_keyboard=True))
    return 2


def end(update, contex):
    update.message.reply_text('Чтобы выйти из чата напиши: /stop', reply_markup=ReplyKeyboardRemove)
    return ConversationHandler.END


def stop(update, contex):
    update.message.reply_text('Ещё увидимся',
                              reply_markup=ReplyKeyboardRemove)
    return ConversationHandler.END


def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher

    # text_handler = MessageHandler(Filters.text & ~Filters.command, echo)
    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('find_chat', find_chat)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(Filters.text & ~Filters.command, find_chat2)],
            2: [MessageHandler(Filters.text & ~Filters.command, end)],
            # Функция читает ответ на второй вопрос и завершает диалог.
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )

    dp.add_handler(conv_handler)

    dp.add_handler(CommandHandler('start', start))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
