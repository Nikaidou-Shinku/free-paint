import platform
import json
import asyncio
import aiohttp

if platform.system() == "Linux":
    import uvloop

PAINTBOARD_URL = "https://www.luogu.com.cn/paintboard"
WEBSOCKET_URL = "wss://ws.luogu.com.cn/ws"
JOIN_PAINTBOARD = {
    "type": "join_channel",
    "channel": "paintboard",
    "channel_param": ""
}

TOKEN_LIST = []
tasks = {}
total_num = 0
finish_num = 0

def load_tokens(filename):
    global TOKEN_LIST
    with open(filename, "r", encoding = "UTF-8") as token_file:
        TOKEN_LIST = token_file.readlines()
    TOKEN_LIST = [token.strip() for token in TOKEN_LIST]

def load_picture(filename, dx, dy):
    global tasks
    global total_num
    with open(filename, "r", encoding = "UTF-8") as pic_file:
        pic = json.load(pic_file)
    tasks = {(px[0] + dx, px[1] + dy): (px[2], 0) for px in pic}
    total_num = len(tasks)

def alpha2number(c):
    return ord(c) - 87 if c.isalpha() else ord(c)

async def get_board(client):
    global finish_num
    url = PAINTBOARD_URL + "/board"
    async with client.get(url) as res:
        board = await res.text()
    board = board.split()
    for px in tasks:
        x, y = px
        c, nowc = tasks[px]
        nowc = alpha2number(board[x][y])
        tasks[px] = (c, nowc)
        if nowc == c:
            finish_num += 1

async def get_pxs(client):
    global finish_num
    async with client.ws_connect(WEBSOCKET_URL) as ws:
        await ws.send_str(json.dumps(JOIN_PAINTBOARD))
        async for msg in ws:
            res = json.loads(msg.data)
            if res["type"] == "paintboard_update":
                x, y = res["x"], res["y"]
                if (x, y) in tasks:
                    c, nowc = tasks[(x, y)]
                    mark1 = c == nowc
                    nowc = res["color"]
                    mark2 = c == nowc
                    tasks[(x, y)] = (c, nowc)
                    if mark1 and (not mark2):
                        print("Position (%d, %d) changed from to %d. (expect %d)" % (x, y, nowc, c))
                        finish_num -= 1
                    if (not mark1) and mark2:
                        print("Position (%d, %d) changed from to %d. (expect %d)" % (x, y, nowc, c))
                        finish_num += 1

def getToken():
    pass

async def paint_px(client, data):
    url = PAINTBOARD_URL + "/paint?token=" + getToken()
    # async with client.post(url, )
    pass

async def paint_pxs(client):
    pass

async def print_infos():
    while True:
        print("[Info] Current progress: %.1lf%% (%d/%d)." % (finish_num / total_num, finish_num, total_num))
        await asyncio.sleep(2)

async def main():
    load_tokens("tokens.txt")
    load_picture("picture.json", 0, 0)
    async with aiohttp.ClientSession() as client:
        await get_board(client)

        task_get_new_pxs = asyncio.create_task(get_pxs(client))
        task_paint_pxs = asyncio.create_task(paint_pxs(client))
        task_print_infos = asyncio.create_task(print_infos())

        await task_get_new_pxs
        await task_paint_pxs
        await task_print_infos

if __name__ == "__main__":
    if platform.system() == "Linux":
        uvloop.install()
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
