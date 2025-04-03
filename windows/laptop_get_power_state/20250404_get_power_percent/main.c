#include <windows.h>
#include <stdio.h>

int main() {
    SYSTEM_POWER_STATUS powerStatus;
    if (GetSystemPowerStatus(&powerStatus)) {
        if (powerStatus.BatteryFlag == 128) {
            printf("没有检测到电池。\n");
        } else {
            printf("电池剩余电量: %d%%\n", powerStatus.BatteryLifePercent);
            if (powerStatus.BatteryFlag & 8) { // 检查是否在充电
                printf("电池正在充电。\n");
            } else {
                printf("电池未在充电。\n");
            }
        }
    } else {
        printf("无法获取电源状态。\n");
    }
    return 0;
}