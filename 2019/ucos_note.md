## UCOS

> ​	本笔记较为详细地记录了UCOSII操作系统实现的大体流程，因为为笔者的学习笔记，故不推荐直接零基础看。推荐对操作系统有大体了解后，并希望更加深入了解时，再翻阅本笔记。
>
> ​	使用操作系统可以更好地实现任务间的协调，虽然运行之会消耗一部分CPU资源，但可以带来更高效的任务协调和同步，从另一层面减小了资源浪费。也可以提供更清晰的程序框架，方便协作交流。
>
> ​	版本：UCOSII V2.91

* II和III的部分区别
  * II中各种操作的参数与III有很多不同，III中要复杂很多。
  * II中任务优先级即为任务ID，同优先级只能存在一个任务；III中同优先级可设置多个任务，初始化每个任务时可为其分配时间片，支持时间片轮转调度同优先级任务。
  * II中分为消息邮箱和消息队列，而III中只有消息队列。
  * III中每个任务都有内嵌信号量和内嵌消息队列。
  * II中所有通讯都基于事件控制块ECB，创建和操作都是基于ECB；而III中取消了这一设计，信号量是信号量，消息队列是消息队列，创建和操作时都直接使用各自的数据结构，并没有进行统一管理。

* UCOS中的任务堆栈
  * 任务堆栈是UCOS实现任务调度的关键，其本体是ram中栈区外静态分配的一块数组，实现与内存栈相似的功能。即像内存中的栈区一样存储运行时的局部变量，并在任务调度发生时将CPU寄存器值入栈，保存当前任务的现场，在重获执行权之后恢复现场。
  * 其大小应根据任务需要使用的局部变量，和函数的嵌套调用导致的所需栈空间大小进行分配。
* UCOS任务调度
  * 任务调度通过任务级调度OS_Sched()和中断级调度OSIntExit()中调用OS_TASK_SW()实现的。
  * 任务调度过程的本质大概可以理解为：1.查询任务就绪表中最高优先级的任务。2.保存当前执行任务的现场，恢复目标任务的现场至CPU。 3.若为UCOS-III则再多一个时间片轮转的逻辑。
  * 每次退出硬件中断时，ucos都会进行一次任务切换，其系统心跳节拍在stm32上是通过滴答计时器来实现的，周期由滴答定时器选择的时钟和滴答计时器的重装载值决定。在SysTick_Handler的硬件中断处理时会不断进行任务切换。

### UCOS源码阅读笔记

> 下文代码源自ucosii-V2.91，根据个人理解进行了部分删减，适合用于理解其基本功能的运行逻辑。

#### 头文件 

```c 
/****************************************************************************************
*						ucos_ii.h头文件部分,仅记录了一些重要部分，并不完全 
****************************************************************************************/
```

##### 宏定义部分

```c
/***** 宏定义部分 *****/
// MISCELLANEOUS 杂毛宏定义
#define  OS_TASK_STAT_PRIO (OS_LOWEST_PRIO - 1u)  		/* 统计任务优先级，倒数第二 */
#define  OS_TASK_IDLE_PRIO (OS_LOWEST_PRIO)  	  		/* 空闲任务优先级，优先级最低 */
#define  OS_EVENT_TBL_SIZE ((OS_LOWEST_PRIO) / 8u + 1u) /* 事件表大小 */
#define  OS_RDY_TBL_SIZE   ((OS_LOWEST_PRIO) / 8u + 1u) /* 就绪任务表大小 */
#define  OS_TCB_RESERVED        ((OS_TCB *)1)           /* 用于表示某优先级任务已被留存 */

// TASK STATUS 任务状态宏定义
#define  OS_STAT_RDY       0x00u  /* 就绪 */
#define  OS_STAT_SEM       0x01u  /* 等待信号量 */
#define  OS_STAT_MBOX      0x02u  /* 等待消息邮箱 */
#define  OS_STAT_Q         0x04u  /* 等待消息队列 */
#define  OS_STAT_SUSPEND   0x08u  /* 任务挂起 */
#define  OS_STAT_MUTEX     0x10u  /* 等待互斥信号量 */
#define  OS_STAT_FLAG      0x20u  /* 等待事件标志组 */
#define  OS_STAT_MULTI     0x80u  /* Pending on multiple events             */
 
#define  OS_STAT_PEND_ANY  (OS_STAT_SEM | OS_STAT_MBOX | OS_STAT_Q | OS_STAT_MUTEX | OS_STAT_FLAG)

// TASK PEND STATUS 任务等待状态标志
#define  OS_STAT_PEND_OK                0u  /* 正常等待完成 */
#define  OS_STAT_PEND_TO                1u  /* 等待超时标志 */
#define  OS_STAT_PEND_ABORT             2u  /* 等待放弃标志 */

// OS_EVENT types 事件种类
#define  OS_EVENT_TYPE_UNUSED           0u  /* 未分配 */
#define  OS_EVENT_TYPE_MBOX             1u  /* 消息邮箱 */
#define  OS_EVENT_TYPE_Q                2u  /* 消息队列 */
#define  OS_EVENT_TYPE_SEM              3u  /* 信号量 */
#define  OS_EVENT_TYPE_MUTEX            4u  /* 互斥信号量 */
#define  OS_EVENT_TYPE_FLAG             5u  /* 事件标志组 */

// EVENT FLAGS 事件标志组宏定义
#define  OS_FLAG_WAIT_CLR_ALL           0u  /* 触发逻辑为标志组全为0 */
#define  OS_FLAG_WAIT_CLR_AND           0u

#define  OS_FLAG_WAIT_CLR_ANY           1u  /* 触发逻辑为标志组任意一个为0 */
#define  OS_FLAG_WAIT_CLR_OR            1u

#define  OS_FLAG_WAIT_SET_ALL           2u  /* 触发逻辑为标志组全为1 */
#define  OS_FLAG_WAIT_SET_AND           2u

#define  OS_FLAG_WAIT_SET_ANY           3u  /* 触发逻辑为标志组任意一个为1 */
#define  OS_FLAG_WAIT_SET_OR            3u

#define  OS_FLAG_CONSUME             0x80u  /* 满足条件后是否清除flag */

#define  OS_FLAG_CLR                    0u
#define  OS_FLAG_SET                    1u

// 事件删除函数可选项
#define  OS_DEL_NO_PEND                 0u
#define  OS_DEL_ALWAYS                  1u

// OSXXXPend() OPTIONS 等待函数可选项
#define  OS_PEND_OPT_NONE               0u  /* 使在等待该事件的最高优先级的任务放弃等待*/
#define  OS_PEND_OPT_BROADCAST          1u  /* Abort时使用，取消所有等待该事件的任务 */

// OSXXXPostOpt() OPTIONS 发送函数可选项
#define  OS_POST_OPT_NONE            0x00u  /* 默认 */
#define  OS_POST_OPT_BROADCAST       0x01u  /* 仅在邮箱和消息队列使用，同时向所有等待任务发送 */
#define  OS_POST_OPT_FRONT           0x02u  /* 仅在消息队列使用，发到消息队列最前 */
#define  OS_POST_OPT_NO_SCHED        0x04u  /* 仅在邮箱和消息队列使用，不触发任务调度 */

// TIMER OPTIONS (软件定时器相关可选项)
#define  OS_TMR_OPT_NONE                0u  /* 默认 */

#define  OS_TMR_OPT_ONE_SHOT            1u  /* 单次计时 */
#define  OS_TMR_OPT_PERIODIC            2u  /* 周期性重置 */
    
// TIMER STATES 软件定时器状态
#define  OS_TMR_STATE_UNUSED            0u  /* 未被分配 */
#define  OS_TMR_STATE_STOPPED           1u  /* 创建了但未被加入轮辐 */
#define  OS_TMR_STATE_COMPLETED         2u  /* 单次计时完成 */
#define  OS_TMR_STATE_RUNNING           3u  /* 计时中 */

// ERROR CODES 错误码
......
```

##### 数据结构部分

