import time
import gevent
from gevent import monkey

#------------------------test1--------------------------
def task_1():
    while True:
        print("--1--")
        time.sleep(0.5)
        yield

def task_2():
    while True:
        print("--2--")
        time.sleep(0.5)
        yield

t1_gen = task_1()
t2_gen = task_2()

while True:
    next(t1_gen)
    next(t2_gen)


#------------------------test2--------------------------

monkey.patch_all()  # 将所有耗时操作转换成gevent内的耗时操作函数

def task(n, data):
    for i in range(n):
        print(data, i)
        time.sleep(0.5)  # 用gevent实现多任务时，需要将所有耗时操作函数换成gevent内的对应函数

gevent.joinall([
            gevent.spawn(task, 5, "task1"),  #输入参数(函数，参数1, 参数2)
            gevent.spawn(task, 5, "task2"),
            gevent.spawn(task, 5, "task3")
        ])
