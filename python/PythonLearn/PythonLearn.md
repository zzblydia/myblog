# Python3 Learn  

## Basic  

### 1.main方法
py文件自上而下运行, 不一定从main开始运行  
py文件被import时, 非main中的代码会被执行  
main中可以可以用作当前文件调试  

### 2.转义  
print(r'C:\some\name')  
print(a, end=',')  

### 3.切片  
```
字符串:
string[-1:-2] 为空
```

```
列表
letters[2:5] = ['C', 'D', 'E']
letters[2:5] = []
letters[:] = []
```
### 4.列表  
1.len()支持列表长度  
2.列表可以嵌套, 访问类似二维数组  

### 5.for循环迭代  
```
# 创建示例多项集
users = {'Hans': 'active', 'Éléonore': 'inactive', '景太郎': 'active'}

# 策略：迭代一个副本
for user, status in users.copy().items():
    if status == 'inactive':
        del users[user]

# 策略：创建一个新多项集
active_users = {}
for user, status in users.items():
    if status == 'active':
        active_users[user] = status
```

### 6.内置函数 range() 用于生成等差数列  
```
list(range(5, 10))
list(range(0, 10, 3))
list(range(-10, -100, -30))
```

```
a = ['Mary', 'had', 'a', 'little', 'lamb']
for i in range(len(a)):
    print(i, a[i])
```

```
sum(range(4))  # 0 + 1 + 2 + 3
```


## Medium  
## Advanced  

