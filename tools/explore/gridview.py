import sys
import numpy as np
from PIL import Image, ImageDraw

base = Image.open('work/we/base.png').convert('RGB')

def gridded(box, scale, step, out, labels=True):
    x0, y0, x1, y1 = box
    im = base.crop(box).resize(((x1-x0)*scale, (y1-y0)*scale), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for x in range(x0 - x0 % step, x1 + 1, step):
        px = (x - x0) * scale
        major = (x % (step*5) == 0)
        d.line([(px, 0), (px, im.height)], fill=(255, 0, 255) if major else (90, 90, 90), width=1)
        if major and labels: d.text((px+2, 2), str(x), fill=(255, 80, 255))
    for y in range(y0 - y0 % step, y1 + 1, step):
        py = (y - y0) * scale
        major = (y % (step*5) == 0)
        d.line([(0, py), (im.width, py)], fill=(255, 0, 255) if major else (90, 90, 90), width=1)
        if major and labels: d.text((2, py+2), str(y), fill=(255, 80, 255))
    im.save(out)
    print(out, im.size)

if __name__ == '__main__':
    gridded((160, 150, 620, 380), 2, 20, 'work/we/crops/g_hatebrim.png')
    gridded((150, 360, 620, 700), 2, 20, 'work/we/crops/g_body.png')
    gridded((280, 10, 920, 300), 2, 20, 'work/we/crops/g_hat.png')
    gridded((600, 300, 980, 700), 2, 20, 'work/we/crops/g_hair.png')
    gridded((200, 620, 950, 936), 2, 20, 'work/we/crops/g_bottom.png')
