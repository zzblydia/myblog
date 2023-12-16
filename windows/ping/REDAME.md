# ping脚本  
用于在windows上长时间ping ip/domain以监测网络状态  
设置开机启动时, 可辅助定位机器重启记录  

## 快捷方式启动  
用户登录到系统后即运行, 并不是开机启动.且会有cmd弹窗  
创建cmd的快捷方式, 并复制到以下目录  
所有用户:C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup  
单个用户:C:\Users\xxx\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup  

# #(推荐)任务计划启动
可以实现用户不登陆也执行,且无弹窗, 注意cmd文件内需要绝对路径  
开始菜单---任务计划程序---Microsoft---创建基本任务  
任务何时开始---计算机启动时---启动程序---选择cmd脚本  
点击完成时,打开任务属性对话框---完成----不管用户是否登录都要运行---不存储密码---隐藏---windows10  