``` c
/***** 数据结构部分 *****/
  // EVENT CONTROL BLOCK 事件控制块
  typedef struct os_event {
      INT8U    OSEventType;                    /* 事件种类 */
      /* 可以在各种地方使用，FreeList指向下个ECB、传消息时指向消息、在Mutex中指向占有信号量的TCB */
      void    *OSEventPtr;                     
      INT16U   OSEventCnt;                     /* 信号量计数(仅信号量有用) */
      /* 等待该事件的任务优先级组 OS_PRIO根据优先级总数选择为u8或u16*/
      OS_PRIO  OSEventGrp;                   
      OS_PRIO  OSEventTbl[OS_EVENT_TBL_SIZE];/* 等待该事件的任务优先级表 */
#if OS_EVENT_NAME_EN > 0u
      INT8U   *OSEventName;                    /* 事件名 */
  #endif
  } OS_EVENT;

  // EVENT FLAGS CONTROL BLOCK 事件标志组
  typedef struct os_flag_grp {
      INT8U         OSFlagType;    /* 等价OSEventType,只能为OS_EVENT_TYPE_FLAG */
      void         *OSFlagWaitList;/* 等待该事件标志组的事件标志组任务节点链表头 */
      OS_FLAGS      OSFlagFlags;   /* 根据OS_FLAGS_NBITS设置为8/16/32 */
#if OS_FLAG_NAME_EN > 0u
      INT8U        *OSFlagName;    /* 事件标志组名 */
  #endif
  } OS_FLAG_GRP;

  // 事件标志组等待任务节点
  typedef struct os_flag_node {
      void         *OSFlagNodeNext;           /* 指向下个节点 */
      void         *OSFlagNodePrev;           /* 指向前一个节点 */
      void         *OSFlagNodeTCB;            /* 指向当前节点对应的任务控制块 */
      void         *OSFlagNodeFlagGrp;        /* 指回OS_FLAG_GRP */
      OS_FLAGS      OSFlagNodeFlags;          /* 该任务实际要等待哪些标志位 */
      INT8U         OSFlagNodeWaitType;       /* 触发逻辑全0/任意0/全1/任意1 */
  } OS_FLAG_NODE;
  #endif

  // MESSAGE MAILBOX DATA 消息邮箱
  typedef struct os_mbox_data {
   	  void   *OSMsg;                         /* 指向对应消息 */
      OS_PRIO OSEventTbl[OS_EVENT_TBL_SIZE]; /* 等待该事件的任务优先级表 */
      OS_PRIO OSEventGrp;                    /* 等待该事件的任务优先级组 */
  } OS_MBOX_DATA;

  // MEMORY PARTITION DATA STRUCTURES 内存分配数据结构
  typedef struct os_mem {                   /* 内存控制块 */
      void   *OSMemAddr;                    /* 对应内存区头地址 */
      void   *OSMemFreeList;                /* 空闲内存块链表头 */
      INT32U  OSMemBlkSize;                 /* 单个块内存大小(byte) */
      INT32U  OSMemNBlks;                   /* 该区中的内存块数目 */
      INT32U  OSMemNFree;                   /* 该区中空闲内存块数目 */
  #if OS_MEM_NAME_EN > 0u
      INT8U  *OSMemName;                    /* 内存区名 */
  #endif
  } OS_MEM;
  // 另有一个结构基本一致的 OS_MEM_DATA, 其作用为作为OSMemQuery函数的输入，之所以多此一举是尽量防止用户直接操作系统内核数据结构OS_MEM
  // UCOS提供的动态内存管理机制并不好用，创建内存区时所有内存块大小相同，取用时一次只能取用一个内存块。

  // MUTUAL EXCLUSION SEMAPHORE DATA 互斥信号量
  typedef struct os_mutex_data {
      OS_PRIO OSEventTbl[OS_EVENT_TBL_SIZE];  /* 等待该事件的任务优先级表 */
      OS_PRIO OSEventGrp;                     /* 等待该事件的任务优先级组 */
      BOOLEAN OSValue;                        /* 互斥信号量值 */
      INT8U   OSOwnerPrio;                    /* 使用者优先级，无人使用则置为0xff */
      INT8U   OSMutexPIP;                     /* 优先级继承优先级,防止优先级反转 */
} OS_MUTEX_DATA;

  // MESSAGE QUEUE DATA 消息队列
  typedef struct os_q {                   /* 消息队列控制块 */
      struct os_q   *OSQPtr;              /* 指向下一个消息队列控制块 */
      void         **OSQStart;            /* 循环队列起始地址 */
      void         **OSQEnd;              /* 循环队列结束地址 */
      void         **OSQIn;               /* 下个消息进入的地址 */
      void         **OSQOut;              /* 下个消息取出的地址 */
      INT16U         OSQSize;             /* 队列长度 */
      INT16U         OSQEntries;          /* 队列内消息总数 */
  } OS_Q;
  // 另有结构相近的 OS_Q_DATA, 其作用同OS_MEM_DATA
  
  // SEMAPHORE DATA 信号量DATA，作用同上
  typedef struct os_sem_data {
      INT16U  OSCnt;                          /* 信号量计数 */
      OS_PRIO OSEventTbl[OS_EVENT_TBL_SIZE];  /* 等待该事件的任务优先级表 */
      OS_PRIO OSEventGrp;                     /* 等待该事件的任务优先级组 */
} OS_SEM_DATA;

  // TASK STACK DATA 任务堆栈
  typedef struct os_stk_data {
      INT32U  OSFree;                    /* 任务栈内空闲字节数 */
      INT32U  OSUsed;                    /* 任务栈内已使用字节数 */
} OS_STK_DATA;

  // TASK CONTROL BLOCK 任务控制块 只记录了部分基础成员
  typedef struct os_tcb {
      OS_STK          *OSTCBStkPtr;           /* 任务栈顶指针 */
      
      struct os_tcb   *OSTCBNext;             /* 双向链表下一个 */
      struct os_tcb   *OSTCBPrev;             /* 双向链表前一个 */
  
      OS_EVENT        *OSTCBEventPtr;	 	  /* 指向任务在等待的事件控制块 */
      void            *OSTCBMsg;			  /* 保存从邮箱或队列得到的消息 */  
      
      INT32U           OSTCBDly;              /* Delay的系统时钟次数，或等待事件的timeout */
      INT8U            OSTCBStat;             /* 任务状态 */
      INT8U            OSTCBStatPend;         /* 等待事件状态 */
      INT8U            OSTCBPrio;             /* 优先级 */
  
      INT8U            OSTCBX;                /* 就绪表中X轴实际数 */
      INT8U            OSTCBY;                /* 就绪表中Y轴实际数 */
      OS_PRIO          OSTCBBitX;             /* 就绪表中X轴字节表示 */
      OS_PRIO          OSTCBBitY;             /* 就绪表中Y轴字节表示 */
      /* 若prio=15=1111b, 则OSTCBY = prio>>3 = 1, OSTCBBitY = 1<<OSTCBY = 10b;
      OSTCBX = prio&0x07 = 7, OSTCBBitX = 1 << OSTCBX = 10000000b */
} OS_TCB;

  // TIMER DATA TYPES 软件定时器
  typedef  void (*OS_TMR_CALLBACK)(void *ptmr, void *parg);
  typedef  struct  os_tmr {
      INT8U            OSTmrType;        /* 仅可为OS_TMR_TYPE */
      OS_TMR_CALLBACK  OSTmrCallback;    /* 回调函数,宏定义如上 */
      void            *OSTmrCallbackArg; /* 回调函数传参 */
      void            *OSTmrNext;        /* 双向链表 */
      void            *OSTmrPrev;
      INT32U           OSTmrMatch;       /* OSTmrTime等于该值时认为计时结束 */
      INT32U           OSTmrDly;         /* 周期计时前的等待计数 */
      INT32U           OSTmrPeriod;      /* 计时周期 */
      INT8U            OSTmrOpt;         /* 定时器可选项,见OS_TMR_OPT_XXX */
      INT8U            OSTmrState;       /* 定时器状态:UNUSED/RUNNING/STOPPED */
  } OS_TMR;
  
  typedef  struct  os_tmr_wheel {        /* 计时器轮,在大量计时器时可通过散列操作有效提高效率 */
      OS_TMR          *OSTmrFirst;       /* 该轮辐指向的第一个定时器OS_TMR */
      INT16U           OSTmrEntries;     /* 该轮辐上的计时器总数 */
} OS_TMR_WHEEL;
```

##### 全局变量部分

``` CQL
/***** 全局变量部分，仅记录了部分重要变量 *****/
OS_EXT  INT8U   OSCPUUsage;    /* 统计任务计算的CPU占用率 */
OS_EXT  INT32U  OSIdleCtrMax;  /* 1s内空闲任务执行的最大次数 */
OS_EXT  INT32U  OSIdleCtrRun;  /* 当前1s内空闲任务执行的次数 */
OS_EXT  INT8U   OSIntNesting;  /* 中断嵌套层数 */
OS_EXT  INT8U   OSPrioCur;     /* 当前任务优先级 */
OS_EXT  INT8U   OSPrioHighRdy; /* 最高已就绪任务优先级 */
extern INT8U const OSUnMapTbl[256];         /* 用于优先级判断时的查表 */
OS_EXT  OS_PRIO OSRdyGrp;                   /* 任务就绪组,用于快速查找当前最高优先级任务 */
OS_EXT  OS_PRIO OSRdyTbl[OS_RDY_TBL_SIZE];  /* 任务就绪表,用于快速查找当前最高优先级任务 */
OS_EXT  BOOLEAN OSRunning;     /* 系统内核是否正常工作 */
OS_EXT  INT8U   OSTaskCtr;     /* 创建过的任务计数 */
OS_EXT  OS_TCB  *OSTCBCur;     /* 当前进行任务的TCB */
OS_EXT  OS_TCB  *OSTCBHighRdy; /* 当前就绪态最高优先级任务的TCB */
OS_EXT  OS_TCB  *OSTCBFreeList;/* 仍可使用的空闲TCB单向链表的链表头 */
OS_EXT  OS_TCB  *OSTCBList;    /* 已被使用的TCB双向链表的链表头,新任务向表头添加 */
OS_EXT  OS_TCB  *OSTCBPrioTbl[OS_LOWEST_PRIO + 1u]; /* 根据优先级存储的TCB指针数组，方便查找 */
OS_EXT  OS_TCB   OSTCBTbl[OS_MAX_TASKS + OS_N_SYS_TASKS];  /* 所有TCB本体实际存储的数据结构 */
// 其他诸如event,flag,Q,Tmr,Mem等都有类似*XXXFreeList和XXXTbl[MAX_SIZE]的全局变量

OS_EXT  INT32U    OSTmrTime;       /* 当前计时器计数,会不断溢出回0 */
OS_EXT  OS_EVENT *OSTmrSemSignal;  /* 定时器信号量,每次发送该信号量时会使OSTmrTime加一 */
OS_EXT  OS_STK    OSTmrTaskStk[OS_TASK_TMR_STK_SIZE];  /* 定时器管理任务所用栈 */
OS_EXT  OS_TMR_WHEEL OSTmrWheelTbl[OS_TMR_CFG_WHEEL_SIZE];  /* 定时器轮本体数组 */
```

#### 函数实现部分

```c
/***************************************************************************************  *		  	    	    函数部分,仅细读一些重要函数的实现，以便于方便理解流程 
* 		 	本部分整理的函数仅保留核心部分，对于一些条件编译和异常情况判断的代码会予以剔除
****************************************************************************************/
```

##### os_mem.c

```c
/* ******************* os_mem.c (ucos为用户提供的内存管理，并不常用)  ***************** 
* 内存管理流程大致梳理：ucos全局变量OS_MEM OSMemTbl[]用于存储预定大小的OS_MEM内存区结构体，另有
* OS_MEM *OSMemFreeList作为空闲内存区结构体的链表头指针。创建内存区时即从Tbl中拿取一个内存区结构
* 体，并将结构体中的void *OSMemFreeList成员变量(与空闲内存区链表头指针重名-_-)按照函数输入的起始地
* 址，内存块大小，内存块数目此三个参数，从指定起始地址开始初始化一个内存块链表。之后的取用和释放都以目
* 标内存区结构体下的单个内存块为单位操作(所以不好用)
*********************************************************************************** */

/* **** 创建内存区函数 ****
 * 输入:  addr     起始地址
 *        nblks    内存区中内存块数目
 *        blksize  单个内存块大小
 *        perr     错误码
 * 返回:  OS_MEM * 内存控制块结构体指针
*/
OS_MEM  *OSMemCreate (void   *addr,
                    INT32U  nblks,
                    INT32U  blksize,
                    INT8U  *perr)
{
    OS_MEM    *pmem;
    INT8U     *pblk;
    void     **plink;
    INT32U     loops;
    INT32U     i;

    OS_ENTER_CRITICAL();
    pmem = OSMemFreeList;  /* 用内存区空闲链表OSMemFreeList从全局内存区OSMemTbl[]中拿取一块 */
    if (OSMemFreeList != (OS_MEM *)0) {  /* 更新全局内存区空闲链表 */
        OSMemFreeList = (OS_MEM *)OSMemFreeList->OSMemFreeList;
    }
    OS_EXIT_CRITICAL();
    if (pmem == (OS_MEM *)0) {  /* 判断拿到的内存区是否为空 */
        *perr = OS_ERR_MEM_INVALID_PART;
        return ((OS_MEM *)0);
    }
    /* 将内存区初始化成nklks个内存块的链表结构 */
    plink = (void **)addr;  /* 起始地址转换为二重指针 */
    pblk  = (INT8U *)addr;  /* 起始地址转换为字节指针，方便后面分配空间 */
    loops  = nblks - 1u;
    for (i = 0u; i < loops; i++) {
        pblk +=  blksize;  /* 字节指针向后一个块 */
       *plink = (void  *)pblk;  /* 二重指针解引用，即将addr下的第一个字存为上一行结果处的地址 */
        plink = (void **)pblk;  /* 二重指针向后移一个块 */ 
    }
    *plink              = (void *)0;  /* 内存最后一个块，链表指针指向空 */ 
    /* 初始化内存控制块结构体 */
    pmem->OSMemAddr     = addr; 
    pmem->OSMemFreeList = addr;  /* 此处可能会有疑问，该成员在描述中是指向下一个内存块的，但此处仅为一个不定型指针。解释：其被使用时形如*(void **)OSMemFreeList,强制转换加解引用表示直接取addr地址下第一个字代表的指针 */
    pmem->OSMemNFree    = nblks; 
    pmem->OSMemNBlks    = nblks;
    pmem->OSMemBlkSize  = blksize; 
    *perr               = OS_ERR_NONE;
    return (pmem);
}

/* **** 从内存区中拿取单个内存块函数 ****
 * 输入:  pmem     内存控制块结构体指针
 *        perr     错误码
 * 返回:  void  
*/
void  *OSMemGet (OS_MEM  *pmem,
                 INT8U   *perr)
{
  void      *pblk;
  OS_ENTER_CRITICAL();
  if (pmem->OSMemNFree > 0u) {  
      pblk                = pmem->OSMemFreeList;    /* pblk置为当前空闲内存块的地址 */
      pmem->OSMemFreeList = *(void **)pblk;         /* 将内存控制块的空闲内存块链表指向下个块,具体实现原理见前面函数 */
      pmem->OSMemNFree--;                           /* 可用内存块数目减一 */
      OS_EXIT_CRITICAL();
      *perr = OS_ERR_NONE;                          
      return (pblk);                                /* 返回单个空闲内存块的地址 */
  }
  OS_EXIT_CRITICAL();
  *perr = OS_ERR_MEM_NO_FREE_BLKS;                  /* 无空闲内存块错误 */
  return ((void *)0);                               
}
```

