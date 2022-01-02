import sys, json
from PIL import Image

LUOGU_PAINTBOARD_COLORS = [
    (0, 0, 0),
    (255, 255, 255),
    (170, 170, 170),
    (85, 85, 85),
    (254, 211, 199),
    (250, 172, 142),
    (255, 139, 131),
    (244, 67, 54),
    (233, 30, 99),
    (226, 102, 158),
    (156, 39, 176),
    (103, 58, 183),
    (63, 81, 181),
    (0, 70, 112),
    (5, 113, 151),
    (33, 150, 243),
    (0, 188, 212),
    (59, 229, 219),
    (151, 253, 220),
    (22, 115, 0),
    (55, 169, 60),
    (137, 230, 66),
    (215, 255, 7),
    (255, 246, 209),
    (248, 203, 140),
    (255, 235, 59),
    (255, 193, 7),
    (255, 152, 0),
    (255, 87, 34),
    (184, 63, 39),
    (121, 85, 72),
    (255, 196, 206)
]

PALETTE = [item for color in LUOGU_PAINTBOARD_COLORS for item in color]
while len(PALETTE) < 768: PALETTE.append(0)

def getPalette():
    pal_image = Image.new("P", (1, 1))
    pal_image.putpalette(PALETTE)
    return pal_image

def findAvailablePixels(pic: Image.Image):
    w, h = pic.size
    pxs = pic.load()
    if (len(pxs[0, 0]) < 4):
        return [(i, j) for i in range(w) for j in range(h)]
    return [(i, j) for i in range(w) for j in range(h) if pxs[i, j][3] != 0]

def attachColor(pic: Image.Image, pxlist: list):
    pxs = pic.load()
    return [(px[0], px[1], pxs[px[0], px[1]]) for px in pxlist]

def handle(fileName: str):
    pic = Image.open(fileName)
    pxlist = findAvailablePixels(pic)
    pic = pic.convert("RGB").quantize(palette = getPalette())
    pxlist = attachColor(pic, pxlist)
    with open("output.json", "w", encoding = "UTF-8") as result:
        result.write(json.dumps(pxlist, separators = (',', ':')))
    pic.save("preview.png")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please check usage:\n  python pic2json.py <pictureFileName>")
    else: handle(sys.argv[1])
