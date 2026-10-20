# 4 로시 표정·깜빡임 (DHL 10-21 06:06 시트 6칸 = 원화 머리 다시 그리기 3×2): 칸마다 두건·이마 띠·머리카락(얼굴 빼고)에
# SIFT(닮음) → ECC(affine)로 원화에 맞춘 뒤, 얼굴만 오려 원화 머리 위에 얹는 조각으로 (사례집 faces7.py 와 같은 방법)
#  · 표정 4(웃음·화남·슬픔·놀람) = 얼굴 전체(이마 띠 아래 가장자리까지) · 깜빡임 2 = 눈 부분만(입·코 끝은 원화 그대로 — 깜빡일 때 입이 안 바뀜)
#  python3 faces4.py SHEET.png RIGDIR OUTPREVIEW.png
import sys, json, cv2, numpy as np
from PIL import Image, ImageDraw
SHEET, RD, PREV = sys.argv[1], sys.argv[2], sys.argv[3]
R = json.load(open(RD + '/rig.json')); J = R['jointMap']
O = Image.open(RD + '/source/ref512.png').convert('RGBA'); bg = Image.new('RGBA', O.size, (255, 0, 255, 255)); bg.alpha_composite(O)
O4 = np.array(bg.convert('RGB').resize((2048, 2048), Image.LANCZOS))
HB = (165, 78, 345, 258); X0, Y0 = HB[0] * 4, HB[1] * 4; ref = O4[Y0:HB[3] * 4, X0:HB[2] * 4]          # 720×720
# 머리 조각(head.png) 알파 = 맞춤에 쓰는 곳 (가방·칼라 빼고), 얼굴 둘레는 뺌
hp = R['parts']['head']; H = Image.open(RD + '/' + hp['src']).split()[3]; hx, hy = J['head'][0] * 4 - hp['pivot'][0], J['head'][1] * 4 - hp['pivot'][1]
HM = np.zeros((2048, 2048), np.uint8); hpaste = Image.fromarray(HM); hpaste.paste(H, (int(round(hx)), int(round(hy)))); HM = np.array(hpaste) > 100
def pmask(poly, k=4):
    m = Image.new('L', (2048, 2048), 0); ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in poly], fill=255); return np.array(m) > 0
REGFACE = [(234,160),(262,152),(292,153),(303,160),(307,184),(303,201),(294,214),(277,225),(254,225),(240,214),(233,197),(230,175)]
FACE = [(234,160),(262,152),(292,153),(303,160),(307,184),(303,201),(294,214),(277,225),(254,225),(240,214),(233,197),(230,175)]   # 이마 띠 아래 가장자리 포함(눈썹이 올라가는 표정)
EYE = [(234,170),(262,169),(284,171),(292,174),(301,174),(305,182),(303,195),(291,199),(280,197),(276,183),(265,183),(262,198),(246,200),(237,196),(232,180)]   # 눈·눈 밑 그늘만 — 위 = y169(다시 그린 눈썹 줄 빼고, 원화엔 눈썹이 이마 띠 밑), 코 선·코 끝·입 = 원화
fm = pmask(REGFACE)[Y0:Y0 + 720, X0:X0 + 720]
tmask = (HM[Y0:Y0 + 720, X0:X0 + 720] & ~(cv2.dilate(fm.astype(np.uint8), np.ones((41, 41))) > 0)).astype(np.uint8)
g = lambda a: cv2.GaussianBlur(cv2.cvtColor(a, cv2.COLOR_RGB2GRAY), (0, 0), 2).astype(np.float32)
def feath(poly):
    m = pmask(poly); f = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 7); return np.minimum(1, f * 1.7) * m