##### os_time.c

```c
/* ********************** os_time.c (时间管理，并不是软件计时器)  *********************** 
* 	系统延时：ucos中实现延时的方式是在任务就绪表中为当前运行任务清0，并在OSTCBDly中装载延时周期数，
* 然后执行一次任务调度让出CPU，该任务便停在delay处直到再次获得CPU。
*
* 	系统心跳时钟管理(本应在os_core.c中，跟系统时间管理关系比较大，故拿到此处)：基本流程为：先对一些
* 表示全局系统时间的变量加一，然后遍历已使用任务控制块链表，对其中一般延时和等待事件的任务分别减Dly周
* 期，若减到零且该任务未被挂起则在就绪表中恢复。
*********************************************************************************** */

/* **** 从内存区中拿取单个内存块函数 ****
 * 输入:  ticks     延时周期数
*/
void  OSTimeDly (INT32U ticks)
{
    INT8U      y;
    if (OSIntNesting > 0u) {                     /* 中断中不可调用 */
        return;
    }
    if (OSLockNesting > 0u) {                    /* 调度器上锁时不可调用 */
        return;
    }
    if (ticks > 0u) {                            
        OS_ENTER_CRITICAL();
        y            =  OSTCBCur->OSTCBY;        
        OSRdyTbl[y] &= (OS_PRIO)~OSTCBCur->OSTCBBitX;  /* 更新任务就绪表和任务就绪组 */
        if (OSRdyTbl[y] == 0u) {
            OSRdyGrp &= (OS_PRIO)~OSTCBCur->OSTCBBitY;
        }
        OSTCBCur->OSTCBDly = ticks;              /* 装载延时计数 */
      OS_EXIT_CRITICAL();
        OS_Sched();                              /* 执行一次调度 */
    }
}

/* **** 系统心跳时间管理 ****
 * 无输入无输出
*/
void  OSTimeTick (void)
{
      OS_TCB    *ptcb;
  #if OS_TIME_GET_SET_EN > 0u  /* 可使用拿取系统时间功能 */
      OS_ENTER_CRITICAL();                                   
      OSTime++;
      OS_EXIT_CRITICAL();
  #endif
      if (OSRunning == OS_TRUE) {
          ptcb = OSTCBList;                              /* 取已使用的任务控制块链表头 */
          while (ptcb->OSTCBPrio != OS_TASK_IDLE_PRIO) { /* 遍历直到链表尾的空闲任务 */
              OS_ENTER_CRITICAL();
              if (ptcb->OSTCBDly != 0u) {                /* 操作每一个处于延时状态的任务 */
                  ptcb->OSTCBDly--;                          
                  if (ptcb->OSTCBDly == 0u) {            /* 若减到零 */
                      /* 若在等待某个事件,并非一般延时 */
                      if ((ptcb->OSTCBStat & OS_STAT_PEND_ANY) != OS_STAT_RDY) {       
                          /* 清除等待事件状态 */
                          ptcb->OSTCBStat  &= (INT8U)~(INT8U)OS_STAT_PEND_ANY;         
                          /* 等待状态置为超时 */
                          ptcb->OSTCBStatPend = OS_STAT_PEND_TO;
                      } else { 	/* 不在等待事件，则为一般延时，等待状态清0 */
                          ptcb->OSTCBStatPend = OS_STAT_PEND_OK; 
                      }
                      /* 未在挂起状态 */
                      if ((ptcb->OSTCBStat & OS_STAT_SUSPEND) == OS_STAT_RDY) {  
                          /* 就绪表和就绪组更新 */
                          OSRdyGrp               |= ptcb->OSTCBBitY;             
                          OSRdyTbl[ptcb->OSTCBY] |= ptcb->OSTCBBitX;
                    }
                  }
              }
              ptcb = ptcb->OSTCBNext;                    /* 遍历链表 */
              OS_EXIT_CRITICAL();
          }
      }
  }
```

##### os_tmr.c

```c
/* **************************** os_tmr.c (软件计时器)  ******************************* 
* 	软件计时器创建：根据入口参数从全局数组拿取资源，返回计时器控制块。
*
* 	计时器启动：根据目标计时器的不同状态执行不同逻辑，使计时器加入轮辐，启动计时。
*
* 	加入轮辐：根据一次性或周期为OSTmrMatch赋值，然后根据Match和轮辐总数进行散列，确定目标计时器应在
* 的轮辐，并加入对应轮辐的链表头。
*
* 	移出轮辐：将目标计时器从轮辐中移出，更新相关全局变量，并将计时器状态置为STOP。
*
* 	软件计时器管理任务：接收TimeTick发出的信号量，维护与系统心跳周期相同的int型全局变量TmrTime,每一
* 次均遍历当前时间散列得到的定时器轮辐，判断轮辐中的每一个计时器是否到时，并进行相应处理。
*********************************************************************************** */

/* **** 创建软件计时器 ****
*  输入:    dly           延时周期数
*           period        若非单次计时器，设定其触发周期
*           opt           设定计时器为单次或周期
*           callback      回调函数指针 
*           callback_arg  回调函数入口参数指针 
*           pname `       计时器名字符串指针
*           perr          错误码
*  返回:    tmr           计时器控制块
*/
OS_TMR  *OSTmrCreate (INT32U           dly,
                    INT32U           period,
                    INT8U            opt,
                    OS_TMR_CALLBACK  callback,
                    void            *callback_arg,
                    INT8U           *pname,
                    INT8U           *perr)
{
    OS_TMR   *ptmr;
    if (OSIntNesting > 0u) {  /* 中断中不可创建 */
        *perr  = OS_ERR_TMR_ISR;
        return ((OS_TMR *)0);
    }
    OSSchedLock();  /* 调度器上锁 */
    ptmr = OSTmr_Alloc();  /* 从全局计时器数组取出一个计时器控制块 */
    if (ptmr == (OS_TMR *)0) {  /* 若无可用计时器控制块 */
        OSSchedUnlock();
        *perr = OS_ERR_TMR_NON_AVAIL;
        return ((OS_TMR *)0);
    }
    /* 成员变量初始化 */
    ptmr->OSTmrState       = OS_TMR_STATE_STOPPED;  /* 计时器状态置为停止 */
    ptmr->OSTmrDly         = dly;
    ptmr->OSTmrPeriod      = period;
    ptmr->OSTmrOpt         = opt;
    ptmr->OSTmrCallback    = callback;
    ptmr->OSTmrCallbackArg = callback_arg;
    OSSchedUnlock();  /* 调度器解锁 */
    *perr = OS_ERR_NONE;  
    return (ptmr);
}

/* **** 启动计时器 ****
*  输入:    ptmr           计时器控制块
*           perr          错误码
*  返回:    BOOLEAN        是否启动成功
*/
BOOLEAN  OSTmrStart (OS_TMR   *ptmr,
                     INT8U    *perr)
{
    if (ptmr->OSTmrType != OS_TMR_TYPE) {  /* 没啥用的判断,OS_Init时将全局数组内所有tmr均置为此类型 */
        *perr = OS_ERR_TMR_INVALID_TYPE;
        return (OS_FALSE);
    }
    if (OSIntNesting > 0u) {                     /* 中断服务函数中禁止 */
        *perr  = OS_ERR_TMR_ISR;
        return (OS_FALSE);
    }
    OSSchedLock();
    switch (ptmr->OSTmrState) {                  /* 依据当前状态执行动作 */
        /* RUNNING说明正在计时器轮辐中 */
        case OS_TMR_STATE_RUNNING:               /* 若在运行中，重启 */
             OSTmr_Unlink(ptmr);                 /* 从时间轮辐中移除 */
             OSTmr_Link(ptmr, OS_TMR_LINK_DLY);  /* 重新加入时间轮辐 */
             OSSchedUnlock();
             *perr = OS_ERR_NONE;
             return (OS_TRUE);
        /* STOP或COMPLETE说明创建了但不在计时器轮辐中 */
        case OS_TMR_STATE_STOPPED:               /* 若停止或已完成 */
        case OS_TMR_STATE_COMPLETED:
             OSTmr_Link(ptmr, OS_TMR_LINK_DLY);  /* 重新加入时间轮辐 */
             OSSchedUnlock();
             *perr = OS_ERR_NONE;
             return (OS_TRUE);
        /* UNUSED说明还未创建 */
        case OS_TMR_STATE_UNUSED:                /* 若还没有Create,返回err */
             OSSchedUnlock();
             *perr = OS_ERR_TMR_INACTIVE;
             return (OS_FALSE);
        default:                                 /* 若状态不合法 */
             OSSchedUnlock();
             *perr = OS_ERR_TMR_INVALID_STATE;
             return (OS_FALSE);
  }
}

/* **** Link加入计时器轮辐 ****
* 	输入：ptmr 目标计时器
* 	      type 计时单次或周期
*     返回：无
*/
static void OSTmr_Link (OS_TMR  *ptmr,
                        INT8U    type)
{
    OS_TMR       *ptmr1;
    OS_TMR_WHEEL *pspoke;  // spoke：轮辐
    INT16U        spoke;

    ptmr->OSTmrState = OS_TMR_STATE_RUNNING;
    /* 为OSTmrMatch赋值,该成员与TmrTime比较来判断计时器是否到时 */
    if (type == OS_TMR_LINK_PERIODIC) {               /* 若为周期计时 */
        ptmr->OSTmrMatch = ptmr->OSTmrPeriod + OSTmrTime;
    } else {                                          /* 若为单次计时 */
        if (ptmr->OSTmrDly == 0u) {
            ptmr->OSTmrMatch = ptmr->OSTmrPeriod + OSTmrTime;
        } else {
            ptmr->OSTmrMatch = ptmr->OSTmrDly    + OSTmrTime;
        }
    }
    /* 根据到时计数TmrMatch进行散列得到轮辐编号 */
    spoke  = (INT16U)(ptmr->OSTmrMatch % OS_TMR_CFG_WHEEL_SIZE);
    /* 拿到全局轮辐数组对应结构体指针 */
    pspoke = &OSTmrWheelTbl[spoke];

    /* 将目标计时器加入对应轮辐 */
    if (pspoke->OSTmrFirst == (OS_TMR *)0) {           /* 若轮辐为空 */
        /* 使目标计时器成为轮辐中第一个计时器 */
        pspoke->OSTmrFirst   = ptmr;
        ptmr->OSTmrNext      = (OS_TMR *)0;
        pspoke->OSTmrEntries = 1u;
    } else {                                           /* 若轮辐非空 */
        /* 在链表头插入目标计时器,更新双向链表 */
        ptmr1                = pspoke->OSTmrFirst;     
        pspoke->OSTmrFirst   = ptmr;
        ptmr->OSTmrNext      = (void *)ptmr1;
        ptmr1->OSTmrPrev     = (void *)ptmr;
        pspoke->OSTmrEntries++;
    }
    ptmr->OSTmrPrev = (void *)0;  /* 各轮辐的第一个计时器的前驱节点均为空 */
}

