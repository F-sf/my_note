# FreeRTOS笔记

> 这篇只记录一些重点的地方，和大体逻辑流程，不会像ucos笔记一样那么详细。会在最后简单分析两操作系统设计上的一些异同。

## 综述

​	FreeRTOS对一些资源的分配采取动态或静态的内存分配和释放，具体管理方式由作为接口的heap.c文件实现。

​	对任务状态的管理基于列表和列表项，每个任务具有状态列表项和事件列表项，任务的状态列表项存在不同列表中即表明任务处于不同状态，事件列表项用于存在队列的等待列表中，标记任务正在等待消息入队或出队，并标记任务优先级；

​	任务间的通讯主要有队列、信号量、事件标志组、任务通知几种，队列和信号量都通过队列实现，事件标志组有独立数据结构用于处理复杂同步逻辑，任务通知基于任务控制块，用于实现轻量的信号和消息邮箱。

## 中断，内存，时钟

### 临界区和系统中断

* 临界区原理：ucos中使用汇编指令`CPSID I`关中断，具体是将寄存器`PRIMASK`置1，仅保留NMI不可屏蔽中断和Hard Fault硬件错误、而FreeRTOS中操作寄存器`BASEPRI`，其和`PRIMASK`一样都是ARM CPU用于控制中断的存器，但非全部屏蔽，而是屏蔽比某优先级更低的中断。`configMAX_SYSCALL_INTERRUPT_PRIORITY`为最高可屏蔽的中断优先级(默认为5)。比此优先级更高的中断在临界区内不会被屏蔽，故其中断服务函数中不应执行带系统调用函数。
* 系统使用的中断优先级：系统在开始调度的函数`xPortStartScheduler()`中设置PendSV和SysTick硬件中断优先级为`configKERNEL_INTERRUPT_PRIORITY`，一般为硬件支持的最低优先级。
* 为保证系统正常运行，在中断中调用的系统API务必为带FromISR的函数。

### 内存管理

* 与ucos中全系统未使用动态内存分配不同，FreeRTOS有大量功能是以动态内存分配的方式实现的，而标准库中的malloc和free在嵌入式实时系统中虽一般情况下可用，但会有低效，和系统不适配等等问题，故FreeRTOS将内存管理函数作为接口函数，并提供了heap_1.c到heap_5.c等分配方案，也可用户自己实现。
  * heap_3：对malloc和free封装，使用的是.s文件中定义的堆，不使用ucHeap[]
  * heap_1：有分配无释放
  * heap_2：有分配释放但无合并管理，大量碎片
  * heap_4：有类似malloc的合并管理，且效率更高
  * heap_5：支持内存堆跨越多个不连续内存段，其余和4相似

### 时钟系统和延时

* 系统时钟依靠SysTick中断维护，全局的xTickCount在此中断中不断加一，其为32位无符号整型，会溢出。
* vTaskDelay()相对延时函数，从调用该函数起开始延时若干个周期。

* vTaskDelayUntil()绝对延时函数，从上次该函数解阻塞起开始延时若干个周期，可让任务以一个绝对的周期解阻塞。
* 延时功能的实现依赖于xDelayedTaskList1和xDelayedTaskList2两个列表，其管理的每一个列表项对应某一个任务的状态列表项，按升序排列，即列表的第一个列表项永远对应下一个要结束延时的任务。相对于ucos中`遍历已使用任务控制块链表,再对表内每一个延时和等待事件的任务的延时时间减一`这种维护方式要高效很多。但如此管理就必须考虑全局系统时钟计数器溢出的问题，所以需要两个列表在不同时刻间歇交替地表示未溢出和溢出的列表，与之配合的有两个列表指针，一个永远指向未溢出列表，一个永远指向溢出列表，这两个指针在每一次溢出时进行对换。
* 任务间通讯的超时时间也是通过这套延时系统来维护的。

## 系统结构

### 重要数据结构

