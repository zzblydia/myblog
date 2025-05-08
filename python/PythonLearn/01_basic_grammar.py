def test_01():
    print(f"hello world")
    # 不换行输出
    x = "a"
    y = "b"
    print(x, end=" ")
    print(y, end=" ")
    print(x + y)


def test_string():
    print('day\nup')
    print(r'good\nstudy')  # 在字符串前面添加一个 r，表示原始字符串，不会发生转义
    string = "20250508"  # str是内置函数,变量命名避开
    print(f"string1: {string}")

    string = """这是一个段落，
    可以由多行组成"""
    print(f"string2: {string}")

    string = '123456789'
    print(string)  # 输出字符串
    print(string[0:-1])  # 输出第一个到倒数第二个的所有字符
    print(string[0])  # 输出字符串第一个字符
    print(string[2:5])  # 输出从第三个开始到第六个的字符（不包含）
    print(string[2:])  # 输出从第三个开始后的所有字符
    print(string[1:5:2])  # 输出从第二个开始到第五个且每隔一个的字符（步长为2）
    print(string * 2)  # 输出字符串两次
    print(string + '你好')  # 连接字符串


if __name__ == '__main__':
    test_01()
    test_string()