/* **** UnLink移出计时器轮辐 ****
* 	输入：目标计时器
*     返回：无
*/
static  void  OSTmr_Unlink (OS_TMR *ptmr)
{
    OS_TMR        *ptmr1;
    OS_TMR        *ptmr2;
    OS_TMR_WHEEL  *pspoke;
    INT16U         spoke;

    spoke  = (INT16U)(ptmr->OSTmrMatch % OS_TMR_CFG_WHEEL_SIZE);  /* 算出目标计时器所在轮辐 */
    pspoke = &OSTmrWheelTbl[spoke];   /* 拿取目标轮辐结构体指针 */

    /* 根据是否是链表头进行不同操作,将目标计时器移出轮辐 */
    if (pspoke->OSTmrFirst == ptmr) {  /* 若是链表头 */
        ptmr1              = (OS_TMR *)ptmr->OSTmrNext;
        pspoke->OSTmrFirst = (OS_TMR *)ptmr1;
        if (ptmr1 != (OS_TMR *)0) {    /* 若去除目标计时器后，轮辐为空 */
            ptmr1->OSTmrPrev = (void *)0;
        }
    } else {                           /* 若非链表头 */
        ptmr1            = (OS_TMR *)ptmr->OSTmrPrev;
        ptmr2            = (OS_TMR *)ptmr->OSTmrNext;
        ptmr1->OSTmrNext = ptmr2;
        if (ptmr2 != (OS_TMR *)0) {
            ptmr2->OSTmrPrev = (void *)ptmr1;
        }
    }
    ptmr->OSTmrState = OS_TMR_STATE_STOPPED;  /* 状态变为停止 */
    ptmr->OSTmrNext  = (void *)0;
    ptmr->OSTmrPrev  = (void *)0;
  pspoke->OSTmrEntries--;
}

/* **** 计时器管理任务 ****
* 	无输入无输出
*/
static  void  OSTmr_Task (void *p_arg)
{
    INT8U            err;
    OS_TMR          *ptmr;
    OS_TMR          *ptmr_next;
    OS_TMR_CALLBACK  pfnct;
    OS_TMR_WHEEL    *pspoke;
    INT16U           spoke;
    
    for (;;) {                                                   /* 死循环 */
        /* 等待TmrSemSignal信号,该信号由OSTimeTickHook()发出,即周期和系统心跳相同 */
        OSSemPend(OSTmrSemSignal, 0u, &err);                     
        OSSchedLock();
        OSTmrTime++;                                          /* TmrTime加1，表示当前时间 */
        /* 对每一帧进行散列操作，对应不同计时器轮辐，提高效率 */
        spoke  = (INT16U)(OSTmrTime % OS_TMR_CFG_WHEEL_SIZE);    
        pspoke = &OSTmrWheelTbl[spoke];
        ptmr   = pspoke->OSTmrFirst;                      /* 拿到当前对应轮辐上第一个计时器 */
        while (ptmr != (OS_TMR *)0) {                            /* 遍历整个轮辐 */
            /* 先拿到下一个计时器，因为当前计时器可能会到时后从轮辐移出 */
            ptmr_next = (OS_TMR *)ptmr->OSTmrNext;               
            /* 若TmrTime与TmrMatch相同，则表示到时 */
            if (OSTmrTime == ptmr->OSTmrMatch) {                 
                OSTmr_Unlink(ptmr);                              /* 移出当前计时器 */
                if (ptmr->OSTmrOpt == OS_TMR_OPT_PERIODIC) {   /* 若当前计时器为循环计时器 */
                    OSTmr_Link(ptmr, OS_TMR_LINK_PERIODIC);      /* 重新加入计时器轮 */
                } else {                                         /* 若为单次计时器 */
                    /* 单次计时结束后，状态切换为完成计时 */
                    ptmr->OSTmrState = OS_TMR_STATE_COMPLETED;   
                }
                pfnct = ptmr->OSTmrCallback;                     
                if (pfnct != (OS_TMR_CALLBACK)0) {        /* 若回调函数不为空，执行回调函数 */
                    (*pfnct)((void *)ptmr, ptmr->OSTmrCallbackArg);
                }
            }
            ptmr = ptmr_next;                                    /* 判断下一个计时器 */
        }
        OSSchedUnlock();
    }
}
```

##### os_task.c

```c
/* ****************************** os_task.c ***************************************
* 	任务创建流程梳理：创建过程中一些重要的全局变量：1.OS_TCB *OSTCBPrioTbl[]按优先级维护的指针数
* 组，方便随时按优先级查找任务。2.OS_TCB *OSTCBFreeList任务控制块空闲链表 3.OS_TCB OSTCBTbl[]
* 存任务控制块本体的数组。 4. OS_TCB *OSTCBList就绪任务链表，新创建的任务被置于表头。 |  创建一个
* 任务的流程大致为：判断当前优先级是否已存在、任务栈初始化、任务控制块初始化、进行一次任务调度。
* 	
* 	任务调度流程梳理：任务调度分为任务级和中断级两种，区别：中断级调度需要判断当前是否处于中断嵌套状
* 态，因为硬件中断的优先级高于系统任务，故在中断嵌套状态下不必进行任务调度。另外中断级调度过程相对于任
* 务级调度少了一步保存现场，因为进入中断前运行的任务现场已被保存。任务级调度流程简述如下：判断是否处于
* 中断嵌套状态，若不是则查任务就绪表，找到已就绪的最高优先级任务，若此任务不为当前任务，则执行
* OS_TASK_SW()保存和恢复现场。(任务调度、函数调用、中断发生，虽然有很多细节上的不同，但其基本原理大
* 致相同，任务调度过程可以说是对中断发生过程的模仿。)任务调度函数在许多地方都会被调用。
*
*	任务挂起：挂起任务的流程很简单，若该优先级任务存在，则将挂起标志位置1，若挂起的为自身，则执行一次
* 调度。 | 任务解挂：若任务为挂起状态，将挂起标志置1，若没有等待其他事件且没有在延时，则在就绪表中置
* 1，并执行一次调度。 | 在ucos中，挂起、等待事件、延时，三种操作都可以让任务解除就绪态，且这三种操作
* 基本可以理解成是各自独立的，即一个任务想恢复就绪，需要同时满足不在挂起态、延时周期数为零、未处于等待
* 事件状态三个条件。
*
*	任务删除：任务删除的主要工作为：1.从全局变量角度清除该优先级任务存在的一些记录。2.初始化该任务控制
* 块。3.更新已使用任务链表和空闲任务链表。
*********************************************************************************** */

/* **** 任务创建 ****
 * 输入:  task     任务函数
 *        p_arg    任务函数入口参数
 *        ptos     任务栈栈顶
 *        prio     任务优先级
 * 返回:  错误码  
*/
INT8U  OSTaskCreate (void   (*task)(void *p_arg),
                     void    *p_arg,
                     OS_STK  *ptos,
                     INT8U    prio)
{
    OS_STK    *psp;
    INT8U      err;
    OS_ENTER_CRITICAL();
    if (OSIntNesting > 0u) {                 /* 不允许在中断中创建任务 */
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_CREATE_ISR);
    }
    if (OSTCBPrioTbl[prio] == (OS_TCB *)0) { /* 如果任务控制块指针数组中该优先级任务不存在 */
        OSTCBPrioTbl[prio] = OS_TCB_RESERVED;/* 先将任务控制块指针数组中对应优先级占用 */
        OS_EXIT_CRITICAL();
        /* 任务栈初始化，其内容为从输入参数ptos栈顶指针开始，伪造一个任务调度所产生的系统栈区，包括cpu寄存器，函数入口作为PC等。返回新的栈顶指针SP */
        psp = OSTaskStkInit(task, p_arg, ptos, 0u);
        /* 任务控制块初始化，内容大致为：1.申请一个任务控制块 2.初始化一些成员变量 3.更新OSTCBList链表，将新任务加到表头 4.更新全局任务就绪表 5.返回错误码 */
        err = OS_TCBInit(prio, psp, (OS_STK *)0, 0u, 0u, (void *)0, 0u);
        if (err == OS_ERR_NONE) {
            if (OSRunning == OS_TRUE) {
                OS_Sched();  // 一切正常，执行一次任务调度
            }
        } else {  // 任务控制块初始化不正常
            OS_ENTER_CRITICAL();
            OSTCBPrioTbl[prio] = (OS_TCB *)0;
            OS_EXIT_CRITICAL();
        }
        return (err);
    }
     OS_EXIT_CRITICAL();
    return (OS_ERR_PRIO_EXIST);
}

/* **** 任务级调度 ****
*    无输入无返回
*/
void  OS_Sched (void)
{
    OS_ENTER_CRITICAL();
    if (OSIntNesting == 0u) {        /* 不是中断嵌套状态 */
        if (OSLockNesting == 0u) {   /* 调度器未被锁定 */
			/* OS_SchedNew()实际是在查全局的任务就绪表，得到已就绪的最高优先级任务的优先级，并将此值赋给OSPrioHighRdy。任务就绪表实现原理很有意思，感兴趣可自行查阅 */
            OS_SchedNew();
            /* 更新全局最高优先级已就绪任务的任务控制块指针OSTCBHighRdy */
            OSTCBHighRdy = OSTCBPrioTbl[OSPrioHighRdy];  
            if (OSPrioHighRdy != OSPrioCur) {  /* 若已就绪最高优先级任务非当前任务，则调度 */
                OSCtxSwCtr++;  /* 上下文切换计数器加一,其他地方没用到，意义不明 */
                /* OS_TASK_SW()是OSCtxSw()的宏，实际是一段汇编，功能为触发PendSV系统异常，其异常服务函数用汇编实现，为保存现场和恢复现场两部分,执行完成后CPU对应的当前任务已然切换 */
                OS_TASK_SW();
            }
        }
    }
    OS_EXIT_CRITICAL();
}

