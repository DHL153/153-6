# 11 머리 위 키트 v1(전체 자세) 에서 몸통·가까운 윗팔·먼 윗팔(보이는 부분) 오리기 + 따로 그린 팔뚝 2장 자르기
# 출력: kitoh/out/*.png (키트 px 그대로, 알파) + kitoh/out/meta.json (키트 좌표의 기준점)
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SRC, '..', '..', 'carden-rust', 'source'))
from cut_sheet import key
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
rgb = np.asarray(Image.open(os.path.join(SRC, 'sheets', 'kitOH_v1.png')).convert('RGB'))
rgba, alpha = key(rgb); H, W = alpha.shape
f = rgb.astype(float) / 255; r, g, b = f[..., 0], f[..., 1], f[..., 2]; mx = f.max(2); mn = f.min(2); sat = (mx - mn) / (mx + 1e-6)
skin = (r > .75) & (g > .45) & (g < .85) & (b < .55) & (sat > .3)
lab, n = ndimage.label(skin)
def comp_at(x, y): return lab == lab[y, x]
dark = mx < .2                                   # 외곽선(검정)
hair = (sat < .18) & (mx > .22) & (mx < .97)      # 머리카락(회색·흰색) — 외곽선보다 밝고 채도 낮음
def poly(pts):
    im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=1); return np.asarray(im) > 0
def save(name, m, fill=None):
    a = rgba.copy(); a[..., 3] = np.where(m, a[..., 3], 0)
    if fill is not None: fm, col = fill; a[fm, :3] = col; a[fm, 3] = 255
    ys, xs = np.nonzero(a[..., 3] > 8); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    Image.fromarray(a[y0:y1, x0:x1], 'RGBA').save(os.path.join(OUT, name + '.png')); return [int(x0), int(y0)]
meta = {}
# --- 가까운 윗팔: 피부 덩어리(368,513) + 붙은 외곽선 + 어깨 검은 마개
upN = comp_at(368, 513)
ring = ndimage.binary_dilation(upN, iterations=7) & dark
cap = poly([(380, 598), (402, 592), (440, 596), (462, 612), (460, 640), (440, 656), (404, 656), (384, 640)]) & (dark | (mx < .45))
mN = ndimage.binary_fill_holes(upN | ring | cap)
meta['uN'] = {'off': save('uN', mN), 'shoulder': [420, 628], 'elbowTop': [343, 428]}   # 팔꿈치 점을 조금 아래로 — 윗팔 그림 위 끝이 팔뚝 덮개 밑으로 더 들어가 팔꿈치 바깥 홈이 안 보이게
# --- 먼 윗팔(보이는 부분): 피부 덩어리(737,579) + 외곽선
upF = comp_at(737, 579); mF = ndimage.binary_fill_holes(upF | (ndimage.binary_dilation(upF, iterations=7) & dark & ~hair))
meta['uFvis'] = {'off': save('uFvis', mF)}
# --- 몸통: 다각형 − 얼굴·귀·머리카락·팔
P = [(362, 640), (400, 612), (440, 606), (476, 612), (482, 636), (500, 650), (540, 656), (600, 656), (612, 648), (640, 645), (672, 660), (668, 700), (640, 715),
     (612, 718), (600, 760), (640, 785), (660, 805), (650, 828), (640, 850), (618, 868), (590, 876), (545, 877), (500, 877), (468, 868), (448, 845), (420, 832), (330, 822), (296, 812), (300, 788),
     (350, 768), (420, 752), (428, 712), (380, 702), (362, 680)]
mT = poly(P) & (alpha > 0)
face = comp_at(594, 601) | comp_at(445, 583) | comp_at(507, 650)
band = poly([(470, 600), (515, 630), (540, 650), (606, 650), (606, 640), (606, 700), (470, 700)])   # 턱·머리카락 끝이 닿는 띠
mNs = ndimage.binary_dilation(upN, iterations=4)   # 가까운 윗팔 살 부분만 뺌(어깨 검은 마개는 몸통에도 남김 — 팔이 조금 돌아도 홈이 안 보이게)
rm = (ndimage.binary_dilation(face, iterations=2) & band) | (hair & band & (np.arange(H)[:, None] < 682)) | mNs | mF
under = rm & poly(P) & band & ~mNs & ~mF          # 턱 밑: 깃 색으로 메움(리그 머리 턱이 조금 달라도 구멍이 안 보이게)
mT2 = (mT & ~rm) | under
meta['torso'] = {'off': save('torsoOH', mT2, fill=(under, (40, 40, 46)))}
json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'), indent=1); print(meta)
# --- 따로 그린 팔뚝 2장(조각 px 그대로, 자르기 없이 다각형 밖만 투명)
def piece_cut(src, name, keep, drop=None):
    a = np.array(Image.open(os.path.join(SRC, 'pieces', 'kitOH', src)).convert('RGBA')); h, w = a.shape[:2]
    im = Image.new('L', (w, h), 0); ImageDraw.Draw(im).polygon([tuple(p) for p in keep], fill=1); m = np.asarray(im) > 0
    if drop is not None: m &= ~drop(a, h, w)
    a[..., 3] = np.where(m, a[..., 3], 0); Image.fromarray(a, 'RGBA').save(os.path.join(OUT, name + '.png'))
