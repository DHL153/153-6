"""눈 깜빡임 얼굴 패치 (2026-10-16, DHL 시트 B-깜빡임)
표정 패치(face_*)와 같은 방법: 시트 칸을 기본 머리(parts/head.png)에 실루엣 IoU + ECC로 맞추고, 얼굴 피부 영역만 오려 패치로.
세 칸(뜬 눈·반쯤·감음)을 모두 패치로 만든다. 깜빡일 때 뜬 눈 → 반쯤 → 감음 → 반쯤 → 뜬 눈이 같은 그림 계열이라 눈 크기가 튀지 않음.
(기본 머리의 눈을 코드로 덮어 그리는 방식은 시험했으나 손그림처럼 안 보여 버림: scratchpad 기록)
실행: cd source && python3 -I build_blink.py [blink_B2.png]
"""
import sys, os, json, cv2, numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'parts')
sheet = sys.argv[1] if len(sys.argv) > 1 else 'blink_B3.png'   # B2·B3 거의 같음, B3가 칸끼리 어긋남이 더 적음(1.1px)
base = np.asarray(Image.open(os.path.join(OUT, 'head.png')).convert('RGBA')).astype(np.float32); bh, bw = base.shape[:2]
def prem(a): b = a.copy(); b[..., :3] *= b[..., 3:4] / 255; return b
B = prem(base)
r, g, b, al = base[..., 0], base[..., 1], base[..., 2], base[..., 3]
skin = (al > 200) & (r > 170) & (g > 100) & (g < 200) & (b < 140) & (r - b > 70)
skin = cv2.morphologyEx(skin.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(skin); big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); skin = (lab == big).astype(np.uint8)
cnts, _ = cv2.findContours(skin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); face = np.zeros_like(skin); cv2.drawContours(face, cnts, -1, 1, -1)
face = cv2.erode(face, np.ones((5, 5), np.uint8))
cv2.ellipse(face, (366, 248), (30, 40), 0, 0, 360, 1, -1)      # 머리카락에 붙은 먼 눈도 패치 범위에 (face_* 와 같은 처리)
feather = cv2.GaussianBlur(face.astype(np.float32), (0, 0), 2.0)

def split(fn):
    a = np.asarray(Image.open(os.path.join(HERE, 'sheets_v3', fn)).convert('RGB')).astype(float); rr, gg, bb = a[..., 0], a[..., 1], a[..., 2]
    bgc = np.median(a[:8, :8].reshape(-1, 3), 0); s = np.minimum(rr, bb) - gg; alpha = np.clip((175 - s) / 80, 0, 1); A = alpha[..., None]
    col = np.clip(np.where(A > .02, (a - (1 - A) * bgc) / np.maximum(A, 1e-3), 0), 0, 255); rgba = np.dstack([col, alpha * 255]).astype(np.float32)
    lab, n = nd.label(nd.binary_dilation(alpha > .5, iterations=3)); cells = []
    for i, sl in enumerate(nd.find_objects(lab)):
        m = lab[sl] == i + 1
        if m.sum() < 5000: continue
        p = rgba[sl].copy(); p[..., 3] *= m; cells.append((sl[1].start, p))
    return [p for _, p in sorted(cells, key=lambda t: t[0])]