/* **** 任务挂起 ****
*    输入：任务优先级
*    返回：错误码
*/
INT8U  OSTaskSuspend (INT8U prio)
{
    BOOLEAN    self;
    OS_TCB    *ptcb;
    INT8U      y;
    OS_ENTER_CRITICAL();
    if (prio == OS_PRIO_SELF) {  /* 是否挂起自身 */
        prio = OSTCBCur->OSTCBPrio;
        self = OS_TRUE;
    } else if (prio == OSTCBCur->OSTCBPrio) {  /* 同上 */
        self = OS_TRUE;
    } else {
        self = OS_FALSE;
    }
    ptcb = OSTCBPrioTbl[prio];  /* 拿到要挂起的任务控制块 */
    if (ptcb == (OS_TCB *)0) {  /* 任务控制块不存在 */
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_SUSPEND_PRIO);
    }
    if (ptcb == OS_TCB_RESERVED) {  /* 该优先级被用于作为互斥信号量的PIP */
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST);
    }
    y            = ptcb->OSTCBY;
    OSRdyTbl[y] &= (OS_PRIO)~ptcb->OSTCBBitX;   /* 任务就绪表清零 */
    if (OSRdyTbl[y] == 0u) {
        OSRdyGrp &= (OS_PRIO)~ptcb->OSTCBBitY;  /* 任务就绪组清零 */
    }
    ptcb->OSTCBStat |= OS_STAT_SUSPEND;  		/* 更改任务状态至挂起 */
    OS_EXIT_CRITICAL();
    if (self == OS_TRUE) {  /* 仅在挂起自己时执行任务调度 */
      OS_Sched();  			/* 若自挂起，找新任务执行 */
    }
    return (OS_ERR_NONE);
}

/* **** 挂起任务恢复 ****
*    输入：任务优先级
*    返回：错误码
*/
INT8U  OSTaskResume (INT8U prio)
{
    OS_TCB    *ptcb;
    OS_ENTER_CRITICAL();
    ptcb = OSTCBPrioTbl[prio];  /* 拿到要恢复的任务控制块 */
    if (ptcb == (OS_TCB *)0) {  /* 控制块不存在 */
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_RESUME_PRIO);
    }
    if (ptcb == OS_TCB_RESERVED) {  /* 该优先级被用于作为互斥信号量的PIP */
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST);
    }
    if ((ptcb->OSTCBStat & OS_STAT_SUSPEND) != OS_STAT_RDY) { /* 若任务确实被挂起 */
        ptcb->OSTCBStat &= (INT8U)~(INT8U)OS_STAT_SUSPEND;    /* 挂起标志位清零 */
        if (ptcb->OSTCBStat == OS_STAT_RDY) {                 /* 若没有其他的pend */
            if (ptcb->OSTCBDly == 0u) {                       /* 若未在延时,同时满足这两个条件则认为任务就绪 */
                OSRdyGrp               |= ptcb->OSTCBBitY;    /* 在就绪表中置1 */
                OSRdyTbl[ptcb->OSTCBY] |= ptcb->OSTCBBitX;
                OS_EXIT_CRITICAL();
                if (OSRunning == OS_TRUE) {
                    OS_Sched();                               /* 进行一次任务调度 */
                }
            } else {
                OS_EXIT_CRITICAL();
          }
        } else {                                              /* 若还有其他pend */
            OS_EXIT_CRITICAL();
        }
        return (OS_ERR_NONE);
    }
    OS_EXIT_CRITICAL();
    return (OS_ERR_TASK_NOT_SUSPENDED);  /* 任务并未被挂起 */
}

/* **** 任务删除 ****
*    输入：任务优先级
*    返回：错误码
*/
INT8U  OSTaskDel (INT8U prio)
{
    OS_TCB       *ptcb;
    if (OSIntNesting > 0u) {         /* 是否在中断中调用 */
        return (OS_ERR_TASK_DEL_ISR);
    }
    if (prio == OS_TASK_IDLE_PRIO) { /* 目标任务是否是空闲任务 */
        return (OS_ERR_TASK_DEL_IDLE);
    }

    OS_ENTER_CRITICAL();
    if (prio == OS_PRIO_SELF) {      /* 若删除自身(正在运行的任务) */
        prio = OSTCBCur->OSTCBPrio;  /* 拿到自身的优先级 */
    }
    ptcb = OSTCBPrioTbl[prio];       /* 拿到任务控制块 */
    if (ptcb == (OS_TCB *)0) {       /* 控制块不存在 */
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST);
    }
    if (ptcb == OS_TCB_RESERVED) {   /* 该优先级被用于作为互斥信号量的PIP */
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_DEL);
    }

    OSRdyTbl[ptcb->OSTCBY] &= (OS_PRIO)~ptcb->OSTCBBitX;  /* 更新任务就绪表 */
    if (OSRdyTbl[ptcb->OSTCBY] == 0u) {                 /* 当前Y全为0，则更新任务就绪组 */
        OSRdyGrp           &= (OS_PRIO)~ptcb->OSTCBBitY;
    }

    ptcb->OSTCBDly      = 0u;                   /* 清除控制块的一些成员变量 */
    ptcb->OSTCBStat     = OS_STAT_RDY;                  
    ptcb->OSTCBStatPend = OS_STAT_PEND_OK;
    if (OSLockNesting < 255u) {                         
        OSLockNesting++;
    }
    OS_EXIT_CRITICAL();                                 
    OS_Dummy();                                        
    OS_ENTER_CRITICAL();                              
    if (OSLockNesting > 0u) {                        
        OSLockNesting--;
    }
    OSTaskDelHook(ptcb);                        /* 钩子函数 */
    OSTaskCtr--;                                /* 全局已创建任务计数减一 */
    OSTCBPrioTbl[prio] = (OS_TCB *)0;           /* 更新根据优先级排布的全局控制块指针数组 */
    if (ptcb->OSTCBPrev == (OS_TCB *)0) {       /* 更新OSTCBList,将控制块移出链表 */
        ptcb->OSTCBNext->OSTCBPrev = (OS_TCB *)0;
        OSTCBList                  = ptcb->OSTCBNext;
    } else {
        ptcb->OSTCBPrev->OSTCBNext = ptcb->OSTCBNext;
        ptcb->OSTCBNext->OSTCBPrev = ptcb->OSTCBPrev;
    }
    ptcb->OSTCBNext     = OSTCBFreeList;        /* 更新OSTCBFreeList,将控制块加入链表 */
    OSTCBFreeList       = ptcb;
    OS_EXIT_CRITICAL();
    if (OSRunning == OS_TRUE) {
        OS_Sched();                             /* 进行一次调度 */
    }
    return (OS_ERR_NONE);
}
```

##### os_sem.c

```c
/* ********************** os_sem.c (多任务通讯方式之一，信号量)  *********************** 
* 	  信号量创建：从空闲数组取一个事件控制块，将其初始化为信号量后返回该控制块。
*
*     请求信号量：若仍剩余，则信号量减一并返回；若无剩余，更新任务的状态为等待、装载超时时间，更新事件
* 的等待任务优先级表，再更新全局任务就绪表使当前任务取消就绪，然后执行调度，让出CPU，可理解为在此阻
* 塞。解除阻塞后根据OK/ABORT/TO三种状态进行对应处理。
*     
*     发送信号量：若事件的任务等待表无任务，信号量加一；若有等待任务，执行OS_EventTaskRdy(),将等待
* 事件的最高优先级任务恢复就绪，并调度。
*
*     放弃等待信号量：根据输入选项使等待输入信号量的全部任务或最高优先级任务变为就绪，并将等待状态置为
* 放弃(Abort)。
*
*     请求但不阻塞(Accept)信号量：将目标信号量减一，不操作就绪表也不调度。
*********************************************************************************** */

/* **** 信号量创建 ****
*    输入：cnt    信号量总数
*    返回：pevent 信号量事件控制块
*/
OS_EVENT  *OSSemCreate (INT16U cnt)
{
    OS_EVENT  *pevent;
    if (OSIntNesting > 0u) {                               
        return ((OS_EVENT *)0);                            
    }
    OS_ENTER_CRITICAL();
    pevent = OSEventFreeList;                          /* 从事件控制块空闲链表取表头 */
    if (OSEventFreeList != (OS_EVENT *)0) {            /* 更新空闲链表 */
        OSEventFreeList = (OS_EVENT *)OSEventFreeList->OSEventPtr;
    }
    OS_EXIT_CRITICAL();
    if (pevent != (OS_EVENT *)0) {                        
        /* 初始化一些成员变量 */
        pevent->OSEventType    = OS_EVENT_TYPE_SEM;
        pevent->OSEventCnt     = cnt;                    
        pevent->OSEventPtr     = (void *)0;            /* 从空闲链表脱离 */
        /* 初始化该事件控制块的OSEventGrp和OSEventTbl[],即表示无任务在等待该信号 */
        OS_EventWaitListInit(pevent);  /* 清空等待任务优先级表 */                   
    }
    return (pevent);
}

/* **** 请求信号量 ****
*    输入：pevent     请求的目标信号量
*          timeout    超时时间
*          perr       错误码
*    返回：无
*/
void  OSSemPend (OS_EVENT  *pevent,
                 INT32U     timeout,
                 INT8U     *perr)
{
    /* 一些错误状况 */
    if (pevent->OSEventType != OS_EVENT_TYPE_SEM) {   
        *perr = OS_ERR_EVENT_TYPE;
        return;
    }
    if (OSIntNesting > 0u) {                         
        *perr = OS_ERR_PEND_ISR;                    
        return;
    }
    if (OSLockNesting > 0u) {                      
        *perr = OS_ERR_PEND_LOCKED;               
        return;
    }
    OS_ENTER_CRITICAL();
    if (pevent->OSEventCnt > 0u) {    /* 信号量有剩余 */
        pevent->OSEventCnt--;         
        OS_EXIT_CRITICAL();
        *perr = OS_ERR_NONE;
        return;
    }
    /* 信号量已为零，等待信号量 */
    OSTCBCur->OSTCBStat     |= OS_STAT_SEM;     /* 更改当前任务控制块状态为等待信号量状态 */
    OSTCBCur->OSTCBStatPend  = OS_STAT_PEND_OK; /* 等待状态置为未超时 */
    OSTCBCur->OSTCBDly       = timeout;         /* 装载超时时间 */
    /* 将当前任务置于等待pevent事件状态。具体是将当前任务的OSTCBEventPtr指向等待的事件，将目标事件的Grp和Tbl更新，再更新任务就绪表，使当前任务脱离就绪态 */
    OS_EventTaskWait(pevent);                       
    OS_EXIT_CRITICAL();
    OS_Sched();                                       /* 执行一次调度，使当前任务释放CPU */
    /* ********** 程序在此保存现场，可理解为阻塞在此处，直到此任务重获CPU使用权 ************ */
    OS_ENTER_CRITICAL();
    switch (OSTCBCur->OSTCBStatPend) {    /* 根据StatPend执行不同操作 */
        case OS_STAT_PEND_OK:             /* 正常收到事件 */
             *perr = OS_ERR_NONE;
             break;

        case OS_STAT_PEND_ABORT:          /* 手动放弃等待事件 */
             *perr = OS_ERR_PEND_ABORT;   
             break;

        case OS_STAT_PEND_TO:             /* 等待事件超时 */
        default:
             /* 将当前任务从事件的等待列表Grp和Tbl移出 */
             OS_EventTaskRemove(OSTCBCur, pevent);
             *perr = OS_ERR_TIMEOUT;             
             break;
    }
    /* 更新一些任务的成员变量 */
    OSTCBCur->OSTCBStat          =  OS_STAT_RDY;      
    OSTCBCur->OSTCBStatPend      =  OS_STAT_PEND_OK; 
    OSTCBCur->OSTCBEventPtr      = (OS_EVENT  *)0;  
    OS_EXIT_CRITICAL();
}