``` c
// 任务控制块，省略了很多条件编译成员变量
typedef struct tskTaskControlBlock
{
	volatile StackType_t *pxTopOfStack;						// 指向该任务堆栈栈顶
	ListItem_t			 xStateListItem;					// 任务的状态列表项
	ListItem_t			 xEventListItem;					// 任务的事件列表项
	UBaseType_t			 uxPriority;						// 优先级
	StackType_t			 *pxStack;							// 堆栈栈底
	char				 pcTaskName[ configMAX_TASK_NAME_LEN ];  // 任务名
} tskTCB;
typedef tskTCB TCB_t;

// 列表:FreeRTOS中最核心的数据结构之一
typedef struct xLIST
{
	listFIRST_LIST_INTEGRITY_CHECK_VALUE			  // 完整性校验1
	configLIST_VOLATILE UBaseType_t uxNumberOfItems;  // 列表内列表项数目
	ListItem_t * configLIST_VOLATILE pxIndex;		  // 当前索引，用于遍历
	 // 存在列表结构体内的列表项，逻辑上表示最后一个列表项，其Item值为最大(32位系统中为0xFFFFFFFF)
    MiniListItem_t xListEnd;						 
	listSECOND_LIST_INTEGRITY_CHECK_VALUE			  // 完整性校验2
} List_t;

// 列表项
struct xLIST_ITEM
{
	listFIRST_LIST_ITEM_INTEGRITY_CHECK_VALUE 			// 完整性校验1
	// 列表项值，用于记录任务延时到时时间(状态列表项)或存任务优先级的反逻辑补数(越小优先级越高)(事件列表项)。列表项在列表中的排序以xItemValue升序排列。
    configLIST_VOLATILE TickType_t xItemValue;
	struct xLIST_ITEM * configLIST_VOLATILE pxNext;		// 后继指针
	struct xLIST_ITEM * configLIST_VOLATILE pxPrevious; // 前向指针
	void * pvOwner;										// 用于记录拥有该列表项的任务控制块
	void * configLIST_VOLATILE pvContainer;				// 用于记录目前该列表项存在哪个列表
	listSECOND_LIST_ITEM_INTEGRITY_CHECK_VALUE			// 完整性校验2
};
typedef struct xLIST_ITEM ListItem_t;	

// 队列:实现任务间通讯的核心数据结构
typedef struct QueueDefinition
{
    int8_t *pcHead;             /* 指向队列存储区起始位置,即第一个队列项 */
    int8_t *pcTail;             /* 指向队列存储区结束后的下一个字节 */
    int8_t *pcWriteTo;          /* 指向队列存储区的下一个写入位置 */
    union                       /* 使用联合体用来确保两个互斥的结构体成员不会同时出现 */
    {
        int8_t *pcReadFrom;     /* 当结构体用于队列时,指向队列存储区的下一个取出位置 */
        /* 当结构体用于互斥量时,用作计数器,保存递归互斥量被"获取"的次数. */
        UBaseType_t u xRecursiveCallCount;
    } u;

    List_t xTasksWaitingToSend;      /* 因等待入队而阻塞的任务列表,按照优先级顺序存储 */
    List_t xTasksWaitingToReceive;   /* 因请求队列内容而阻塞的任务列表,按照优先级顺序存储 */

    volatile UBaseType_t uxMessagesWaiting; /* 当前队列的队列项数目，在信号量中表示当前资源数 */
    UBaseType_t uxLength;            		/* 最大队列项个数，在信号量中表示最大资源数 */
    UBaseType_t uxItemSize;          		/* 每个队列项的大小，在信号量中为0 */

	/* 队列上锁后,存储移出列列表项的数目，如果队列没有上锁，设置为queueUNLOCKED */
    volatile BaseType_t xRxLock;
    /* 队列上锁后,存储存入列列表项的数目，如果队列没有上锁，设置为queueUNLOCKED */
	volatile BaseType_t xTxLock;
} xQUEUE;
typedef xQUEUE Queue_t;
```

### 重要全局和静态变量

