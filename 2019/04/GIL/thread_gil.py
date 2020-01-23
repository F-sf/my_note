import threading
import time

a = 0
start_time = time.time()

def task():
    global a
    for i in range(10000000):
        a += 1


t1 = threading.Thread(target = task)
t1.start()
t2 = threading.Thread(target = task)
t2.start()
t3 = threading.Thread(target = task)
t3.start()

for i in range(10000000):
    a += 1

cost_time = time.time() - start_time
print(a)
print(cost_time)