S = np.array(Image.open(SHEET).convert('RGB'))
cells = [[29, 72, 473, 386], [521, 71, 473, 387], [1009, 71, 473, 387], [29, 540, 474, 387], [522, 540, 473, 387], [1010, 540, 473, 387]]
JOBS = [('face_happy', FACE), ('face_angry', FACE), ('face_sad', FACE), ('face_surprised', FACE), ('blink_half', EYE), ('blink_closed', EYE)]
sift = cv2.SIFT_create(4000); kr, dr = sift.detectAndCompute(cv2.cvtColor(ref, cv2.COLOR_RGB2GRAY), tmask * 255)
prev = [ref]; rep = {}
for (name, poly), (cx, cy, cw, ch) in zip(JOBS, cells):
    m = 24; C = S[max(0, cy - m):cy + ch + m, max(0, cx - m):cx + cw + m].copy(); ox, oy = max(0, cx - m), max(0, cy - m)
    Cm = ~((C[..., 0] > 200) & (C[..., 2] > 200) & (C[..., 1] < 90))
    kc, dc = sift.detectAndCompute(cv2.cvtColor(C, cv2.COLOR_RGB2GRAY), Cm.astype(np.uint8) * 255)
    mt = cv2.BFMatcher().knnMatch(dc, dr, k=2); good = [a for a, b in mt if a.distance < .75 * b.distance]
    src = np.float32([kc[a.queryIdx].pt for a in good]); dst = np.float32([kr[a.trainIdx].pt for a in good])
    A, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=6)
    warped = cv2.warpAffine(C, A, (720, 720), flags=cv2.INTER_CUBIC, borderValue=(255, 0, 255))
    try:
        cc, D = cv2.findTransformECC(g(ref), g(warped), np.eye(2, 3, dtype=np.float32), cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 400, 1e-6), tmask, 5)
    except Exception as e: print(name, 'ECC', e); cc, D = None, np.eye(2, 3, dtype=np.float32)
    M = np.linalg.inv(np.vstack([D, [0, 0, 1]])) @ np.vstack([A, [0, 0, 1]]); M[0, 2] += X0; M[1, 2] += Y0
    full = cv2.warpAffine(C.astype(np.float32), M[:2], (2048, 2048), flags=cv2.INTER_CUBIC, borderValue=(255, 0, 255))
    mag = (full[..., 0] > 180) & (full[..., 2] > 180) & (full[..., 1] < 110)
    fe = feath(poly) * (~mag)
    sk = lambda a: (a[..., 0] > 170) & (a[..., 1] > 110) & (a[..., 1] < 200) & (a[..., 2] > 80) & (a[..., 2] < 170) & (a[..., 0] > a[..., 1] + 15)
    reg = fe > .3; so = sk(O4.astype(np.float32)) & reg; sc_ = sk(full) & reg
    gain = np.median(O4[so].astype(np.float32), 0) / np.maximum(np.median(full[sc_], 0), 1) if so.sum() > 200 and sc_.sum() > 200 else np.ones(3)
    full = np.clip(full * gain, 0, 255)
    # 맞춤 확인: 얼굴 밖 머리 조각 안에서 원화와의 차이(평균 밝기 차)
    ring = HM & ~(cv2.dilate(pmask(REGFACE).astype(np.uint8), np.ones((41, 41))) > 0) & ~mag
    err = float(np.abs(g(full.astype(np.uint8)) - g(O4))[ring].mean())
    patch = np.dstack([full, fe * 255]).astype(np.uint8)
    ys, xs = np.nonzero(patch[..., 3] > 3); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    Image.fromarray(patch[y0:y1, x0:x1]).save(f'{RD}/parts/{name}.png')
    R['parts'][name] = {'src': f'parts/{name}.png', 'pivot': [float(J['head'][0] * 4 - x0), float(J['head'][1] * 4 - y0)], 'scale': .5}
    sc = float(np.hypot(*M[:2, 0])); rep[name] = dict(inliers=int(inl.sum()), ecc=round(float(cc), 3) if cc else None, scale=round(sc, 3), gain=gain.round(3).tolist(), ringErr=round(err, 1))
    pv = O4.astype(np.float32) * (1 - fe[..., None]) + full * fe[..., None]
    prev.append(np.clip(pv[Y0:Y0 + 720, X0:X0 + 720], 0, 255).astype(np.uint8))
    print(name, rep[name])
R['faces'].update({'happy': 'face_happy', 'angry': 'face_angry', 'sad': 'face_sad', 'surprised': 'face_surprised', 'grimace': 'face_surprised'})
R['blinkFaces'] = {'half': 'blink_half', 'closed': 'blink_closed'}
json.dump(R, open(RD + '/rig.json', 'w'), ensure_ascii=False, indent=1)
row = lambda L: np.hstack(L); top = row(prev[:4]); bot = row(prev[4:] + [np.full_like(ref, 255)])
Image.fromarray(np.vstack([top, bot])).resize((1440, 720)).save(PREV); json.dump(rep, open(PREV + '.json', 'w'))
