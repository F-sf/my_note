# ARM_note

### 寄存器

> r0-r3：程序日常使用，传递参数
>
> r4-r11：保存局部变量
>
> r13：栈指针SP
>
> r15：程序计数器PC
>
> CPSR(Current Program Status Register)：存放一些状态标志位
>
> SPSR(Saved Program Status Register)：记录进入中断前CPSR值

### 汇编指令

| 指令 | 全称                    | 作用                         |
| ---- | ----------------------- | ---------------------------- |
| LDR  | Load to Register        | 后值存至前寄存器中           |
| LDRD | Load to Register Double | 两个字的LDR                  |
| LDM  | Load Multiple           | 前一系列数据存至后寄存器组中 |
| B    | Branch                  | 跳转                         |
| BL   | Branch with Link        | 带链接跳转                   |
| ADD  | Add                     | 加                           |
| ADC  | Add with Carry          | 带进位加                     |

