import random

import telebot
from telebot import types
import json
from datetime import date, timedelta

TOKEN = "7341169752:AAHHpOj9d1eJgdQ93MjTv46QO3TFMavhvqs"

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет")


@bot.message_handler(commands=['show_dates'])
def handle_schedule(message):
    """Выбор даты"""
    # Отправляем клавиатуру с кнопками

    keyboard = choose_option()
    bot.send_message(message.chat.id, "Выберите процедуру:", reply_markup=keyboard)
@bot.message_handler(commands=['add_review'])
def handle_add_review(message):
    bot.send_message(message.chat.id, 'Напишите отзыв:')

    bot.register_next_step_handler(message, save_review)


@bot.message_handler(commands=['move_appointment'])
def handle_move_appointment(message):
    keyboard = move_appointment()

    bot.send_message(message.chat.id, 'Выберите опцию', reply_markup=keyboard)

def choose_option():
    options = ['Стрижка', 'Маникюр','Вечерний макияж','Педикюр']
    keyboard = types.InlineKeyboardMarkup()
    for option in options:
        callback_data = f"option:{option}"
        button = types.InlineKeyboardButton(text=option, callback_data=callback_data)
        keyboard.add(button)
    return keyboard


def generate_date_schedule(option):
    keyboard = types.InlineKeyboardMarkup()

    # Получаем кнопки для указанной даты
    days = []

    for i in range(7):
        days.append(date.today() + timedelta(days=i))

    # Создаем кнопки и добавляем их на клавиатуру
    for button_text in days:
        callback_data = f"day:{button_text}:{option}"
        button = types.InlineKeyboardButton(text=str(button_text), callback_data=callback_data)
        keyboard.add(button)

    return keyboard


def move_appointment():
    options = ['Удалить запись','Перенести запись']
    keyboard = types.InlineKeyboardMarkup()
    for option in options:
        callback_data = f"move:{option}"
        button = types.InlineKeyboardButton(text=option, callback_data=callback_data)
        keyboard.add(button)
    return keyboard


def generate_time_keyboard(date, option):
    keyboard = types.InlineKeyboardMarkup()

    # Получаем кнопки для указанной даты
    times = ["10:00", "12:00", "15:00", "17:00"]
    with (open('./data.json', 'r', encoding='utf-8') as file):
        data = json.load(file)
        for appointment in data['appointments']:
            if appointment['option'] == option:
                if appointment['date'] == date:
                    times.remove(appointment['time'])


    # Создаем кнопки и добавляем их на клавиатуру
    for time in times:
        callback_data = f"appointment${date}${time}${option}"
        button = types.InlineKeyboardButton(text=time, callback_data=callback_data)
        keyboard.add(button)

    return keyboard


# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data.startswith("day:"):
        chosen_date, chosen_option = call.data.split(":")[1], call.data.split(":")[2]
        bot.send_message(call.message.chat.id, f"Вы выбрали дату: {chosen_date}")
        # Отправляем клавиатуру с доступным временем
        bot.send_message(call.message.chat.id, "Выберите время:", reply_markup=generate_time_keyboard(chosen_date, chosen_option))
    elif call.data.startswith("appointment$"):
        chosen_date, chosen_time, chosen_option = call.data.split('$')[1], call.data.split('$')[2], call.data.split('$')[3]
        bot.send_message(call.message.chat.id, f"Вы записаны на {chosen_option}, {chosen_date} в {chosen_time}")
        add_appointment(chosen_date, chosen_time, call.message.chat.id, chosen_option)
    elif call.data.startswith("option:"):
        chosen_option = call.data.split(':')[1]
        bot.send_message(call.message.chat.id, f"Вы выбрали {chosen_option}")
        keyboard = generate_date_schedule(chosen_option)
        bot.send_message(call.message.chat.id, "Выберите день:", reply_markup=keyboard)
    elif call.data.startswith("move:"):
        chosen_option = call.data.split(':')[1]
        if chosen_option == 'Удалить запись':
            generate_delete_keyboard(call.message.chat.id)
        else:
            ...
    elif call.data.startswith('delete$'):
        chosen_option, chosen_date, chosen_time = call.data.split('$')[1], call.data.split('$')[2], call.data.split('$')[3]
        try:
            with open('data.json', 'w+', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {"appointments": [], "review": []}

        for appointment in data['appointments']:
            if chosen_option == appointment['option'] and chosen_date == appointment['date'] and chosen_time == appointment['time']:
                data['appointments'].remove({"date": chosen_date, "time": chosen_time, "client": call.message.chat.id, "option": chosen_option})
                with open('data.json', 'w', encoding='utf-8') as file:
                    json.dump(data, file, ensure_ascii=False)

def generate_delete_keyboard(id):
    try:
        with open('data.json', 'w+', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"appointments": [], "review": []}

    keyboard = types.InlineKeyboardMarkup()

    for appointment in data['appointments']:
        if id == appointment['client']:
            callback_data = f"delete${appointment['option']}${appointment['date']}${appointment['time']}"
            button = types.InlineKeyboardButton(text=f"{appointment['option']}, {appointment['date']}, {appointment['time']}", callback_data=callback_data)
            keyboard.add(button)

    return keyboard


def add_appointment(date, time, client, option):
    # Чтение существующих данных из файла
    try:
        with open('data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"appointments": [], "review": []}

    # Добавление новой записи
    new_appointment = {'date': date, 'time': time, 'client': client, 'option' : option}
    data['appointments'].append(new_appointment)

    # Запись обновленных данных в файл
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)


def save_review(message):
    id = message.chat.id
    review = message.text
    add_review(id, review)
    bot.send_message(message.chat.id, 'Спасибо за оставленный отзыв')


def add_review(client, text):
    try:
        # Чтение данных из файла
        with open("data.json", "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        # Если файла нет, создаем пустую структуру
        data = {"appointments": [], "review": []}

    # Добавление нового отзыва в список отзывов
    data["review"].append({
        "client": client,
        "text": text
    })

    # Сохранение обновленных данных в файл
    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False)

# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)