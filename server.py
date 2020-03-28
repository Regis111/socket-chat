import socket
import threading
import os
import json

IP = '127.0.0.1'
PORT = 4444


class ClientThread:
    def __init__(self, nick, socket, server):
        self.nick = nick
        self.socket = socket
        self.server = server

    def __str__(self):
        return f'Client {self.nick} ' \
            f'with tcp address: {self.socket.getpeername()}'

    def handle_client(self):
        while True:
            msg = self.socket.recv(100).decode('utf-8')
            if msg == 'exit':
                self.exit()
                return
            self.server.broadcast(msg, self.nick)

    def exit(self):
        print(f'client {self.nick} exit')
        self.socket.close()
        del self.server.clients[self.nick]

    def run(self):
        threading.Thread(target=self.handle_client, daemon=True).start()


class ServerTCP:
    def __init__(self):
        self.clients = {}

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((IP, PORT))
        self.socket.listen()

    def handle_connections(self):
        print('TCP# enter handle_connections')
        while True:
            try:
                client_socket, _ = self.socket.accept()
            except KeyboardInterrupt:
                self.kill_server()
            print('TCP# after tcp connect')
            threading.Thread(
                target=self.init_client, args=(client_socket,)).start()

    def init_client(self, client_socket):
        while True:
            nick = client_socket.recv(20).decode('utf-8')
            if nick == 'exit':
                return
            if nick in self.clients.keys():
                print('Not Correct nick :(')
                client_socket.send(bytes(f'NO', 'utf-8'))
            else:
                print('Correct nick :D')
                client_socket.send(bytes(f'YES', 'utf-8'))
                break

        new_client = ClientThread(nick, client_socket, self)
        print(f'TCP# {new_client} just logged')
        new_client.run()
        self.clients[nick] = new_client

    def kill_server(self):
        print('server got KeyboardInterrupt, stopping...')
        for client_nick, client in self.clients.items():
            client.socket.send(bytes('exit', 'utf-8'))
            client.socket.close()
        self.socket.close()
        os._exit(0)

    def broadcast(self, message, sender_nick):
        print(f'TCP# {sender_nick} sends TCP broadcast with {message}')
        for client_nick, client in self.clients.items():
            if client_nick != sender_nick:
                data = f'TCP# {sender_nick}: {message}'
                client.socket.send(bytes(data, 'utf-8'))
                print(f'TCP# Message sent from {sender_nick} to {client_nick}')

    def run(self):
        threading.Thread(target=self.handle_messages, daemon=True).start()


class ServerUDP:
    def __init__(self):
        self.clients = {}

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((IP, PORT))

    def handle_messages(self):
        print('UDP# enter handle_messages')
        while True:
            message, address = self.socket.recvfrom(100)

            message = json.loads(message)
            nick = message['nick']
            data = message['data']

            if data == 'exit':
                del self.clients[nick]
                continue
            elif data == 'init':
                self.clients[nick] = address
                continue

            self.broadcast(data, nick)

    def broadcast(self, message, sender_nick):
        print(f'UDP# {sender_nick} sends broadcast {message}')
        print(f'UDP# clients: {self.clients.values()}')
        for client_nick, client_address in self.clients.items():
            if client_nick != sender_nick:
                data = f'UDP# {sender_nick}: {message}'
                self.socket.sendto(bytes(data, 'utf-8'), client_address)
                print(f'UDP# Message sent from server to {client_nick}')

    def run(self):
        threading.Thread(
            target=self.handle_messages, daemon=True).start()


ServerUDP().run()
ServerTCP().handle_connections()