/* **** 发送信号量 ****
*    输入：pevent     发送的目标信号量
*    返回：错误码
*/
INT8U  OSSemPost (OS_EVENT *pevent)
{
    if (pevent->OSEventType != OS_EVENT_TYPE_SEM) {   /* 目标ECB非信号量 */
        return (OS_ERR_EVENT_TYPE);
    }
    OS_ENTER_CRITICAL();
    if (pevent->OSEventGrp != 0u) {                   /* 若有任务在等待该信号量 */
        /* 使该事件等待表中优先级最高的任务就绪,具体实现在后贴出 */
        (void)OS_EventTaskRdy(pevent, (void *)0, OS_STAT_SEM, OS_STAT_PEND_OK);
        OS_EXIT_CRITICAL();
        OS_Sched();                                   /* 任务调度 */
        return (OS_ERR_NONE);
    }
    if (pevent->OSEventCnt < 65535u) {                /* 若无任务等待,且信号量未溢出,将信号量加一 */
        pevent->OSEventCnt++;                     
        OS_EXIT_CRITICAL();
        return (OS_ERR_NONE);
    }
    OS_EXIT_CRITICAL();                               /* 执行到此处，则信号量溢出 */
    return (OS_ERR_SEM_OVF);
}

/* **** 放弃等待信号量 ****
*    输入：pevent     请求的目标信号量
*         opt        BROADCAST/NONE
*         perr       错误码
*    返回：0          无任务在等待该信号或发生错误
*         >0         放弃等待的任务数目
*/
INT8U  OSSemPendAbort (OS_EVENT  *pevent,
                       INT8U      opt,
                       INT8U     *perr)
{
    INT8U      nbr_tasks;
    if (pevent->OSEventType != OS_EVENT_TYPE_SEM) {   /* 输入事件非信号量 */
        *perr = OS_ERR_EVENT_TYPE;
        return (0u);
    }
    OS_ENTER_CRITICAL();
    if (pevent->OSEventGrp != 0u) {              /* 若有任务在等待事件 */
        nbr_tasks = 0u;
        switch (opt) {
            case OS_PEND_OPT_BROADCAST:          /* 广播，使等待该信号的所有任务放弃等待 */
                 while (pevent->OSEventGrp != 0u) {   /* 循环直到事件的等待表为空 */
                     /* 使等待该事件的最高优先级任务就绪 */
                     (void)OS_EventTaskRdy(pevent, (void *)0, OS_STAT_SEM, OS_STAT_PEND_ABORT);
                     nbr_tasks++;
                 }
                 break;

            case OS_PEND_OPT_NONE:
            default:                          /* 不广播，只使等待该信号的最高优先级任务放弃*/
                 (void)OS_EventTaskRdy(pevent, (void *)0, OS_STAT_SEM, OS_STAT_PEND_ABORT);
                 nbr_tasks++;
                 break;
        }
        OS_EXIT_CRITICAL();
        OS_Sched();                           /* 调度 */
        *perr = OS_ERR_PEND_ABORT;
        return (nbr_tasks);
    }
    OS_EXIT_CRITICAL();
    *perr = OS_ERR_NONE;
    return (0u);                              /* 无任务在等待 */
}

/* **** 请求信号量但不阻塞 ****
*    输入：pevent     请求的目标信号量
*    返回：0          输入事件不是信号信号数目为零
*         >0         请求前剩余的信号数目
*/
INT16U  OSSemAccept (OS_EVENT *pevent)
{
    INT16U     cnt;
    if (pevent->OSEventType != OS_EVENT_TYPE_SEM) {   /* 输入事件非信号量 */
        return (0u);
    }
    OS_ENTER_CRITICAL();
    cnt = pevent->OSEventCnt;
    if (cnt > 0u) {                /* 若信号量有剩余 */
        pevent->OSEventCnt--;
    }
    OS_EXIT_CRITICAL();
    return (cnt);                  /* 返回请求前的信号量剩余数目 */
}

/* **** 有事件发生或任务ABORT时,使等待事件的最高优先级任务就绪 ****
*                 此函数适用于所有事件类型
*    输入：pevent      发生事件的事件控制块
*         pmsg       消息或消息队列传递的消息
*         msk        事件类型，用于清任务状态标志位
*         pend_stat  标志正常OK/手动结束等待ABORT
*    返回：就绪的任务优先级
*/
INT8U  OS_EventTaskRdy (OS_EVENT  *pevent,
                        void      *pmsg,
                        INT8U      msk,
                        INT8U      pend_stat)
{
    OS_TCB   *ptcb;
    INT8U     y;
    INT8U     x;
    INT8U     prio;

    /* 拿取等待该事件的最高优先级任务的优先级 */
    y    = OSUnMapTbl[pevent->OSEventGrp];              
    x    = OSUnMapTbl[pevent->OSEventTbl[y]];
    prio = (INT8U)((y << 3u) + x);                     
    ptcb                  =  OSTCBPrioTbl[prio];  /* 拿取上文拿到优先级对应的任务控制块 */
    /* 修改一些成员变量 */
    ptcb->OSTCBDly        =  0u;                        
    ptcb->OSTCBMsg        =  pmsg;                      
    ptcb->OSTCBStat      &= (INT8U)~msk;                
    ptcb->OSTCBStatPend   =  pend_stat;                 
    /* 若目标任务未被挂起，将其置为就绪 */
    if ((ptcb->OSTCBStat &   OS_STAT_SUSPEND) == OS_STAT_RDY) {
        OSRdyGrp         |=  ptcb->OSTCBBitY;           
        OSRdyTbl[y]      |=  ptcb->OSTCBBitX;
    }
    OS_EventTaskRemove(ptcb, pevent);             /* 将目标任务移出事件等待的任务优先级表 */
    return (prio);
}
```

##### os_mutex.c

```c 
/* ********************* os_mutex.c (多任务通讯方式之一，互斥信号量) ********************* 
*     创建互斥信号量：和Sem基本一致，区别是Cnt高8位存PIP，第8位存互斥信号状态。
*
*     请求互斥信号量：和Sem区别较大，基本思路为，若无人占有，当前任务可直接占有，更新一些相关信息至ECB、
* 若已被占有，则需判断是否可能出现优先级反转问题，若优先级请求高于占有，且PIP高于占有，则全面将占有任务从原
* 优先级移出，并将PIP作为占有任务的新优先级全面更新。余下的阻塞和恢复逻辑和Sem基本一致。
*
*     发送互斥信号量：和请求的流程对应，相比Sem多了关于对当前任务优先级是否被提高过的判断，以及一些Mutex
* 的ECB不同于Sem的存储内容。
*********************************************************************************** */

/* **** 互斥信号量创建 ****
*    输入：prio       防止优先级反转的较高优先级，即当较低优先级任务获得信号量时，将其优先级提升至prio
*          perr       错误码
*    返回：互斥信号量事件控制块
*/
OS_EVENT  *OSMutexCreate (INT8U   prio,
                          INT8U  *perr)
{
    OS_EVENT  *pevent;
    if (OSIntNesting > 0u) {                               /* ISR中不允许调用 */
        *perr = OS_ERR_CREATE_ISR;                         
        return ((OS_EVENT *)0);
    }
    OS_ENTER_CRITICAL();
    if (OSTCBPrioTbl[prio] != (OS_TCB *)0) {               /* 该优先级不能存在任务 */
        OS_EXIT_CRITICAL();                                
        *perr = OS_ERR_PRIO_EXIST;                        
        return ((OS_EVENT *)0);
    }
    OSTCBPrioTbl[prio] = OS_TCB_RESERVED;             /* 将TCB指针数组中该优先级对应部分保留 */
    pevent             = OSEventFreeList;                  /* 拿取一个空闲ECB */
    if (pevent == (OS_EVENT *)0) {                         /* 无空闲ECB */
        OSTCBPrioTbl[prio] = (OS_TCB *)0;                  
        OS_EXIT_CRITICAL();
        *perr              = OS_ERR_PEVENT_NULL;          
        return (pevent);
    }
    OSEventFreeList        = (OS_EVENT *)OSEventFreeList->OSEventPtr;   /* 正常情况，更新ECB空闲链表 */
    OS_EXIT_CRITICAL();
    pevent->OSEventType    = OS_EVENT_TYPE_MUTEX;
    pevent->OSEventCnt     = (INT16U)((INT16U)prio << 8u) | OS_MUTEX_AVAILABLE; /* Cnt高8位存优先级，低8位为信号状态 */
    pevent->OSEventPtr     = (void *)0;                         /* 去除和空闲ECB数组的连接 */
    OS_EventWaitListInit(pevent);  /* 清空等待任务优先级表 */
    *perr                  = OS_ERR_NONE;
    return (pevent);
}

