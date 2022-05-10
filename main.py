import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, firestore
from telebot.types import LabeledPrice


max_id = 60
place = 'Place1'

#поключаемся к боту
bot = telebot.TeleBot('TOKEN')
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)


#подключаемся к базе и забираем данные из таблицы
def get_data_from_firebase():
    global place
    db = firestore.client()
    ref = db.collection(place)
    docs = ref.get()

    return docs


#записываем инфу в базу
def set_data_to_firebase(id, name):
    global place
    db = firestore.client()
    ref = db.collection(place).document('Visitor{}'.format(id))
    ref.set({
                'ID': id,
                'Name': name
            })


#генерируем маркап для меню
def generate_markup(buttons = []):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for text in buttons:
        item1 = types.KeyboardButton(text)
        markup.add(item1)

    return markup


#главное меню
def main_menu(message):
    mk = generate_markup(['Оплатить'])
    bot.send_message(message.chat.id, 'Ты попал на Локацию.\n1. Следуй инструкциям\n2. Оплати билет\n3. Получи номер',
                     reply_markup=mk)


#обрабатываем текстовые команды
@bot.message_handler(content_types=['text'])
def start(message):
    global max_id

    if message.text == '/start' or message.text == 'Вернуться в главное меню':

        docs = get_data_from_firebase()

        if len(docs) == 0 or docs[-1].to_dict()['ID'] < max_id:
            main_menu(message)
        else:
            mk = generate_markup()
            bot.send_message(message.chat.id, 'Ты попал на Локацию. Но, к сожалению, в данный момент проходки '
                                              'закончились. Ждём тебя в следующий раз!', reply_markup=mk)

    elif message.text == 'Оплатить':
        print('test')
        bot.send_invoice(chat_id=message.from_user.id, title='Проходка в Локацию', description='Та самая',
                         invoice_payload='tiket', provider_token='YOUR_PROVIDER_TOKEN',
                         currency='RUB', start_parameter='tiket', prices=[LabeledPrice(label='Руб.', amount=15000)])

    elif message.text == '/help':
        mk = generate_markup('Вернуться в главное меню')
        bot.send_message(message.chat.id, 'А что тут писать, всё же и так интуитивно))', reply_markup=mk)

    elif message.text == '/change_max_visitors':
        mk = generate_markup(['Вернуться в главное меню'])
        bot.send_message(message.chat.id, 'Введите максимальное количество проходок',
                         reply_markup=mk)
        bot.register_next_step_handler(message, set_number_of_visitors)

    elif message.text == '/show_visitors':
        docs = get_data_from_firebase()
        id_name = ''
        for doc in docs:
            id = 0
            name = ''
            for key, value in doc.to_dict().items():
                if key == 'ID':
                    id = value
                elif key == 'Name':
                    name = value
            id_name += '{} - {}\n'.format(id, name)

        mk = generate_markup(['Вернуться в главное меню'])
        bot.send_message(message.chat.id, id_name, reply_markup=mk)

    elif message.text == '/show_number_of_visitors':
        docs = get_data_from_firebase()

        if len(docs) == 0:
            id = 0
        else:
            id = docs[-1].to_dict()['ID']

        mk = generate_markup(['Вернуться в главное меню'])
        bot.send_message(message.chat.id, 'Количество проданных проходок - {}'.format(id), reply_markup=mk)

    elif message.text == '/change_place':
        bot.send_message(message.chat.id, 'Введите новое название на латынице без пробелов')
        bot.register_next_step_handler(message, set_placename)

    elif message.text == '/admin_help':
        mk = generate_markup(['Вернуться в главное меню'])
        bot.send_message(message.chat.id, '/change_max_visitors - изменить количество проходок (по умолчанию 60)\n'
                                          '/show_visitors - показать тех, кто купил билеты\n'
                                          '/show_number_of_visitors - количество купивших билеты\n'
                                          '/change_place - изменить место (нужно для того, чтобы создалась новая '
                                          'база данных на мероприятие)', reply_markup=mk)


#устанавливаем название таблицы в базе данных
def set_placename(message):
    global place
    place = message.text
    mk = generate_markup(['Вернуться в главное меню'])
    bot.send_message(message.chat.id, 'Новое название места установлено', reply_markup=mk)


#устанавливаем количество проходок
def set_number_of_visitors(message):
    global max_id
    prev = max_id
    try:
        max_id = int(message.text)
        mk = generate_markup(['Вернуться в главное меню'])
        bot.send_message(message.chat.id, 'Новое максимальное количество проходок установлено', reply_markup=mk)
    except:
        max_id = prev
        bot.send_message(message.chat.id, 'Что-то пошло не так, попробуй ещё раз', reply_markup=mk)


#узнаём имя посетителя
def get_name(message):
    #запоминаем имя посетителя
    name = message.text

    #читаем данные из базы
    docs = get_data_from_firebase()

    if len(docs) == 0:
        id = 0
    else:
        id = docs[-1].to_dict()['ID']

    mk = generate_markup(['Вернуться в главное меню'])
    bot.send_message(message.chat.id, 'Твой номер - {}'.format(id + 1), reply_markup=mk)

    set_data_to_firebase(id + 1, name)


#реагируем на пре чекаут квери
@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    print('test2')
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


#если оплата прошла успещно, выводим сообщение и двигаемся дальше по алгоритму
@bot.message_handler(content_types=['successful_payment'])
def process_pay(message):
    print('test3')
    if message.successful_payment.invoice_payload == 'tiket':
        mk = generate_markup()
        bot.send_message(message.from_user.id, 'Платеж прошёл успешно. Представьтесь, пожалуйста. После этого вам будет выслан код, '
                                               'который нужно будет сказать на входе', reply_markup=mk)
        bot.register_next_step_handler(message, get_name)


#главная зацикленная функция
bot.polling(none_stop=True, interval=0)