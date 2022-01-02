import platform
import json
import time
import asyncio
import aiohttp
import collections
import colorama

if platform.system() == "Linux":
    import uvloop

SLEEP_TIME = 31
PAINTBOARD_URL = "https://www.luogu.com.cn/paintboard"
WEBSOCKET_URL = "wss://ws.luogu.com.cn/ws"
JOIN_PAINTBOARD = {
    "type": "join_channel",
    "channel": "paintboard",
    "channel_param": ""
}

TOKEN_LIST = []
tasks = {}
change_time = collections.Counter()
total_num = 0
finish_num = 0
VERY_BIG_NUMBER = 998244353

def load_tokens(filename):
    global TOKEN_LIST
    global token_idx
    with open(filename, "r", encoding = "UTF-8") as token_file:
        TOKEN_LIST = token_file.readlines()
    TOKEN_LIST = [token.strip() for token in TOKEN_LIST]
    token_idx = len(TOKEN_LIST)

def load_picture(filename, dx, dy):
    global tasks
    global total_num
    with open(filename, "r", encoding = "UTF-8") as pic_file:
        pic = json.load(pic_file)
    tasks = {(px[0] + dx, px[1] + dy): (px[2], 0) for px in pic}
    total_num = len(tasks)

def alpha2number(c):
    return ord(c) - 87 if c.isalpha() else ord(c) - 48

async def get_board(client):
    global finish_num
    url = PAINTBOARD_URL + "/board"
    async with client.get(url) as res:
        board = await res.text()
    board = board.split('\n')
    for px in tasks:
        x, y = px
        c, nowc = tasks[px]
        nowc = alpha2number(board[x][y])
        tasks[px] = (c, nowc)
        if nowc == c:
            finish_num += 1
            change_time[px] = -VERY_BIG_NUMBER
        else:
            change_time[px] = 0

async def get_pxs(client):
    global finish_num
    async with client.ws_connect(WEBSOCKET_URL) as ws:
        await ws.send_str(json.dumps(JOIN_PAINTBOARD))
        async for msg in ws:
            res = json.loads(msg.data)
            if res["type"] == "paintboard_update":
                px = (res["x"], res["y"])
                if px in tasks:
                    c, nowc = tasks[px]
                    mark1 = c == nowc
                    nowc = res["color"]
                    mark2 = c == nowc
                    tasks[px] = (c, nowc)
                    if mark1 and (not mark2):
                        finish_num -= 1
                        change_time[px] += VERY_BIG_NUMBER + 1
                        print(colorama.Fore.RED + "[Warn] Position (%d, %d) is damaged with time %d." % (px + (change_time[px],)))
                    if (not mark1) and mark2:
                        finish_num += 1
                        change_time[px] -= VERY_BIG_NUMBER
                        print(colorama.Fore.GREEN + "[Info] Position (%d, %d) is ok." % px)

token_idx = 0
head_time = 0
async def getToken():
    global token_idx
    global head_time
    if token_idx >= len(TOKEN_LIST):
        now_time = time.time()
        if now_time < head_time:
            await asyncio.sleep(head_time - now_time)
        token_idx = 1
        head_time = time.time() + SLEEP_TIME
        return TOKEN_LIST[0]
    token_idx += 1
    return TOKEN_LIST[token_idx - 1]

async def paint_px(client, data, token):
    url = PAINTBOARD_URL + "/paint?token=" + token
    async with client.post(url, data = data) as res:
        if res.status == 200:
            x, y = data["x"], data["y"]
            change_time[(x, y)] -= 1
            print(colorama.Fore.BLUE + "[Info] Paint successed at position (%d, %d)." % (x, y))
        elif res.status == 403:
            msg = await res.text()
            msg = json.loads(msg)
            if msg["data"] == "Invalid token":
                print(colorama.Fore.RED + "[Error] Token does not work.")
            elif msg["data"] == "操作过于频繁":
                print(colorama.Fore.RED + "[Error] Cooling time is not up.")
            else:
                print(colorama.Fore.RED + "[Error] 403:")
                print(colorama.Fore.RED + msg)
        else:
            print(colorama.Fore.RED + "[Error] %d:" % (res.status))
            print(colorama.Fore.RED + await res.text())

async def paint_pxs(client):
    await asyncio.sleep(1)
    while True:
        token = await getToken()
        px = change_time.most_common(1)[0]
        x, y = px[0]
        print(colorama.Fore.YELLOW + "[Info] get px (%d, %d) with change time %d." % (x, y, px[1]))
        c, nowc = tasks[px[0]]
        await paint_px(client, {"x": x, "y": y, "color": c}, token)

async def print_infos():
    while True:
        print("[Info] Current progress: {:.1f}% ({}/{}).".format(finish_num / total_num * 100, finish_num, total_num))
        await asyncio.sleep(5)

async def main():
    load_tokens("tokens.txt")
    load_picture("picture.json", 158, 400)
    async with aiohttp.ClientSession() as client:
        await get_board(client)

        task_get_new_pxs = asyncio.create_task(get_pxs(client))
        task_paint_pxs = asyncio.create_task(paint_pxs(client))
        task_print_infos = asyncio.create_task(print_infos())

        await task_get_new_pxs
        await task_paint_pxs
        await task_print_infos

if __name__ == "__main__":
    colorama.init(autoreset = True)
    if platform.system() == "Linux":
        uvloop.install()
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