``` c
PRIVILEGED_DATA TCB_t * volatile pxCurrentTCB;  /* 当前运行的任务TCB */
PRIVILEGED_DATA static volatile UBaseType_t uxTopReadyPriority;  /* 优先级就绪标志 */
PRIVILEGED_DATA static volatile TickType_t xTickCount;  /* 系统时钟计数 */

/* 以下均属于状态列表，任务控制块成员变量中的状态列表项会存在以下列表中的某一个 */
PRIVILEGED_DATAstatic List_t pxReadyTasksLists[ configMAX_PRIORITIES ]; /*就绪任务列表数组*/
/* 因为FreeRTOS管理延时是通过List_t中列表项的升序排列，故计数器溢出会影响正常逻辑，所以取两个管理延时的列表，如果延时时算出的目标计数小于当前计数，则存在当前列表的另一个列表，发生溢出时将两列表调换即可 */
PRIVILEGED_DATA static List_t * volatile pxDelayedTaskList; /* 指向当前使用的延时List_t */
PRIVILEGED_DATAstatic List_t xDelayedTaskList1;			/* 延时的任务1 */
PRIVILEGED_DATA static List_t * volatile pxOverflowDelayedTaskList; /*指向溢出的延时List_t*/
PRIVILEGED_DATAstatic List_t xDelayedTaskList2;			/* 延时的任务2 */
PRIVILEGED_DATAstatic List_t xPendingReadyList; 		/* 任务已就绪,但调度器被挂起 */
PRIVILEGED_DATA static List_t xTasksWaitingTermination; /* 任务已经被删除,但内存尚未释放 */
PRIVILEGED_DATA static List_t xSuspendedTaskList;       /* 当前挂起的任务 */
```

### 任务

#### 存储思路 

* xTaskCreate() 动态分配任务的任务控制块和任务堆栈内存，将任务堆栈初始化，并将任务的状态列表项加入就绪列表。返回任务控制块的句柄(结构体头指针)。

#### 调度思路 

* 调度函数taskYIELD()

  ​    与ucos相同，产生一个PendSV(可挂起的系统调用)异常，在异常处理函数PendSV_Handler中执行任务切换。具体的汇编级的切换流程也和ucos基本相同。

* 如何获取最高优先级已就绪任务？

  ​    对于有硬件支持的CPU如Cotex-M，可用CLZ指令计算一个32数的前导0数目，以此为依据设计全局变量uxTopReadyPriority，其bit0代表最低优先级0，bit31代表最高优先级31。维护此全局变量来确定最高优先级已就绪任务。相对ucos维护优先级就绪表的方式要高效不少。
  
  ​	而对于没有硬件支持的CPU，则会从最高优先级遍历`pxReadyTasksLists[configMAX_PRIORITAIES]`，找到第一个非空列表指针，若任务较多则相当浪费资源。
  
* 执行调度的时机也和ucos不同，ucos会在各种操作以及滴答计时器中断的系统心跳中每次都执行任务调度；而FreeRTOS在包括系统心跳时钟之内的各种可能触发调度的地方，都对当前帧就绪的新任务是否优先级高于当前运行的任务进行了判断，在需要调度时才进行调度。

### 软件计时器

* FreeRTOS的软件计时器和ucos一样由一个独立的任务管理，系统提供的相关API实质都是向该任务用队列传递消息。
* 其处理逻辑与ucos有很大区别，并非一直跑与系统心跳相同的循环，而是和系统延时采用类似思路，维护当前和溢出两个列表，只判断最早可能就绪的任务，并在合适的时机阻塞至最早可能就绪的任务就绪。

### 任务间通讯

#### 队列

* 队列是ucos中实现任务间通讯最核心的数据结构，所有的事件都是依赖队列实现的。其核心在于维护一个环形队列，创建时指定了单个队列项的长度和队列项数目，任何一个入队的数据入队的都是数据本身而不是指针，相较于ucos传递指针的方式，更不易出现目标地址处数据被意外修改等与逻辑不符的问题，但也会牺牲一部分的RAM资源；但是，使用者仍可以用这种机制以引用的方式传递数据，即将数据指针入队。另外队列还维护了入队等待列表和出队等待列表来存放任务的事件列表项，保证高优先级任务优先使用队列，使队列即使满或空也可正常工作。

