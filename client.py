import socket
import threading
import select
import os
import json
import struct

class Client:
    PORT = 4444
    SERVER_ADDRESS = ('127.0.0.1', PORT)
    MULTICAST_GRP = '224.0.0.1'

    def __init__(self):
        """ initialize all sockets and client's nick"""
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.mcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        mreq = struct.pack('4sl', socket.inet_aton(self.MULTICAST_GRP), socket.INADDR_ANY)
        self.mcast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.mcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mcast_socket.bind((self.MULTICAST_GRP, self.PORT))

        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.connect(self.SERVER_ADDRESS)

        self.nick = self.init_nick()

        init = json.dumps({'nick': self.nick, 'data': 'init'})
        self.udp_socket.sendto(bytes(init, 'utf-8'), self.SERVER_ADDRESS)
    
    def init_nick(self):
        while True:
            try:
                nick = input('Enter your nick: ')
            except KeyboardInterrupt:
                self.tcp_socket.send(bytes('exit', 'utf-8'))
                self.exit()

            self.tcp_socket.send(bytes(nick, 'utf-8'))
            msg = self.tcp_socket.recv(20).decode('utf-8')
            if msg == 'YES':
                print('Correctly added to server')
                return nick
            elif msg == 'NO':
                print('This nick is already used, try again')

    def send(self):
        while True:
            try:
                data = input('')
            except KeyboardInterrupt:
                self.tcp_socket.send(bytes('exit', 'utf-8'))
                exit = json.dumps({'nick': self.nick, 'data': 'exit'})
                self.udp_socket.sendto(bytes(exit, 'utf-8'), self.SERVER_ADDRESS)
                self.exit()

            if data == 'U':
                send_data = input()
                msg = json.dumps({'nick': self.nick, 'data': send_data})
                self.udp_socket.sendto(bytes(msg, 'utf-8'), self.SERVER_ADDRESS)
            elif data == 'M':
                send_data = input()
                send_data = json.dumps({'nick': self.nick, 'data': f'MCAST# {self.nick}:{send_data}'})
                self.mcast_socket.sendto(bytes(send_data, 'utf-8'), (self.MULTICAST_GRP, self.PORT))
            else:
                self.tcp_socket.send(bytes(data, 'utf-8'))

            if data == 'exit':
                self.exit()

    def receive(self):
        while True:
            read_connections, _, _ = \
                select.select([self.tcp_socket, self.udp_socket, self.mcast_socket], [], [])
            if self.tcp_socket in read_connections:
                message = self.tcp_socket.recv(100).decode('utf-8')
                if message == 'exit':
                    print('Got exit from server')
                    self.exit()
                print(message)
            if self.udp_socket in read_connections:
                message, _ = self.udp_socket.recvfrom(100)
                print(message.decode('utf-8'))
            if self.mcast_socket in read_connections:
                message, _ = self.mcast_socket.recvfrom(100)
                message = json.loads(message)
                if message['nick'] != self.nick:
                    print(message['data'])

    def run(self):
        threading.Thread(target=self.receive, daemon=True).start()
        self.send()

    def exit(self):
        print('client ending his life...')
        self.tcp_socket.close()
        self.udp_socket.close()
        os._exit(0)


Client().run()
