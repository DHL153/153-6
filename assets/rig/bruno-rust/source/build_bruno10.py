"""10 러스트 브루노 리그 조립 v1 (2026-10-20 22:45) · v1.1 (23:48 — 가려진 곳 = 프롬프트 2·3 '부품만 지운 원화') — 쌍도끼 계열 기준(자리 10), 공격 = 번갈아 내려찍기(DHL 21:49)
입력: ref512.png(0번 합격 원화 = 게임 char_0010) · sheets/nonear_2345.png·nofar_2344.png(팔·도끼만 지운 원화) · work/labels.npy(seg10.py) · pieces/(조각 시트 27칸, cut10.py) · measure10.json · review/plan_alt10.json(키 풀이 engine)
출력: ../rig.json · ../rig.def.js · ../parts/*.png
실행: cd source && python3 -I cut10.py && python3 -I seg10.py && python3 -I tools/plan_alt10.py && python3 -I build_bruno10.py
원칙(DHL): 대기 = 원화 · 도끼 크기 그대로 · 팔다리 길이 고정(늘이지 않음) · 팔꿈치(팔뚝)가 어깨(윗팔)보다 앞 · 먼 팔은 몸 뒤, 주먹·도끼만 앞
엔진 이름: 먼 팔 armF→foreF→fistF→weapon = swordGrip 칼(9·19 팔로메와 같은 길, 키 gx·gy·sa + 길이 고정 IK)
          가까운 팔 armU→armL(+ axeN 가까운 도끼, fistN 가까운 주먹) = 자유 팔(freeArm 키 fuA·flA) — 도끼는 팔뚝 뼈에 붙음(손목 고정)
좌표: 원화 512px 로 적고, 리그 단위 = ×2
"""
import json, math, os, shutil, hashlib
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); PC = os.path.join(HERE, 'pieces'); W = os.path.join(HERE, 'work'); OUT = os.path.join(HERE, '..'); PARTS = os.path.join(OUT, 'parts')
if os.path.isdir(PARTS): shutil.rmtree(PARTS)
os.makedirs(PARTS)
RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA'))
LAB = np.load(os.path.join(W, 'labels.npy')); NAMES = json.load(open(os.path.join(W, 'label_names.json'))); LID = {n: i + 1 for i, n in enumerate(NAMES)}
lab = lambda *ns: np.logical_or.reduce([LAB == LID[n] for n in ns])
M = json.load(open(os.path.join(HERE, 'measure10.json'))); PLAN = json.load(open(os.path.join(HERE, 'review', 'plan_alt10.json')))
YY, XX = np.mgrid[0:512, 0:512]
# v1.1 라벨 고침: 왼쪽 볼(눈 아래 피부·눈 아래 선)이 seg 에서 상체(칼라) 라벨로 감 → 숨쉬기·공격에 얼굴을 가로지르는 금, 표정 조각이 볼을 못 덮음.
#   칼라 위 끝 선(크림 맨 윗줄, x 220~257 직선 맞춤 — 잔차 < 1px) 위의 상체 픽셀(x 212~261) = 머리
_hsv0 = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV).astype(int)
_cream = (_hsv0[..., 0] >= 8) & (_hsv0[..., 0] <= 30) & (_hsv0[..., 1] >= 20) & (_hsv0[..., 1] <= 110) & (_hsv0[..., 2] > 170)
_cx = [x for x in range(220, 258) if _cream[270:320, x].any()]; _cy = [270 + int(np.nonzero(_cream[270:320, x])[0].min()) for x in _cx]
_k, _b = np.polyfit(_cx, _cy, 1); _cheek = (XX >= 212) & (XX < 262) & (YY >= 250) & (YY < np.floor(_k * XX + _b) - 2) & (LAB == LID['torso'])
LAB = LAB.copy(); LAB[_cheek] = LID['head']; print('  볼 라벨 상체 → 머리', int(_cheek.sum()), 'px · 칼라 선 y = %.3f x + %.1f' % (_k, _b))
V = lambda p: np.array(p, float)
def desp(a):   # 자홍 배경 번짐 지움
    a = a.astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None); a[..., 0] -= m; a[..., 2] -= m; return np.clip(a, 0, 255).astype(np.uint8)
def sheet(n): return desp(np.array(Image.open(os.path.join(PC, n + '.png')).convert('RGBA')))
def art(mask): a = RA.copy(); a[..., 3] = np.where(mask, a[..., 3], 0); return a
def dil(m, r): return cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
OFF = {}
def save(name, a, pad=2):
    ys, xs = np.nonzero(a[..., 3] > 0); x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad); x1, y1 = min(a.shape[1], xs.max() + 1 + pad), min(a.shape[0], ys.max() + 1 + pad)
    Image.fromarray(a[y0:y1, x0:x1]).save(os.path.join(PARTS, name + '.png')); OFF[name] = (x0, y0); return np.array([x0, y0], float)
def under(a, b, where):   # a 밑에 b 를 where 에서만
    out = a.copy(); w = where & (b[..., 3] > 0) & (a[..., 3] < 250); fa = a[..., 3:4] / 255.0; fb = b[..., 3:4] / 255.0
    col = a[..., :3] * fa + b[..., :3] * fb * (1 - fa); al = fa + fb * (1 - fa)
    out[w, :3] = np.clip(col[w] / np.maximum(al[w], 1e-3), 0, 255).astype(np.uint8); out[w, 3] = np.clip(al[w, 0] * 255, 0, 255).astype(np.uint8); return out
def col_match(im, ref_m, k=1.0):   # 시트 조각 색 → 원화 같은 부위(채널별 평균·편차)
    im = im.astype(np.float32); m = im[..., 3] > 200; R = RA[..., :3].astype(np.float32)[ref_m & (RA[..., 3] > 200)]
    for c in range(3):
        v = im[..., c][m]; im[..., c] = np.where(im[..., 3] > 0, (im[..., c] - v.mean()) / max(1.0, v.std()) * R[:, c].std() + R[:, c].mean(), im[..., c])
    im[..., :3] *= k; return np.clip(im, 0, 255).astype(np.uint8)
