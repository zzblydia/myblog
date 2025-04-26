# note  

## file list  

## action-client.py  
windows下安装netifaces失败, 原因是:  
```
error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/

```

因为在pycharm的venv里能运行, 则打开到action-client.py所在的文件夹执行:  
```
source ./.venv/Scripts/activate
pip list
pip install pyinstaller
pyinstaller.exe --version
pyinstaller.exe -F action-client.py
```

