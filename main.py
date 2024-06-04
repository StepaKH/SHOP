import subprocess
import time


# Функция для запуска бота и возвращения процесса
def start_bot(script_name):
    return subprocess.Popen(["python3", script_name])


# Запуск обоих ботов
bot1_process = start_bot("bot.py")
bot2_process = start_bot("bot2.py")

try:
    while True:
        # Проверка состояния первого бота
        if bot1_process.poll() is not None:
            print("Bot 1 has stopped. Restarting...")
            bot1_process = start_bot("bot.py")

        # Проверка состояния второго бота
        if bot2_process.poll() is not None:
            print("Bot 2 has stopped. Restarting...")
            bot2_process = start_bot("bot2.py")

        # Ожидание 5 минут перед следующей проверкой
        time.sleep(300)  # 300 секунд = 5 минут

except KeyboardInterrupt:
    print("Script interrupted")
    # Завершение обоих процессов, если скрипт main.py прерван
    bot1_process.terminate()
    bot2_process.terminate()
