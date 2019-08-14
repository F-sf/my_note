# 2019自习笔记

### 1.CMakeLists相关

#### g++操作

* 静态链接库的生成`add_library(aaa STATIC 源文件)`  生成libaaa.a
* 动态链接库的生成`add_library(aaa SHARED 源文件)`或`g++ aaa.cpp -shared -o libaaa.so`  生成libaaa.so
* 静态链接库使用`g++ main.c libaaa.a -I include -o outcome`
* 动态链接库使用`g++ main.c -I include -L. -laaa.so -o outcome`

#### CMakeLists常用操作

> 个人理解CMakeList做的主要工作就是指定源文件/头文件/链接库的目录，相当于暂时指定了一系列环境变量
>
> CmakeLists 中的变量只有字符串和LIST类型（字符串的LIST），注释用#。

* 指定最小版本: `cmake_minimum_required(VERSION X.X)`

* find_package(aaa REQUIRED) : 在一些环境变量指定的路径下搜索aaa.cmake，然后将其include以拿到一些变量。

* print:  `message(string ${VAR})`

* 变量引用: `${VAR}`

* 设置项目名称: `project(name)`

  > 该命令会引入name_BINARY_DIR 和 name_SOURCE_DIR。
  >
  > 其中name_BINARY_DIR为CMakeLists根目录/build, name_SOURCE_DIR为CMakeLists根目录

* 拿取路径下的所有源文件，存为变量SRCS: `aux_source_directory(. SRCS)`

* 将头文件目录引入: `include_directories(include)`

* 将子目录下的CMakeLists加入此处: `include_directories(subdir)`

* 将SRCS中的源文件生成可执行文件name: `add_executable(name ${SRCS})`

* 将LIB_SRCS中的源文件生成库文件libaaa.so/libaaa.a: `add_library(aaa SHARED/STATIC ${LIBS_SRCS})`

  > 若不加SHARED或STATIC，会默认生成静态链接库。

* 为可执行文件name添加动态/静态链接库libaaa.so/libaaa.a: `target_link_libraries(name aaa)`

* 另外有一个link_libraries() 的命令，用在add_executable/add_library之前，作用和target_link_libraries相同，同类命令link_directories() ，指定到库的路径而不是库本身

#### Nvidia独显驱动安装

```
https://linuxconfig.org/how-to-install-the-nvidia-drivers-on-ubuntu-18-04-bionic-beaver-linux
按上网站方法一配置后重启时在perform mok management界面选择enroll mok
```

#### 修改grub

```shell
sudo vim /etc/default/grub
sudo update-grub
```

#### Gazebo

