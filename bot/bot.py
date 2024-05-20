import sys
import logging
import re
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import os
from dotenv import load_dotenv
import paramiko
import subprocess
import psycopg2
from psycopg2 import Error

load_dotenv()
host = os.getenv('RM_HOST')
port = os.getenv('RM_PORT')
username = os.getenv('RM_USER')
password = os.getenv('RM_PASSWORD')

hostdb = os.getenv('DB_HOST')
portdb = os.getenv('DB_PORT')
dbname = os.getenv('DB_DATABASE')
usersql = os.getenv('DB_USER')


CHUNK_SIZE = 4000
TOKEN = os.getenv('TOKEN')

logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def prettyData(data):
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    return data

def useCommand(commandLine):
    global host, port, username, password
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(commandLine)
    data = stdout.read() + stderr.read()
    client.close()
    return data

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')

def helpCommand(update: Update, context):
    update.message.reply_text('Help!')

def findPhoneNumbersCommand(update: Update, context: CallbackContext):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'

def findPhoneNumbers (update: Update, context: CallbackContext):
    user_input = update.message.text

    phoneNumRegex = re.compile(r"(?:8|\+7)[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}")

    phoneNumberList = phoneNumRegex.findall(user_input) 

    if not phoneNumberList: 
        update.message.reply_text('Телефонные номера не найдены')
        return 
    
    phoneNumbers = '' 
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n' 
        
    update.message.reply_text(phoneNumbers)

    context.user_data['phone_numbers'] = phoneNumberList

    update.message.reply_text('Хотите добавить найденные номера в базу данных? (да/нет)')

    return 'add_number_db'

def add_number_db(update: Update, context: CallbackContext):
    user_input = update.message.text
    if user_input == 'да':
        phoneNumbers = context.user_data.get('phone_numbers')
        global usersql, password, hostdb, portdb, dbname
        connection = None
        try:
            connection = psycopg2.connect(user=usersql, password=password, 
                                        host=hostdb, port=portdb, database=dbname)
            cursor = connection.cursor()
            for number in phoneNumbers:
                cursor.execute("INSERT INTO Phones (phone) VALUES (%s);", (number, ))
            connection.commit()
            update.message.reply_text('Номера были успешно добавленны в базу данных.')
    
        except (Exception, Error) as error:
            update.message.reply_text(f'Ошибка при добавлении в базу данных: {error}')
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
        
    else:
        update.message.reply_text("Данные не были добавлены в базу данных.")

    return ConversationHandler.END

def findEmailCommand(update: Update, context: CallbackContext):
    update.message.reply_text('Введите текст для поиска email-адресов: ')

    return 'find_email'

def findEmail (update: Update, context: CallbackContext):
    user_input = update.message.text

    emailRegex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    emailList = emailRegex.findall(user_input) 

    if not emailList: 
        update.message.reply_text('Email-адреса не найдены')
        return 
    
    emails = '' 
    for i in range(len(emailList)):
        emails += f'{i+1}. {emailList[i]}\n' 
        
    update.message.reply_text(emails)
    context.user_data['emails'] = emailList
    update.message.reply_text('Хотите добавить найденные emails в базу данных? (да/нет)')
    return 'add_email_db'

def add_email_db(update: Update, context: CallbackContext):
    user_input = update.message.text
    if user_input == 'да':
        emails = context.user_data.get('emails')
        global usersql, password, hostdb, portdb, dbname
        connection = None
        try:
            connection = psycopg2.connect(user=usersql, password=password, 
                                        host=hostdb, port=portdb, database=dbname)
            cursor = connection.cursor()
            for email in emails:
                cursor.execute("INSERT INTO Emails (email) VALUES (%s);", (email, ))
            connection.commit()
            update.message.reply_text('Электронные адреса были успешно добавленны в базу данных.')
    
        except (Exception, Error) as error:
            update.message.reply_text(f'Ошибка при добавлении в базу данных: {error}')
        finally:
            if connection is not None:
                cursor.close()
                connection.close()

    else:
        update.message.reply_text("Данные не были добавлены в базу данных.")

    return ConversationHandler.END

def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите ваш пароль для проверки сложности: ')
    return 'verify_password'

