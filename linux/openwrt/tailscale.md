# tailscale on openwrt  

## ps | grep tailscale  
```
11739 root      714m S    /usr/sbin/tailscaled --port 41641 --state /etc/tailscale/tailscaled.state
```

## service | grep tailscale  
```
/etc/init.d/tailscale              enabled         running
```

## cat /etc/init.d/tailscale  
类似systemd管理中的/etc/systemd/system/tailscaled.service
```
#!/bin/sh /etc/rc.common

# Copyright 2020 Google LLC.
# Copyright (C) 2021 CZ.NIC z.s.p.o. (https://www.nic.cz/)
# SPDX-License-Identifier: Apache-2.0

USE_PROCD=1 # 使用 OpenWrt 的 procd 系统来管理服务
START=80 # 服务启动顺序为 80

start_service() {
  local state_file
  local port
  local std_err std_out

  config_load tailscale # 加载 Tailscale 的配置文件，通常是 /etc/config/tailscale
  config_get_bool std_out "settings" log_stdout 1   # config_get_bool 和 config_get：从配置文件中读取参数 log_stdout(默认值 1)
  config_get_bool std_err "settings" log_stderr 1
  config_get port "settings" port 41641
  config_get state_file "settings" state_file /etc/tailscale/tailscaled.state

  /usr/sbin/tailscaled --cleanup    # 在启动服务前，运行 tailscaled --cleanup，清理之前的运行状态
  config_get enabled "settings" enabled 0
  if [ "$enabled" -eq "1" ];then
        procd_open_instance
        procd_set_param command /usr/sbin/tailscaled

        # Set the port to listen on for incoming VPN packets.
        # Remote nodes will automatically be informed about the new port number,
        # but you might want to configure this in order to set external firewall
        # settings.
        procd_append_param command --port "$port"
        procd_append_param command --state "$state_file"
        procd_append_param command --advertise-exit-node    # 增加这一行, 进程无法启动, 很奇怪

        procd_set_param respawn # 如果 tailscaled 进程意外退出，procd 会自动重启它
        procd_set_param stdout "$std_out"
        procd_set_param stderr "$std_err"

        procd_close_instance
  fi
}
```

## cat /etc/config/tailscale  
这是openwrt下的配置文件
```
config settings 'settings'
        option log_stderr '0'
        option log_stdout '0'
        option port '41641'
        option state_file '/etc/tailscale/tailscaled.state'
        option enabled '1'
        option lan_enabled '1'
        option wan_enabled '0'
```

## to be exit node  
tailscale up --advertise-exit-node --accept-routes --advertise-routes=192.168.31.0/24  
```
如果你运行 tailscale up 并尝试更改某个选项，Tailscale 会提示你当前配置与新配置不匹配，并显示完整的当前配置。
tailscale up --advertise-exit-node

Error: changing settings via 'tailscale up' requires mentioning all
non-default flags. To proceed, either re-run your command with --reset or
use the command below to explicitly mention the current value of
all non-default settings:

        tailscale up --advertise-exit-node --accept-routes --advertise-routes=192.168.31.0/24
```

## tailscale debug prefs  

## tailscale status  
查看所有设备和状态  


