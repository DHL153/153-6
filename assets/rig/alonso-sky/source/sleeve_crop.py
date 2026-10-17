# 소매 밑단에서 자르기 (DHL 01:54 '팔이 여러 개' → 윗팔 = 소매까지만, 팔뚝 조각의 팔꿈치 살이 소매 안으로 들어가게)
#  흰 소매 픽셀의 열마다 가장 아래 = 밑단(이웃 열과 매끄럽게), 그 아래는 지우고 밑단 선을 4배 크기로 그려 줄여 붙임(계단 없음)
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
def crop_hem(src, out, y_min=60, width=3.2, ink=(52, 36, 34)):
    im = Image.open(src).convert('RGBA'); a = np.array(im).astype(int); r, g, b, al = [a[..., i] for i in range(4)]
    white = (al > 200) & (r > 190) & (g > 180) & (r - b < 75)
    H, W = al.shape; xs, ys = [], []
    for x in range(W):
        c = np.where(white[:, x])[0]; c = c[c > y_min]
        if len(c): xs.append(x); ys.append(int(c.max()) + 1)
    md = np.median(ys); keep = [i for i, y in enumerate(ys) if y >= md - 18]; xs = [xs[i] for i in keep]; ys = [ys[i] for i in keep]   # 옆 가장자리(소매 위쪽에서 끝나는 열)는 밑단 아님
    ys = ndimage.median_filter(np.array(ys, float), 5, mode='nearest'); ys = ndimage.uniform_filter1d(ys, 3, mode='nearest')
    hem = dict(zip(xs, ys)); x0, x1 = xs[0], xs[-1]
    o = a.copy()
    for x in range(W):   # 밑단 아래(선 두께 절반 넘게) 지움
        y = hem.get(x, hem[x0] if x < x0 else hem[x1])
        o[int(np.ceil(y + width * .5)):, x, 3] = 0
        if x < x0 - 3 or x > x1 + 3: o[int(y) - 2:, x, 3] = 0
    S = 4; ln = Image.new('L', (W * S, H * S), 0); d = ImageDraw.Draw(ln)
    pts = [((x + .5) * S, (hem[x] + .3) * S) for x in xs]; d.line(pts, fill=255, width=int(width * S), joint='curve')
    for p in (pts[0], pts[-1]): d.ellipse([p[0] - width * S / 2, p[1] - width * S / 2, p[0] + width * S / 2, p[1] + width * S / 2], fill=255)
    m = np.array(ln.resize((W, H), Image.LANCZOS)).astype(float) / 255
    for i, v in enumerate(ink): o[..., i] = np.round(o[..., i] * (1 - m) + v * m)
    o[..., 3] = np.maximum(o[..., 3], (m * 255).astype(int))
    lab, n = ndimage.label(o[..., 3] > 8)
    if n > 1:
        big = 1 + int(np.argmax(ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)))); o[..., 3] = np.where(lab == big, o[..., 3], 0)
    Image.fromarray(np.clip(o, 0, 255).astype(np.uint8)).save(out)
    cx = min(xs, key=lambda q: abs(q - W / 2)); return cx, float(hem[cx])
if __name__ == '__main__':
    import sys; print(crop_hem(sys.argv[1], sys.argv[2]))