# ---------------- 관절(원화 px — measure10.json) ----------------
N_, F_ = M['near'], M['far']
SOLE = float(M['sole_y']); HIP = V(M['hip']); NECK = V(M['neck']); O = V([243.0, SOLE])        # 뿌리 = 두 발 가운데 땅
SH_N, EL_N, WR_N, FI_N = V(N_['SH']), V(N_['EL']), V(N_['WR']), V(N_['fist'])
SH_F, EL_F, WR_F, FI_F = V(F_['SH']), V(F_['EL']), V(F_['WR']), V(F_['fist'])
HD_N, HD_F = V(N_['head']), V(F_['head'])
UN = (HD_N - FI_N) / np.linalg.norm(HD_N - FI_N); UF = (HD_F - FI_F) / np.linalg.norm(HD_F - FI_F)   # 도끼 축(주먹 → 도끼 머리)
LEG = {sd: {k: V(v) for k, v in M['legs'][sd].items()} for sd in ('near', 'far')}
PONY = V([118.0, 378.0])   # 포니테일 뿌리(주황 끈 위)
SC = 2.0
# ---------------- 머리·포니테일·상체·골반(원화) + 가려진 곳 = '그 부품만 지운 원화'(프롬프트 2·3) — v1.1 (2026-10-20 23:48) ----------------
# sheets/nonear_2345.png = 가까운 팔·도끼만 지운 원화 · sheets/nofar_2344.png = 먼 팔·도끼만 지운 원화 (DHL 23:45·23:44 — 원화와 SIFT 1.0000 · 0px,
#   지운 곳 밖 평균 차 0.23·0.01, tools/check_remove10.py). v1 의 임시 TELEA 메움(공격 때 머리 옆 회색 덩어리)을 이 픽셀로 바꿈.
# 지운 곳(앞 부품 라벨) 픽셀마다 '무슨 부품의 뒤 그림인가' = 그 그림 위 watershed(씨앗 = 지운 곳 밖 원화 라벨, 투명 = 배경).
# 대기 = 원화: 그 픽셀을 덮던 앞 부품(P)보다 뒤 부품(X)이 나중에 그려지면(예: 가까운 윗팔 armU 뒤 머리숱 — 머리는 armU 다음)
#   X 조각에 넣으면 대기에 P 를 덮음 → X 의 '뒤 조각'(headB·torsoB …, X 뼈의 자식, 다리 바로 다음 = 모든 팔보다 먼저)에 넣음
DRAW_IDLE = ['pony', 'legFar', 'legNear', 'armF', 'foreF', 'armU', 'skirt', 'torso', 'weapon', 'fistF', 'head', 'axeN', 'armL', 'fistN']
BONE_OF = {'head': 'head', 'pony': 'pony', 'torso': 'torso', 'hips': 'skirt', 'legN': 'legNear', 'legF': 'legFar', 'upperN': 'armU', 'foreN': 'armL', 'fistN': 'fistN',
           'axeN': 'axeN', 'upperF': 'armF', 'foreF': 'foreF', 'fistF': 'fistF', 'axeF': 'weapon'}
NONEAR = np.array(Image.open(os.path.join(HERE, 'sheets', 'nonear_2345.png')).convert('RGBA'))
NOFAR = np.array(Image.open(os.path.join(HERE, 'sheets', 'nofar_2344.png')).convert('RGBA'))
ADD, BACK = {}, {}   # 부품 이름 → [(그림, 마스크)] — ADD = 그 조각에 바로, BACK = 그 부품의 뒤 조각에
def reveal(IMG, rem_names, tag):
    R = lab(*rem_names); BG = len(NAMES) + 1; mk = np.zeros((512, 512), np.int32)
    for n in NAMES:
        if n not in rem_names: mk[(LAB == LID[n]) & ~R] = LID[n]
    mk[(LAB == 0) & ~R] = BG; mk[R & (IMG[..., 3] < 24)] = BG
    al = IMG[..., 3:4] / 255.0; rgb = np.ascontiguousarray((IMG[..., :3] * al + 52 * (1 - al)).astype(np.uint8))
    ws = cv2.watershed(rgb, mk.copy())
    for y, x in zip(*np.nonzero((ws <= 0) & R)):   # 경계(−1) = 3×3 이웃 다수결
        nb = ws[max(0, y - 1):y + 2, max(0, x - 1):x + 2].ravel(); nb = nb[nb > 0]; ws[y, x] = np.bincount(nb).argmax() if len(nb) else BG
    rep = {}
    for n in NAMES:
        if n in rem_names: continue
        m = R & (ws == LID[n]) & (IMG[..., 3] > 0)
        if not m.any(): continue
        for p in rem_names:   # 덮던 앞 부품마다: 뒤 부품이 앞 부품보다 나중에 그려지면 뒤 조각으로
            mp = m & (LAB == LID[p])
            if not mp.any(): continue
            back = DRAW_IDLE.index(BONE_OF[n]) > DRAW_IDLE.index(BONE_OF[p])
            (BACK if back else ADD).setdefault(n, []).append((IMG, mp)); rep[f"{n}{'(뒤)' if back else ''}←{p}"] = int(mp.sum())
    print(f'  {tag}: 지운 곳 {int(R.sum())} px · 뒤 그림 {int((R & (IMG[..., 3] > 0)).sum())} px →', rep)