/* **** 请求互斥信号量 ****
*    输入：pevent       目标信号量
*          timeout      超时时间
*          perr         错误码
*    返回：无
*/
void  OSMutexPend (OS_EVENT  *pevent,
                   INT32U     timeout,
                   INT8U     *perr)
{
    INT8U      pip;                    /* 该互斥信号量的优先级继承优先级 */
    INT8U      mprio;                  /* 优先级反转时，表示占有信号量的任务的优先级 */
    BOOLEAN    rdy;                    /* 优先级反转时，表示占有信号量的任务是否就绪 */
    OS_TCB    *ptcb;                   /* 优先级反转时，表示占有信号量任务的TCB */
    OS_EVENT  *pevent2;                /* 优先级反转时，表示占有信号量任务在等待事件的ECB */
    INT8U      y;
    /* 一些错误情况判断 */
    if (pevent->OSEventType != OS_EVENT_TYPE_MUTEX) {      
        *perr = OS_ERR_EVENT_TYPE;
        return;
    }
    if (OSIntNesting > 0u) {                              
        *perr = OS_ERR_PEND_ISR;                         
        return;
    }
    if (OSLockNesting > 0u) {                              
        *perr = OS_ERR_PEND_LOCKED;                       
        return;
    }

    OS_ENTER_CRITICAL();
    pip = (INT8U)(pevent->OSEventCnt >> 8u);               /* 从Cnt高8位取优先级继承优先级 */

    /* 若Cnt低8位表示AVAILABLE,使当前任务占有该互斥信号量 */
    if ((INT8U)(pevent->OSEventCnt & OS_MUTEX_KEEP_LOWER_8) == OS_MUTEX_AVAILABLE) {
        pevent->OSEventCnt &= OS_MUTEX_KEEP_UPPER_8;       /* 清掉低8位 */
        pevent->OSEventCnt |= OSTCBCur->OSTCBPrio;         /* 存占有信号量的任务原始优先级,用于后续恢复 */
        pevent->OSEventPtr  = (void *)OSTCBCur;            /* 指向占有该信号量的TCB */
        if (OSTCBCur->OSTCBPrio <= pip) {                  /* 若请求任务的优先级比PIP更高 */
            OS_EXIT_CRITICAL();                            
            *perr = OS_ERR_PIP_LOWER;
        } else {
            OS_EXIT_CRITICAL();
            *perr = OS_ERR_NONE;
        }
        return;
    }

    /* 若当前状态并非AVAILABLE,表示互斥信号量已被其他任务占有,此时需要判断是否可能出现优先级反转，并阻塞当前任务 */
    mprio = (INT8U)(pevent->OSEventCnt & OS_MUTEX_KEEP_LOWER_8);  /* 取得占有信号量任务的优先级 */
    ptcb  = (OS_TCB *)(pevent->OSEventPtr);                    /* 取得占有信号量任务的TCB */
    /* 若占有信号量任务的优先级低于PIP,为防止优先级反转,需要暂时将其提至PIP,若高于PIP则不需处理 */
    if (ptcb->OSTCBPrio > pip) {                                  
        /* 若占有任务优先级低于当前请求任务的优先级 */
        if (mprio > OSTCBCur->OSTCBPrio) {
            y = ptcb->OSTCBY;  /* 占有的Y */
            /* 若占有任务为就绪态，清零对应优先级的任务就绪表 */
            if ((OSRdyTbl[y] & ptcb->OSTCBBitX) != 0u) {          
                OSRdyTbl[y] &= (OS_PRIO)~ptcb->OSTCBBitX;         
                if (OSRdyTbl[y] == 0u) {                         
                    OSRdyGrp &= (OS_PRIO)~ptcb->OSTCBBitY;
                }
                rdy = OS_TRUE;
            } else {  /* 若占有任务不为就绪态 */
                pevent2 = ptcb->OSTCBEventPtr;   /* 拿取占有任务在等待的事件的ECB */
                if (pevent2 != (OS_EVENT *)0) {  /* 先将占有任务从其等待的事件的任务优先级表中去除 */                   
                    y = ptcb->OSTCBY;
                    pevent2->OSEventTbl[y] &= (OS_PRIO)~ptcb->OSTCBBitX;
                    if (pevent2->OSEventTbl[y] == 0u) {
                        pevent2->OSEventGrp &= (OS_PRIO)~ptcb->OSTCBBitY;
                    }
                }
                rdy = OS_FALSE;
            }
            /* 为占有任务更新优先级为pip */
            ptcb->OSTCBPrio = pip;                         
            ptcb->OSTCBY    = (INT8U)( ptcb->OSTCBPrio >> 3u);
            ptcb->OSTCBX    = (INT8U)( ptcb->OSTCBPrio & 0x07u);
            ptcb->OSTCBBitY = (OS_PRIO)(1uL << ptcb->OSTCBY);
            ptcb->OSTCBBitX = (OS_PRIO)(1uL << ptcb->OSTCBX);

            /* 根据占有任务是否在pend为其更新优先级表 */
            if (rdy == OS_TRUE) {                          
                OSRdyGrp               |= ptcb->OSTCBBitY;
                OSRdyTbl[ptcb->OSTCBY] |= ptcb->OSTCBBitX;
            } else {
                pevent2 = ptcb->OSTCBEventPtr;
                if (pevent2 != (OS_EVENT *)0) {          
                    pevent2->OSEventGrp               |= ptcb->OSTCBBitY;
                    pevent2->OSEventTbl[ptcb->OSTCBY] |= ptcb->OSTCBBitX;
                }
            }
            OSTCBPrioTbl[pip] = ptcb;
        }
    }
    /* 余下的操作和Sem的Pend没啥子区别，不做注释 */
    OSTCBCur->OSTCBStat |= OS_STAT_MUTEX;    /* Mutex not available, pend current task */
    OSTCBCur->OSTCBStatPend  = OS_STAT_PEND_OK;
    OSTCBCur->OSTCBDly       = timeout;         /* Store timeout in current task's TCB */
    OS_EventTaskWait(pevent);         /* Suspend task until event or timeout occurs    */
    OS_EXIT_CRITICAL();
    OS_Sched();                               /* Find next highest priority task ready */
    OS_ENTER_CRITICAL();
    switch (OSTCBCur->OSTCBStatPend) {               /* See if we timed-out or aborted */
        case OS_STAT_PEND_OK:
             *perr = OS_ERR_NONE;
             break;
        case OS_STAT_PEND_ABORT:
             *perr = OS_ERR_PEND_ABORT;      /* Indicate that we aborted getting mutex */
             break;
        case OS_STAT_PEND_TO:
        default:
             OS_EventTaskRemove(OSTCBCur, pevent);
             *perr = OS_ERR_TIMEOUT;    /* Indicate that we didn't get mutex within TO */
             break;
    }
    OSTCBCur->OSTCBStat      =  OS_STAT_RDY;      /* Set   task  status to ready */
    OSTCBCur->OSTCBStatPend  =  OS_STAT_PEND_OK;  /* Clear pend  status */
    OSTCBCur->OSTCBEventPtr  = (OS_EVENT  *)0;    /* Clear event pointers */
    OS_EXIT_CRITICAL();
    // return;
}

/* **** 发送互斥信号量 ****
*    输入：pevent       目标信号量
*    返回：错误码
*/
INT8U  OSMutexPost (OS_EVENT *pevent)
{
    INT8U      pip;                                   
    INT8U      prio;
    if (pevent->OSEventType != OS_EVENT_TYPE_MUTEX) { /* 类型错误 */
        return (OS_ERR_EVENT_TYPE);
    }
    OS_ENTER_CRITICAL();
    pip  = (INT8U)(pevent->OSEventCnt >> 8u);         /* 拿取PIP */
    prio = (INT8U)(pevent->OSEventCnt & OS_MUTEX_KEEP_LOWER_8);/* 拿取占有任务的原始优先级 */
    if (OSTCBCur != (OS_TCB *)pevent->OSEventPtr) {   /* 若当前任务不是占有任务，报错 */
        OS_EXIT_CRITICAL();
        return (OS_ERR_NOT_MUTEX_OWNER);
    }
    if (OSTCBCur->OSTCBPrio == pip) {                 /* 如果当前任务的优先级是被提高过的 */
        /* 恢复当前任务优先级至原始状态,具体是更新所有跟当前任务优先级有关的全局变量,从PIP回到原始 */
        OSMutex_RdyAtPrio(OSTCBCur, prio);            
    }
    OSTCBPrioTbl[pip] = OS_TCB_RESERVED;              /* 全局TCB指针数组恢复PIP下标状态 */
    if (pevent->OSEventGrp != 0u) {                   /* 若有任务在等待此互斥信号 */
        /* 将该事件等待任务表中最高优先级的移出并就绪 */
        prio                = OS_EventTaskRdy(pevent, (void *)0, OS_STAT_MUTEX, OS_STAT_PEND_OK);
        pevent->OSEventCnt &= OS_MUTEX_KEEP_UPPER_8;  
        pevent->OSEventCnt |= prio;                   /* 低8位存占有任务的原始优先级 */ 
        pevent->OSEventPtr  = OSTCBPrioTbl[prio];     /* EventPtr指向占有任务的TCB本体 */
        /* 信号量释放完毕，调度 */
        if (prio <= pip) {                            
            OS_EXIT_CRITICAL();                       
            OS_Sched();                               
            return (OS_ERR_PIP_LOWER);
        } else {
            OS_EXIT_CRITICAL();
            OS_Sched();                               
            return (OS_ERR_NONE);
        }
    }
    pevent->OSEventCnt |= OS_MUTEX_AVAILABLE;         /* 无任务在等待此互斥信号 */
    pevent->OSEventPtr  = (void *)0;
    OS_EXIT_CRITICAL();
    return (OS_ERR_NONE);
}

```

##### os_mbox.c

```c
/* ********************* os_mbox.c (多任务通讯方式之一，消息邮箱) ********************* 
*   邮箱的所有操作都和Sem基本相同，只是对于ECB成员变量的处理有些不同。
*********************************************************************************** */

/* **** 创建消息邮箱 ****
*    输入：pmsg       邮箱存放的初始值
*    返回：mbox的事件控制块
*/
OS_EVENT  *OSMboxCreate (void *pmsg)
{
    OS_EVENT  *pevent;
    if (OSIntNesting > 0u) {                     
        return ((OS_EVENT *)0);                 
    }
    OS_ENTER_CRITICAL();
    pevent = OSEventFreeList;                   
    if (OSEventFreeList != (OS_EVENT *)0) {  /* 更新ECB空闲链表 */
        OSEventFreeList = (OS_EVENT *)OSEventFreeList->OSEventPtr;
    }
    OS_EXIT_CRITICAL();
    if (pevent != (OS_EVENT *)0) {
        pevent->OSEventType    = OS_EVENT_TYPE_MBOX;
        pevent->OSEventCnt     = 0u;
        pevent->OSEventPtr     = pmsg;   /* 存入消息初值 */        
        OS_EventWaitListInit(pevent);
    }
    return (pevent);                            
}


/* **** 等待消息邮箱 ****
*    输入：pevent   目标事件控制块
*          timeout  超时时间
*          perr     错误码
*    返回：pmsg     指向邮箱内消息的指针
*/
void  *OSMboxPend (OS_EVENT  *pevent,
                   INT32U     timeout,
                   INT8U     *perr)
{
    void      *pmsg;
    /* 一些不合法判断 */
    if (pevent->OSEventType != OS_EVENT_TYPE_MBOX) {  
        *perr = OS_ERR_EVENT_TYPE;
        return ((void *)0);
    }
    if (OSIntNesting > 0u) {                         
        *perr = OS_ERR_PEND_ISR;                    
        return ((void *)0);
    }
    if (OSLockNesting > 0u) {                      
        *perr = OS_ERR_PEND_LOCKED;               
        return ((void *)0);
    }
    OS_ENTER_CRITICAL();
    pmsg = pevent->OSEventPtr;
    if (pmsg != (void *)0) {                          /* 若邮箱内已存在消息 */
        pevent->OSEventPtr = (void *)0;               /* 邮箱清零取出 */
        OS_EXIT_CRITICAL();
        *perr = OS_ERR_NONE;
        return (pmsg);                                /* 返回指向消息的指针 */
    }
    /* 若邮箱内不存在消息，将当前任务置为等待状态，余下流程和Sem基本一致 */
    OSTCBCur->OSTCBStat     |= OS_STAT_MBOX;          
    OSTCBCur->OSTCBStatPend  = OS_STAT_PEND_OK;
    OSTCBCur->OSTCBDly       = timeout;              
    OS_EventTaskWait(pevent);  /* Suspend task until event or timeout occurs    */
    OS_EXIT_CRITICAL();
    OS_Sched();                /* Find next highest priority task ready to run  */
    OS_ENTER_CRITICAL();
    switch (OSTCBCur->OSTCBStatPend) {        /* See if we timed-out or aborted */
        case OS_STAT_PEND_OK:
             pmsg =  OSTCBCur->OSTCBMsg;
            *perr =  OS_ERR_NONE;
             break;
        case OS_STAT_PEND_ABORT:
             pmsg = (void *)0;
            *perr =  OS_ERR_PEND_ABORT;       /* Indicate that we aborted */
             break;
        case OS_STAT_PEND_TO:
        default:
             OS_EventTaskRemove(OSTCBCur, pevent);
             pmsg = (void *)0;
            *perr =  OS_ERR_TIMEOUT;  /* Indicate that we didn't get event within TO */
             break;
    }
    OSTCBCur->OSTCBStat = OS_STAT_RDY; /* Set   task  status to ready */
    OSTCBCur->OSTCBStatPend      =  OS_STAT_PEND_OK; /* Clear pend  status */
    OSTCBCur->OSTCBEventPtr      = (OS_EVENT  *)0;   /* Clear event pointers */
    OSTCBCur->OSTCBMsg           = (void      *)0;   /* Clear  received message */
    OS_EXIT_CRITICAL();
    return (pmsg);                                   /* Return received message */
}

