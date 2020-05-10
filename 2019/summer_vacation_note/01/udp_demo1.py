import socket
import time
import threading 

class UdpDemo():
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("127.0.0.1", 2333))
        self.spin()
        self.socket.close()


    def spin(self):
        t_send = threading.Thread(target = self.send_loop)
        t_recv = threading.Thread(target = self.recv_loop)
        t_send.start()
        t_recv.start()
        while True:
            time.sleep(1)


    def send_loop(self):
        while True:
            input_msg = str(input("Input message:")).encode("utf-8")
            self.socket.sendto(input_msg, ("127.0.0.1", 2334))


    def recv_loop(self):
        while True:
            recv_msg = self.socket.recvfrom(1024)
            print("\nRecv_msg: {}".format(recv_msg[0].decode("utf-8")))


if __name__ == "__main__":
    mudp = UdpDemo()
