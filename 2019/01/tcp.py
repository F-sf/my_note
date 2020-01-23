#!/usr/bin/env python3
#coding:utf-8

import socket

def client():

    #-------------------------------创建---------------------------------

    # 第一个参数固定，第二个STREAM表示创建的是tcp套接字，返回tcp套接字实例
    tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #----------------------------客户端操作---------------------------------

    server_addr = ("ip", port)
    # 相对于udp多出一步连接
    tcp_client_socket.connect(server_addr)

    # 相对于udp不需要再次指定目标ip和port
    tcp_client_socket.send("content".encode("utf-8"))

    # 相对于udp,此处的recv_data仅有content
    recv_data = tcp_client_socket.recv(1024)
    
    #-------------------------------关闭---------------------------------

    tcp_client_socket.close()

def server():

    #-------------------------------创建---------------------------------

    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #----------------------------服务器操作---------------------------------

    # 服务器需要绑定本地端口 
    local_addr = ("", port)
    tcp_server_socket.bind(local_addr)

    # 使套接字变为被动, 等待客户端的connect
    tcp_server_socket.listen(128)  # 128表示最多同时128个客户端连接

    # client_socket: 专门为这个客户端服务的新套接字
    # clientAddr   : 新套接字的地址(client_ip, client_port)
    # tcp_server_socket在此之后依然存在,仍可用于被动监听
    client_socket, clientAddr = tcp_server_socket.accept()

    # Send "content" to ip:port
    client_socket.send("content".encode("utf-8"))

    # 相对于udp,此处的recv_data仅有content
    recv_data = client_socket.recv(1024)

    #-------------------------------关闭---------------------------------
    client_socket.close()
    tcp_server_socket.close()

