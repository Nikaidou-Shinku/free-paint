import platform
import json
import asyncio
import aiohttp
import collections
import colorama

if platform.system() == "Linux":
    import uvloop

FROM_X = 160
FROM_Y = 391
CONCURRENCY = 6

TIMEOUT_TIME = 1
SLEEP_TIME = 31
RETRY_TIME = 5
PAINTBOARD_URL = "https://www.luogu.com.cn/paintboard"
WEBSOCKET_URL = "wss://ws.luogu.com.cn/ws"
JOIN_PAINTBOARD = {
    "type": "join_channel",
    "channel": "paintboard",
    "channel_param": ""
}
VERY_BIG_NUMBER = 998244353
CHANGE_TIME_LOCK = asyncio.Lock()

tasks = {}
change_time = collections.Counter()
total_num = 0
finish_num = 0
TOKEN_NUM = 0


def moveCurse(line, row):
    print("\033[%d;%dH" % (line, row), end = "")


def load_tokens(filename):
    with open(filename, "r", encoding = "UTF-8") as token_file:
        tokens = token_file.readlines()
    tokens = [token.strip() for token in tokens]
    return tokens


def load_picture(filename, dx, dy):
    global tasks
    global total_num

    with open(filename, "r", encoding = "UTF-8") as pic_file:
        pic = json.load(pic_file)
    tasks = {(px[0] + dx, px[1] + dy): (px[2], 0) for px in pic}
    total_num = len(tasks)


async def get_board(client):
    global finish_num
    global change_time

    url = PAINTBOARD_URL + "/board"
    async with client.get(url) as res:
        board = await res.text()
    board = board.split()
    for px in tasks:
        x, y = px
        c, nowc = tasks[px]
        nowc = int(board[x][y], 32)
        tasks[px] = (c, nowc)
        if nowc == c:
            finish_num += 1
            change_time[px] = -VERY_BIG_NUMBER
        else:
            change_time[px] = 0


def add_change_time(px, num):
    global change_time
    change_time[px] += num


def damage(px):
    global finish_num

    finish_num -= 1
    add_change_time(px, VERY_BIG_NUMBER + 1)
    print("\033[2K", end = "")
    print(colorama.Fore.RED + "[Warn] Position (%d, %d) is damaged with time %d." % (px[0], px[1], change_time[px]))


def finish(px):
    global finish_num

    finish_num += 1
    add_change_time(px, -VERY_BIG_NUMBER)
    print("\033[2K", end = "")
    print(colorama.Fore.GREEN + "[Info] Position (%d, %d) is ok." % px)


def px_change(x, y, c):
    px = (x, y)
    if px not in tasks:
        return
    target, old = tasks[px]
    mark1 = target == old
    mark2 = target == c
    tasks[px] = (target, c)
    if mark1 and (not mark2):
        damage(px)
    if (not mark1) and mark2:
        finish(px)


def print_board_info():
    moveCurse(TOKEN_NUM + 1, 1)
    print("\033[2K[Info] Current progress: {:.1f}% ({}/{}).".format(finish_num / total_num * 100, finish_num, total_num))


async def refresh_board(client):
    url = PAINTBOARD_URL + "/board"

    try:
        async with client.get(url) as res:
            board = await res.text()
    except asyncio.exceptions.TimeoutError:
        moveCurse(TOKEN_NUM + 1, 1)
        print("\033[2K", end = "")
        print(colorama.Fore.RED + "[Error] Get paintboard failed.")
        return

    board = board.split()

    if len(board) != 1000:
        moveCurse(TOKEN_NUM + 1, 1)
        print("\033[2K", end = "")
        print(colorama.Fore.RED + "[Error] Get empty paintboard.")
        return

    moveCurse(TOKEN_NUM + 2, 1)
    for px in tasks:
        x, y = px
        nowc = int(board[x][y], 32)
        async with CHANGE_TIME_LOCK:
            px_change(x, y, nowc)


async def get_pxs(client):
    while True:
        print_board_info()
        await asyncio.sleep(5)
        moveCurse(TOKEN_NUM + 2, 1)
        print('\033[0J', end = "")
        await refresh_board(client)


async def paint_px(client, data, idx, token):
    global finish_num

    url = PAINTBOARD_URL + "/paint?token=" + token
    px = (data["x"], data["y"])
    try:
        async with client.post(url, data = data) as res:
            if res.status == 200:
                target, old = tasks[px]
                tasks[px] = (target, data["color"])
                finish_num += 1
                print_token_info(idx, token, colorama.Fore.GREEN,
                    "[info] Paint successed at position (%d, %d)." % px)
                print_board_info()
                return SLEEP_TIME
            elif res.status == 403:
                add_change_time(px, VERY_BIG_NUMBER)
                msg = await res.text()
                msg = json.loads(msg)
                if msg["data"] == "Invalid token":
                    print_token_info(idx, token, colorama.Fore.RED,
                        "[Error] Token does not work.")
                    return -1
                elif msg["data"] == "操作过于频繁":
                    print_token_info(idx, token, colorama.Fore.RED,
                        "[Error] Cooling time is not up.")
                    return RETRY_TIME
                else:
                    print_token_info(idx, token, colorama.Fore.RED,
                        "[Error] Code: 403")
                    return 0.1
            else:
                add_change_time(px, VERY_BIG_NUMBER)
                print_token_info(idx, token, colorama.Fore.RED,
                    "[Error] Code: %d" % (res.status))
                return 0.1
    except asyncio.exceptions.TimeoutError:
        add_change_time(px, VERY_BIG_NUMBER)
        print_token_info(idx, token, colorama.Fore.RED,
            "[Error] Timeout.")
        return 0.1

def print_token_info(idx, token, color, msg):
    moveCurse(idx + 1, 1)
    print("\033[2K", end = "")
    msg = color + "[{}]: {}".format(token, msg)
    print(msg)

async def paint_pxs(sem, idx, token, client):
    while True:
        paint_mark = True
        async with CHANGE_TIME_LOCK:
            px = change_time.most_common(1)[0]
            if px[1] >= 0:
                add_change_time(px[0], -VERY_BIG_NUMBER)
            else:
                paint_mark = False
                print_token_info(idx, token, colorama.Fore.BLUE,
                    "[info] No pixel need to paint.")
                # Reliability has yet to be tested
        if paint_mark:
            x, y = px[0]
            print_token_info(idx, token, colorama.Fore.YELLOW,
                "[Info] get px (%d, %d) with change time %d." % (x, y, px[1]))
            c, nowc = tasks[px[0]]
            async with sem:
                res = await paint_px(client, {"x": x, "y": y, "color": c}, idx, token)
            if res < 0: return
        else: res = RETRY_TIME
        await asyncio.sleep(res)


async def main():
    global TOKEN_NUM

    tokens = load_tokens("tokens.txt")
    TOKEN_NUM = len(tokens)
    load_picture("picture.json", FROM_X, FROM_Y)
    sem = asyncio.Semaphore(CONCURRENCY)
    timeout = aiohttp.ClientTimeout(TIMEOUT_TIME)

    async with aiohttp.ClientSession(timeout = timeout) as client:
        await get_board(client)

        async_tasks = [asyncio.create_task(get_pxs(client))]
        for idx, token in enumerate(tokens):
            task = asyncio.create_task(paint_pxs(sem, idx, token, client))
            async_tasks.append(task)
        
        await asyncio.gather(*async_tasks)


if __name__ == "__main__":
    colorama.init(autoreset = True)
    print('\033[2J', end = "")
    if platform.system() == "Linux":
        uvloop.install()
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
