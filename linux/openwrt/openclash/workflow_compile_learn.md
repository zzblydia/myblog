# openclash

## 代码仓库

如果完整克隆过代码仓库,就会发现比较大. 一般都是按分支和深度拷贝.\
分支有四个, 作用大概是:

*   master 发布版本的正式代码
*   dev 开始调试分支, 发布后会合并到master
*   core 主要是clash相关
*   package 用于存储发布后的产物(dev和master最新版)

## 工作流

工作流文件比较多,逐个学习. 从`0.47.028 #340`的发布来看, 有四个:

*   Compile The New Version OpenClash (dev)
*   Clean jsDelivr Cache (dev)
*   Clean jsDelivr Cache (master)
*   Sync Core and Package to Master When release (tag)

### Compile The New Version OpenClash
对应的yml文件`compile_new_ipk.yml`, `dev`分支的`luci-app-openclash/Makefile`更新后自动触发工作流.

#### Get-Version
```
git clone -b dev --depth=1 https://github.com/vernesong/OpenClash.git OpenClash_dev
new_version=$(grep 'PKG_VERSION:=' ./luci-app-openclash/Makefile |awk -F '=' '{print $2}')

git clone -b package --depth=1 https://github.com/vernesong/OpenClash.git OpenClash_package
current_version=$(sed -n 1p ./dev/version |awk -F 'v' '{print $2}')
```
如果`new_version`和`current_version`不相等, 则触发编译

#### compile_ipk

##### Set up job
```
Ubuntu, 24.04.3, LTS
```

##### Check OpenClash Source
```
git clone -b dev --depth=1 https://github.com/vernesong/OpenClash.git
```

##### Install Dependencies
```
sudo apt-get update
sudo apt-get -y install curl git tar zstd python3 python3-pyelftools python3-setuptools
```

##### Download SDK
```
mkdir -p tmp
cd tmp
curl -SLk --connect-timeout 30 --retry 2 "https://mirrors.pku.edu.cn/openwrt/releases/22.03.0/targets/x86/64/openwrt-sdk-22.03.0-x86-64_gcc-11.2.0_musl.Linux-x86_64.tar.xz" -o "./tmp/SDK.tar.xz"
或者
curl -SLk --connect-timeout 30 --retry 2 "https://archive.openwrt.org/chaos_calmer/15.05.1/ar71xx/generic/OpenWrt-SDK-15.05.1-ar71xx-generic_gcc-4.8-linaro_uClibc-0.9.33.2.Linux-x86_64.tar.bz2" -o "./tmp/SDK.tar.xz"

tar xvf SDK.tar.xz
mv openwrt-sdk-* SDK

cd -
mkdir -p tmp/SDK/package/luci-app-openclash
cp -rfp ./luci-app-openclash/. tmp/SDK/package/luci-app-openclash/
```

##### Update third-Party Resources
```
CHNR_PATH=tmp/SDK/package/luci-app-openclash/root/etc/openclash/china_ip_route.ipset
CHNR6_PATH=tmp/SDK/package/luci-app-openclash/root/etc/openclash/china_ip6_route.ipset
YACD_PATH=tmp/SDK/package/luci-app-openclash/root/usr/share/openclash/ui/yacd
ZASHBOARD_PATH=tmp/SDK/package/luci-app-openclash/root/usr/share/openclash/ui/zashboard
METACUBEXD_PATH=tmp/SDK/package/luci-app-openclash/root/usr/share/openclash/ui/metacubexd
GEOSITE_PATH=tmp/SDK/package/luci-app-openclash/root/etc/openclash/GeoSite.dat
COUNTRY_MMDB_PATH=tmp/SDK/package/luci-app-openclash/root/etc/openclash/Country.mmdb

# 更新 China IP Route
mkdir -p tmp
curl -sSL https://ispip.clang.cn/all_cn.txt -o tmp/china_ip_route.ipset
mkdir -p $(dirname $CHNR_PATH)
cp tmp/china_ip_route.ipset $CHNR_PATH
curl -sSL https://ispip.clang.cn/all_cn_ipv6.txt -o tmp/china_ip6_route.ipset
mkdir -p $(dirname $CHNR6_PATH)
cp tmp/china_ip6_route.ipset $CHNR6_PATH

# 更新 Yacd UI
mkdir -p tmp/yacd_zip
curl -sSL https://github.com/MetaCubeX/Yacd-meta/archive/refs/heads/gh-pages.zip -o tmp/yacd.zip
unzip -q -o tmp/yacd.zip -d tmp/yacd_zip
YACD_UNZIP_PATH="tmp/yacd_zip/Yacd-meta-gh-pages"
mkdir -p "$YACD_PATH"
rm -rf "$YACD_PATH"/*
cp -rf "$YACD_UNZIP_PATH"/* "$YACD_PATH"

# 更新 ZashBoard UI
mkdir -p tmp/zashboard_zip
curl -sSL https://github.com/Zephyruso/zashboard/releases/latest/download/dist-cdn-fonts.zip -o tmp/zashboard.zip
unzip -q -o tmp/zashboard.zip -d tmp/zashboard_zip
mkdir -p "$ZASHBOARD_PATH"
rm -rf "$ZASHBOARD_PATH"/*
cp -rf tmp/zashboard_zip/dist/* "$ZASHBOARD_PATH"

# 更新 GeoSite.dat
RULES_RELEASE=$(curl -s https://api.github.com/repos/Loyalsoldier/v2ray-rules-dat/releases/latest | jq -r '.tag_name')
curl -sSL "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/download/${RULES_RELEASE}/geosite.dat" -o tmp/GeoSite.dat
mkdir -p $(dirname "$GEOSITE_PATH")
cp tmp/GeoSite.dat "$GEOSITE_PATH"

# 更新 Country.mmdb
curl -sSL "https://github.com/alecthw/mmdb_china_ip_list/releases/latest/download/Country-lite.mmdb" -o tmp/Country.mmdb
mkdir -p $(dirname "$COUNTRY_MMDB_PATH")
cp tmp/Country.mmdb "$COUNTRY_MMDB_PATH"
```

##### Compile po2lom
```
cd tmp/SDK/package/luci-app-openclash/tools/po2lmo
make && sudo make install
```

##### Compile OpenClash
```
cd tmp/SDK

ll ../SDK.tar.xz
make defconfig

Build dependency: Please install ncurses. (Missing libncurses.so or ncurses.h)
sudo apt-get install libncurses-dev libncursesw-dev

Build dependency: Please install GNU 'awk'
sudo apt install gawk

sudo make package/luci-app-openclash/compile V=99
```

#### compile_apk
上传最终产物
```
tmp/SDK/bin/packages/x86_64/base/luci-app-openclash_0.47.028_all.ipk
```
#### Post-Process