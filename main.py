import json
import os
import telebot
from telebot import types

bot = telebot.TeleBot('7039781421:AAEUqlh32yopQK8y3nKv1ZwB3CyKJLTVVcI')

# Список лекций
lectures = [f'Лекция {i}' for i in range(1, 11)]

# Состояние пользователей
user_progress = {}

# Функция для чтения содержимого файла лекции
def read_lecture(lecture_number):
    filename = f'lecture{lecture_number}.json'
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return None

# Функция для обновления прогресса пользователя
def update_user_progress(user_id, lecture_number=None, correct_answers=None, total_questions=None):
    if user_id not in user_progress:
        user_progress[user_id] = {
            'completed_lectures': set(),
            'completed_tests': {},
        }
    if lecture_number is not None:
        user_progress[user_id]['completed_lectures'].add(lecture_number)
    if correct_answers is not None and total_questions is not None:
        user_progress[user_id]['completed_tests'][lecture_number] = {
            'correct_answers': correct_answers,
            'total_questions': total_questions,
        }

# Функция для получения прогресса пользователя
def get_user_progress(user_id):
    if user_id in user_progress:
        completed_lectures = len(user_progress[user_id]['completed_lectures'])
        completed_tests = user_progress[user_id]['completed_tests']
        total_tests = len(completed_tests)
        total_correct_answers = sum(test['correct_answers'] for test in completed_tests.values())
        total_questions = sum(test['total_questions'] for test in completed_tests.values())
        if total_questions > 0:
            test_percentage = (total_correct_answers / total_questions) * 100
        else:
            test_percentage = 0
        return completed_lectures, total_tests, test_percentage
    else:
        return 0, 0, 0

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Пройти курс лекций', callback_data='course'))
    markup.add(types.InlineKeyboardButton('Выполнить тесты', callback_data='tests'))
    markup.add(types.InlineKeyboardButton('Прогресс', callback_data='progress'))
    bot.send_message(
        message.chat.id,
        f'Привет, {message.from_user.first_name}! Вы попали на лекционный курс сотрудников! Вам необходимо пройти курс лекций и выполнить тесты для определения усвоения материала. Выберите действие:',
        reply_markup=markup
    )

# Обработчик выбора курса лекций
@bot.callback_query_handler(func=lambda call: call.data == 'course')
def course_callback(call):
    user_id = call.from_user.id
    markup = types.InlineKeyboardMarkup()
    for i, lecture in enumerate(lectures, 1):
        lecture_label = lecture
        if i in user_progress.get(user_id, {}).get('completed_lectures', set()):
            lecture_label += ' (лекция пройдена)'
        if i in user_progress.get(user_id, {}).get('completed_tests', {}):
            lecture_label += ' (тест пройден)'
        markup.add(types.InlineKeyboardButton(lecture_label, callback_data=f'lecture_{i}'))
    markup.add(types.InlineKeyboardButton('Назад', callback_data='back_to_main'))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Выберите лекцию:',
        reply_markup=markup
    )

# Обработчик выбора лекции
@bot.callback_query_handler(func=lambda call: call.data.startswith('lecture_'))
def lecture_callback(call):
    lecture_number = int(call.data.split('_')[1])
    lecture = read_lecture(lecture_number)
    if lecture:
        lecture_title = lecture['lecture_title']
        lecture_content = lecture['lecture_content']
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Пройти тест по лекции', callback_data=f'test_{lecture_number}'))
        markup.add(types.InlineKeyboardButton('Назад', callback_data='course'))
        markup.add(types.InlineKeyboardButton('Вернуться в меню', callback_data='back_to_main'))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'{lecture_title}\n\n{lecture_content}',
            reply_markup=markup
        )
        # Обновление прогресса пользователя после прочтения лекции
        update_user_progress(call.from_user.id, lecture_number=lecture_number)
    else:
        bot.send_message(call.message.chat.id, 'Файл лекции не найден. Убедитесь, что все файлы лекций находятся в правильной директории.')

# Обработчик кнопки "Назад" для возврата к выбору действия
@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
def back_to_main_callback(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Пройти курс лекций', callback_data='course'))
    markup.add(types.InlineKeyboardButton('Выполнить тесты', callback_data='tests'))
    markup.add(types.InlineKeyboardButton('Прогресс', callback_data='progress'))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Выберите действие:',
        reply_markup=markup
    )