reveal(NONEAR, ['upperN', 'foreN', 'fistN', 'axeN'], 'nonear(가까운 팔·도끼 지움)')
reveal(NOFAR, ['upperF', 'foreF', 'fistF', 'axeF'], 'nofar(먼 팔·도끼 지움)')
# 앞 부품 가장자리 '유령 선'(23:53 v1.1 공격 확대에서 찾음): 원화 라벨에서 뒤 부품(머리)에 남은 앞 부품(팔뚝·주먹·도끼) 외곽선 번짐·조각
#   = 지운 그림(뒤 그림 h)과 원화(p)가 다른, 앞 부품 둘레 3px(가까운 쪽 5px — 외곽선이 굵음) 의 뒤 부품 픽셀. p = a·외곽선색 + (1−a)·h 로 풀어(남는 차 < 18 이면)
#   앞 조각에 (외곽선색, a), 뒤 조각에 h — 대기 합성은 원화 그대로, 앞 부품이 비키면 뒤는 깨끗한 머리숱. 풀리지 않는 픽셀(팔 색 조각)·뒤가 투명인 번짐은 통째로 앞 조각에
REPL, FRONT_ADD = {}, {}
def unmix_edges(IMG, rem_names, tag, band_r=3, T=20):
    fr = [f for f in rem_names if f in ('foreN', 'fistN', 'axeN', 'fistF', 'axeF')]   # 대기에 뒤 부품보다 나중에 그려지는 앞 부품만(윗팔·먼 팔뚝은 상체 뒤)
    dist = np.stack([cv2.distanceTransform((~lab(f)).astype(np.uint8), cv2.DIST_L2, 3) for f in fr]); own = dist.argmin(0); dmin = dist.min(0)
    p = RA[..., :3].astype(np.float32); h = IMG[..., :3].astype(np.float32)
    cand = (dmin <= band_r) & ~lab(*rem_names) & (LAB > 0) & (RA[..., 3] > 200) & (IMG[..., 3] > 200) & (np.abs(p - h).max(-1) > T)
    bgc = (dmin <= band_r) & ~lab(*rem_names) & (LAB > 0) & (RA[..., 3] > 0) & (IMG[..., 3] < 30)   # 뒤가 투명(배경)인데 원화엔 칠해진 곳 = 앞 부품 번짐 → 통째로 앞 조각
    rep = {}
    for i, f in enumerate(fr):
        om = lab(f) & (RA[..., :3].astype(int).mean(-1) < 50); oc = np.median(RA[om][:, :3], 0).astype(np.float32)
        for b in NAMES:
            if b in rem_names or DRAW_IDLE.index(BONE_OF[b]) > DRAW_IDLE.index(BONE_OF[f]): continue
            m = cand & (own == i) & (LAB == LID[b]); mb = bgc & (own == i) & (LAB == LID[b])
            if not (m.any() or mb.any()): continue
            lay = FRONT_ADD.setdefault(f, np.zeros((512, 512, 4), np.float32))
            if m.any():
                dv = oc - h[m]; a = np.clip(((p[m] - h[m]) * dv).sum(-1) / np.maximum((dv * dv).sum(-1), 1e-3), 0, 1)
                res = np.abs(p[m] - (h[m] + a[:, None] * dv)).max(-1); full = res >= 18
                # 풀리지 않는 픽셀: 머리숱(회색) 위의 팔 색(채도 > 50)·검은 선(밝기 < 60)만 앞 조각으로, 나머지(그림 AI 가 머리 결·재킷을 조금 다르게 그린 곳)는 원화 그대로 둠
                pm = RA[m]; hs = cv2.cvtColor(pm[None, :, :3], cv2.COLOR_RGB2HSV)[0]
                armlike = (b in ('head', 'pony')) & ((hs[:, 1] > 50) | (pm[:, :3].astype(int).mean(-1) < 60))
                keep = full & ~armlike; mm = m.copy(); mm[np.nonzero(m)[0][keep], np.nonzero(m)[1][keep]] = False
                ys, xs = np.nonzero(m); sel = ~keep
                lay[ys[sel], xs[sel], :3] = np.where(full[sel][:, None], p[m][sel], oc); lay[ys[sel], xs[sel], 3] = np.where(full[sel], 255, a[sel] * 255)
                REPL.setdefault(b, []).append((IMG, mm)); rep[f'{b}→{f}'] = (int(mm.sum()), int((full & armlike).sum()), int(keep.sum()))
            if mb.any():
                ys, xs = np.nonzero(mb); lay[ys, xs] = RA[mb].astype(np.float32); REPL.setdefault(b, []).append((np.zeros_like(RA), mb)); rep[f'{b}→{f}(배경)'] = int(mb.sum())
    print(f'  {tag} 가장자리 풀기 (옮김, 통째, 원화 그대로)', rep)
unmix_edges(NONEAR, ['upperN', 'foreN', 'fistN', 'axeN'], 'nonear', band_r=5)
unmix_edges(NOFAR, ['upperF', 'foreF', 'fistF', 'axeF'], 'nofar')
def front_with(n, a):   # 앞 조각 + 풀어 낸 가장자리
    if n not in FRONT_ADD: return a
    lay = FRONT_ADD[n]; o = a.astype(np.float32); w = lay[..., 3] > 0; o[w] = lay[w]; return np.clip(o, 0, 255).astype(np.uint8)
def with_reveal(n):
    a = art(lab(n))
    for IMG, m in REPL.get(n, []): a[m] = IMG[m]
    for IMG, m in ADD.get(n, []): a = under(a, IMG, m)
    return a
# ---------------- 도끼(원화 그대로 + 주먹 밑 손잡이 = 보이는 손잡이 단면을 축으로 이음) ----------------
def axe_img(name, fist, U, lm, lf):
    a = art(lm); nv = np.array([-U[1], U[0]]); u = (XX - fist[0]) * U[0] + (YY - fist[1]) * U[1]; v = (XX - fist[0]) * nv[0] + (YY - fist[1]) * nv[1]
    vis = lm & (np.abs(v) <= 9)
    us = u[vis]; hole = (np.abs(v) <= 9.5) & (u > us.min() if False else u > -40) & (u < 60) & dil(lf, 2) & (a[..., 3] < 250)   # 주먹 자리 손잡이
    src_u = [k for k in range(24, 34)]   # 주먹 위 보이는 손잡이 단면(u 24~33) 평균
    cols = []
    for k in src_u:
        px = fist[0] + k * U[0] + v * nv[0]; py = fist[1] + k * U[1] + v * nv[1]
        cols.append(cv2.remap(RA.astype(np.float32), px.astype(np.float32), py.astype(np.float32), cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)))
    src = np.mean(cols, 0); put = hole & (src[..., 3] > 128)
    a = under(a, np.clip(src, 0, 255).astype(np.uint8), put)
    print(f'  {name}: handle under fist filled {int(put.sum())} px')
    return a
