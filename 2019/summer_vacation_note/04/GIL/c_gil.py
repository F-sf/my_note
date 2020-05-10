from ctypes import *
import threading

loop_lib = cdll.LoadLibrary("./c_loop/libc_loop.so")

t1 = threading.Thread(target = loop_lib.loop)
t1.start()
t2 = threading.Thread(target = loop_lib.loop)
t2.start()
t3 = threading.Thread(target = loop_lib.loop)
t3.start()

while True:
    pass
