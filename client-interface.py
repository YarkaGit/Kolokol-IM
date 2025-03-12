import socket
import threading
import random
import string
import os
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, Listbox, Frame, Button

def generate_random_auin(length=10):
    """Генерация случайного AUIN заданной длины."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Kolokol")
        self.master.geometry("350x300")  # Установка размера окна

        # Путь к иконке
        current_directory = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_directory, 'icon.ico')  # Укажите имя вашего файла иконки
        self.master.iconbitmap(icon_path)  # Установка иконки

        self.client_socket = None
        self.my_auin = ''

        # Кнопка подключения
        self.connect_button = tk.Button(master, text="Подключиться/Connect", command=self.connect)
        self.connect_button.pack(pady=10)

        # Контакт-лист
        self.contact_listbox = Listbox(master)
        self.contact_listbox.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Frame для кнопок
        button_frame = Frame(master)
        button_frame.pack(pady=5)

        # Кнопка открытия чата
        self.open_chat_button = Button(button_frame, text="Открыть чат/Open Chat", command=self.open_chat, state=tk.DISABLED)
        self.open_chat_button.pack(side=tk.LEFT, padx=5)

        # Кнопка добавления контакта
        self.add_contact_button = Button(button_frame, text="Добавить контакт/Add Contact", command=self.add_contact, state=tk.DISABLED)
        self.add_contact_button.pack(side=tk.LEFT, padx=5)

        # Проверка наличия файла контактов
        self.contacts_file = "contacts.dat"
        if not os.path.exists(self.contacts_file):
            with open(self.contacts_file, "w") as f:
                pass  # Создание пустого файла, если он отсутствует

    def load_contacts(self):
        """Загрузка контактов из файла contacts.dat."""
        self.contact_listbox.delete(0, tk.END)  # Очистка списка перед загрузкой
        try:
            with open(self.contacts_file, "r") as f:
                lines = f.readlines()

            auin_found = False  # Флаг для проверки, найден ли AUIN
            contactlist_end_found = False  # Флаг для проверки, найден ли конец контакт-листа

            # Проверка существующих контактов и добавление их в список
            for line in lines:
                line = line.strip()  # Убираем пробелы в начале и конце строки

                # Проверка на конец контакт-листа
                if line == "contactlist_end":
                    contactlist_end_found = True
                    break  # Прерываем цикл, если нашли конец контакт-листа

                # Сравниваем с AUIN текущего пользователя
                if line == self.my_auin:
                    auin_found = True
                    continue  # Пропускаем строку с AUIN

                if auin_found:  # Если AUIN уже найден, загружаем контакты
                    self.contact_listbox.insert(tk.END, line)  # Добавляем контакты в список

            # Если конец контакт-листа не был найден, добавляем его
            if not contactlist_end_found:
                with open(self.contacts_file, "a") as f:  # Открываем файл в режиме добавления
                    f.write("contactlist_end\n")  # Добавляем метку конца контакт-листа

        except FileNotFoundError:
            # Если файл не найден, создаем новый файл с AUIN и добавляем конец контакт-листа
            with open(self.contacts_file, "w") as f:
                f.write(self.my_auin + "\n")
                f.write("contactlist_end\n")  # Обязательно добавляем конец контакт-листа

    def add_contact(self, new_contact):
        # Считываем текущий контакт-лист
        try:
            with open(self.contacts_file, "r") as f:
                lines = f.readlines()

            # Проверяем, есть ли уже конец контакт-листа
            contactlist_end_found = False
            for line in lines:
                if line.strip() == "contactlist_end":
                    contactlist_end_found = True
                    break

            # Если конец контакт-листа не найден, добавляем его
            if not contactlist_end_found:
                lines.append("contactlist_end\n")

            # Находим индекс строки "contactlist_end"
            end_index = lines.index("contactlist_end\n")

            # Добавляем новый контакт сразу перед "contactlist_end"
            lines.insert(end_index, new_contact + "\n")

        except FileNotFoundError:
            # Если файла нет, создаем новый и добавляем контакт и конец
            lines = [self.my_auin + "\n", new_contact + "\n", "contactlist_end\n"]

        # Записываем все обратно в файл
        with open(self.contacts_file, "w") as f:
            f.writelines(lines)

    def connect(self):
        """Подключение к серверу."""
        try:
            # Используем параметры из настроек
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(("192.168.1.145", 12345))  # Используем ip и порт

            # Получение и отправка AUIN
            self.my_auin = self.get_auin()
            self.client_socket.send(self.my_auin.encode('utf-8'))

            # Получение ответа от сервера
            response = self.client_socket.recv(1024).decode('utf-8')
            self.append_message(response)

            # Проверка на необходимость регистрации AUIN
            if "Хотите зарегистрировать ваш AstroUIN?" in response:
                self.register_auin()

            # Проверяем, зарегистрирован ли AUIN
            if self.my_auin and response:
                if "зарегистрирован" in response or "Добро пожаловать!" in response:  # Подтверждение успешной регистрации
                    self.connect_button.pack_forget()  # Скрыть кнопку подключения
                    self.load_contacts()  # Загрузить контакты после подключения
                    self.add_contact_button.config(state=tk.NORMAL)  # Активировать кнопку добавления контакта
                    self.open_chat_button.config(state=tk.NORMAL)  # Разблокировать кнопку открытия чата

                    # Запускаем поток для получения сообщений
                    threading.Thread(target=self.receive_messages, daemon=True).start()
                else:
                    messagebox.showwarning("KlID не зарегистрирован/KlID is not registered.",
                                           "Регистрация отменена/Registration cancelled.")
                    self.client_socket.close()  # Закрываем сокет, если AUIN неправильный

        except Exception as e:
            messagebox.showerror("Ошибка/Error", f"Не удалось подключиться/Failed to connect: {e}")

    def get_auin(self):
        """Получение AUIN от пользователя."""
        return simpledialog.askstring("KlID", "Введите ваш KlID/Input your KlID:")

    def register_auin(self):
        """Регистрация AUIN."""
        register_decision = simpledialog.askstring("Регистрация/Registration", "Введите 'yes' для регистрации или "
                                                                               "'no' для отмены/Input 'yes' for "
                                                                               "registration or 'no' for cancel.:")
        self.client_socket.send(register_decision.encode('utf-8'))

        if register_decision.lower() == 'yes':
            self.my_auin = generate_random_auin()
            self.client_socket.send(self.my_auin.encode('utf-8'))

    def receive_messages(self):
        """Получение сообщений от сервера."""
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    self.append_message(f"Новое сообщение/New Message: {message}")
                else:
                    break
            except Exception as e:
                self.append_message(f"Ошибка при получении сообщения/Error getting message: {e}")
                break

    def append_message(self, message):
        """Добавление сообщения в текстовое поле."""
        messagebox.showinfo("Сообщение/Message", message)  # Для упрощения вывода сообщений

    def open_chat(self):
        """Открытие нового окна для общения с выбранным контактом."""
        selected_contact = self.contact_listbox.get(tk.ACTIVE)
        if selected_contact:
            chat_window = ChatWindow(self.client_socket, selected_contact)

class ChatWindow:
    def __init__(self, socket, contact):
        self.socket = socket
        self.contact = contact

        self.chat_window = tk.Toplevel()
        self.chat_window.title(f"Чат с/Chat with {self.contact}")

        self.text_area = scrolledtext.ScrolledText(self.chat_window, state='disabled')
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.input_field = tk.Entry(self.chat_window)
        self.input_field.pack(fill=tk.X, padx=10, pady=10)
        self.input_field.bind("<Return>", self.send_message)

    def send_message(self, event=None):
        """Отправка сообщения собеседнику."""
        message = self.input_field.get()
        if message:
            full_message = f"{self.contact}: {message}"
            self.socket.send(full_message.encode('utf-8'))
            self.append_message(f"Вы/You: {message}")
            self.input_field.delete(0, tk.END)

    def append_message(self, message):
        """Добавление сообщения в текстовое поле чата."""
        self.text_area.config(state='normal')
        self.text_area.insert(tk.END, message + "\n")
        self.text_area.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    chat_client = ChatClient(root)
    root.mainloop()