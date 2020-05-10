# Tkinter

> python下的图形界面开发库

## 基本用法

### 创建

```python
import tkinter
root = tkinter.Tk()
root.title('My Title')
root.mainloop()
```

### Var

> 变量，可用于实现类似web开发中的数据绑定功能

```python
# 如此操作可保证当str_var变化时，lable跟着更新，即页面和后台数据绑定
str_var = tk.StringVar(root, "xxx")
lable = tk.Label(root, textvariable = str_var)

# 有StringVar、IntVar、DoubleVar等，用法一致
```

### 组织逻辑

1. 有大量控件，在初始化GUI部分进行控件的初始化和布局
   * 布局方式有pack、grid、place三种风格，与网页布局思路相似
   * 布局时可使用绝对像素值，也可使用relxxx按父窗体的一定比例布局
2. 控件的操作逻辑可使用command可选参数绑定一些自行实现的函数
3. 控件也可通过bind绑定一些鼠标和键盘事件，只在这个控件上会被触发
4. LableFrame可提供用于复杂布局的容器，将功能区分块布局