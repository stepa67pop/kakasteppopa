from socket import *
from threading import Thread

clients = []
active_rooms = set()  # Храним список активных созданных комнат


def send_message_for_all(message, sender_socket):
    for client in clients:
        try:
            client.send(message.encode('utf-8'))
        except:
            if client in clients:
                clients.remove(client)


def accept_message(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            print(f"Get msg: {message}")
            if not message:
                break

            # Запрос списка публичных комнат
            if message == "GAME:TTT:GET_ROOMS":
                rooms_list = ",".join(active_rooms) if active_rooms else "EMPTY"
                client_socket.send(f"GAME:TTT:ROOMS_LIST:{rooms_list}".encode('utf-8'))

            # Регистрация новой созданной комнаты
            elif message.startswith("GAME:TTT:CREATE_ROOM:"):
                room_name = message.split(":")[3]
                active_rooms.add(room_name)
                # Уведомляем всех об обновлении списка комнат
                rooms_list = ",".join(active_rooms)
                send_message_for_all(f"GAME:TTT:ROOMS_LIST:{rooms_list}", client_socket)

            else:
                send_message_for_all(message, client_socket)
        except:
            break

    if client_socket in clients:
        clients.remove(client_socket)
    client_socket.close()


server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(("127.0.0.1", 7070))
server_socket.listen()
print("SERVER IS RUNNING")

while True:
    clients_socket, address = server_socket.accept()
    print(f"{address} is joined")
    clients.append(clients_socket)
    thread = Thread(target=accept_message, args=(clients_socket,), daemon=True)
    thread.start()