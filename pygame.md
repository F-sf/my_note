# Pygame

### 常用功能整理

#### 最基本部分

``` python
import pygame
from pygame.locals import *  # 包括一些宏定义和其他

# 初始化pygame，为使用硬件做准备
pygame.init() 

# 创建一个窗口 
# arg: 分辨率(x,y),标志位如0/FULLSCREEN全屏/RESIZABLE可变尺寸,色深
# return: 返回一个Surface对象
screen = pygame.display.set_mode((1440, 1280), 0, 32)

# 设置窗口标题
# arg: 标题字符串
pygame.display.set_caption("hello,world!")

# 刷新画面
pygame.display.update()
```

#### Surface对象创建和操作

``` python
# 加载图片并转换为Surface
# arg: 图片路径
# return: Surface对象
surface1 = pygame.image.load(“surface1.png”)

# blit画图
# arg: 一个Surface对象, 相对于左上角坐标(x,y)
surface1.blit(surface2, (0, 0))

# Surface拿取宽高
width = surface1.get_width()
height = surface1.get_height()
```

#### 事件相关

``` python
pygame.event.get()  # 拿取所有事件,返回一个元组
pygame.event.wait()  # 拿取一个事件，若没有则阻塞
# 主循环处理示例
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            exit()
        if event.type == KEYDOWN:
            if event.key == K_LEFT:
                move_x = -1
            elif event.key == K_RIGHT:
                move_x = 1
            elif event.key == K_UP:
                move_y = -1
            elif event.key == K_DOWN:
                move_y = 1
        elif event.type == KEYUP:
            move_x = 0
            move_y = 0
# 对于各种事件及其内容，可运行event_test.py查看
```

#### 键鼠相关

``` python
# 获得鼠标位置
# return: (x,y)
x, y = pygame.mouse.get_pos()
```

## ClassProj

>  单片机型号STM32F103CB，操作系统用UCOSII

### 电机驱动任务(张安迪)

* 直流电机转动控制 (IO高低)
* 编码器读取, 计算两轮速度, 存入数组(定时器)
* 根据编码器数据实现直流电机PWM闭环调速 (定时器)
* 给出两电机的速度控制函数接口

### 红外传感器读取任务(卓钇江)

* 读4路红外传感器 (ADC, DMA)置入数组

### 主控任务(魏文萱)

* 实现车体控制函数，输入线速度和角速度，控制电机
* 自控下，根据四路距离数据控制车体，实现巡线和避障

* 手控下，上位机用WASD控制，转化成速度分量，对应实现车体控制

### 单片机上串口通讯任务(吴宗轩、刘一鸣)

* 与上位机通讯协议的实现 (串口, 位操作)

### 上位机(傅帅)

* 图形界面，遥控自控切换，车体状态图形化展示