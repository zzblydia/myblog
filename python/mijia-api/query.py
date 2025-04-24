# https://github.com/Do1e/mijia-api

import json
import sys
from mijiaAPI import mijiaAPI

with open('jsons/auth.json') as f:
    auth = json.load(f)
api = mijiaAPI(auth)

devices = api.get_devices_list()['list']
with open('jsons/devices.json', 'w', encoding="utf-8") as f:
    json.dump(devices, f, indent=2, ensure_ascii=False)