# Обработчик выбора тестов
@bot.callback_query_handler(func=lambda call: call.data == 'tests')
def tests_callback(call):
    user_id = call.from_user.id
    markup = types.InlineKeyboardMarkup()
    for i, lecture in enumerate(lectures, 1):
        lecture_label = lecture
        if i in user_progress.get(user_id, {}).get('completed_tests', {}):
            lecture_label += ' (тест пройден)'
        markup.add(types.InlineKeyboardButton(lecture_label, callback_data=f'test_{i}'))
    markup.add(types.InlineKeyboardButton('Назад', callback_data='back_to_main'))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Выберите тест:',
        reply_markup=markup
    )

# Обработчик кнопки "Пройти тест по лекции"
@bot.callback_query_handler(func=lambda call: call.data.startswith('test_'))
def test_callback(call):
    lecture_number = int(call.data.split('_')[1])
    lecture = read_lecture(lecture_number)
    if lecture:
        questions = lecture['questions']
        if questions:
            # Инициализация сессии тестирования
            bot.send_message(call.message.chat.id, 'Начинаем тестирование...')
            send_question(call.message.chat.id, lecture_number, 0, questions, correct_answers=0)
        else:
            bot.send_message(call.message.chat.id, 'В этой лекции нет вопросов.')
    else:
        bot.send_message(call.message.chat.id, 'Файл лекции не найден. Убедитесь, что все файлы лекций находятся в правильной директории.')

def send_question(chat_id, lecture_number, question_index, questions, correct_answers):
    question = questions[question_index]
    markup = types.InlineKeyboardMarkup()
    for i, answer in enumerate(question['answers']):
        callback_data = f'answer_{lecture_number}_{question_index}_{i}_{correct_answers}'
        markup.add(types.InlineKeyboardButton(answer['option'], callback_data=callback_data))
    bot.send_message(
        chat_id,
        f'Вопрос {question_index + 1}: {question["question"]}',
        reply_markup=markup
    )

# Обработчик выбора ответа
@bot.callback_query_handler(func=lambda call: call.data.startswith('answer_'))
def answer_callback(call):
    try:
        data = call.data.split('_')
        lecture_number = int(data[1])
        question_index = int(data[2])
        answer_index = int(data[3])
        correct_answers = int(data[4])
    except ValueError:
        bot.send_message(call.message.chat.id, 'Произошла ошибка при обработке ответа.')
        return

    lecture = read_lecture(lecture_number)
    if lecture:
        questions = lecture['questions']
        question = questions[question_index]
        answer = question['answers'][answer_index]
        if answer['is_correct']:
            correct_answers += 1
            response = 'Правильно!'
        else:
            response = 'Неправильно.'
        bot.send_message(call.message.chat.id, response)

        if question_index + 1 < len(questions):
            send_question(call.message.chat.id, lecture_number, question_index + 1, questions, correct_answers)
        else:
            total_questions = len(questions)
            score_message = f'Вы прошли все вопросы.\n\nРезультат: {correct_answers} из {total_questions} правильных ответов.'
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Вернуться в меню', callback_data='back_to_main'))
            bot.send_message(call.message.chat.id, score_message, reply_markup=markup)
            # Обновление прогресса пользователя после прохождения теста
            update_user_progress(call.from_user.id, lecture_number=lecture_number, correct_answers=correct_answers, total_questions=total_questions)
    else:
        bot.send_message(call.message.chat.id, 'Файл лекции не найден. Убедитесь, что все файлы лекций находятся в правильной директории.')

# Обработчик кнопки "Прогресс"
@bot.callback_query_handler(func=lambda call: call.data == 'progress')
def progress_callback(call):
    user_id = call.from_user.id
    completed_lectures, total_tests, test_percentage = get_user_progress(user_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Вернуться в меню', callback_data='back_to_main'))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Прогресс:\nПройдено лекций: {completed_lectures}/{len(lectures)}\nПройдено тестов: {total_tests}\nПроцент правильных ответов: {test_percentage:.2f}%',
        reply_markup=markup
    )

bot.polling(none_stop=True)

##"dfngkdnf"