def drop_N(a, h, w):   # 가까운 팔뚝: 팔꿈치 아래 살(짧은 윗팔)·검은 공(어깨) 지움 — 노란 마름모·팔꿈치 덮개는 남김
    f = a[..., :3].astype(float) / 255; yy, xx = np.mgrid[0:h, 0:w]
    skin_ = (f[..., 0] > .75) & (f[..., 1] > .45) & (f[..., 1] < .72) & (f[..., 2] < .55) & (yy > 262) & (xx > 70)   # 마름모(노랑, g 높음)는 남김
    return ndimage.binary_dilation(skin_, iterations=1) | ((xx < 44) & (yy > 250)) | (yy > 303)
piece_cut('kitArmN.png', 'gN', [(95, 0), (217, 0), (217, 135), (195, 140), (185, 200), (160, 250), (148, 270), (120, 280), (98, 292), (92, 306), (45, 306), (40, 282), (50, 240), (65, 205), (80, 175), (95, 120)], drop_N)
piece_cut('kitArmF.png', 'gF', [(40, 0), (180, 0), (190, 60), (172, 110), (182, 150), (195, 228), (200, 262), (150, 262), (112, 236), (100, 200), (95, 150), (88, 118), (55, 100), (40, 60)])
meta['gN'] = {'grip': [155, 50], 'elbow': [90, 272], 'fistRect': [92, 0, 125, 118]}
meta['gF'] = {'grip': [110, 55], 'elbow': [150, 240], 'fistRect': [40, 0, 150, 112]}
json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'), indent=1)
# --- 먼 팔(머리 뒤로 올라가는 윗팔·팔꿈치·팔뚝 아래쪽): 따로 그린 먼 팔에서 주먹·손목 띠를 뺀 것 — 상체에 고정, 팔뚝 끝은 머리카락 뒤로 숨음
piece_cut('kitArmF.png', 'fArm', [(60, 128), (200, 128), (203, 380), (0, 380), (0, 240), (60, 200)])
meta['fArm'] = {'shoulder': [43, 318], 'elbow': [150, 240]}
json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'), indent=1)
# --- 휘두름·런지(20:48 DHL 시트 v2): 가까운 팔 = 토시 팔뚝+주먹(칼에 붙음) · 윗팔(어깨갑 밑에서 팔꿈치까지) / 먼 주먹 — 손잡이 토막은 지움(칼 그림이 손잡이)
def cut2(src, name, keep, erase=()):
    a = np.array(Image.open(os.path.join(SRC, 'pieces', 'kitOH', src)).convert('RGBA')); h, w = a.shape[:2]
    im = Image.new('L', (w, h), 0); ImageDraw.Draw(im).polygon([tuple(p) for p in keep], fill=1); m = np.asarray(im) > 0
    for x0, y0, x1, y1 in erase: m[y0:y1, x0:x1] = False
    a[..., 3] = np.where(m, a[..., 3], 0)
    lab_, n_ = ndimage.label(a[..., 3] > 8)
    if n_ > 1: big = 1 + int(np.argmax(ndimage.sum(np.ones_like(lab_), lab_, range(1, n_ + 1)))); a[..., 3] = np.where(lab_ == big, a[..., 3], 0)
    Image.fromarray(a, 'RGBA').save(os.path.join(OUT, name + '.png'))
cut2('k2Strike.png', 'gNst', [(150, 0), (410, 0), (410, 133), (150, 133), (150, 70)], erase=[(384, 0, 410, 133)])
f2 = np.asarray(Image.open(os.path.join(SRC, 'pieces', 'kitOH', 'k2Strike.png')).convert('RGB')).astype(float) / 255
blue2 = (f2[..., 2] > .6) & (f2[..., 0] < .45)
def drop_pad(a, h, w): return ndimage.binary_dilation(blue2, iterations=2)
cut2('k2Strike.png', 'uNst', [(60, 30), (180, 40), (180, 125), (60, 125)])
_a = np.array(Image.open(os.path.join(OUT, 'uNst.png'))); _pad = ndimage.binary_dilation(blue2 | ((f2.max(2) > .85) & (np.arange(133)[:, None] < 60) & (np.arange(410)[None, :] < 120)), iterations=3)
_a[..., 3] = np.where(_pad, 0, _a[..., 3]); Image.fromarray(_a, 'RGBA').save(os.path.join(OUT, 'uNst.png'))
cut2('k2FistF.png', 'gFst', [(0, 0), (134, 0), (134, 106), (0, 106)], erase=[(0, 0, 27, 106), (108, 0, 134, 106)])
meta['gNst'] = {'grip': [340, 78], 'elbow': [168, 82], 'shaftDir': [1, 0]}
meta['uNst'] = {'shoulder': [70, 80], 'elbow': [168, 82]}
meta['gFst'] = {'grip': [67, 50], 'elbow': [67, 100], 'shaftDir': [1, 0]}
json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'), indent=1)
