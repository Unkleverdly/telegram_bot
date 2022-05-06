import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from time import sleep

con = sqlite3.connect('database', check_same_thread=False)
cursor = con.cursor()

subchat = False
chat = ''

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
        answer.append([list_topics[-1]])
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
        answer.append([list_topics[-1]])
        return answer


markup = ReplyKeyboardMarkup(themes() + [['⬅️', '➡️']], one_time_keyboard=True, resize_keyboard=True)

logger = logging.getLogger(__name__)

TOKEN = '5349950152:AAHdYch7YjjhXyro-CbbQwtHuIPCF5MM2-U'


def start(update, context):
    list_users = [i[0] for i in cursor.execute(f"""SELECT user_name FROM users""").fetchall()]
    if update.message.from_user.username not in list_users:
        cursor.execute(
            f"""INSERT INTO users(user_name, user_id) VALUES('{update.message.from_user.username}', '{update.message.from_user.id}')""")
        con.commit()
        update.message.reply_text(f'Привет @{update.message.from_user.username}')
        sleep(0.5)
        update.message.reply_text(f'Чтобы выбрать чат напиши: /find_chat',
                                  reply_markup=ReplyKeyboardMarkup([['/find_chat']], one_time_keyboard=True,
                                                                   resize_keyboard=True))
    else:
        update.message.reply_text(f'Рад снова тебя видеть @{update.message.from_user.username}')
        update.message.reply_text(f'Чтобы выбрать чат напиши: /find_chat',
                                  reply_markup=ReplyKeyboardMarkup([['/find_chat']], one_time_keyboard=True,
                                                                   resize_keyboard=True))


def find_chat(update, contex):
    if not subchat:
        update.message.reply_text(f'Выбери интересующую тебя тему', reply_markup=markup)
        return 1
    else:
        update.message.reply_text(f'Вы уже находитесь в чате, чтобы выйти напишите /stop')


def find_chat2(update, contex):
    answer1 = update.message.text
    update.message.reply_text('Отлично', reply_markup=ReplyKeyboardRemove())
    update.message.reply_text('Выбери интересный тебе чат',
                              reply_markup=ReplyKeyboardMarkup(subtopics(topic=answer1) + [['⬅️', '➡️']]))
    return 2


def end(update, contex):
    global subchat, chat
    subchat = True
    chat = update.message.text
    if chat not in [i[0] for i in cursor.execute("""SELECT subtopic FROM subtopics""").fetchall()]:
        update.message.reply_text('Извините, такого чата нет', reply_markup=ReplyKeyboardRemove())
        subchat = False
        chat = ''
        return ConversationHandler.END
    else:
        cursor.execute(
            f"""UPDATE subtopics SET users = ((SELECT users FROM subtopics WHERE subtopic = '{chat}') +
             '{update.message.from_user.id},') WHERE subtopic = '{chat}'""")

        con.commit()
    update.message.reply_text('Чтобы выйти из чата напиши: /stop', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def stop(update, contex):
    global subchat
    subchat = False
    update.message.reply_text('Ещё увидимся)))')
    return ConversationHandler.END


def message(update, contex):
    if subchat:
        update.message.reply_text('Вы написали сообщение')
    else:
        update.message.reply_text('Извините, я вас не понимаю')


def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher

    text_handler = MessageHandler(Filters.text & ~Filters.command, message)
    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /find_chat. Она задаёт первый вопрос.
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
    dp.add_handler(CommandHandler('stop', stop))
    dp.add_handler(conv_handler)
    dp.add_handler(text_handler)
    dp.add_handler(CommandHandler('start', start))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