* 所有的任务间通讯API中的创建， 发送，请求等操作都是对队列操作API的封装。

  ```c 
  QueueHandle_t xQueueGenericCreate(
                  const UBaseType_t uxQueueLength,  	/* 队列最大长度 */
                  const UBaseType_t uxItemSize, 		/* 队列项大小 */
                  uint8_t *pucQueueStorage, 			/* 静态时使用，队列项起始地址 */
                  StaticQueue_t *pxStaticQueue, 		/* 静态时使用，队列结构体起始地址 */
                  const uint8_t ucQueueType			/* 表示队列/各种信号量/队列集合 */
  	)
      
  BaseType_t xQueueGenericSend(
  					QueueHandle_t xQueue, 				/* 队列句柄 */
  					const void * const pvItemToQueue, 	/* 要入队的数据 */
  					TickType_t xTicksToWait,/* 超时时间 0:不阻塞 portMAX_DELAY:永远阻塞*/
  					const BaseType_t xCopyPosition 		/* 入队位置 */
  	)
  ```

* FreeRTOS对入队和出队都提供了阻塞超时功能，超时时间0代表不阻塞，portMAX_DELAY代表永久阻塞，其他代表正常。该功能的实现也是交由处理Delay的逻辑判断TimeOut。

#### 信号量

* 信号量种类：计数/二值/互斥/递归互斥，和ucos相同，常用为计数/互斥。计数/二值用于任务同步，一个任务可以请求但不释放；互斥用于公共资源保护，请求和释放必须在一个任务，一般用以实现互斥锁的机制。互斥信号量拥有优先级继承机制，用以减少优先级翻转带来的影响。
* 信号量的实现：创建一个队列项Size为零的队列，用uxMessagesWaiting表示当前可获取信号量数目，用uxLength表示最大信号量资源数。在递归互斥信 号量中用xRecursiveCallCount表示递归调用次数。

#### 事件标志组

* 用于进行多个任务的逻辑同步。
* 事件标志组并未使用队列结构，它有一套自己的简单数据结构。

### 任务通知

* 原理是在任务控制块加了通知状态和通知值两个成员变量。
* 可以用小很多的RAM和CPU资源实现轻量级的信号量，消息邮箱，事件标志组的机制。
* 局限性在于发送事件时不能阻塞，而且基于任务控制块实现，一个任务受多个控制，不能多个任务受一个事件控制；灵活性不如常规事件，但大多数情况下其提供的功能已然足够。

### Question

1. 在请求队列项时，若将TimeOut设置为MAX_Delay，则会将任务的状态列表项放在SuspendedList上，将任务的事件列表项放在队列的WaitingToSend列表上，这种管理逻辑和Timeout/Suspend独立管理的ucos完全不同，为何？

   > 其实是一样的，这里将状态列表项挂在挂起列表上并不是真的挂起，解挂函数在执行时会判断这个列表项对应的任务的事件列表项的挂载列表是否为空，若非空则不解挂。也就是说依然只有事件到来能使该任务解阻塞，挂在挂起列表上只是为了不被延时列表管理。

2. 中断服务函数中的系统API有什么区别？

   > 主要是将API中可能会有的延时去掉，再加入一个确定是否有高优先级任务就绪的标志，用于判断是否需要接下来在中断中手动执行任务调度。
   >
   > 高于系统可管理优先级的中断，不会被临界区屏蔽，不受系统管理，故不应该使用XXXISR的系统API

3. 操作系统的临界区到底在保护什么?

   > 主要是为了防系统自己，若无临界区机制，滴答时钟及其他中断可能会在操作系统运行的任何一行代码处打断，因对系统维护的共享内存区的一些数据的存取并非原子操作，故这么搞可能会导致严重逻辑问题的出现。所以设置临界区对操作系统来说主要是为了保证运行逻辑和设计逻辑一致，而并非为保证严格的时序。当然，应用层也可用临界区保证一些精确时序的控制。

### 总结对比

**[]内为实际测试后发现和之前想的不同，故进行二次修改**

#### 相同点

* 都使用滴答计时器的硬件中断提供系统的心跳时钟
* 任务调度部分保存现场恢复现场的流程基本一致
* 整体调度思路和实际以及实现的一些通讯方式都较为一致，只是实现方式有所不同。

