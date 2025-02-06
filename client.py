import socket
import threading

def receive_messages(client_socket):
    """Функция для получения и отображения сообщений от других клиентов."""
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print("Новое сообщение:", message)
        except Exception as e:
            print(f"Произошла ошибка при получении сообщения: {e}")
            break

def main():
    # Настройка сокета для подключения к серверу
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('192.168.1.145', 12345))  # Подключение к серверу

    # Запрашиваем AUIN пользователя
    my_auin = input("Введите ваш AstroUIN: ")
    client_socket.send(my_auin.encode('utf-8'))  # Отправляем серверу свой AUIN

    # Получение ответа от сервера
    response = client_socket.recv(1024).decode('utf-8')
    print(response)  # Печатаем ответ сервера

    # Проверяем, надо ли регистрироваться
    if "Хотите зарегистрировать ваш AstroUIN?" in response:
        register_decision = input("Введите 'Да' для регистрации или 'нет' для отмены: ")
        client_socket.send(register_decision.encode('utf-8'))  # Отправляем решение серверу
        response = client_socket.recv(1024).decode('utf-8')  # Получаем ответ
        print(response)  # Печатаем новый AUIN или сообщение об отмене

    # Если AUIN существует, продолжаем общение
    if "Ваш новый AstroUIN зарегистрирован" in response or "Добро пожаловать!" in response:
        # Запускаем поток для получения сообщений
        threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()

        # Запрашиваем AUIN собеседника один раз
        interlocutor_auin = input("Введите AstroUIN собеседника: ")

        while True:
            try:
                message = input(f"Введите сообщение для {interlocutor_auin} (или 'exit' для выхода): ")
                if message.lower() == 'exit':
                    break

                full_message = f"{interlocutor_auin}:{message}"
                client_socket.send(full_message.encode('utf-8'))

                # Не ждем ответа, так как поток получения сообщений будет обрабатывать их
            except Exception as e:
                print(f"Произошла ошибка: {e}")
                break

    # Закрываем сокет при выходе
    client_socket.close()

if __name__ == "__main__":
    main()