#!/usr/bin/env python3
#coding:utf-8

from collections import Iterable
from collections import Iterator

#---------------------------迭代器--------------------------

class Fibnoacci():
    def __init__(self, num):
        self.num = num
        self.a = 0
        self.b = 1
        self.current_num = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.current_num < self.num:
            fib = self.a
            self.a, self.b = self.b, self.a + self.b
            self.current_num += 1
            return fib
        else:
            raise StopIteration

#---------------------------生成器--------------------------

def fib(num):
    a, b = 0, 1
    current_num = 0
    while current_num < num:
        send_msg = yield a
        print(send_msg)
        a, b = b, a+b
        current_num += 1
    return "Finish!"


#---------------------------test------------------------------

if __name__ == "__main__":
    #for _ in Fibnoacci(10):
    #    print(_)
    #for _ in Fibnoacci(10):
    #    print(_)

    obj = fib(10)
    next(obj)  # 第一次不能用send

    while True:
        try:
            # print(next(obj))
            print(obj.send("send_msg"))  # send功能同next，但可传参
        except StopIteration as err:
            print(err.value)
            break
        




