---
title:  "some notes in work"
date:   2025-06-09 23:58:00 +0800
last_modified_at: 2025-06-09 23:59:00 +0800
categories: work
tags: issues
---

# some notes in work  

## issues list  

### 20250609  
insmod self-defined kernel module on suse11sp3 error `Unknown symbol __x86_indirect_thunk_r11 (err 0)`  
```
The self-defined kernel was compiled on suse11sp3 with kernel version 3.0.101-0.47.106 with `CONFIG_RETPOLINE=y`  
When it runs on suse11sp3 with kernel version 3.0.101-0.47.90, it shows error above.  

Check the configuration by `cat /boot/config-$(uname -r) | grep CONFIG_RETPOLINE`  
It had to recompile on lower version(0.47.90) and it runs normally on higher version(0.47.106)  
```

