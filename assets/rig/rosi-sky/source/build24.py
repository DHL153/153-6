# 24 스카이 로시 v1 조립 (10-21 11:20): 4 러스트 로시 v1.1 리그 구조 그대로 + 조각만 새 원화(art_v1_0730)·지운 원화(noarms_0800)·조각 시트(parts1_0759)
#  조각 = 2048 공간(512 원화 ×4, 1254 → ×1.633) · scale .5 · 피벗 = 뼈 자리(512 원화 좌표 J ×4) − 자른 상자 왼쪽 위
#  총 묶음(gun) = 총 + 두 팔뚝(감은 띠·맨살) + 두 장갑 — 손잡이와 한 몸(rigidFore, 러스트 G40) · 소매(armN/armF) = 어깨판+윗팔+감은 띠, 어깨에서 돎
#  몸(chest·torsoFill·skirt) = 지운 원화(팔·총 뒤가 그려져 있음) · 가방 = 지운 원화(호스 빠진 입구) · 머리 = 원화 · 표정 = 시트 머리 맞춤
#  다리 = 시트 허벅지·정강이(무릎판)·부츠, 호스 = 시트 마디 사슬(러스트 탄띠와 같은 닮음 변환 곡선)
#  실행: python3 -I build14.py   → ../rig.json · ../parts/ · work/build14.json
import json, os, math, copy
import numpy as np, cv2
from PIL import Image, ImageDraw
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); W = os.path.join(H, 'work'); PD = os.path.join(R, 'parts'); os.makedirs(PD, exist_ok=True)
K = 2048 / 1254.0
def up(p):   # 1254 RGBA → 2048 (미리 곱한 알파로 늘림 — 가장자리 번짐 없음)
    a = np.array(Image.open(p).convert('RGBA')).astype(np.float32) / 255.; pm = a[..., :3] * a[..., 3:4]
    pm2 = cv2.resize(pm, (2048, 2048), interpolation=cv2.INTER_LANCZOS4); al2 = np.clip(cv2.resize(a[..., 3], (2048, 2048), interpolation=cv2.INTER_LANCZOS4), 0, 1)
    rgb = np.clip(pm2 / np.maximum(al2[..., None], 1e-4), 0, 1); return np.dstack([rgb, al2])
O2 = up(os.path.join(H, 'sheets/art_v1_0958.png')); N2 = up(os.path.join(H, 'sheets/noarms_1104.png'))
LAB = np.load(os.path.join(W, 'labels24.npy')); NAMES = json.load(open(os.path.join(W, 'labels24.json')))
def clean(m, r=2):   # 가는 선(외곽선 따라 샌 watershed) 지우고 가장 큰 덩어리만
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    n, lb, st, _ = cv2.connectedComponentsWithStats(m); keep = np.zeros_like(m)
    for i in range(1, n):
        if st[i, 4] >= max(400, .02 * st[1:, 4].max()): keep[lb == i] = 1
    return keep > 0
def lab2(*ns, cl=0):   # 1254 라벨 → 2048 부드러운 마스크
    m = np.logical_or.reduce([LAB == NAMES.index(n) + 1 for n in ns])
    if cl: m = clean(m, cl)
    m = m.astype(np.float32)
    return np.clip(cv2.resize(m, (2048, 2048), interpolation=cv2.INTER_LINEAR), 0, 1)
def poly512(pts, k=4):
    m = Image.new('L', (2048, 2048), 0); ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in pts], fill=255); return np.array(m).astype(np.float32) / 255.
def dil(m, r): return cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
# ---------- 뼈 자리(512 원화 좌표) ----------
J = {'root': (237, 460), 'hip': (240, 344), 'torso': (242, 318), 'chest': (246, 272), 'neck': (247, 246), 'head': (250, 233),
     'shoulderN': (178, 262), 'elbowN': (165, 302), 'wristN': (190, 320), 'shoulderF': (290, 262), 'elbowF': (308, 292), 'wristF': (334, 298),
     'gun': (250, 345), 'pack': (150, 236), 'skirt': (246, 322)}   # 새 원화(art_v1_0958) 512 좌표 — 10-21 11:15 격자로 읽음(work/g_armN·g_armF·g_head·g_pack)
J['gripN'] = J['wristN']; J['gripF'] = J['wristF']; J['torsoFill'] = J['torso']; J['neckP'] = J['neck']; J['collar'] = (246, 244); J['cape'] = (150, 120)
J['handBackN'] = J['shoulderN']; J['gripBackN'] = J['gun']; J['cuffN'] = J['gripN']; J['foreRigF'] = J['gripF']; J['capeFill'] = J['cape']
parts = {}; info = {}
def save(name, rgba, bone, mask=None):
    a = rgba.copy()
    if mask is not None: a[..., 3] = a[..., 3] * mask
    ys, xs = np.nonzero(a[..., 3] > 2 / 255.); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    Image.fromarray((np.clip(a[y0:y1, x0:x1], 0, 1) * 255).astype(np.uint8)).save(os.path.join(PD, name + '.png'))
    bx, by = J[bone][0] * 4, J[bone][1] * 4; parts[name] = {'src': f'parts/{name}.png', 'pivot': [round(float(bx - x0), 1), round(float(by - y0), 1)], 'scale': .5}
    info[name] = [int(x0), int(y0), int(x1), int(y1)]; return x0, y0
