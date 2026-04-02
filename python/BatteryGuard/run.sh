#!/bin/bash

source /vol1/python/BatteryGuard/.venv/bin/activate
nohup python3 /vol1/python/BatteryGuard/battery_guard_single_client.py >/dev/null 2>&1 &
