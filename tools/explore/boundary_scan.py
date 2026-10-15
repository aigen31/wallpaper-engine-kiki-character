import numpy as np
from PIL import Image, ImageDraw
base = Image.open('work/we/base.png').convert('RGB')
A = np.asarray(base).astype(np.int16)
R, G, B = A[..., 0], A[..., 1], A[..., 2]
lum = A.mean(2)
green = G - (R + B) / 2

def boundary(y, x0=380, x1=760):
    """First x where the pixel looks like girl (warm hair/skin) rather than screen."""
    warm = (R - G > 6) & (R > 22)
    for x in range(x0, x1):
        w = warm[y, x:x + 6]
        if w.sum() >= 4:
            return x
    return None

pts = []
for y in range(190, 680, 10):
    b = boundary(y)
    pts.append((y, b))
print("y -> first warm x")
for y, b in pts:
    print(f"  {y:4d} {b}")
vis = base.copy(); d = ImageDraw.Draw(vis)
for y, b in pts:
    if b: d.point((b, y), fill=(255, 0, 255))
Image.fromarray(np.asarray(vis)).save('work/we/crops/boundary.png')