# ---------- 원화에서 ----------
# 총 묶음: 총 + 두 팔뚝·장갑(라벨 foreN·foreF) — 손잡이와 한 몸
gunM = lab2('gun', 'foreN', 'foreF', cl=3); gunM = np.maximum(gunM, dil(lab2('foreN', 'foreF'), 10) * lab2('armN', 'armF'))   # 팔뚝을 소매 안으로 10px 더(소매 밑에 숨음) — 소매·팔뚝 이음에 배경이 비치던 가는 선(10-21 12:55)
gunM[1300:, :612] = 0; gx0, gy0 = save('gun', O2, 'gun', gunM)   # 총 왼쪽 끝(x 153) 왼쪽 아래 = 탄띠(사슬이 그림)
# 소매: 어깨판 + 부푼 소매(라벨 armN/armF — 손으로 따라 그린 다각형) · 맨살(팔뚝) 뺌
rgb8 = O2[..., :3] * 255; skin = ((rgb8[..., 0] > 190) & (rgb8[..., 1] > 120) & (rgb8[..., 1] < 200) & (rgb8[..., 2] > 90) & (rgb8[..., 2] < 175) & (rgb8[..., 0] - rgb8[..., 1] > 40)).astype(np.float32)   # 크림 소매(r−g 10~25)는 살 아님
noskin = 1 - dil(cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)), 2)   # 맨살만 뺌(소매 입구 외곽선은 소매에 남김 — 밑의 팔뚝 조각이 소매 안으로 10px 더 있어 틈 없음)
# 소매 입구 안(팔뚝 맨살이 있던 곳) = 어두운 소매 속 색 — 소매가 몇 도 돌 때 팔뚝 옆으로 배경이 비치지 않게(총 묶음 팔뚝이 그 위)
inner = np.array([0.30, 0.22, 0.20])
ARM_ = {'armN': [(150,252),(170,243),(192,241),(201,249),(201,266),(199,290),(197,306),(190,311),(170,315),(150,316),(142,306),(140,292),(142,276),(147,262)],   # seg24.py ARM 과 같음
        'armF': [(276,250),(292,247),(302,255),(312,267),(326,275),(329,292),(321,306),(301,307),(290,297),(282,283),(276,266)]}
for nm_, lb_, bn_ in (('sleeveN', 'armN', 'shoulderN'), ('sleeveF', 'armF', 'shoulderF')):
    # 소매 = 소매 라벨 + 소매 다각형 안의 팔뚝 라벨 천(맨살 아님) — 두 라벨 경계가 크림 천 가운데를 지나 반투명 금이 생기던 것(10-21 13:00)
    m_ = np.maximum(lab2(lb_, cl=2), lab2('fore' + lb_[3:]) * dil(poly512(ARM_[lb_]), 3)) * noskin
    m_ = (cv2.GaussianBlur((m_ > .5).astype(np.float32), (0, 0), 1.0)) * (m_ > .02); save(nm_, O2, bn_, m_)   # 소매 = 천만(맨살 = 투명) — 소매가 총 묶음(팔뚝) 위에 그려져 소매 입구가 팔뚝을 덮음(10-21 12:50)