/* **** 发送消息邮箱 ****
*    输入：pevent   目标事件控制块
*          pmsg     指向邮箱内消息的指针
*    返回：错误码
*/
INT8U  OSMboxPost (OS_EVENT  *pevent,
                   void      *pmsg)
{
    if (pevent->OSEventType != OS_EVENT_TYPE_MBOX) {  
        return (OS_ERR_EVENT_TYPE);
    }
    OS_ENTER_CRITICAL();
    /* 若有任务在等待该事件,将最高优先级任务恢复就绪,移出事件等待队列,并将消息指针传给OSTCBMsg */
    if (pevent->OSEventGrp != 0u) {          
        (void)OS_EventTaskRdy(pevent, pmsg, OS_STAT_MBOX, OS_STAT_PEND_OK);
        OS_EXIT_CRITICAL();
        OS_Sched();                                   
        return (OS_ERR_NONE);
    }
    /* 若无任务在等待该事件,且邮箱非空,返回错误 */
    if (pevent->OSEventPtr != (void *)0) {   
        OS_EXIT_CRITICAL();
        return (OS_ERR_MBOX_FULL);
    }
    /* 若无任务在等待，且邮箱为空，将消息存入邮箱 */
    pevent->OSEventPtr = pmsg;               
    OS_EXIT_CRITICAL();
    return (OS_ERR_NONE);
}

```

##### os_q.c

```c
/* ********************* os_q.c (多任务通讯方式之一，消息队列) ********************* 
*   消息队列和其他event有很大不同，除了ECB还有一个维护[指针数组循环队列]的OS_Q队列控制块。
*   最大的区别就是ECB的Ptr指向OS_Q结构体而非单个消息。
*********************************************************************************** */

/* **** 创建消息队列 ****
*    输入：start    消息队列起始地址
*          size     消息队列大小
*    返回：pevent   消息队列ECB
*/
OS_EVENT  *OSQCreate (void    **start,
                      INT16U    size)
{
    OS_EVENT  *pevent;
    OS_Q      *pq;

    if (OSIntNesting > 0u) {  /* ISR中禁止创建 */
        return ((OS_EVENT *)0);                  
    }
    OS_ENTER_CRITICAL();
    pevent = OSEventFreeList;                    /* 从全局数组取一个ECB，并更新空闲链表 */
    if (OSEventFreeList != (OS_EVENT *)0) {      
        OSEventFreeList = (OS_EVENT *)OSEventFreeList->OSEventPtr;
    }
    OS_EXIT_CRITICAL();
    if (pevent != (OS_EVENT *)0) {               /* 若ECB非空，初始化其成员变量 */
        OS_ENTER_CRITICAL();
        pq = OSQFreeList;                        /* 拿取一个队列控制块 */
        if (pq != (OS_Q *)0) {                   /* 队列控制块非零 */
            OSQFreeList            = OSQFreeList->OSQPtr; /* 更新队列空闲链表 */
            OS_EXIT_CRITICAL();
            pq->OSQStart           = start;               /* 初始化队列控制块 */
            pq->OSQEnd             = &start[size];
            pq->OSQIn              = start;
            pq->OSQOut             = start;
            pq->OSQSize            = size;
            pq->OSQEntries         = 0u;
            pevent->OSEventType    = OS_EVENT_TYPE_Q;     /* 初始化事件控制块 */
            pevent->OSEventCnt     = 0u;
            pevent->OSEventPtr     = pq;
            OS_EventWaitListInit(pevent);  /* 清空等待任务优先级表 */ 
        } else {     /* 若队列控制块为空，将任务控制块送回空闲链表 */
            pevent->OSEventPtr = (void *)OSEventFreeList; 
            OSEventFreeList    = pevent;
            OS_EXIT_CRITICAL();
            pevent = (OS_EVENT *)0;
        }
    }
    return (pevent);
}

/* **** 从队列中请求消息 ****
*    输入：pevent   目标消息队列
*          timeout  超时时间
*          perr     错误码
*    输出：无
*/
void  *OSQPend (OS_EVENT  *pevent,
                INT32U     timeout,
                INT8U     *perr)
{
    void      *pmsg;
    OS_Q      *pq;
    /* 异常状态判断 */
    if (pevent->OSEventType != OS_EVENT_TYPE_Q) 
        *perr = OS_ERR_EVENT_TYPE;
        return ((void *)0);
    }
    if (OSIntNesting > 0u) {                   
        *perr = OS_ERR_PEND_ISR;              
        return ((void *)0);
    }
    if (OSLockNesting > 0u) {                    
        *perr = OS_ERR_PEND_LOCKED;             
        return ((void *)0);
    }
    OS_ENTER_CRITICAL();
    pq = (OS_Q *)pevent->OSEventPtr;             /* 拿取队列控制块 */
    if (pq->OSQEntries > 0u) {                   /* 若队列内有消息 */
        pmsg = *pq->OSQOut++;                    /* 取一个消息，更新消息队列，返回*/
        pq->OSQEntries--;                        
        if (pq->OSQOut == pq->OSQEnd) {          
            pq->OSQOut = pq->OSQStart;
        }
        OS_EXIT_CRITICAL();
        *perr = OS_ERR_NONE;
        return (pmsg);                           
    }
    /* 若队列内无消息,执行与其他基本一致的挂起等待流程 */
    OSTCBCur->OSTCBStat     |= OS_STAT_Q;        /* Task will have to pend for a message to be posted  */
    OSTCBCur->OSTCBStatPend  = OS_STAT_PEND_OK;
    OSTCBCur->OSTCBDly       = timeout;          /* Load timeout into TCB                              */
    OS_EventTaskWait(pevent);                    /* Suspend task until event or timeout occurs         */
    OS_EXIT_CRITICAL();
    OS_Sched();
    OS_ENTER_CRITICAL();
    switch (OSTCBCur->OSTCBStatPend) {               /* See if we timed-out or aborted */
        case OS_STAT_PEND_OK:         /* Extract message from TCB (Put there by QPost) */
             pmsg =  OSTCBCur->OSTCBMsg;
            *perr =  OS_ERR_NONE;
             break;
        case OS_STAT_PEND_ABORT:
             pmsg = (void *)0;
            *perr =  OS_ERR_PEND_ABORT;               /* Indicate that we aborted */
             break;
        case OS_STAT_PEND_TO:
        default:
             OS_EventTaskRemove(OSTCBCur, pevent);
             pmsg = (void *)0;
            *perr =  OS_ERR_TIMEOUT;   /* Indicate that we didn't get event within TO */
             break;
    }
    OSTCBCur->OSTCBStat          =  OS_STAT_RDY;      /* Set task status to ready */
    OSTCBCur->OSTCBStatPend      =  OS_STAT_PEND_OK;  /* Clear pend  status */
    OSTCBCur->OSTCBEventPtr      = (OS_EVENT  *)0;    /* Clear event pointers */
    OSTCBCur->OSTCBMsg           = (void      *)0;    /* Clear  received message */
    OS_EXIT_CRITICAL();
    return (pmsg);                                    /* Return received message */
}

/* **** 发送消息到消息队列 ****
*    输入：pevent   目标消息队列
*          pmsg     目标消息
*    返回：err      错误码
*/
INT8U  OSQPost (OS_EVENT  *pevent,
                void      *pmsg)
{
    OS_Q      *pq;
    if (pevent->OSEventType != OS_EVENT_TYPE_Q) {      
        return (OS_ERR_EVENT_TYPE);
    }
    OS_ENTER_CRITICAL();
    /* 若有任务在等待,说明此时队列为空,直接把新入队的msg给最高优先级等待任务 */
    if (pevent->OSEventGrp != 0u) {                    
        (void)OS_EventTaskRdy(pevent, pmsg, OS_STAT_Q, OS_STAT_PEND_OK);
        OS_EXIT_CRITICAL();
        OS_Sched();
        return (OS_ERR_NONE);
    }
    /* 若无任务在等待，更新消息队列 */
    pq = (OS_Q *)pevent->OSEventPtr;
    if (pq->OSQEntries >= pq->OSQSize) {  /* 若队列已满，报错 */
        OS_EXIT_CRITICAL();
        return (OS_ERR_Q_FULL);
    }
    *pq->OSQIn++ = pmsg;  /* 若队列未满，更新队列 */
    pq->OSQEntries++;
    if (pq->OSQIn == pq->OSQEnd) {
        pq->OSQIn = pq->OSQStart;
    }
    OS_EXIT_CRITICAL();
    return (OS_ERR_NONE);
}
```

### Question

1. 任务堆栈如何保证运行任务内代码时将全局区的任务堆栈对应的内存充当栈区进行使用?

   >  ARM架构中有MSP(主堆栈指针)和PSP(进程堆栈指针)两个栈顶指针，分别用于系统堆栈和任务堆栈，main和中断处理会使用MSP，而OS中的任务堆栈则会使用PSP。任务创建时会将任务栈初始化并将栈顶指针存入任务控制块，任务调度时将任务的栈顶指针赋给PSP然后进行恢复现场即可使任务开始运行。

2. 任务栈大小是如何发挥作用的？(任务创建整个流程中未涉及到任务栈大小，仅在任务栈数组创建时定了数组大小)

   > 任务栈的大小并不会发生作用 -_- ，仅仅是在分配时为其提供了确定大小的内存空间。如若溢出时产生了hardfault，其真正的产生原因也并非因为栈溢出，而是因为栈溢出后可能导致的一系列不合法操作。如对只读区域的修改，对其他内存区域的错误修改导致cpu运行时的逻辑异常等。
   >
   > 所谓的数组越界其底层原理也是如此，并非数组越界就一定会导致hardfault，而是因其产生的其他不合法行为才会导致异常。因为数组是一个编译器级别的东西，cpu根本就不知道这玩意是个数组，更不会知道编译好的程序这么操作会不会导致越界。

3. 为什么任务中延时就会使任务进入挂起状态？不用系统提供的延时函数是否也能如此？

   > 首先，延时和挂起是两种完全无关的机制，延时是延时，挂起是挂起。ucos中的延时函数会将当前运行的任务在任务就绪表中清零，并进行一次任务调度，不用ucos提供的延时函数并不能释放CPU。原子教程中用自己的delay是因为他们封装的比较好，适配了ucosii和iii。

4. SysTick滴答时钟的更新中断优先级到底高还是低？

   > 在FreeRTOS中，PendSV和SysTick异常一般被设置为硬件支持的最低逻辑优先级。

5. 既然系统时钟的中断优先级低于一般的硬件中断，那如何保证系统时钟的准确性？

   > 因为中断是有Pend等待机制的，故即使在滴答计时器溢出中断发生的瞬间没有更新系统时钟，稍晚一些也会更新，除非高优先级中断在两次滴答计时器溢出中断期间持续占用CPU，此时才会有丢帧这种宏观上的计时错误。故无论对于FreeRTOS或UCOS，虽然从宏观上系统时钟是准确的，但和系统时钟周期在一个数量级的系统延时函数都是不准确的。
   
6. ucosii优先级反转问题的解决是仅在互斥信号量中还是信号量中也有？

   > 仅在互斥信号量中有关于优先级反转的解决。互斥信号量创建时就必须指定一个无任务占有的优先级继承优先级，用于防止优先级反转。

