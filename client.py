import socket
import sys

class MessengerClient:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.user_id = None
        self.target_id = None
        self.socket = None

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def send_command(self, cmd, *lines):
        try:
            self.socket.send(f"{cmd}\n".encode('utf-8'))
            for line in lines:
                self.socket.send(f"{line}\n".encode('utf-8'))
            return True
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            return False

    def recv_line(self):
        data = b''
        while True:
            chunk = self.socket.recv(1)
            if not chunk:
                return None
            if chunk == b'\n':
                break
            data += chunk
        return data.decode('utf-8')

    def get_history(self):
        if not self.socket:
            return []
        if not self.send_command("GET_HISTORY", self.user_id, self.target_id):
            return []
        response_line = self.recv_line()
        if response_line is None:
            print("Сервер разорвал соединение.")
            return []
        if response_line.startswith("ERROR"):
            print("Ошибка получения истории:", response_line)
            return []
        parts = response_line.split()
        if len(parts) != 2 or parts[0] != "OK":
            print("Неожиданный ответ:", response_line)
            return []
        count = int(parts[1])
        history = []
        for _ in range(count):
            line = self.recv_line()
            if line is None:
                break
            if '|' in line:
                from_id, text = line.split('|', 1)
                history.append({'from_id': from_id, 'text': text})
        return history

    def send_message(self, text):
        if not text.strip():
            return False
        if not self.send_command("SEND_MESSAGE", self.user_id, self.target_id, text):
            return False
        response = self.recv_line()
        return response == "OK"

    def show_history(self):
        print("\n--- История сообщений ---")
        history = self.get_history()
        if not history:
            print("Нет сообщений")
        else:
            for msg in history:
                if msg['from_id'] == self.user_id:
                    print(f"Вы: {msg['text']}")
                else:
                    print(f"{msg['from_id']}: {msg['text']}")
        print("--------------------------\n")

    def run_chat(self):
        if not self.connect():
            print("Не удалось подключиться к серверу.")
            return

        print(f"Чат с {self.target_id}. Введите сообщение (или команду /history, /exit)")
        while True:
            try:
                msg = input("> ").strip()
                if not msg:
                    continue
                if msg == "/history":
                    self.show_history()
                elif msg == "/exit":
                    break
                else:
                    if self.send_message(msg):
                        self.show_history()
                    else:
                        print("Не удалось отправить сообщение.")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Ошибка: {e}")
                break

        self.close()

    def close(self):
        if self.socket:
            self.socket.close()

def main():
    print("=== Консольный мессенджер ===")
    host = input("Введите IP сервера (по умолчанию 127.0.0.1): ").strip()
    if not host:
        host = '127.0.0.1'
    port = input("Введите порт (по умолчанию 5555): ").strip()
    if not port:
        port = 5555
    else:
        port = int(port)

    client = MessengerClient(host, port)

    client.user_id = input("Ваш ID: ").strip()
    if not client.user_id:
        print("ID не может быть пустым.")
        return

    client.target_id = input("ID собеседника: ").strip()
    if not client.target_id:
        print("ID собеседника не может быть пустым.")
        return

    client.run_chat()

if __name__ == "__main__":
    main()