#### 不同点

* 内存分配：UCOS倾向于使用静态内存分配的策略，系统的各种资源如task，event，tmr，queue都有各自的全局数组，使用时直接从全局数组中取；而FreeRTOS对于各种资源都是用heap_x.c中设置的内存分配策略进行分配和释放，有用静态数组实现的，也有封装malloc和free实现的。

  > 在配置不得当时，UCOS这种提前分配内存的方式会造成很大资源浪费，但若配置合适时，静态分配内存和动态分配内存其实各有优劣。动态分配更加灵活节省空间，而静态内存分配一般来说更加稳定。

* 对延时的管理：UCOS处理延时的方式为`在每一次滴答计时器中断中, 遍历整个已使用任务列表，将其中表示延时的成员变量不为0的值减一`，感觉比较浪费资源；FreeRTOS是维护了一个延时列表，其中的列表项为`处于延时或等待事件`状态任务的状态列表项，列表项升序排列，排列依据为列表项值，在此处为延时到时时间，FreeRTOS在每个滴答计时器中断中比较当前计数和下个到时时间，以此判定是否有任务到时。

  > 个人认为在任务较多时，UCOS这种遍历的方式相当浪费资源；FreeRTOS的处理方式应该明显更优。 
  >
  > [后经测试发现，多个任务空跑延时加调度时其实是UCOS占用CPU资源较少，分析应该是因为FreeRTOS实现列表内列表项升序排列的过程也很消耗资源]

* 确定最高优先级任务的方法： UCOS确定当前已就绪的最高优先级任务的方式是维护了一个全局的任务就绪表，查询最高优先级任务需要两次查表，一次乘法一次移位；FreeRTOS则维护了一个32位的优先级就绪数，每一位对应一个优先级任务的就绪情况，用CLZ汇编指令拿取该就绪数的前导0数目，用以获取最高优先级的已就绪任务。(仅在有CLZ硬件支持的情况下可以使用)

  >  UCOS的就绪表机制设计的很有趣，其获取最高优先级就绪任务和事件等待中的最高优先级任务都是基于就绪表实现的；但FreeRTOS中用寻找最高优先级任务的硬件方法明显更快，事件等待列表的升序排列机制应该也会比UCOS快。
  >
  >  [升序排列机制应该并不比就绪表的方式快...毕竟相比于就绪表的查表、移位、置位的操作，实现插入列表需要一系列操作，甚至可能需要多次比较实现升序排列]

* 执行任务调度的时机：UCOS在各种诸如创建删除挂起解挂请求等等操作后均会执行一次任务调度；FreeRTOS则仅在判断新就绪任务的优先级高于当前任务时才会执行调度

  > 这个可能影响不大，但FreeRTOS应该全面更优。

* 软件计时器的实现策略：ucos设计了计时器控制块，计时器轮辐，在独立任务中以和系统心跳同频的频率持续判断有无到时任务；FreeRTOS也设计了和任务控制块相似的计时器控制块，基于列表管理，在独立任务中不断阻塞任务至下个计时器到时或任务到来。

  > 从直观上看来当计时器不那么多时，在软件计时器上FreeRTOS消耗的资源要少于UCOS。

* 任务间传递消息的方式：UCOS中mbox和queue均是通过任务控制块传递消息的引用，故用队列时需要自己对 目标消息动态分配内存；而FreeRTOS通过队列实现各种任务间通讯，该结构传递的是数据的内存拷贝，而不是引用，在数据入队和出队时使用的时memcpy()，如此设计使用时会简单不少，而且当目标数据过长时，仍可以手动传递数据的指针。

  > 相对于传指针，性能上内存拷贝要慢不少，但使用时不需要自行分配和管理内存，用起来方便很多。

#### 杂记

`Program Size: Code=41338 RO-data=4558 RW-data=368 ZI-data=25832  `

* FreeRTOS动态分配的用于任务堆栈的内存区会从ZI区(零初始化区)取，config中`configTOTAL_HEAP_SIZE`会被编译器分配到ZI区。

  