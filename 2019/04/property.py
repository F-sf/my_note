#! /usr/bin/env python3
# coding: utf-8
class MyClass():
    def __init__(self):
        self.org_data = 10

# -------------方式1----------------
    @property
    def data(self):
        return self.org_data * 2

    @data.setter
    def data(self, value):
        self.org_data = value/2

    @data.deleter
    def data(self):
        print("delet data")
    
# -------------方式2----------------
class Money():
    '''
    演示对于私有变量get/set函数利用property升级，使之以看起来像直接调用属性的方式调用函数
    '''
    def __init__(self):
        self.__money = 0

    def get_money(self):
        return self.__money

    def set_money(self, value):
        if isinstance(value, int):
            self.__money = value
        else:
            print("Error: 需要输入值为int !")

    moeny = property(get_money, set_money)

# 调用方式即可如下
a = Money()
print(a.moeny)
a.moeny = 100
print(a.moeny)

