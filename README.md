# Free Paint

### 简介

自用[洛谷冬日绘板](https://www.luogu.com.cn/paintboard)作画脚本。

预计完成图片抖动到 32 色的脚本，以及获取绘板状态 & 调度 Token 作画的脚本。

考虑到会使用 [uvloop](https://github.com/MagicStack/uvloop)，可能无法支持 Windows。

### 使用方法

```bash
git clone https://github.com/Nikaidou-Shinku/free-paint.git
cd free-paint
pip install -r requirements.txt
# 把图片放进目录（假设为 picname.png）
python pic2json.py picname.png
# 生成 picture.json 目标文件与 preview.png 预览图片
# 打开 paint.py，修改第 12 与第 13 行的值（表示图片左上角在绘板上的坐标）
# 新建 tokens.txt 文件，每行存放一个 Token
python paint.py
```

