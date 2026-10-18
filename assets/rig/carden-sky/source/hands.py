"""26 스카이아크 카르덴 쥔 손 다듬기 (2026-10-18 22:27, 16 네온 hands.py 복사 — fistF 자리만 스카이 원화로 다시 잼)
16 네온 카르덴 쥔 손 다듬기 (2026-10-18, 6 러스트 hands.py 복사 — fistF 자리만 네온 원화로 다시 잼)
6 카르덴 쥔 손 다듬기 (2026-10-17) — 장갑이 어두운 갈색이라 18 의 피부색 방식 대신 '알파 폭' 방식
- 가로 자루(handL·handR): 열마다 불투명 세로 폭 → 양 끝에서 폭 ≤ 자루 굵기+6 인 열 = 자루 토막 → 지움 (게임 봉이 같은 선에 그려짐)
- 자루 축 y = 토막 열들의 위·아래 가운데 중앙값, 쥔 점 = 주먹 열 가운데 × 자루 축
- fistF(먼 손, 대기·달리기) = 원화(ref1024)에서 오림: 시트 주먹은 손 좌우가 원화와 반대(엄지·소매 쪽이 뒤바뀜, 2026-10-17 21:58 확인)
결과: parts_work/*.png + hands.json"""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'parts_work'); os.makedirs(OUT, exist_ok=True)

FISTW = {'handR': 46}
def horiz(name, sides):
    a = np.asarray(Image.open(os.path.join(HERE, 'cut', name + '.png')).convert('RGBA')).copy(); al = a[..., 3] > 128; H, W = al.shape
    ext = np.array([(np.ptp(np.nonzero(al[:, x])[0]) + 1) if al[:, x].any() else 0 for x in range(W)])
    nz = np.nonzero(ext)[0]; th = float(np.median(ext[nz[-12:-3]]))          # 자루 굵기: 오른쪽 끝 토막(두 손 모두 오른쪽에 자루가 나옴)
    stub = np.zeros(W, bool); thv = []
    for side in sides:
        rng = range(W) if side == 'left' else range(W - 1, -1, -1)
        for x in rng:
            if ext[x] == 0: continue
            if ext[x] <= th + 5: stub[x] = True; ys = np.nonzero(al[:, x])[0]; thv.append((ys.min() + ys.max()) / 2)
            else: break
    cy = float(np.median(thv)); fx = np.nonzero(~stub & (ext > 0))[0]
    a[:, stub, 3] = 0
    ys, xs = np.nonzero(a[..., 3] > 0); x0, y0 = int(xs.min()), int(ys.min()); a = a[y0:ys.max() + 1, x0:xs.max() + 1]
    Image.fromarray(a, 'RGBA').save(os.path.join(OUT, name + '.png'))
    fist = FISTW.get(name); fl = fx.max() - fist + 1 if fist else fx.min()   # 주먹 폭(그림에서 읽음): 팔뚝이 붙은 handR 은 오른쪽 끝에서 이 폭만 주먹
    g = [(fl + fx.max()) / 2 - x0, cy - y0]
    return dict(file=f'parts_work/{name}.png', grip=[round(g[0], 1), round(g[1], 1)], shaftDir=[1, 0], off=[x0, y0], fistX=[int(fx.min() - x0), int(fx.max() - x0)], thick=round(float(np.median([ext[x] for x in np.nonzero(stub)[0]])), 1))

def fist_from_ref():
    """스카이 원화(ref1024) 봉 쥔 주먹: 주먹 x 748~893 · y 540~690, 자루 x 792~840, 주먹 아래·오른쪽 = 크림 소맷단 고리, 왼쪽 아래 = 남색 소매(지움 — 먼 팔뚝 foreF 가 뒤에서 들어옴), 그 왼쪽 = 땋은 수염 (g/fist2 격자, 10-18 22:27)"""
    R = np.asarray(Image.open(os.path.join(HERE, 'ref1024.png')).convert('RGBA')).copy()
    x0, y0, x1, y1 = 736, 528, 904, 730; a = R[y0:y1, x0:x1].copy(); H, W = a.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]; X, Y = xx + x0, yy + y0
    k = np.ones((H, W)); sh = (X >= 789) & (X <= 847)
    k[sh & (Y < 543)] = 0; k[sh & (Y > 694)] = 0                     # 자루 토막(주먹 위·아래)
    k *= np.clip((X - 750) / 5, 0, 1)                                  # 왼쪽(땋은 수염·소매) 부드럽게 지움
    k[(Y > 694) & (X < 792)] = 0                                       # 주먹 아래 왼쪽 소매·소맷단 아래쪽(팔뚝 그림이 이어 줌)
    a[..., 3] = (a[..., 3] * k).astype(np.uint8)
    m = a[..., 3] > 20; lb, n = nd.label(m); sz = nd.sum(m, lb, range(1, n + 1)); a[..., 3] = np.where(lb == 1 + int(np.argmax(sz)), a[..., 3], 0)
    ys, xs = np.nonzero(a[..., 3] > 0); ox, oy = int(xs.min()), int(ys.min()); a = a[oy:ys.max() + 1, ox:xs.max() + 1]
    Image.fromarray(a, 'RGBA').save(os.path.join(OUT, 'fistF.png'))
    # 쥔 점 = 자루 가운데선(x 816) × 주먹 세로 가운데(y 615), 손목(팔뚝 끝) = 주먹 왼쪽 아래 소맷단 가운데(778, 684)
    return dict(file='parts_work/fistF.png', origin=[x0 + ox, y0 + oy], gripRef=[816, 615], wristRef=[778, 684])

if __name__ == '__main__':
    R = {'handL': horiz('handL', ['left', 'right']), 'handR': horiz('handR', ['right']), 'fistF': fist_from_ref()}
    json.dump(R, open(os.path.join(HERE, 'hands.json'), 'w'), indent=1); print(json.dumps(R))
