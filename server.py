import socket
import threading
import numpy as np
import time


class Server:
    def __init__(self):
        bind_ip = '0.0.0.0'
        bind_port = 1729

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((bind_ip, bind_port))
        server.listen(2)  # max backlog of connections

        self.clientslist = []
        i = 0

        print('Listening on {}:{}'.format(bind_ip, bind_port))
        print('waiting for connection...')
        while True:
            client, address = server.accept()
            print('%s:%s has connected.' % address)
            self.clientslist.append(client)
            t = threading.Thread(target=self.new_client, args=[i])
            t.start()

            i += 1


    def new_client(self, index):
        '''
        Loop that recieves and sends landmarks from the clients.
        :param index: index of the client in the list
        :return: if connection closed return
        '''
        while len(self.clientslist) < 2:
            time.sleep(0.5)

        # send client index to the client
        try:
            self.clientslist[index].send(str(index).encode())
        except Exception:
            print('Client connection closed')
            return

        # recieving from client the ip
        data = self.clientslist[index].recv(1024)

        time.sleep(0.5)

        # send other client the ip of the client
        if index == 1:
            try:
                self.clientslist[0].send(data)
            except Exception:
                print('Client connection closed')
                return
        if index == 0:
            try:
                self.clientslist[1].send(data)
            except Exception:
                print('Client connection closed')
                return


        # loop recieving and sending landmarks list from one client to the other
        while True:
            try:
                data = self.clientslist[index].recv(1024)
            except Exception:
                print('Client connection closed')
                return
            if index == 1:
                try:
                    self.clientslist[0].send(data)
                except Exception:
                    print('Client connection closed')
                    return
            if index == 0:
                try:
                    self.clientslist[1].send(data)
                except Exception:
                    print('Client connection closed')
                    return


if __name__ == '__main__':
    Server()

