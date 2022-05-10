import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import sqlite3
from time import sleep

TOKEN = '5309964868:AAGKe6Oq2h2tAW99ftRxUcHDJ7iQzJSYvB0'  # токен для бота

con = sqlite3.connect('database.db', check_same_thread=False)
cursor = con.cursor()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


# берёт названия тем из БД и создаёт из них кнопки
def themes():
    answer = []
    answer_time = []
    count = 0
    list_topics = [i[0] for i in cursor.execute(f"""SELECT topic FROM themes""").fetchall()]
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


# берёт название чатов из БД и создаёт кнопки
def subtopics(topic):
    answer = []
    answer_time = []
    count = 0
    list_topics = [i[0] for i in cursor.execute(
        f"""SELECT subtopic FROM subtopics WHERE id_topic = (SELECT id_topic FROM THEMES WHERE topic = '{topic}')""").fetchall()]
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


# начало общения с пользователем
def start(update, context):
    list_users = [i[0] for i in cursor.execute(f"""SELECT user_name FROM users""").fetchall()]
    if update.message.from_user.username not in list_users:
        cursor.execute(
            f"""INSERT INTO users(user_name, user_id) VALUES('{update.message.from_user.username}', '{update.message.from_user.id}')""")
        con.commit()
        update.message.reply_text(f'Привет @{update.message.from_user.username}')
        sleep(0.5)
        update.message.reply_text(
            f'Чтобы выбрать чат напиши: /find_chat\nЧтобы найти друзей: /find_friend',
            reply_markup=ReplyKeyboardMarkup([['/find_chat', '/find_friend']], one_time_keyboard=True,
                                             resize_keyboard=True))
    else:
        update.message.reply_text(f'Рад снова тебя видеть @{update.message.from_user.username}')
        update.message.reply_text(
            f'Чтобы выбрать чат напиши: /find_chat\nЧтобы найти друзей: /find_friend',
            reply_markup=ReplyKeyboardMarkup([['/find_chat', '/find_friend']], one_time_keyboard=True,
                                             resize_keyboard=True))
    if context.bot.get_user_profile_photos(user_id=update.message.from_user.id)["photo"]:
        cursor.execute(
            f"""UPDATE users SET photo =
{context.bot.get_user_profile_photos(user_id=update.message.from_user.id)["photo"][0]} 
WHERE user_name = '{update.message.from_user.username}'""")

    global chat
    chat = \
        cursor.execute(
            f"""SELECT chat FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()[0][0]
    print(chat, [chat], type(chat))
    con.commit()


# выбор темы
def find_chat(update, contex):
    chat = \
        cursor.execute(
            f"""SELECT chat FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()[
            0][0]
    if chat == 'none':
        update.message.reply_text(f'Выбери интересующую тебя тему',
                                  reply_markup=ReplyKeyboardMarkup(themes(), one_time_keyboard=True,
                                                                   resize_keyboard=True))
        return 1
    else:
        update.message.reply_text(f'Вы уже находитесь в чате, чтобы выйти напишите /stop')


# выбор чата
def find_chat2(update, contex):
    answer1 = update.message.text
    update.message.reply_text('Отлично', reply_markup=ReplyKeyboardRemove())
    update.message.reply_text('Выбери интересный тебе чат',
                              reply_markup=ReplyKeyboardMarkup(subtopics(topic=answer1),
                                                               one_time_keyboard=True, resize_keyboard=True))
    return 2


# конец выборов
def end(update, context):
    cursor.execute(
        f"""UPDATE users SET chat = '{update.message.text}' WHERE user_name = '{update.message.from_user.username}'""")
    con.commit()
    chat = \
        cursor.execute(
            f"""SELECT chat FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()[
            0][0]
    if chat not in [i[0] for i in cursor.execute("""SELECT subtopic FROM subtopics""").fetchall()]:
        update.message.reply_text('Извините, такого чата нет', reply_markup=ReplyKeyboardRemove())
        cursor.execute(
            f"""UPDATE users SET chat = 'none' WHERE user_name = '{update.message.from_user.username}'""")
        con.commit()
        return ConversationHandler.END
    else:
        users = cursor.execute(f"""SELECT users FROM subtopics WHERE subtopic = '{chat}'""").fetchall()[0][0]
        new = f'{users}{update.message.from_user.id}, '
        cursor.execute(
            f"""UPDATE subtopics SET users = '{new}' WHERE subtopic = '{chat}'""")

        subtopics_db = [i[0] for i in cursor.execute(
            f"""SELECT subtopic FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()]
        topics_db = [i[0] for i in cursor.execute(
            f"""SELECT topic FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()]

        new_id_topic = cursor.execute(f"""SELECT id_topic FROM subtopics WHERE subtopic = '{chat}'""").fetchall()[0][0]
        new_id_subtopic = \
            cursor.execute(f"""SELECT id_subtopic FROM subtopics WHERE subtopic = '{chat}'""").fetchall()[0][0]

        photo = cursor.execute(f"""SELECT photo FROM subtopics WHERE subtopic = '{chat}'""").fetchall()[0][0]
        print(topics_db, subtopics_db)
        if subtopics_db != ['none'] and topics_db != ['none']:
            subtopics_db = subtopics_db[0].split(', ')
            topics_db = topics_db[0].split(', ')

            while len(subtopics_db) >= 10:
                subtopics_db = subtopics_db[1:]

            while len(topics_db) >= 10:
                topics_db = topics_db[1:]

            subtopics_db = [f"{', '.join(subtopics_db)}"]
            topics_db = [f"{', '.join(topics_db)}"]

            answer_subtopic = ' '.join(subtopics_db) + str(new_id_subtopic)
            answer_topic = ' '.join(topics_db) + str(new_id_topic)


        else:
            answer_subtopic = str(new_id_subtopic)
            answer_topic = str(new_id_topic)

        cursor.execute(
            f"""UPDATE users SET subtopic = '{answer_subtopic}, ' WHERE user_name = '{update.message.from_user.username}'""")
        cursor.execute(
            f"""UPDATE users SET topic = '{answer_topic}, ' WHERE user_name = '{update.message.from_user.username}'""")
        if photo:
            context.bot.send_photo(update.message.from_user.id, photo=photo)
        con.commit()

    update.message.reply_text('Чтобы выйти из чата напиши: /stop',
                              reply_markup=ReplyKeyboardMarkup([['/stop']], one_time_keyboard=True,
                                                               resize_keyboard=True))
    return ConversationHandler.END


# выход из чата
def stop(update, contex):
    chat = \
        cursor.execute(
            f"""SELECT chat FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()[
            0][0]
    print(cursor.execute(f"""SELECT users FROM subtopics WHERE subtopic = '{chat}'""").fetchall())
    users = cursor.execute(f"""SELECT users FROM subtopics WHERE subtopic = '{chat}'""").fetchall()[0][0].split(', ')[
            :-1]

    new = ', '.join(' '.join(' '.join(users).split(f'{update.message.from_user.id}')).split())

    cursor.execute(
        f"""UPDATE subtopics SET users = '{new}, ' WHERE subtopic = '{chat}'""")
    cursor.execute(
        f"""UPDATE users SET chat = 'none' WHERE user_name = '{update.message.from_user.username}'""")
    con.commit()
    update.message.reply_text('Ещё увидимся)))',
                              reply_markup=ReplyKeyboardMarkup([['/find_chat', '/find_friend']], resize_keyboard=True,
                                                               one_time_keyboard=True))
    return ConversationHandler.END


# находит друзей по интересам
def find_friend(update, context):
    main_user = cursor.execute(
        f"""SELECT topic, subtopic FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()[0]
    users = [i for i in cursor.execute(f"""SELECT user_name, topic, photo, subtopic FROM users""").fetchall() if
             i[-1] is not None and i[0] != update.message.from_user.username]
    if main_user == ('', ''):
        update.message.reply_text(
            f'Похоже вы ещё не заходили в чаты. Чтобы найти друзей заходите в чаты и, на основе ваших предпочтений, '
            f'мы подберём вам друга', reply_markup=ReplyKeyboardRemove())
        return
    answer = []
    for i in users:
        count_topic = 0
        count_subtopic = 0

        for j in main_user[0].split(', ')[:-1]:
            for x in i[1].split(', ')[:-1]:
                if x == j:
                    count_topic += 1
                    break

        for j in main_user[-1].split(', ')[:-1]:
            for x in i[-1].split(', ')[:-1]:
                if x == j:
                    count_subtopic += 1
                    break

        if count_topic >= 60 / (100 / len(main_user[1].split(', ')[:-1])) or count_subtopic >= 50 / (
                100 / len(main_user[-1].split(', ')[:-1])):
            answer.append(i)
    if answer:
        update.message.reply_text(f'У вас такие же интересы как и у этих людей:', reply_markup=ReplyKeyboardRemove())

        for i in answer:
            update.message.reply_text(f'@{i[0]}')

            if i[2] is not None:
                context.bot.send_photo(update.message.from_user.id, photo=i[2])
    else:
        update.message.reply_text(f'Простите, мы не нашли людей со схожими предпочтениями',
                                  reply_markup=ReplyKeyboardRemove())
        sleep(3)
        update.message.reply_text('😢😢😢')


# позволяет добавить темы и чаты
def admin(update, context):
    update.message.reply_text('Введите название новой или старой темы темы')
    return 11


def admin_new_subchat(update, context):
    global topic_admin
    topic_admin = update.message.text
    update.message.reply_text('Ввдеите название нового чата для темы')
    return 12


def admin_new_photo(update, context):
    global new_subchat
    new_subchat = update.message.text
    update.message.reply_text('Пришлите новую картинку для чата')
    return 13


def admin_last(update, context):
    photo_id = update.message.photo[-1]["file_id"]
    topics = [i[0] for i in cursor.execute(f"""SELECT topic FROM themes""").fetchall()]
    if topic_admin not in topics:
        cursor.execute(f"""INSERT INTO themes(topic) VALUES('{topic_admin}')""")
    id_topic = cursor.execute(f"""SELECT id_topic FROM themes WHERE topic = '{topic_admin}'""").fetchall()[0][0]
    print(photo_id, id_topic)
    cursor.execute(
        f"""INSERT INTO subtopics(id_topic, subtopic, photo) VALUES({id_topic}, '{new_subchat}', '{photo_id}')""")
    con.commit()
    update.message.reply_text('Изменения сохранены')

    return ConversationHandler.END


def stop_admin(update, context):
    return ConversationHandler.END


# отправление текстового сообщения пользователем в чате
def message(update, context):
    chat = \
        cursor.execute(
            f"""SELECT chat FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()[
            0][0]
    if chat != 'none':
        users = cursor.execute(f"""SELECT users FROM subtopics WHERE subtopic = '{chat}'""").fetchall()[0][0].split(
            ', ')[
                :-1]
        for i in users:
            if i != str(update.message.from_user.id) and i != '' and i != ' ':
                context.bot.send_message(i, text=f'@{update.message.from_user.username}\n{update.message.text}')
    else:
        update.message.reply_text('Извините, я вас не понимаю')


# отправление фото пользователем в чате
def photo(update, context):
    update.message.reply_text(update.message.photo[-1]["file_id"])
    chat = \
        cursor.execute(
            f"""SELECT chat FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()[
            0][0]
    if chat != 'none':
        users = cursor.execute(f"""SELECT users FROM subtopics WHERE subtopic = '{chat}'""").fetchall()[0][0].split(
            ', ')[
                :-1]
        for i in users:
            if i != str(update.message.from_user.id) and i != '' and i != ' ':
                context.bot.send_photo(i, photo=update.message.photo[-1]["file_id"])
    else:
        update.message.reply_text('Извините, я вас не понимаю')


# отправление голосового сообщения пользователем в чате
def voice(update, context):
    chat = \
        cursor.execute(
            f"""SELECT chat FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()[
            0][0]
    if chat != 'none':
        users = cursor.execute(f"""SELECT users FROM subtopics WHERE subtopic = '{chat}'""").fetchall()[0][0].split(
            ', ')[
                :-1]
        for i in users:
            if i != str(update.message.from_user.id) and i != '' and i != ' ':
                file_id = update.message.voice["file_id"]
                context.bot.sendVoice(i, file_id)

    else:
        update.message.reply_text('Извините, я вас не понимаю')


# отправление видео пользователем в чате
def video(update, context):
    chat = \
        cursor.execute(
            f"""SELECT chat FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()[
            0][0]
    if chat != 'none':
        users = cursor.execute(f"""SELECT users FROM subtopics WHERE subtopic = '{chat}'""").fetchall()[0][0].split(
            ', ')[
                :-1]
        for i in users:
            if i != str(update.message.from_user.id) and i != '' and i != ' ':
                file_id = update.message.video["file_id"]
                context.bot.sendVideo(i, video=file_id)
    else:
        update.message.reply_text('Извините, я вас не понимаю')


# отправление стикера пользователем в чате
def stick(update, context):
    chat = \
        cursor.execute(
            f"""SELECT chat FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()[
            0][0]
    if chat != 'none':
        users = cursor.execute(f"""SELECT users FROM subtopics WHERE subtopic = '{chat}'""").fetchall()[0][0].split(
            ', ')[
                :-1]
        for i in users:
            if i != str(update.message.from_user.id) and i != '' and i != ' ':
                file_id = update.message.sticker["file_id"]
                context.bot.sendSticker(i, sticker=file_id)
    else:
        update.message.reply_text('Извините, я вас не понимаю')


# отправление круглого видео сообщения пользователем в чате
def vid_note(update, context):
    chat = \
        cursor.execute(
            f"""SELECT chat FROM users WHERE user_name = '{update.message.from_user.username}'""").fetchall()[
            0][0]
    if chat != 'none':
        users = cursor.execute(f"""SELECT users FROM subtopics WHERE subtopic = '{chat}'""").fetchall()[0][0].split(
            ', ')[
                :-1]
        for i in users:
            if i != str(update.message.from_user.id) and i != '' and i != ' ':
                file_id = update.message.video_note["file_id"]
                context.bot.sendVideoNote(chat_id=i, video_note=file_id)
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

    admin_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /admin. Она задаёт первый вопрос.
        entry_points=[CommandHandler('admin', admin)],

        # Состояние внутри диалога.
        # Вариант с тремя обработчиками, фильтрующими текстовые сообщения.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            11: [MessageHandler(Filters.text & ~Filters.command, admin_new_subchat)],
            12: [MessageHandler(Filters.text & ~Filters.command, admin_new_photo)],
            13: [MessageHandler(Filters.photo & ~Filters.command, admin_last)]
            # Функция читает ответ на третий вопрос и завершает диалог.
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop_admin', stop_admin)]
    )

    dp.add_handler(admin_handler)
    dp.add_handler(conv_handler)

    dp.add_handler(text_handler)
    dp.add_handler(MessageHandler(Filters.photo, photo))
    dp.add_handler(MessageHandler(Filters.voice, voice))
    dp.add_handler(MessageHandler(Filters.video, video))
    dp.add_handler(MessageHandler(Filters.sticker, stick))
    dp.add_handler(MessageHandler(Filters.video_note, vid_note))

    dp.add_handler(CommandHandler('stop', stop))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', start))
    dp.add_handler(CommandHandler('find_friend', find_friend))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
