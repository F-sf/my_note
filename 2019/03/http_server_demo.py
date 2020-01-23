#!/usr/bin/env python3
#coding:utf-8

import socket
import re
import gevent
from gevent import monkey

def serve_client(client_socket):
    while True:
        recv_data = client_socket.recv(1024).decode("utf-8")
        if recv_data:
            recv_data_lines = recv_data.splitlines()
            # 默认网页index.html
            file_name = "/index.html" if re.search(r"(/.*) ", recv_data_lines[0]).group(1) == "/" else \
                                         re.search(r"(/.*) ", recv_data_lines[0]).group(1)
            file_path = "./moban3955"+file_name
            try:
                f = open(file_path, 'rb')
            except Exception as err:
                print(err)
                html_data = "<h1>Oh No! 404 File not found!</h1>"  # Body
                ret_data = "HTTP/1.1 404 NOT FOUND\r\n"  # Header
                ret_data += "Content-Length:{}\r\n".format(len(html_data))
                ret_data += "\r\n"  # 换行Windows \r\n Linux \n
                ret_data += html_data
                ret_data = ret_data.encode("utf-8")
            else:
                html_data = f.read()
                ret_data = "HTTP/1.1 200 OK\r\n"
                ret_data += "Content-Length:{}\r\n".format(len(html_data))
                ret_data += "\r\n"
                ret_data = ret_data.encode("utf-8") + html_data
            client_socket.send(ret_data)
        else:
            client_socket.close()
            return

def main():
    monkey.patch_all()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind local port
    server_socket.bind(("", 2333))
    # listen
    server_socket.listen(128)
    while True:
        # waiting for client
        client_socket, client_addr = server_socket.accept()
        gevent.spawn(serve_client, client_socket)

if __name__ == "__main__":
    main()
