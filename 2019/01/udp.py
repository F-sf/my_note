#!/usr/bin/env python3
#coding:utf-8

import socket

#-------------------------------创建---------------------------------

# 第一个参数固定，第二个DGRAM表示创建的是udp套接字，返回udp套接字实例
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#-------------------------------发送---------------------------------

target_address = ("ip", port)
# Send "content" to ip:port，注意发送内容需要进行编码
udp_socket.sendto("content".encode("utf-8"), target_address)

#-------------------------------接收---------------------------------

# ''表示本机全部ip
local_address = ('', port)  
# 接收端端口号需确定
udp_socket.bind(local_address)
# 等待接受数据，阻塞 返回值recv_data: ("content", ("src_ip", src_port))
recv_data = udp_socket.recvfrom(1024)  # Receive most 1024 bytes

#-------------------------------关闭---------------------------------

udp_socket.close()