def verifyPassword (update: Update, context):
    user_input = update.message.text

    passwordRegex = re.compile(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()])(?!.*[^A-Za-z\d!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}$')

    passwordList = passwordRegex.findall(user_input) 

    if not passwordList: 
        update.message.reply_text('Пароль простой')
        return 
        
    update.message.reply_text('Пароль сложный')
    return ConversationHandler.END 

def echo(update: Update, context):
    update.message.reply_text(update.message.text)

def get_release(update: Update, context):
    data = useCommand('lsb_release -a')
    data = prettyData(data)
    update.message.reply_text(data)

def get_uname(update: Update, context):
    data1 = prettyData(useCommand('uname -m'))
    data2 = prettyData(useCommand('uname -n'))
    data3 = prettyData(useCommand('uname -r'))
    update.message.reply_text('Архитектура процессора: ' + data1 + 'Имя хоста системы: ' + data2 + 'Версия ядра: ' + data3)

def get_uptime(update: Update, context):
    data = prettyData(useCommand('uptime'))
    update.message.reply_text(data)

def get_df(update: Update, context):
    data = prettyData(useCommand('df -h'))
    update.message.reply_text(data)

def get_free(update: Update, context):
    data = prettyData(useCommand('free -h'))
    update.message.reply_text(data)

def get_mpstat(update: Update, context):
    data = prettyData(useCommand('mpstat'))
    update.message.reply_text(data)

def get_w(update: Update, context):
    data = prettyData(useCommand('w'))
    update.message.reply_text(data)

def get_auths(update: Update, context):
    data = prettyData(useCommand('last -n 10'))
    update.message.reply_text(data)

def get_critical(update: Update, context):
    data = prettyData(useCommand('tail -n 5 /var/log/syslog'))
    update.message.reply_text(data)

def get_ps(update: Update, context):
    data = prettyData(useCommand('ps'))
    update.message.reply_text(data)

def get_ss(update: Update, context):
    data = prettyData(useCommand('ss -tuln'))
    update.message.reply_text(data)

def get_services(update: Update, context):
    data = prettyData(useCommand('systemctl list-units --type=service --state=running'))
    update.message.reply_text(data)

def get_apt_list(update: Update, context):
    message = update.message
    
    if len(message.text.split()) > 1:
        package_name = message.text.split()[1]
        data = prettyData(useCommand(f'dpkg -l | grep {package_name}'))
        
    else:
        chunks = []
        start = 0
        data = prettyData(useCommand("dpkg -l | awk '{print $2}'"))
        while start < len(data):
            end = min(start + CHUNK_SIZE, len(data))
            if end < len(data) and data[end] != '\n':
                while end > start and data[end] != '\n':
                    end -= 1
            chunks.append(data[start:end])
            start = end
    
        for chunk in chunks:
            update.message.reply_text(chunk)

        
    update.message.reply_text(data)

def get_repl_logs(update: Update, context: CallbackContext):
    log_file_path = "/var/log/postgresql/postgresql.log"
    grep_command = f'cat {log_file_path} | grep "replica"'

    try:
        result = subprocess.run(grep_command, shell=True, capture_output=True, text=True, check=True)
        data = result.stdout
    except subprocess.CalledProcessError as e:
        data = e.output if e.output else e.stderr
        if not data.strip():
            data = "No replica logs found."

    data = prettyData(data)
    update.message.reply_text(data)

def get_emails(update: Update, context):
    global usersql, password, hostdb, portdb, dbname
    connection = None
    try:
        connection = psycopg2.connect(user=usersql, password=password, 
                                      host=hostdb, port=portdb, database=dbname)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Emails;")
        data = cursor.fetchall()
        update.message.reply_text(data)
  
    except (Exception, Error) as error:
         logging.error("%(asctime)s - %(name)s - %(levelname)s - %(error)s")
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def get_phone_numbers(update: Update, context):
    global usersql, password, hostdb, portdb, dbname
    connection = None
    try:
        connection = psycopg2.connect(user=usersql, password=password, 
                                      host=hostdb, port=portdb, database=dbname)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Phones;")
        data = cursor.fetchall()
        update.message.reply_text(data)
  
    except (Exception, Error) as error:
        logging.error("%(asctime)s - %(name)s - %(levelname)s - %(error)s")
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'add_number_db': [MessageHandler(Filters.text & ~Filters.command, add_number_db)]
        },
        fallbacks=[]
    )

    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'add_email_db' : [MessageHandler(Filters.text & ~Filters.command, add_email_db)]
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )
		
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler("get_apt_list", get_apt_list))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
