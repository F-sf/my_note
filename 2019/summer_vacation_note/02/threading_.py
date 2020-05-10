#!/usr/bin/env python3
#coding:utf-8

import threading

def hello():
    print("hello world")

#-----------------------创建------------------------

#  1.初始化Thread实例，内部存了hello函数指针作为目标函数,可用args = 参数元组的方式传入参数，若在类内为类内方法开子线程，则不需要将self当作传入args
t1 = threading.Thread(target = hello, args = (arg1,))
# 创建并开始子线程
t1.start()

# 2.继承Thread类
class MyThread(threading.Thread):
    def run(self):
        '''do something'''
# 创建并开始子线程
t = MyThread()
t.start()

#----------------------常用方法-------------------

# 设置全局变量mutex互斥锁，以保证多个子线程不会同时修改同一全局变量
mutex = threading.Lock()
mutex.acquire()  # 如果未上锁，则上锁;如果已上锁，则阻塞，等待开锁后再上锁
mutex.release()  # 开锁
# 拿取当前程序正在跑的所有线程，thread_list: [thread1, thread2]
thread_list = threading.enumerate()
