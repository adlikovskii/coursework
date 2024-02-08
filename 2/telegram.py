import random
import configparser

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from models import add_default_status, Default, User, Status, Personal

settings = configparser.ConfigParser()
settings.read('setting.ini')
engine = sq.create_engine(settings['DEFAULT']['DSN'])
Session = sessionmaker(bind=engine)
session = Session()

print('Start telegram bot...')

state_storage = StateMemoryStorage()
TOKEN = settings['DEFAULT']['TOKEN']
bot = TeleBot(TOKEN, state_storage=state_storage)

known_users = [i.cid for i in session.query(User).all()]
userStep = {}
buttons = []
add = []


def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


def all_words(id_user):
    default = []
    for i in session.query(Status).filter(Status.id_user == id_user).all():
        for w in dir(i)[38:]:
            if eval(f'i.{w}'):
                default.append(w.replace('w', ''))
    words = []
    for d in default:
        for i in session.query(Default).filter(Default.id == d).all():
            words.append([i.eng, i.rus])
    for i in session.query(Personal).filter(Personal.id_user == id_user).all():
        words.append([i.eng, i.rus])
    return words


def random_words(words):
    random_word = random.choice(words)
    random_list = []
    while len(random_list) < 4 or len(random_list) == random.choice(words):
        new_random_word = random.choice(words)
        if new_random_word != random_word:
            if new_random_word[0] not in random_list:
                random_list.append(new_random_word[0])
    return random_word, random_list


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    cid = message.chat.id
    user_first_name = str(message.chat.first_name)
    if cid not in known_users:
        session.add(User(cid=cid))
        session.commit()
        id_user = [i.id for i in session.query(User).filter(User.cid == cid).all()][0]
        add_default_status(session, id_user=id_user)
        session.commit()
        bot.send_message(cid, f"Привет, {user_first_name} 👋 Давай попрактикуемся в английском языке. Тренировки "
                              f"можешь проходить в удобном для себя темпе.")
    markup = types.ReplyKeyboardMarkup(row_width=2)

    id_user = [i.id for i in session.query(User).filter(User.cid == cid).all()][0]
    random_word, random_list = random_words(all_words(id_user))
    global buttons
    buttons = []
    target_word = random_word[0]  # брать из БД
    translate = random_word[1]  # брать из БД
    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    others = random_list  # брать из БД
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    with bot.retrieve_data(message.chat.id) as data:
        # удалить из БД
        cid = message.chat.id
        id_user = [i.id for i in session.query(User).filter(User.cid == cid).all()][0]
        for i in session.query(Default).all():
            if data['target_word'] == i.eng:
                session.query(Status).filter(Status.id_user == id_user).update({f"w{i.id}": False})
        for i in session.query(Personal).filter(Personal.id_user == id_user).all():
            if data['target_word'] == i.eng:
                session.query(Personal).filter(Personal.eng == data['target_word']).delete()
        session.commit()


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    msg = bot.send_message(message.chat.id, 'Введите слово на английском')
    bot.register_next_step_handler(msg, add_eng)


def add_eng(message):
    bot.delete_message(message.chat.id, message.message_id - 1)
    add.append(message.text)
    msg = bot.send_message(message.chat.id, f'Введите перевод слова: {message.text}')
    bot.register_next_step_handler(msg, add_rus)


def add_rus(message):
    bot.delete_message(message.chat.id, message.message_id - 1)
    add.append(message.text)
    cid = message.chat.id
    id_user = [i.id for i in session.query(User).filter(User.cid == cid).all()][0]

    session.add(Personal(eng=add[0], rus=add[1], id_user=id_user))
    session.commit()

    bot.send_message(message.chat.id, f'Слово {add[0]}, c переводом {add[1]} успешно добавлено в ваш словарь')
    add.clear()
    create_cards(message)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons.extend([next_btn, add_word_btn, delete_word_btn])
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)
