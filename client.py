import socket
import dlib
import cv2
import numpy as np
from tkinter import *
import threading
from vidstream import AudioReceiver
from vidstream import AudioSender


class Client:

    def __init__(self):

        self.sender = None
        self.reciever = None
        self.cam1 = None
        self.my_socket = None
        self.canvas = None

        # defining DLIB detectors (face and landmarks)
        self.predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
        self.detector = dlib.get_frontal_face_detector()

        self.landmarks = None

        self.root = Tk()
        self.root.geometry("1000x800")

        self.m = Menu(self.root, self)


        self.root.mainloop()


    def continue1(self, my_socket):
        '''
        Destroy the menu socket and create new socket for the chat.
        Creates the audio threads of the audio sender and the reciever
        defines ports by data from server and sets the connection
        :param my_socket: menu socket to destroy and recreate
        :return:
        '''
        self.my_socket = my_socket
        self.root.destroy()
        print('waiting for other client')

        # recieving from the server index of client from server to set the ports
        try:
            data = self.my_socket.recv(1024).decode()
        except Exception:
            print('Server closed')
            return
        print(data)
        if data is '0':
            port1 = 5555
            port2 = 9999
        else:
            port1 = 9999
            port2 = 5555

        # sending this client ipv4 to the server
        self.my_socket.send(socket.gethostbyname(socket.gethostname()).encode())

        # recieving from server the ip of the other client
        try:
            ip = self.my_socket.recv(1024).decode()
        except Exception:
            print('Server closed')
            return
        print(ip)

        # Audio reciever and sender threads setup, and start
        self.sender = AudioSender(ip, port1)
        sender_thread = threading.Thread(target=self.sender.start_stream())

        self.reciever = AudioReceiver(socket.gethostbyname(socket.gethostname()), port2)
        recieve_thread = threading.Thread(target=self.reciever.start_server())

        recieve_thread.start()
        sender_thread.start()


        # Starting webcam capture (640*480)
        self.cam1 = cv2.VideoCapture(self.m.getvariable())
        print('starting cam')

        self.root = Tk()
        self.root.geometry("300x300")
        self.root.title('Chat1')
        self.canvas = Canvas(self.root, width=300, height=300)
        self.canvas.pack()

        self.root.after(1, self.run())

        self.root.mainloop()

    def run(self):
        '''
        Sends and recieves the landmarks (sends what returned from find_landmarks and recieves from socket)
        This function loops forever.
        '''
        print("1")
        # Getting the landmarks and making them byte string, if didn't find face encoding the message noface
        landmarks = self.find_landmarks()
        if landmarks is 'noface':
            landmarks = landmarks.encode()
        else:
            landmarks = landmarks.tostring()
        print('2')

        # sending the landmarks string to the server
        try:
            self.my_socket.send(landmarks)
        except Exception:
            print('Server closed')
            self.sender.stop_stream()
            self.reciever.stop_server()
            self.root.destroy()
            return
        print('3')

        # recieving from the server the landmarks of the other client
        try:
            data = self.my_socket.recv(1024)
        except Exception:
            print('Server closed')
            self.sender.stop_stream()
            self.reciever.stop_server()
            self.root.destroy()
            return

        # if decoding works that means its a string, which is 'noface' if it doesnt its the numpy array of coords
        try:
            data = data.decode()
        except Exception:
            self.landmarks = np.fromstring(data, dtype=int).reshape(68, 2)
            # drawing them on the canvas
            self.updatecanvas()
        print('4')

        self.root.after(1, self.run())

    def find_landmarks(self):
        '''
        Finds and returns the face landmark points. If can't detect a face returns 'noface'.
        '''
        gray = self.getgrayimg()
        facerec = self.findfacerec(gray)
        if facerec is 'Error':
            return 'noface'

        # taking only the face from the full picture
        top, bottom = max(facerec.top() - 20, 0), min(facerec.bottom() + 30, 500)
        left, right = max(facerec.left() - 20, 0), min(facerec.right() + 20, 500)
        gray = gray[top:bottom, left:right]

        gray = cv2.resize(gray, (300, 300))

        # detecting a face from the new to get the right coords
        facerec = self.findfacerec(gray)
        if facerec is 'Error':
            return 'noface'

        # Detecting the face cords and converting them to numpy array
        shape = self.predictor(gray, facerec)
        shape = self.shape_to_np(shape)

        return shape

    def getgrayimg(self):
        '''
        Returns gray img from webcam
        '''
        # ret will get true or false and img will get the image from video captured
        ret_val, img = self.cam1.read()

        # converting to grey
        # img = cv2.flip(img, 1) not need but sometimes better
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return gray

    def findfacerec(self, gray):
        '''
        Returns dlib face rectangle, if there isn't one returns 'Error'
        '''
        # detecting a face
        facerec1 = self.detector(gray, 1)
        try:
            facerec = facerec1[0]
        except Exception:
            return 'Error'
        return facerec

    def shape_to_np(self, shape, dtype="int"):
        '''
        Takes Shape object from dlib face landmark detector and returns numpy array of the coordinates
        '''
        # initialize the list of (x, y)-coordinates
        coords = np.zeros((68, 2), dtype=dtype)
        # loop over the 68 facial landmarks and convert them to a 2-tuple of (x, y)-coordinates
        for i in range(0, 68):
            coords[i] = (shape.part(i).x, shape.part(i).y)
        return coords

    def updatecanvas(self):
        '''
        Resets the canvas and updating it with the face of the new coords
        '''
        # reseting canvas (add this before calling the draw shapes)
        self.canvas.delete('all')

        self.draw_shape(True, 37, 42)
        self.draw_shape(True, 43, 48)
        self.draw_shape(False, 1, 17)
        self.draw_shape(True, 18, 22)
        self.draw_shape(True, 23, 27)
        self.draw_shape(True, 37, 42)
        self.draw_shape(False, 28, 31)
        self.draw_shape(True, 32, 36)
        self.draw_shape(True, 49, 60)
        self.draw_shape(True, 61, 68)

        self.canvas.update()

    def draw_shape(self, endline, startn, endn):
        '''
        Draws the face part by given args: which landmarks and if to close the part
        by line between first and last landmark
        '''
        startn -= 1
        # endn -= 1
        for x in range(startn, endn):
            # canvas.create_oval(shape[x, 0], shape[x, 1], shape[x, 0], shape[x, 1])
            if x > startn:
                self.canvas.create_line(self.landmarks[x, 0], self.landmarks[x, 1], xr, yr, width=2)
            if endline is True and x == startn:
                xr1 = self.landmarks[x, 0]
                yr1 = self.landmarks[x, 1]
            xr = self.landmarks[x, 0]
            yr = self.landmarks[x, 1]

        if endline is True:
            self.canvas.create_line(xr, yr, xr1, yr1, width=2)

        if startn == 36 or startn == 42:
            x = self.landmarks[startn + 1, 0] + (self.landmarks[startn + 2, 0] - self.landmarks[startn + 1, 0]) / 2
            y = self.landmarks[startn, 1] - 3
            self.canvas.create_oval(x, y, x, y, width=7)




