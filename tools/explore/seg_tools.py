import numpy as np
from PIL import Image, ImageFilter


def dilate(mask, r=1):
    im = Image.fromarray((mask * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * r + 1))) > 127


def erode(mask, r=1):
    im = Image.fromarray((mask * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MinFilter(2 * r + 1))) > 127


def largest_cc(mask):
    """4-connected largest component, iterative flood fill."""
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    cur = 0
    best, best_n = 0, 0
    ys, xs = np.nonzero(mask)
    idx = list(zip(ys.tolist(), xs.tolist()))
    for (sy, sx) in idx:
        if lab[sy, sx]:
            continue
        cur += 1
        n = 0
        stack = [(sy, sx)]
        lab[sy, sx] = cur
        while stack:
            y, x = stack.pop()
            n += 1
            if y > 0 and mask[y - 1, x] and not lab[y - 1, x]:
                lab[y - 1, x] = cur; stack.append((y - 1, x))
            if y < h - 1 and mask[y + 1, x] and not lab[y + 1, x]:
                lab[y + 1, x] = cur; stack.append((y + 1, x))
            if x > 0 and mask[y, x - 1] and not lab[y, x - 1]:
                lab[y, x - 1] = cur; stack.append((y, x - 1))
            if x < w - 1 and mask[y, x + 1] and not lab[y, x + 1]:
                lab[y, x + 1] = cur; stack.append((y, x + 1))
        if n > best_n:
            best_n, best = n, cur
    print(f"  components: {cur}, largest: {best_n}px")
    return lab == best


def fill_holes(mask):
    """Background = everything reachable from the border without crossing mask."""
    bg = np.zeros_like(mask)
    h, w = mask.shape
    stack = []
    for x in range(w):
        for y in (0, h - 1):
            if not mask[y, x] and not bg[y, x]:
                bg[y, x] = True; stack.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if not mask[y, x] and not bg[y, x]:
                bg[y, x] = True; stack.append((y, x))
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not mask[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True; stack.append((ny, nx))
    return mask | ~bg