> Solidworks相关操作
>
> [sw_urdf_exporter](http://wiki.ros.org/sw_urdf_exporter) 按其中2.1安装即可，装好后插件在SW -> 工具 -> File -> Export as URDF
>
> 生成urdf过程中只需要设置link和axis，其中子link的基座标系就是它与父link间joint的坐标系，若为旋转其转轴为Z轴，方向按右手确定。

1. [URDF与Gazebo](http://gazebosim.org/tutorials?tut=ros_urdf&cat=connect_ros)

   URDF (Universal Robotic Description Format) 和SDF (Simulation Description Format) 均可以用于机器人的描述，但URDF会缺少一些Gazebo需要的属性，故应在其中加入gazebo元素<gazebo>

   XACRO(XML Macros)可为URDF提供宏定义的功能，以方便编写。工作流程为：XACRO -> URDF -> SDF 其中第一步由xacro包下xacro.py程序完成，将带宏定义的XACRO解析成URDF，第二步由Gazebo完成，将带<gazebo>元素的URDF解析成SDF，可用`gz sdf -p aaa.urdf`检验urdf是否可以正常解析。

   可通过设置<joint>元素中的<limit>子元素的effort和velocity属性限制最大转矩和速度。

2. [Gazebo插件如摄像头和激光雷达的使用](http://gazebosim.org/tutorials?tut=ros_gzplugins&cat=connect_ros)

   可参考rrbot_description/urdf/rrbot.gazebo 

3. [Gazebo中关节电机控制](http://gazebosim.org/tutorials?tut=ros_control&cat=connect_ros)

   简单总结四个必要环节：

   1. urdf中的gazebo_ros_control插件

   2. urdf中的transmission元素。

   ​    其内部<joint>元素下的子元素<hardwareInterface>有Effort/Velocity/PositionJointInterface三种可用, 应与yaml中相应关节控制器种类匹配

   3. yaml文件。

   ​    其可选控制器种类有(可通过rosservice call controller_manager/list_controller_types得到)

   ```
   effort_controllers:  力/力矩控制，需设置PID，单位N N/m，PID可通过测试调节至合理值
   	joint_effort_controller
   	joint_group_effort_controller
   	joint_position_controller
   	joint_group_position_controller
   	joint_velocity_controller
   joint_state_controller:  读取各关节当前位置，使gazebo向joint_state话题上发布关节信息
   	joint_state_controller
   position_controllers:  位置控制，单位rad，不设置PID会瞬移，设置后和力控制表现相近，官方教程未设置
   	joint_position_controller
   	joint_group_position_controller
   以及一个特殊的diff_drive_controller/DiffDriveController对应VelocityJointInterface
   ```

   4. controller_spawner。

4. URDF的构建逻辑

   坐标系间的关系靠<joint>中的<origin>元素维护，<link>内的<origin>描述其自身相对于由<joint>定义好的坐标系的变换情况，一般为0，其中inertial内的origin描述质心。

5. 对于造型较为复杂的模型，可能导入gazebo过程中会出现各种诡异的问题，一般是由于惯性张量引起的，经尝试在每一项惯性张量前加上个1*可解决问题，但原理不明

6. 可调节link<gazebo>标签中的kp属性来降低其刚性

7. 可通过gazebo/link_states及gazebo/model_states拿到每个link和model在世界坐标系下的位姿

8. .world文件中的include url是从环境变量GAZEBO_MODEL_PATH所指路径中读取config文件拿取model，这个model也有其对应的sdf文件，整个模型文件夹可通过在gazebo内使用模型编辑功能导入stl或dae生成

> gazebo-ros仿真基本流程
>
> 1. 启动gazebo(gzserver和gzclient)
>
> ```xml
> <include file="$(find gazebo_ros)/launch/empty_world.launch">
> ```
>
> 2. 将urdf文件送入参数robot_description
>
> ```xml
> <param name="robot_description" command="$(find xacro)/xacro.py $(arg model)" />
> ```
>
> 3. 用spawn_model程序将模型导入gazebo
>
> ```xml
> <node name="urdf_spawner" pkg="gazebo_ros" type="spawn_model"
>      args="-z 1.0 -urdf -model robot_name -param robot_description" output="screen" />
> 除了-param也可以-file urdf路径
> ```
>
> 4. 将ros_control相关的yaml文件读入参数服务器
>
> ```xml
> <rosparam file="$(find sw2urdf_trial)/config/sw2urdf_trial.yaml" command="load"/>
> ```
>
> 5. 用controller_spawner将控制器导入,args为各个控制器的参数名
>
> ```xml
> <node name="controller_spawner" pkg="controller_manager" type="spawner" 
> 	output="screen" ns="sw2urdf_trial" args="joint_state_controller
>                    joint1_pos_controller
>                    joint2_pos_controller
> 				   joint3_pos_controller"/>
> ```
>
> 6. 开启robot_state_publisher来发布tf(其通过拿取robot_description参数和订阅joint_state计算tf)
>
> ```xml
> <node pkg="robot_state_publisher" type="robot_state_publisher"  name="robot_state_publisher">
> ```
>
> 7. 有了robot_description和tf，才可以开rviz查看
>
> ```xml
> <node name="rviz" pkg="rviz" type="rviz" args="$(find sw2urdf_trial)/rviz/urdf.rviz" />
> ```
>
> 

#### Python

- python文件读写可以用f = open(filepath, 'r'/'w'/'a')，也可以用with open(filepath, 'r'/'w'/'a') as f :  区别是后者不需要f.close()

- python读取命令行参数可以用sys.argv[]，也可以用argparse模块，后者较标准，可以产生-h。

- python的字典3.5之前是无序的，3.6之后为有序

- print小技巧: \r回车与end=""取消末尾自动换行可起到同行不断刷新的效果

  ```python
  print("/rDownloading:{:.2f}".format(download_rate), end="")
  ```

- isinstance(obj, class)  判断obj是否是class的实例或继承自class(功能包括但不仅限于此)

  > 例如如果自己定义一个类并加入\__iter__方法，则isinstance(obj, Iterable)将会返回True。但此时obj并未继承Iterable

- dir(obj): 返回包括obj及其继承的所有的属性和方法的 list

- obj.\__dict__: 返回包括obj自身所有属性的字典(不包括继承的属性)

- \__getitem__方法用于使对象能使用obj[0]

- python中类属性，实例属性，类方法，实例方法，静态方法的区别和应用场景：理论上说，从节省资源的角度，可将与类无关的方法用静态方法实现; 将与每个实例都相同的方法和属性用类方法和类属性实现; 每个实例差异化的方法和属性用实例属性和实例方法实现

- python中列表推导式的使用技巧

- 在成功import的情况下，多次import只有第一次会有效，

  若想重新导入需要使用`from imp import reload`, `reload(module)`来重新导入

- 关于单双引号，习惯上长段双引号，短段单引号; docstring三双引号，较短时可写成单行。

#### 杂记

* find命令用法 ： find [路径] [特征] 	e.g : `find / -name "rostopic" | less`

* roslaunch中的一些细节

  args意义 ： shell中命令后附加参数    e.g:

  ```xml
    <node
      name="spawn_model"
      pkg="gazebo_ros"
      type="spawn_model"
      args="-file $(find maxliebao)/robots/maxliebao.urdf -urdf -model maxliebao"
      output="screen" />
  上述语句等价与在shell中运行
  rosrun gazebo_ros spawn_model.py -file maxliebao根目录/robots/......
  ```

  respawn="true"的意义：节点停止时launch会重新启动该节点

  required="true"的意义：该节点停止时launch会关闭其他节点

  ns="aaa"的意义：该节点名称及其创建的话题和服务名称会变成aaa/...

  node元素内部<remap from="aaa" to="bbb" />的意义： 将节点及话题服务名称中的aaa替换为bbb, (包括发布和接收)

  command的意义： 拿取shell命令的输出    e.g:

  ``` xml
    <param name="robot_description" command="$(find xacro)/xacro --inorder '$(find rrbot_description)/urdf/rrbot.xacro'" />
  上述语句用xacro包下的xacro程序将rrbot_description包下的rrbot.xacro解析成URDF并存在rrbot_description这一参数上
  ```

  

* vim中寄存器常用的为`无名寄存器""`,`系统剪贴板"+`,输入模式下可用<C+r>加寄存器号调用其内容

* vim映射设置中回车用<CR>,tab用<Tab>,<Leader>键默认为反斜杠`\`

* 原子操作：不可分割的，一旦开始必须完全完成的操作

* 终端快捷键

  > C-a 开头	C-e 结尾	C-f 前一	C-b 后一	C-w 删前面	C-k 删后面

* vim normal模式下D删至行尾，d0删至行首

# 课程笔记

### 01网络编程

* ip地址，ABCDE类，网络号，主机号
* 私网ip范围`10.0.0.0 ~ 10.255.255.255(A类)  172.16.0.0~172.31.255.255(B类)  192.168.0.0~192.168.255.255(C类)` 用于组建不同规模的局域网
* 端口1024以下为知名端口，不可随意使用（80HTTP，21FTP），1024到65535为动态端口
* socket套接字，进程间通讯的一种方式，可用于不同主机间进程的通讯
* windows默认编码格式gbk
* udp，tcp区别和各自机制，udp像信件，较简单，不区分客户端和服务器;
* tcp像电话，更稳定，区分客户端和服务器，服务器必须绑定port，客户端一般不绑定

### 02多任务

* 并行和并发的概念，并行多核同步进行，并发单核轮流处理

#### 线程

* 线程可理解为对当前执行代码位置的一个指针，多线程即可理解为同时指向并执行多个代码行

* 主线程结束，程序才会结束，若有未跑完的子线程，主线程会等待其结束

* 多线程间共享全局变量，但若多线程同时修改一个全局变量，可能会出现冲突

* 为解决冲突问题，完成多线程协作，可使用互斥锁(mutex)机制让一些线程在特定位置阻塞，防止其同时修改全局变量

* 死锁的概念：两个互斥锁都阻塞在等待对方解锁的位置而导致程序卡死，解决方式：超时检测，银行家算法等

  ``` python
  ThreadA(threading.Thread):
      def run(self):
  		mutexA.acquire()
  		time.sleep(1)
  		mutexB.acquire()
  ThreadB(threading.Thread):
  	def run(self):
      	mutexB.acquire()
  		time.sleep()
  		mutexA.acquire()
  ```

#### 进程

* 运行起来的，占用一定资源的程序称为进程(Process)
* python中每次开启子进程，都会copy一份与主进程一致的资源
* 相对于进程，线程执行开销较小，可轻量地实现多任务，但不利于资源的管理和保护，进程则相反。一般而言会选择使用线程实现多任务
* 进程间不共享全局变量，通讯可用multiprocessing.Queue
* 进程池：创建一个限制最多同时运行进程数的进程池，可向其中无限添加任务，顺序运行
* 进程池中子进程抛出异常，不会显示在终端中

#### 协程

> 迭代器和生成器主要用于降低大量数据对资源的占用，如xrange和range，当数据量很大时，xrange要所占用的资源要远小于range

* 迭代器：能被for _ in obj:遍历的对象称为可迭代的对象，若想使一个对象成为可迭代的对象，须在其中实现`__iter__`方法，该方法应该返回一个迭代器，迭代器是一个至少实现了`__iter__`和`__next__`方法的对象，每次for in: 都会调用一次`__next__`方法, 将其返回值给_

* list(), tuple()等转换也是通过迭代器实现的

* 生成器：生成器是一种特殊的迭代器，也可理解成让一个函数变得可暂停

  1. 将列表生成式的[]换成()则产生一个生成器。 e.g: (_ for _ in range(10))

  2. 若一个函数中有yield语句，则调用该函数变为返回一个生成器的对象obj

     每次调用next(obj)时函数运行到yield处，并返回yield后内容，然后暂停。再次调用next(obj)继续运行至下次yield，返回，暂停，直至函数结束，抛出StopIteration异常

     除了next(obj)，也可以用obj.send(send_msg)实现激活生成器，并传入参数。但send不能在第一次激活生成器时使用, 因为第一次激活时函数从第一行运行，没有send_msg = yield rtn接数据

* 协程即为利用yield机制使多任务通过暂停的方式同步进行，占用资源比线程更少，但用yield实现时遇到阻塞任务时会全部阻塞，故一般使用gevent模块实现协程，gevent对yield机制进行了封装，实现将单任务阻塞的等待时间利用起来去执行其他任务。但协程归根结底还是在单线程下运行。

​        总结：由于GIL的影响，如果使用Cpython的解释器，则协程和线程实际上都是并发执行，也都能共享全局变量和类属性。但由于协程是使用yield机制实现的并发，故其在代码层级保证了同时修改一个变量时不会出问题，而线程的并发是在CPU层级由GIL实现的，故若要想保证同时修改一个变量时不会出问题，还需要手动加锁。故我认为，对于非计算密集型的多任务，若需多任务间通讯，使用协程会方便一些; 若不需通讯，则都行(经简单测试多线程好像相比gevent模块实现协程要快一些)。若对于计算密集型多任务，则最好使用进程，才能真正实现并发，充分利用多核CPU性能。

### 03 web服务器

#### 正则匹配

```
单个：
	[]：匹配单个在一定范围内的字符 e.g:[0-9a-zA-Z_]
	\d：匹配数字
	\D：匹配非数字
	\s：匹配空白，空格/tab
	\S：匹配非空白
	\w：匹配单词，a-z/A-Z/0-9/_/中文等各语言
	\W：匹配非单词
	. ：匹配任意，除了\n，如果想匹配\n可用match("", "", re.S)
多个：
	* ：匹配前一个字符出现任意次
	+ ：匹配前一个字符出现大于0的任意次
	？ ：匹配前一个字符出现0或1次，即可有可无
	{n}：匹配前一个字符出现n次
	{m, n}：匹配前一个字符出现m到n次
其他：
	^：匹配开头
	$：匹配结尾
	(aaa|bbb)：或逻辑
	()：取正则中的部分结果    rst = re.match()    rst.group(1)
	\n：第n个分组中的值
```

re.match(表达式，匹配内容，flag)，从头开始匹配，只能返回第一个匹配结果，返回值为一个Match实例

re.search()与match相同，仅仅是非从头匹配，只能返回第一个匹配结果，返回值为一个Match实例

re.findall()，非从头匹配，返回值为匹配结果的列表

re.sub(表达式，替换内容，匹配内容)，匹配并替换，可以匹配多个结果。替换内容可为函数的引用，示例如下：

```
def add(temp):
	Strnum = temp.group()
	num = int(Strnum) + 1
	return str(num)
re.sub(r'\d+', add, "python = 996")
返回值为替换后的字符串
```

re.split()，以匹配结果为界切片，示例如下：

```
re.split(r':| ', "info:aaa bbb ccc")
返回值：['info', 'aaa', 'bbb', 'ccc']
```

#### HTTP协议



### 04 Python高级语法

#### GIL

* 计算密集型程顺序表序，IO密集型程序(有较多的等待和阻塞)

* GIL全局解释器锁，Cpython解释器层面的未解决的问题，导致用Cpython解释器解释python时的多线程并非真的多个线程同时进行，而是多个线程共享一个锁`(其释放有持续一定时间后释放和阻塞时释放两种机制)`，即同时只能执行一个线程，即以一种和协程效率相似的并发的方式进行执行。其同样实现了阻塞时间的利用，所以和协程一样适用于IO密集型程序。而对于计算密集型程序，多进程才能起到提高效率的作用。

  > 其实对于多核CPU多线程的效率甚至要低于协程，多核间的切换也需要消耗一定资源
  >
  > 之所以有了GIL机制还需要手动上mutex互斥锁，是因为两个操作的层级不同，mutex是py代码层面的，而GIL是CPU层面的，一行代码并非原子级操作，可被解析成若干次CPU层面的操作，所以可能出现AB线程同时修改数据a，A线程读取，加一，但还没有写入就被GIL打断，进入B线程，读取，加一，写入。此时AB读取的值是相同的，也就是说本该加二，但结果只加了一。

* 解决GIL对多线程造成的影响的方法有两种，一是采用Cpythonu以外的解释器，如Jpython; 二是可将多线程部分用其他语言实现，如C，再生成库让python调用。

#### 深拷贝浅拷贝

* 为什么要使用拷贝：如a=[1,2,3] b=a这种操作只是将变量b指向了和变量a相同的list实例，并不是真正意义的复制。当两个变量同时指向一个可变实例时，若一个变量对该实例进行了修改，则另一个变量处也会产生变化。所以若想对实例进行复制时，务必使用copy模块。

* ```python
  import copy
  copy.deepcopy()  # 深拷贝，一直拷贝到最深层的对象
  copy.copy() \ xxx.copy() \ [:]  # 这些均属于浅拷贝，只拷贝最上面一层
  ```

* python中最特殊的几个类：int, float, double, string, tuple等类比较特殊，属于不可变类，也只有他们有\__hash__方法，也就是说只有他们可以作为字典的key。这些类实例化以后我们便不能修改，像a=1 \ a=2这种操作相当于为变量a指向了一个新地址处存放的 新int实例。故无法也无需对这些类型使用拷贝。

* 假设对a = {"A": 1, "B": [1, 2, 3]}这种字典进行浅拷贝，其原理是新开辟一片空间，存放新的字典实例，键“A”和"B"的哈系值经过一次冲突处理得到新地址，而其指向的新内容则分别为**新的不可变对象1**和**老的可变对象[1, 2, 3]的地址**，因而字典会出现copy和deepcopy不同的现象

#### 私有化, import, 封装, 继承, 多态

* python中下划线意义：

  > _var 表示告诉别人这是私有，但实际上并不是
  >
  > __var 可以理解成私有，但其实只是解释器帮它改了个名字
  >
  > \__function__ 魔法方法，存储一些python自用的方法，不推荐吧自己的方法写成这种
  >
  > var_ 如果想以保留字命名自己的变量，可这样写 e.g: class_
  >
  > _ 表示不关心的变量 e.g: for _ in range(10)

* 多py文件维护同一个模块中的变量时import module，module.var 和 from module import var 的区别

* 多态：通过不同子类对同一父类的继承和重写某个方法，实现同一个方法在不同子类对应不同代码的行为

#### 方法解析顺序表MRO

* 类的继承中，其`super().__init__()`的调用顺序在`class.__mro__`中显示
* 调用父类init函数的方式: `Parent.__init__()`, `super().__init__()`, `super(Class, self).__init__()`

* def fun(a, b, *args, **kwargs): 如此定义函数，为不定长参数，a，b为必须。其余的参数形如11, 22, 33等会被以元组形式存入args，形如arg1 = 11, arg2 = 22的参数会被以字典的形式存入kwargs

  > *tuple, **dict意为对元组和字典进行拆包，但好像只能在函数内这么用

#### 类相关的一些知识点

* 静态方法和类方法不依存于实例，在内存中的存放位置和类在一起，创建多个实例时不会额外占用空间。静态方法和类外部方法其实差不多，更大的意义是起到一个命名空间的作用。
* property属性，让函数调用以属性拿取和设置的方式进行。两种调用方式：装饰器，类属性
* 魔法方法\__str__ 并不只是用于print，像str()，“{}”.format等操作也会调用该方法

#### with与上下文管理器

* 实现了`__enter__`和`__exit__`方法的类可以被称为上下文管理器。这种类的实例可以使用with语句。

* ``` 
  with open("a.txt","r") as f:
  with语句把open("a.txt","r").__enter__()的返回值赋给f，当结束或者抛出异常时，便执行f.__exit__()
  ```

* 另一种实现上下文管理器的方式：

  ```python
  from contextlib import contextmanager
  
  @contextmanager
  def my_open(path, mode):
  	f= open(path, mode)  # yield前的代码为__enter__()函数
      yield f  # yield后的为__enter__()返回值
      f.close()  # yield后的代码为__exit__()的函数
  
  with my_open("a.txt", "w") as f:  # my_open依然返回一个上下文管理器
      f.write("content")
  ```

  