class Menu:

    def __init__(self, root, client):

        self.c = client
        self.root = root
        self.root.title('Face Chat program')
        self.my_socket = None

        title = Label(self.root, text='Face Chat', font=("TkDefaultFont ", 50))
        title.place(x=350, y=100)

        button = Button(self.root, text='exit', command=self.root.destroy)
        button.place(x=0, y=0)

        self.ipinput = Entry(self.root)
        self.ipinput.place(x=450, y=250)
        iptext = Label(self.root, text='Enter IP:')
        iptext.place(x=400, y=250)




        options = self.returnCameraIndexes()
        self.variable = StringVar(self.root)
        self.variable.set(options[0])
        selectcam = OptionMenu(self.root, self.variable, *options)
        selectcam.place(x=485, y=350)
        selectcamtext = Label(self.root, text='Select Camera:')
        selectcamtext.place(x=400, y=350)

        proceed = Button(self.root, text='Start', command=self.start)
        proceed.place(x=600, y=300)


    def start(self):
        '''
        Checks if camera selected and if ip exist and starts the connection,
        returns to continue
        :return:
        '''
        if self.variable.get().isnumeric():
            if self.checkip() is False:
                iperror = Label(self.root, text='Server ip does not exist', fg='red')
                iperror.place(x=400, y=270)
                return
            else:
                self.c.continue1(self.my_socket)


    def checkip(self):
        '''
        checks if server with the ip selected is open
        :return:
        '''
        try:
            self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.my_socket.connect((str(self.ipinput.get()), 1729))
        except Exception:
            return False
        return True

    def returnCameraIndexes(self):
        '''
        return all the indexes of cameras connected to the computer
        :return:
        '''
        # checks the first 10 indexes.
        index = 0
        arr = ['No camera available']
        i = 10
        while i > 0:
            cap = cv2.VideoCapture(index)
            if cap.read()[0]:
                arr.append(index)
                cap.release()
            index += 1
            i -= 1
        return arr

    def getvariable(self):
        '''
        :return: returns the selected camera
        '''
        return int(self.variable.get())




if __name__ == '__main__':
    Client()