import multiprocessing

def hello():
    print("hello world")

#-----------------------创建------------------------

p1 = multiprocessing.Process(target = hello, args = (arg1,))
p1.start()

#-----------------多进程中的队列-------------------
# 创建队列,长度为3
q1 = multiprocessing.Queue(3)
# 存入队列
q1.get()
# 从队列取出
q1.put()

#------------------多进程中的进程池-----------------
# 创建进程池,最大同时运行进程数为3
po = multiprocessing.Pool(3)
# 向其中添加任务
po.apply_async(hello,(arg1,))
# 关闭进程池后，其不再接受新的请求
po.close()
# 阻塞，等待子进程全部结束
po.join()
# 进程池中使用队列
q2 = multiprocessing.Manager().Pool()