axN = front_with('axeN', axe_img('axeN', FI_N, UN, lab('axeN'), lab('fistN')))
axF = front_with('axeF', axe_img('axeF', FI_F, UF, lab('axeF'), lab('fistF')))
save('axeN', axN)
# 먼 도끼 = swordGrip 칼 그림(세운 그림: 축이 위, ×2) — 19 칼과 같은 꼴
UPS = 2; ang_tip = math.atan2(UF[1], UF[0]); rot_deg = math.degrees(-math.pi / 2 - ang_tip)
sw2 = cv2.resize(axF, None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LANCZOS4); sw2[..., 3] = np.clip(cv2.resize(axF[..., 3], None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LINEAR), 0, 255)
Rm = cv2.getRotationMatrix2D((float(FI_F[0] * UPS), float(FI_F[1] * UPS)), -rot_deg, 1.0); WS, HS = 700, 900; Rm[0, 2] += WS / 2 - FI_F[0] * UPS; Rm[1, 2] += 640 - FI_F[1] * UPS
swv = cv2.warpAffine(sw2, Rm, (WS, HS), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
ys, xs = np.nonzero(swv[..., 3] > 0); assert xs.min() > 0 and ys.min() > 0 and xs.max() < WS - 1 and ys.max() < HS - 1, '도끼 그림이 캔버스 밖'
x0, y0 = max(0, xs.min() - 2), max(0, ys.min() - 2); swv = swv[y0:ys.max() + 3, x0:xs.max() + 3]; Image.fromarray(swv).save(os.path.join(PARTS, 'weapon.png'))
vpt = lambda p: (Rm[:, :2] @ (np.array(p, float) * UPS) + Rm[:, 2]) - np.array([x0, y0])
W_PIV = vpt(FI_F); W_HEAD = vpt(HD_F); ysw, xsw = np.nonzero(swv[..., 3] > 128); W_TIP = np.array([float(W_PIV[0]), float(ysw.min())]); W_POM = np.array([float(W_PIV[0]), float(ysw.max())])
print('  far axe vertical: pivot', np.round(W_PIV, 1), 'top', np.round(W_TIP, 1), 'pommel', np.round(W_POM, 1), 'rot', round(rot_deg, 1))
# 맞닿는 두 조각 이음(숨쉬기·공격 기울기로 몇 px 벌어지는 곳): 뒤에 그리는 조각이 앞 조각 밑으로 4px 를 앞 조각의 원화 픽셀로 더 가짐
#   (대기엔 앞 조각에 덮여 안 보임 — 원화 알파 ≥ 250 인 곳만, 벌어지면 배경 대신 같은 그림) · 상체 ← 머리 · 골반 ← 상체 · 포니테일 ← 머리 · 선 다리 ← 골반
def underlay(a, back_m, front_m, r=4):
    band = front_m & dil(back_m, r) & (RA[..., 3] >= 250) & (a[..., 3] == 0); a = a.copy(); a[band] = RA[band]; return a, int(band.sum())
head_m = lab('head'); hd = with_reveal('head'); o_head = save('head', hd)
_p, _n1 = underlay(with_reveal('pony'), lab('pony'), head_m); o_pony = save('pony', _p)
tr, _n2 = underlay(with_reveal('torso'), lab('torso'), head_m); o_tor = save('torso', tr)
_hp, _n3 = underlay(with_reveal('hips'), lab('hips'), lab('torso')); o_hips = save('hips', _hp)
print('  이음 밑 덧칠 px: 포니테일←머리', _n1, '· 상체←머리', _n2, '· 골반←상체', _n3)
BACKB = {}   # 뒤 조각 뼈 이름 → (부모 뼈, 세상 점)
_PAR = {'head': ('head', NECK), 'torso': ('torso', HIP), 'hips': ('skirt', HIP), 'pony': ('pony', PONY)}
for n, lst in BACK.items():
    assert n in _PAR, f'뒤 조각 부모 없음: {n}'
    a = np.zeros_like(RA)
    for IMG, m in lst: a = under(a, IMG, m)
    nm = (_PAR[n][0] if n != 'hips' else 'hips') + 'B'; save(nm, a); BACKB[nm] = _PAR[n]
print('  뒤 조각', {k: v[0] for k, v in BACKB.items()})
# ---------------- 팔 ----------------
def sleeve(S, E, w, col, name):   # 윗팔 = 소매 관(가로 음영 캡슐 + 외곽선) — 시트 13·14번이 짧게 와서(0.5배) 원화 색으로 만듦, 길이 = 어깨→팔꿈치 그대로
    L = np.linalg.norm(E - S); Hh = int(L + w + 6); Ww = int(w + 8); im = np.zeros((Hh, Ww, 4), np.float32)
    yy, xx = np.mgrid[0:Hh, 0:Ww].astype(float); cx = Ww / 2; r = w / 2; ya, yb = 3 + r, 3 + r + L
    d = np.where(yy < ya, np.hypot(xx - cx, yy - ya), np.where(yy > yb, np.hypot(xx - cx, yy - yb), np.abs(xx - cx)))
    inside = d <= r; shade = 1 - 0.35 * ((xx - cx) / r) ** 2 + 0.12 * ((cx - xx) / r)
    for c in range(3): im[..., c] = np.clip(col[c] * shade, 0, 255)
    im[..., 3] = np.clip((r + 0.5 - d) * 255, 0, 255); ol = inside & (d > r - 2.2); im[ol, :3] = (28, 24, 26)
    pv = (cx, ya); el = (cx, yb); Image.fromarray(im.astype(np.uint8)).save(os.path.join(PARTS, name + '.png')); OFF[name] = None
    return pv, el, math.degrees(math.atan2(E[1] - S[1], E[0] - S[0])) - 90.0
_sc = RA[lab('upperN', 'upperF') & (RA[..., 3] > 200)][:, :3].astype(float); SLV = np.median(_sc[_sc.mean(1) < 110], 0)
pvN, elN, rotN = sleeve(SH_N, EL_N, 17, SLV, 'armU'); pvF, elF, rotF = sleeve(SH_F, EL_F, 16, SLV, 'armF')
print('  sleeve colour', SLV, 'near rot', round(rotN, 1), 'far rot', round(rotF, 1))
o_aL = save('armL', front_with('foreN', art(lab('foreN'))))          # 가까운 팔뚝(붕대 + 팔꿈치 살)
o_fN = save('fistN', front_with('fistN', art(lab('fistN'))))         # 가까운 주먹(도끼 자루 위에 그림)
o_fF = save('foreF', art(lab('foreF')))         # 먼 팔뚝
o_fiF = save('fistF', front_with('fistF', art(lab('fistF'))))        # 먼 주먹
# ---------------- 다리: 서 있을 땐 원화 다리 통째(부츠 자리에 핀), 달리면 시트 허벅지·정강이·부츠 ----------------
def sole_pts(m, ankle, ground=None):
    ys, xs = np.nonzero(m); xl, xr = xs.min(), xs.max(); bot = {x: ys[xs == x].max() for x in range(xl, xr + 1) if (xs == x).any()}
    xlow = max(bot, key=lambda x: bot[x]); cols_ = sorted(set([int(round(xl + (xr - xl) * f)) for f in (0.02, 0.2, 0.8, 0.98)] + [xlow]))
    lift = 0.0 if ground is None else float(ground - bot[xlow]); return [[float(x - ankle[0]), float(bot[x] - ankle[1] + lift)] for x in cols_ if x in bot]
o_lN = save('bootStandN', underlay(art(lab('legN')), lab('legN'), lab('hips'))[0]); o_lF = save('bootStandF', underlay(art(lab('legF')), lab('legF'), lab('hips'))[0])
def run_boot(nm, lm):   # 시트 부츠(옆모습, 앞코 오른쪽) · 색 = 원화 부츠 · 발목 점 = 목 가운데·밑창 위 16px
    b = col_match(sheet(nm), lm & (YY >= 440)); ys, xs = np.nonzero(b[..., 3] > 128); piv = (float(xs.min() + (xs.max() - xs.min()) * 0.32), ys.max() - 16.0)
    Image.fromarray(b).save(os.path.join(PARTS, f'{nm}Run.png')); bot = {x: ys[xs == x].max() for x in range(xs.min(), xs.max() + 1) if (xs == x).any()}; xl, xr = min(bot), max(bot)
    return piv, [[round(float(x - piv[0]), 1), round(float(bot[x] - piv[1]), 1)] for x in sorted(set(int(round(xl + (xr - xl) * f)) for f in (0.03, 0.25, 0.5, 0.75, 0.97)))]
RB = {'near': run_boot('bootN', lab('legN')), 'far': run_boot('bootF', lab('legF'))}
def limb_piece(nm, lm, top_pad, bot_pad):   # 시트 허벅지·정강이 — 색 = 원화 다리, a = 위 관절(둥근 끝 가운데), b = 아래 관절
    p = col_match(sheet(nm), lm & (YY >= 392) & (YY <= 450)); Image.fromarray(p).save(os.path.join(PARTS, nm + '.png'))
    ys, xs = np.nonzero(p[..., 3] > 128); cx = float((xs.min() + xs.max()) / 2); return {'part': nm, 'a': [round(cx, 1), float(ys.min() + top_pad)], 'b': [round(cx, 1), float(ys.max() - bot_pad)], 'w': 1.0}
TH = {'near': limb_piece('thighN', lab('legN'), 9, 9), 'far': limb_piece('thighF', lab('legF'), 9, 9)}
SHN = {'near': limb_piece('shinN', lab('legN'), 8, 0), 'far': limb_piece('shinF', lab('legF'), 8, 0)}
L_TH = float(np.mean([np.linalg.norm(LEG[s]['knee'] - LEG[s]['hip']) for s in LEG])); L_SH = float(np.mean([np.linalg.norm(LEG[s]['ankle'] - LEG[s]['knee']) for s in LEG]))
print('  leg lengths thigh', round(L_TH, 1), 'shin', round(L_SH, 1), '· sheet a-b', {k: round(float(np.hypot(*(np.subtract(v['b'], v['a'])))), 1) for k, v in {**{f'th_{s}': TH[s] for s in TH}, **{f'sh_{s}': SHN[s] for s in SHN}}.items()})
# ---------------- 표정·깜빡임 (시트 머리 ×0.794 → 원화 머리 자리, 무표정과 다른 곳 + 5px 만, 색 = 원화에 맞춤) ----------------
sift = cv2.SIFT_create()
def gray(a): al = a[..., 3:4] / 255.0; return cv2.cvtColor((a[..., :3] * al + 128 * (1 - al)).astype(np.uint8), cv2.COLOR_RGB2GRAY)
def up(a, k): return cv2.resize(a, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
kA, dA = sift.detectAndCompute(up(gray(RA), 2), (up((head_m * 255).astype(np.uint8), 2) > 0).astype(np.uint8) * 255)
neu_s = sheet('face_neutral'); kS, dS = sift.detectAndCompute(up(gray(neu_s), 2), (up(neu_s[..., 3], 2) > 20).astype(np.uint8) * 255)
mt = cv2.BFMatcher().knnMatch(dS, dA, k=2); good = [a for a, b in mt if a.distance < .75 * b.distance]
MF, inl = cv2.estimateAffinePartial2D(np.float32([kS[a.queryIdx].pt for a in good]) / 2, np.float32([kA[a.trainIdx].pt for a in good]) / 2, ransacReprojThreshold=2.0)
print('  face SIFT', int(inl.sum()), 'scale', round(float(np.hypot(MF[0, 0], MF[1, 0])), 4))
FACE_N = ['happy', 'angry', 'focus', 'shout', 'effort']; BLINK_N = ['half', 'closed']
SRCF = {**{n: f'face_{n}' for n in FACE_N}, 'half': 'blink_half', 'closed': 'blink_closed'}
neu = neu_s.astype(np.int16); U_ = np.zeros(neu.shape[:2], bool)
for n in FACE_N + BLINK_N: U_ |= np.abs(sheet(SRCF[n]).astype(np.int16) - neu).max(2) > 40
reg = cv2.dilate(U_.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
face = (cv2.warpAffine(reg, MF, (512, 512), flags=cv2.INTER_NEAREST) > 0) & head_m
fm = np.clip(cv2.GaussianBlur(cv2.erode(face.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (5, 5), 1.0) * 1.15, 0, 1)
hb = np.array(Image.open(os.path.join(PARTS, 'head.png'))); hx0, hy0 = OFF['head']; hh, hw = hb.shape[:2]
wn = cv2.warpAffine(neu_s, MF, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)).astype(np.float32); cm = face & (wn[..., 3] > 200) & (RA[..., 3] > 200)
CA = [(RA[..., c][cm].astype(np.float32).std() / max(1.0, wn[..., c][cm].std()), 0.0) for c in range(3)]
CA = [(a, float(RA[..., c][cm].mean() - a * wn[..., c][cm].mean())) for c, (a, _) in enumerate(CA)]
for n in FACE_N + BLINK_N:
    wf = cv2.warpAffine(sheet(SRCF[n]), MF, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)).astype(np.float32)
    for c in range(3): wf[..., c] = np.clip(wf[..., c] * CA[c][0] + CA[c][1], 0, 255)
    al = fm * (wf[..., 3] / 255.0); o_ = np.zeros((512, 512, 4), np.float32); o_[hy0:hy0 + hh, hx0:hx0 + hw] = hb
    o_[..., :3] = o_[..., :3] * (1 - al[..., None]) + wf[..., :3] * al[..., None]
    fc = o_[hy0:hy0 + hh, hx0:hx0 + hw].astype(np.uint8); fc[..., 3] = hb[..., 3]
    Image.fromarray(fc).save(os.path.join(PARTS, f'face_{n}.png'))
print('  face patch px', int(face.sum()), 'colour fit', [(round(a, 3), round(b, 1)) for a, b in CA])
# ---------------- 뼈·조각 ----------------
def piv(name, p): o = np.array(OFF[name], float); q = np.array(p, float) - o; return [round(float(q[0]), 1), round(float(q[1]), 1)]
parts = {}
def P_(name, at, **kw): parts[name] = dict({'src': f'parts/{name}.png', 'pivot': piv(name, at), 'scale': SC}, **kw)
P_('torso', HIP); P_('hips', HIP); P_('head', NECK); P_('pony', PONY)
for _nm, (_par, _pt) in BACKB.items(): P_(_nm, _pt)   # 뒤 조각(가려진 곳, 부모와 같은 점)
parts['armU'] = {'src': 'parts/armU.png', 'pivot': [round(pvN[0], 1), round(pvN[1], 1)], 'scale': SC, 'elbow': [round(elN[0], 1), round(elN[1], 1)]}
parts['armF'] = {'src': 'parts/armF.png', 'pivot': [round(pvF[0], 1), round(pvF[1], 1)], 'scale': SC, 'elbow': [round(elF[0], 1), round(elF[1], 1)]}
P_('armL', EL_N, fist=piv('armL', FI_N)); P_('fistN', FI_N); P_('axeN', FI_N)
P_('foreF', EL_F); P_('fistF', WR_F)
parts['weapon'] = {'src': 'parts/weapon.png', 'pivot': [round(float(W_PIV[0]), 1), round(float(W_PIV[1]), 1)], 'scale': SC / UPS,
                   'tip': [round(float(W_TIP[0]), 1), round(float(W_TIP[1]), 1)], 'tips': [[round(float(W_TIP[0]) - 60, 1), round(float(W_TIP[1]) + 60, 1)], [round(float(W_TIP[0]) + 90, 1), round(float(W_TIP[1]) + 80, 1)]],
                   'guard': [round(float(W_HEAD[0]), 1), round(float(W_HEAD[1]) + 60, 1)], 'pommel': [round(float(W_POM[0]), 1), round(float(W_POM[1]), 1)]}
for n in FACE_N + BLINK_N: parts[f'face_{n}'] = {'src': f'parts/face_{n}.png', 'pivot': parts['head']['pivot'], 'scale': SC}
for nm, sd in [('bootStandN', 'near'), ('bootStandF', 'far')]: P_(nm, LEG[sd]['ankle'])
for _sd, _nm in (('near', 'bootNRun'), ('far', 'bootFRun')): parts[_nm] = {'src': f'parts/{_nm}.png', 'pivot': [round(RB[_sd][0][0], 1), round(RB[_sd][0][1], 1)], 'scale': SC}
for nm in ('thighN', 'thighF', 'shinN', 'shinF'): parts[nm] = {'src': f'parts/{nm}.png', 'pivot': [0, 0], 'scale': 1}
WEAPON_ANG = math.atan2(UF[1], UF[0]) + math.pi / 2
world = {'root': (O, 0.0), 'hip': (HIP, 0.0), 'skirt': (HIP, 0.0), 'cape': (NECK, 0.0), 'scarf': (NECK, 0.0), 'pouch': (HIP, 0.0), 'pauldron': (SH_N, 0.0), 'pauldronF': (SH_F, 0.0), 'torso': (HIP, 0.0), 'head': (NECK, 0.0), 'pony': (PONY, 0.0),
         'armU': (SH_N, math.radians(rotN)), 'armL': (EL_N, 0.3), 'axeN': (FI_N, 0.3), 'fistN': (FI_N, 0.3),
         'armF': (SH_F, math.radians(rotF)), 'foreF': (EL_F, 0.0), 'fistF': (WR_F, 0.0), 'weapon': (FI_F, WEAPON_ANG), 'foreFb': (WR_F, 0.0)}
for _nm, (_par, _pt) in BACKB.items(): world[_nm] = (_pt, 0.0)
ARML_REST = 0.3   # 엔진이 서 있을 때 자유 팔뚝을 −0.3 rad 굽힘(armL.ar) → 뼈 rot 에 +0.3(그 자식 도끼·주먹도 같이) → 대기 = 원화
BONES = [('root', None), ('hip', 'root'), ('skirt', 'hip'), ('torso', 'hip'), ('head', 'torso'), ('pony', 'head'), ('armF', 'torso'), ('foreF', 'armF'), ('fistF', 'foreF'), ('weapon', 'fistF'),
         ('armU', 'torso'), ('armL', 'armU'), ('axeN', 'armL'), ('fistN', 'armL'), ('foreFb', 'torso'),
         ('cape', 'torso'), ('scarf', 'torso'), ('pouch', 'hip'), ('pauldron', 'torso'), ('pauldronF', 'torso')]   # 엔진이 찾는 뼈(그림 없음) — 골반 그림 = skirt 뼈(엔진이 치마로 살짝 기울임)
BONES += [(_nm, _par) for _nm, (_par, _pt) in BACKB.items()]   # 뒤 조각 뼈 = 부모 뼈 자식(같은 자리)
WANG = {'armU': math.radians(rotN), 'armL': ARML_REST, 'axeN': ARML_REST, 'fistN': ARML_REST, 'armF': math.radians(rotF), 'weapon': WEAPON_ANG}   # 뼈 세상 각(그 밖 0)
#  armL·axeN·fistN: 그림은 원화 방향 그대로, 뼈 세상 각 +0.3 — 엔진이 대기 때 자유 팔뚝을 −0.3 굽혀 그림 방향 = 원화(19 와 같음)
bones = []
for name, parent in BONES:
    if parent is None: bones.append({'name': 'root', 'parent': None, 'pos': [0, 0]}); continue
    pw_, pa, cw_, ca = world[parent][0], WANG.get(parent, 0.0), world[name][0], WANG.get(name, 0.0)
    if parent == 'armL': pa, ca = 0.0, 0.0   # 팔뚝 자식(도끼·주먹)은 엔진 대기 굽힘(−0.3)이 들어간 뒤의 팔뚝 틀(= 원화 방향) 기준
    dv = (cw_ - pw_) * SC; c, s = math.cos(-pa), math.sin(-pa)
    b = {'name': name, 'parent': parent, 'pos': [round(c * dv[0] - s * dv[1], 1), round(s * dv[0] + c * dv[1], 1)]}
    if abs(ca - pa) > 1e-4: b['rot'] = round(ca - pa, 4)
    if name in parts: b['part'] = name
    if name == 'skirt': b['part'] = 'hips'
    bones.append(b)
# ---------------- 다리 정의 ----------------
legs = {'hip': [0, round(SC * (float(np.mean([LEG[s]['hip'][1] for s in LEG])) - HIP[1]), 1)], 'thigh': round(SC * L_TH, 1), 'shin': round(SC * L_SH, 1),
        'thighImg': TH['near'], 'shinImg': SHN['near'], 'boot': {'part': 'bootNRun', 'sole': RB['near'][1], 'ankleRange': [-1.2, 1.4]}}
for sd, nm, lm in [('near', 'bootStandN', lab('legN')), ('far', 'bootStandF', lab('legF'))]:
    hide = {'part': TH[sd]['part'], 'a': TH[sd]['a'], 'b': TH[sd]['b'], 'w': 0.001}
    _root = round(SC * (LEG[sd]['hip'][0] - HIP[0]), 1); _rest = round(SC * (LEG[sd]['ankle'][0] - HIP[0]), 1)
    # v1.1(00:00): 7 루시아·2 둘시네 구조 — x = 서 있는 발 자리(원화 발목), hipX = 다리 뿌리(IK), runX = 달리는 발 줄(= 뿌리, v1 과 같은 달리기).
    #   v1 은 x = 뿌리 + idleStance(서 있을 때만 벌림)라 공격 중 발 자리가 A(달리기 정도)를 따라 천천히 벌어졌음 → 공격 내내 발이 미끄러지고 선 다리 그림이 제자리 아닌 발목에 꽂힘
    legs[sd] = {'x': _rest, 'hipX': _root, 'runX': _root, 'shade': 0, 'thighImg': TH[sd], 'shinImg': SHN[sd], 'runBoot': 'bootNRun' if sd == 'near' else 'bootFRun',
                'stand': {'fade': [0.05, 0.1], 'thighImg': hide, 'shinImg': dict(hide, part=SHN[sd]['part'], a=SHN[sd]['a'], b=SHN[sd]['b']), 'boot': {'part': nm, 'sole': sole_pts(lm, LEG[sd]['ankle'], SOLE)}}}
idle = {sd: legs[sd]['x'] for sd in ('near', 'far')}   # 서 있는 발 자리(골반 기준, 표시용)
# ---------------- 그리는 순서 (뒤 → 앞): 포니테일 · 다리 · 먼 윗팔·팔뚝 · 가까운 윗팔(재킷 속) · 골반 · 상체 · 먼 도끼·주먹 · 머리 · 가까운 도끼 · 가까운 팔뚝 · 가까운 주먹 ----------------
draw = ['pony', 'legFar', 'legNear'] + list(BACKB) + DRAW_IDLE[3:]   # 뒤 조각은 다리 다음·모든 팔 앞(= 덮던 앞 부품보다 먼저)
assert draw[:3] == DRAW_IDLE[:3]
rig = {'name': 'bruno-rust', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': parts, 'bones': bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': {n: f'face_{n}' for n in FACE_N},
       'blinkFaces': {'half': 'face_half', 'closed': 'face_closed'},
       'gait': {'stance': 0.26, 'strideBase': 40, 'strideK': 0.12, 'hipBase': 6, 'bob': 8, 'lean': 0.1, 'headBob': 3, 'kneeLift': 0.7, 'heelKick': 0.5, 'dropCap': 16,
                'swingReach': 0.05, 'landAng': -0.04, 'elbowRun': 0.12, 'armSwing': 0.06, 'armBias': 0.0, 'headRun': 0.05},
       'carrySwing': 0.15, 'wristRange': 0.2, 'dropLift': 8, 'ponySway': 1.0, 'bounce': [],
       'metrics': {'bodyHeight': round(2 * (SOLE - M['hairTop'][1])), 'note': f"rig units; 머리카락 위(y{M['hairTop'][1]})~발바닥({SOLE:.0f}) ×2, 도끼 제외"},
       'ui': {'attack': 'smash', 'touch': 'hop'}}
# ---------------- 공격: 번갈아 내려찍기(tools/plan_alt10.py 키 그대로) ----------------
fo_off = np.array(OFF['foreF'], float); fi_off = np.array(OFF['fistF'], float)
ipt = lambda off, p: [round(float(p[0] - off[0]), 1), round(float(p[1] - off[1]), 1)]
ud = (EL_F - WR_F) / np.linalg.norm(EL_F - WR_F)
parts['gF'] = {'src': 'parts/fistF.png', 'pivot': ipt(fi_off, WR_F), 'grip': ipt(fi_off, FI_F), 'elbow': ipt(fi_off, WR_F), 'wrist': ipt(fi_off, WR_F), 'scale': SC,
               'shaftDir': [round(float(UF[0]), 4), round(float(UF[1]), 4)], 'fore': 'foreFa', 'foreBone': 'foreFb', 'foreDir': [round(float(ud[0]), 4), round(float(ud[1]), 4)]}
parts['foreFa'] = {'src': 'parts/foreF.png', 'pivot': ipt(fo_off, WR_F), 'elbow': ipt(fo_off, EL_F), 'scale': SC}
rig['swordGrip'] = {'tipDepth': 6, 'near': {'upper': 'armF', 'carry': 'gF', 'pieces': []}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': 0}, 'stretchMax': 1.05, 'shoulderPush': 0}
rig['drawA'] = ['pony', 'legFar', 'legNear'] + list(BACKB) + ['armF', 'foreFb', 'armU', 'skirt', 'torso', 'weapon', 'foreF', 'head', 'axeN', 'armL', 'fistN']
E = PLAN['engine']
trk = lambda f: [[e[0], round(f(e), 4), 'io'] for e in E]
act = {'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': 1.0, 'hitAt': PLAN['summary']['hits'][0], 'hitStop': 0.05, 'cancelAt': 0.8,
       'w': [[0, 1]], 'reach': [[0, 0]], 'nPiece': [[0, 'gF']], 'nUpper': [[0, 'armF']], 'armIK': [[0, 1]], 'ikSideK': {'N': [[0, 1]]},
       'gx': trk(lambda e: SC * e[1]), 'gy': trk(lambda e: SC * (e[2] - e[5])), 'sa': trk(lambda e: math.radians(e[3])),
       'lean': trk(lambda e: e[4]), 'hipY': trk(lambda e: SC * e[5]),
       'head': [[0, 0], [0.1, -0.05, 'io'], [0.28, 0.06, 'io'], [0.4, -0.03, 'io'], [0.54, 0.07, 'io'], [0.8, 0]],
       'freeArm': True, 'fuA': trk(lambda e: e[6]), 'flA': trk(lambda e: e[7]),
       'face': [[0, 'angry'], [0.24, 'shout'], [0.38, 'angry'], [0.5, 'shout'], [0.7, 'focus'], [0.9, None]],   # v1.1: '힘줌'(눈 가늘게 = 감은 것처럼 보임) 뺌 — DHL 23:57 '공격할 때 눈 감지 마요'
       'order': [[0, 'drawA']],
       # v1.1 다리(DHL 23:57 '공격 자세로 변하면서 다리가 꼬면서 나옴 · 공격 중에도 꼼'): 
       #  ① footReach 뺌 — 원화 선 다리가 이미 다리 길이의 .998 이라 공격 중 골반이 오르내릴 때 .55~.68 에 두 발을 몸 가운데로 당겨(±114 → −46·+54) X 자
       #  ② 달리다 공격: 엔진은 가까운 발을 .03~.15, 먼 발을 .17~.29 에 선 자리로 옮김 → 그동안 발을 들어 한 걸음씩(nearLift·farLift, 미끄러짐 없음),
       #     서 있는 다리 그림(원화 다리 통째, 발목에 핀)은 두 발이 자리에 온 뒤(.3 무렵)에 한 프레임에 바뀜(aDamp 9 · standStep · stand.fade [.05,.1]) — 전엔 .1 에 바뀌어 제자리가 아닌 발목에 원화 다리가 꽂혀 X 자
       'nearLift': [[0, 0], [0.03, 0, 'io'], [0.09, 10, 'io'], [0.15, 0]], 'farLift': [[0, 0], [0.17, 0, 'io'], [0.23, 10, 'io'], [0.29, 0]],
       'aDamp': 9, 'standStep': True}
rig['actions'] = {'smash': act}
rig['cutHold'] = 0.1   # 스킬 컷인 멈춤(10-21 게임 넣기): 후보 .10·.17·.20·.23·.48·.53 — .20(가까운 도끼를 머리 위로 곧게)은 컷인 칸 위 끝에 도끼 날이 닿아(1~2px) .10 예비(가까운 도끼를 뒤로 젖히고 먼 도끼 듦, 화남 얼굴)
# 도감 몸 가운데: index.html measureBox(160px) 흉내 → fitArt 가운데, 골반이 가운데
_a = np.array(Image.open(os.path.join(HERE, '..', '..', '..', 'art', 'characters', 'char_0010.png')).convert('RGBA').resize((160, 160), Image.BOX))[..., 3]
_ys, _xs = np.nonzero(_a > 40); FIT_CX = round(float(((_xs.min() + _xs.max() + 1) / 2 + _xs.mean() + .5) / 2 / 160 * 512), 1)
rig['gameRef'] = {'refOrigin': [round(float(O[0] - (HIP[0] - FIT_CX)), 1), float(O[1])], 'refScale': 2.0, 'refLift': 0,
                  'note': f'게임 그림 char_0010.png(512) = 0번 합격 원화(ref512). x = 도감 칸(fitArt 중심 {FIT_CX}, index.html measureBox 와 같은 계산)에서 골반(hip x {HIP[0]:.0f})이 가운데'}
rig['note'] = '10 러스트 브루노 v1.1(대기·달리기·번갈아 내려찍기). 쌍도끼 계열 기준. 조각 = 원화를 부품별로 나눔(seg10.py) + 가려진 곳 = 그 부품만 지운 원화(프롬프트 2·3: sheets/nonear_2345·nofar_2344), 시트 = 표정·깜빡임·달리는 다리·부츠'
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(PARTS)): _h.update(fn.encode()); _h.update(open(os.path.join(PARTS, fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_bruno10.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};window.MR_RIG_DEFS['bruno-rust']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(parts), 'parts, version', rig['version'], 'idle', idle, 'legs', legs['thigh'], legs['shin'], 'hip', legs['hip'], 'FIT_CX', FIT_CX)
