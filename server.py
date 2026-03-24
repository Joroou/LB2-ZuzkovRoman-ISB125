import socket
import threading
import os
import signal
import sys

HISTORY_FILE = "messages.txt"

class MessageServer:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        self.messages = self.load_messages()

    def load_messages(self):
        messages = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split('|', 2)
                        if len(parts) == 3:
                            messages.append({
                                'from_id': parts[0],
                                'to_id': parts[1],
                                'text': parts[2]
                            })
        return messages

    def save_messages(self):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            for msg in self.messages:
                f.write(f"{msg['from_id']}|{msg['to_id']}|{msg['text']}\n")

    def get_chat_history(self, user_id, target_id):
        history = []
        for msg in self.messages:
            if (msg['from_id'] == user_id and msg['to_id'] == target_id) or \
               (msg['from_id'] == target_id and msg['to_id'] == user_id):
                history.append(msg)
        return history

    def add_message(self, from_id, to_id, text):
        message = {'from_id': from_id, 'to_id': to_id, 'text': text}
        self.messages.append(message)
        self.save_messages()
        return message

    def recv_line(self, sock):
        """Читает строку из сокета до символа \n."""
        data = b''
        while True:
            chunk = sock.recv(1)
            if not chunk:
                return None
            if chunk == b'\n':
                break
            data += chunk
        return data.decode('utf-8')

    def handle_client(self, client_socket, addr):
        print(f"Клиент {addr} подключен")
        try:
            while self.running:
                command_line = self.recv_line(client_socket)
                if command_line is None:
                    break
                command = command_line.strip().upper()
                if not command:
                    continue

                if command == 'GET_HISTORY':
                    # ожидаем две строки: user_id и target_id
                    user_id = self.recv_line(client_socket)
                    target_id = self.recv_line(client_socket)
                    if user_id is None or target_id is None:
                        break
                    user_id = user_id.strip()
                    target_id = target_id.strip()
                    history = self.get_chat_history(user_id, target_id)
                    response = f"OK {len(history)}\n"
                    for msg in history:
                        response += f"{msg['from_id']}|{msg['text']}\n"
                    client_socket.send(response.encode('utf-8'))

                elif command == 'SEND_MESSAGE':
                    # ожидаем три строки: from_id, to_id, text
                    from_id = self.recv_line(client_socket)
                    to_id = self.recv_line(client_socket)
                    text = self.recv_line(client_socket)
                    if from_id is None or to_id is None or text is None:
                        break
                    from_id = from_id.strip()
                    to_id = to_id.strip()
                    text = text.strip()
                    if text:
                        self.add_message(from_id, to_id, text)
                        client_socket.send(b"OK\n")
                    else:
                        client_socket.send(b"ERROR Empty message\n")

                else:
                    client_socket.send(b"ERROR Unknown command\n")
        except Exception as e:
            print(f"Ошибка при обработке клиента {addr}: {e}")
        finally:
            client_socket.close()
            print(f"Клиент {addr} отключен")

    def start(self):
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        print(f"Сервер запущен на {self.host}:{self.port}")

        def signal_handler(sig, frame):
            print("\nПолучен сигнал завершения. Останавливаем сервер...")
            self.running = False
            self.server.close()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        while self.running:
            try:
                client_socket, addr = self.server.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_thread.daemon = True
                client_thread.start()
            except OSError:
                break
        print("Сервер остановлен.")

if __name__ == "__main__":
    server = MessageServer()
    server.start()
