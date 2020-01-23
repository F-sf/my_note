#coding:utf-8
import gevent
import time
from gevent import monkey

monkey.patch_all()  # 将所有耗时操作转换成gevent内的耗时操作函数

a = 0
start_time = time.time()

def task():
    global a
    for i in range(10000000):
        a += 1

gevent.joinall([
            gevent.spawn(task),  #输入参数(函数，参数1, 参数2)
            gevent.spawn(task),
            gevent.spawn(task)
        ])


for i in range(10000000):
    a += 1

cost_time = time.time() - start_time
print(a)
print(cost_time)