def align(cell):
    C = prem(cell); a0 = B[..., 3] > 128; cy0, cx0 = np.argwhere(a0).mean(0); best = None
    for s in np.arange(.6, 1.0, .01):
        for d in (-4, -2, 0, 2, 4):
            M = cv2.getRotationMatrix2D((0, 0), d, s); w = cv2.warpAffine(C, M, (bw + 400, bh + 400)); a1 = w[..., 3] > 128
            if a1.sum() < 100: continue
            cy1, cx1 = np.argwhere(a1).mean(0); M[0, 2] += cx0 - cx1; M[1, 2] += cy0 - cy1
            a2 = cv2.warpAffine(C, M, (bw, bh))[..., 3] > 128; iou = (a2 & a0).sum() / (a2 | a0).sum()
            if best is None or iou > best[0]: best = (iou, M)
    iou, M = best
    gb = cv2.cvtColor(B[..., :3].clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    gc = cv2.cvtColor(C[..., :3].clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    Minv = cv2.invertAffineTransform(M).astype(np.float32)
    try: cc, Minv = cv2.findTransformECC(gb, gc, Minv, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 400, 1e-6), (cell[..., 3] > 128).astype(np.uint8), 5)
    except Exception: cc = 0
    return cv2.warpAffine(cell, Minv, (bw, bh), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP), float(iou), float(cc), Minv

cells = split(sheet); assert len(cells) == 3, len(cells)
# 세 칸을 같은 변환으로 맞춘다 (칸마다 따로 맞추면 깜빡일 때 얼굴이 미세하게 흔들림): 뜬 눈 칸으로 변환을 구하고 나머지 칸은 칸끼리 ECC
al0, iou, cc, M0 = align(cells[0])
def to_open(cell):   # 칸 → 뜬 눈 칸 좌표 (평행이동만, 칸 크기 차이 보정)
    g0 = cv2.cvtColor(prem(cells[0])[..., :3].clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    g1 = cv2.cvtColor(prem(cell)[..., :3].clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    h = max(g0.shape[0], g1.shape[0]); w = max(g0.shape[1], g1.shape[1])
    P0 = np.zeros((h, w), np.float32); P0[:g0.shape[0], :g0.shape[1]] = g0; P1 = np.zeros((h, w), np.float32); P1[:g1.shape[0], :g1.shape[1]] = g1
    W = np.eye(2, 3, dtype=np.float32)
    try: _, W = cv2.findTransformECC(P0, P1, W, cv2.MOTION_TRANSLATION, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), None, 5)
    except Exception: pass
    return W
rep = {'sheet': sheet, 'iou': round(iou, 3), 'ecc': round(cc, 3)}
mask_out = {}
for k, name in enumerate(('open', 'half', 'closed')):
    if k == 0: alk = al0
    else:
        W = to_open(cells[k]); M = M0.copy().astype(np.float64)
        A3 = np.vstack([M, [0, 0, 1]]); T = np.vstack([W, [0, 0, 1]])        # base → open → cell
        Mk = (T @ A3)[:2].astype(np.float32)
        alk = cv2.warpAffine(cells[k], Mk, (bw, bh), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP); rep[name + 'Shift'] = [round(float(W[0, 2]), 1), round(float(W[1, 2]), 1)]
    patch = alk.copy(); patch[..., 3] = np.minimum(alk[..., 3], 255) * feather
    ys, xs = np.nonzero(patch[..., 3] > 2); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    Image.fromarray(patch[y0:y1, x0:x1].clip(0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT if name != 'open' else HERE, f'blink_{name}.png'))   # 뜬 눈 칸은 맞춤 확인용(source/)
    rep[name] = [int(x0), int(y0)]
json.dump(rep, open(os.path.join(HERE, 'blink_report.json'), 'w'), indent=1); print(rep)
tiles = []
for name in (None, 'open', 'half', 'closed'):
    comp = Image.fromarray(base.astype(np.uint8), 'RGBA')
    if name: comp.alpha_composite(Image.open(os.path.join(OUT if name != 'open' else HERE, f'blink_{name}.png')), tuple(rep[name]))
    bg = Image.new('RGBA', comp.size, 'white'); bg.alpha_composite(comp); tiles.append(bg.convert('RGB').crop((170, 150, 430, 330)).resize((390, 270)))
S = Image.new('RGB', (400 * 4, 270), 'white')
for i, t in enumerate(tiles): S.paste(t, (i * 400, 0))
S.save(os.path.join(HERE, '_blink_check.png'))