# 머리: 원화 머리(머리카락·얼굴)
headM = lab2('head', cl=3); save('head', O2, 'head', headM)
# ---------- 지운 원화에서 (팔·총·호스 뒤가 그려져 있음) ----------
nop = (N2[..., 3] > .02).astype(np.float32)
PACKBOX = [(34, 176), (54, 148), (98, 134), (103, 122), (168, 122), (172, 148), (176, 246), (152, 250), (150, 300), (156, 318), (150, 332), (96, 332), (60, 322), (38, 294), (32, 230)]
PLATE_N = [(146, 256), (164, 245), (196, 243), (206, 254), (204, 284), (186, 292), (160, 290), (146, 276)]
SCARF = [(134, 246), (160, 239), (172, 250), (160, 264), (138, 264)]   # 가방 앞에 걸친 스카프 자락 = 몸
pbox = poly512(PACKBOX); scD = dil(poly512(SCARF), 2); plN = dil(poly512(PLATE_N), 2); headD = dil(headM, 2); headD4 = dil(headM, 5)
BODYBOX = [(138, 226), (300, 226), (314, 250), (316, 372), (146, 372), (138, 300)]
packVis = pbox * nop * (1 - headD) * (1 - plN) * (1 - scD)
# 가려진 가방(머리·어깨판·스카프 자락 밑) = 조각 시트 18번 '가방 단독'을 보이는 가방에 맞춰(SIFT → ECC) 채움 — 10-21 12:30 DHL 12:19
#   (전에는 둘레 색 메움(inpaint)이라 머리 크림 테두리가 번져 '스카프 잔상'이 생기고, 가방 오른쪽이 x 176 에서 끊겨 연사 때 젖히면 머리 옆이 비었음)
SP = np.array(Image.open(os.path.join(H, 'pieces', '18_pack.png')).convert('RGBA')).astype(np.uint8)
gry = lambda a: cv2.cvtColor(np.ascontiguousarray((a[..., :3] * 255).astype(np.uint8) if a.dtype != np.uint8 else a[..., :3]), cv2.COLOR_RGB2GRAY)
vis8 = (packVis > .5).astype(np.uint8) * 255
sf_ = cv2.SIFT_create(6000); k1, d1 = sf_.detectAndCompute(gry(SP), (SP[..., 3] > 128).astype(np.uint8) * 255); k2, d2 = sf_.detectAndCompute(gry(N2), vis8)
mm = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < .75 * b.distance]
MA, inl = cv2.estimateAffinePartial2D(np.float32([k1[a.queryIdx].pt for a in mm]), np.float32([k2[a.trainIdx].pt for a in mm]), ransacReprojThreshold=5)
WP = cv2.warpAffine(SP, MA, (2048, 2048), flags=cv2.INTER_CUBIC).astype(np.float32) / 255.
gb = lambda a: cv2.GaussianBlur(cv2.cvtColor((np.clip(a[..., :3], 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY), (0, 0), 2).astype(np.float32)
ecc_m = ((packVis > .5) & (WP[..., 3] > .5)).astype(np.uint8)
try:
    cc, D = cv2.findTransformECC(gb(N2), gb(WP), np.eye(2, 3, dtype=np.float32), cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), ecc_m, 5)
    WP = cv2.warpAffine(WP, D, (2048, 2048), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP)
except Exception as e: cc = None
both = (packVis > .5) & (WP[..., 3] > .5); gain = np.median(N2[both, :3], 0) / np.maximum(np.median(WP[both, :3], 0), 1e-3)
WP[..., :3] = np.clip(WP[..., :3] * gain, 0, 1)
PACKFULL = [(26, 114), (226, 114), (226, 336), (26, 336)]   # 가방 전체(시트 가방이 머리 뒤 x 216 까지)
pfull = poly512(PACKFULL) * WP[..., 3]
vf = cv2.GaussianBlur(packVis.astype(np.float32), (0, 0), 1.5) * packVis   # 보이는 곳 = 지운 원화 그대로, 가장자리만 부드럽게
packImg = N2.copy(); packImg[..., :3] = N2[..., :3] * vf[..., None] + WP[..., :3] * (1 - vf[..., None]); packImg[..., 3] = 1
print('pack sheet fit', int(inl.sum()), 'ECC', None if cc is None else round(float(cc), 3), 'gain', np.round(gain, 3))
save('pack', packImg, 'pack', np.clip(np.maximum(packVis, pfull), 0, 1))
# 몸: 지운 원화에서 머리·보이는 가방 뺀 것(어깨판은 몸)
bodyZ = np.clip(nop * (1 - headD4) * (1 - packVis) * poly512(BODYBOX), 0, 1)
bodyZ = bodyZ * clean(bodyZ > .5, 2)
YY = np.arange(2048)[:, None] / 4.0
save('torso', N2, 'chest', bodyZ * (YY < 304)); save('torsoFill', N2, 'torsoFill', bodyZ * (YY < 330)); save('skirt', N2, 'skirt', bodyZ * ((YY >= 300) & (YY < 352)))   # 허리 = 허리띠 + 바지 위(주머니 단추까지)
# 목: 턱 밑(머리 뒤) — 머리를 지우고 깃 둘레 색으로 메운 작은 판(끄덕일 때 턱 밑이 비지 않게)
neckZ = poly512([(186, 214), (228, 216), (270, 222), (276, 236), (266, 248), (236, 250), (200, 250), (184, 236)])   # 턱 밑 + 귀덮개 밑(스카프) — 연사로 젖힐 때 머리 아래가 비지 않게(DHL 12:19)
nk = cv2.cvtColor((N2[..., :3] * 255).astype(np.uint8), cv2.COLOR_RGB2BGR); nh = ((neckZ > .5) & (dil(headM, 6) > .5)).astype(np.uint8) * 255
dark = np.median(N2[240 * 4:246 * 4, 236 * 4:262 * 4, :3].reshape(-1, 3), 0)   # 턱 밑 = 스카프 색
neckImg = N2.copy(); hmN = nh > 0; neckImg[hmN, :3] = dark; neckImg[..., 3] = 1
neckImg[..., :3] = cv2.GaussianBlur(neckImg[..., :3], (0, 0), 1.2) * hmN[..., None] + neckImg[..., :3] * (1 - hmN[..., None]); save('neck', neckImg, 'neckP', neckZ)
json.dump({'info': info, 'parts': parts, 'J': J}, open(os.path.join(W, 'build24_parts.json'), 'w'), indent=1)
print('parts', {k: v['pivot'] for k, v in parts.items()})
