# Pytorch

> 整理记录pytorch中的一些操作，不包括基本原理和数学推导

## 网络定义和训练流程

> 以下代码是从MNIST拿取样本搭建手写字体识别网络中截取的，28x28像素对应0-9，网络结构为[784,30,10]

``` python
import torch
# ------------------------------------- 定义 -----------------------------------------
# 定义方式1 (3层神经网络)
class Net(torch.nn.Module):
    def __init__(self, n_feature, n_hidden, n_output):
        super(Net, self).__init__()  # 继承
        self.hidden = torch.nn.Linear(n_feature, n_hidden)  # hidden layer
        self.output = torch.nn.Linear(n_hidden, n_output)  	# output layer    
    # 前向计算
    def forward(self, a_input):    	
        a_hidden = torch.sigmoid(self.hidden(a_input))      # 经过激活函数算出下一层的输入
        a_output = torch.sigmoid(self.output(a_hidden))		# 经过激活函数算出输出
        return a_output
net = Net(n_feature=784, n_hidden=30, n_output=10)     # define the network

# 定义方式2(快速搭建)
net = torch.nn.Sequential(
    torch.nn.Linear(784, 30),	# 第一个隐藏层
    torch.nn.Sigmoid(),			# 第一个隐藏层的激活函数
    torch.nn.Linear(30, 10),	# 输出层
    torch.nn.Sigmoid(),			# 输出层的激活函数
)

# 选择优化w和b的算法
# [随机梯度下降]
optimizer = torch.optim.SGD(net.parameters(), lr=3.0)  
# [冲量法]
optimizer = torch.optim.SGD(net_Momentum.parameters(), lr=LR, momentum=0.8)
# [Root Mean Square Prop法]
optimizer = torch.optim.RMSprop(net_RMSprop.parameters(), lr=LR, alpha=0.9)
# [Adaptive Moment Estimation法]
optimizer = torch.optim.Adam(net_Adam.parameters(), lr=LR, betas=(0.9, 0.99))
# 选择代价函数CostFunction
# [均方差]
loss_func = torch.nn.MSELoss()  		
# [交叉熵]
loss_func = torch.nn.CrossEntropyLoss() 

# ------------------------------------ 训练数据整理 ---------------------------------------
# 将输入层数据整理为torch.tensor(原始np数据).type(torch.类型).reshape(数据数目，输入层神经元数目)
# 预测层结果整理格式根据选用的代价函数不同有不同情况
# eg: 
train_x = torch.tensor(train_x_np).type(torch.FloatTensor).reshape(50000, 784)
train_y = torch.tensor(train_y_np).type(torch.LongTensor).reshape(50000, 10)

# --------------------------------------- 训练 -------------------------------------------
# 方法1：每次迭代对整个数据集进行计算
for t in range(200):				# 迭代200次
    out = net(train_x)              # 前向计算整个训练集
    loss = loss_func(out, train_y)  # 计算误差(代价)
    optimizer.zero_grad()   		# 清零梯度
    loss.backward()         		# 反向传播计算当前梯度
    optimizer.step()        		# 优化单步(w和b改变)
    
# 方法2：小批次训练mini_batch_training(可显著提高速度)
# 数据集小批训练，10个为一批，每次随机洗牌
import torch.utils.data as Data
torch_dataset = Data.TensorDataset(train_x, train_y)
loader = Data.DataLoader(dataset=torch_dataset, batch_size=10, shuffle=True)
for epoch in range(5):  				# 迭代5次
    for step, (b_x, b_y) in enumerate(loader):  # 小批次训练
        out = net(train_x)              # 前向计算整个训练集
        loss = loss_func(out, train_y)  # 计算误差(代价)
        optimizer.zero_grad()   		# 清零梯度
        loss.backward()         		# 反向传播计算当前梯度
        optimizer.step()        		# 优化单步(w和b改变)
    
# --------------------------------------- 保存 ------------------------------------------- 
torch.save(net1, 'net.pkl')  					  # 方法1：保存整个网络为pickle
torch.save(net1.state_dict(), 'net_params.pkl')   # 方法2：仅将w,b等参数保存为pickle

# --------------------------------------- 读取 ------------------------------------------- 
net = torch.load('net.pkl')		 	# 对应方法1：可直接拿取整个网咯
net = torch.nn.Sequential(   		# 对应方法2：需要先创建一个网络结构完全相同的网络，然后装载参数
    torch.nn.Linear(784, 30),
    torch.nn.Sigmoid(),
    torch.nn.Linear(30, 10),
    torch.nn.Sigmoid(),
)
net.load_state_dict(torch.load('net_params.pkl'))
```

