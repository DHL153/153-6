"""30 스카이 브루노 리그 조립 v1 — 20 네온 브루노 v2.1(build_bruno20) 구조 + 10 러스트의 포니테일(pony 뼈) + 스카프 꼬리(streamers, 21·23 과 같음)
입력: ref512.png(0번 합격 원화 = 게임 char_0030, DHL 17:44) · sheets/nonear_1806.png·nofar_1819.png(팔·도끼만 지운 원화) · work/labels.npy(seg30.py) · pieces/(조각 시트 19칸, cut30.py) · measure30.json · review/plan_alt30.json
출력: ../rig.json · ../rig.def.js · ../parts/*.png
실행: cd source && python3 -I cut30.py && python3 -I seg30.py && python3 -I tools/plan_alt30.py && python3 -I build_bruno30.py
원칙(DHL): 대기 = 원화 · 도끼 크기 그대로 · 팔다리 길이 고정 · 팔꿈치(팔뚝)가 어깨(윗팔)보다 앞 · 먼 팔은 몸 뒤, 주먹·도끼만 앞 · 공격 중 눈 뜸 · 조각을 또 쪼개지 않음(67) · 허리띠 = 상체와 한 몸(66) · 달릴 때 발목 고정(63)
20 과 다른 곳: 포니테일 다발(pony 뼈, 머리 자식) · 스카프 꼬리(tailA — streamers 천 흔들림) · 도끼(원화 + 주먹 밑·자루 끝 = 시트 13번 도끼를 도끼 머리 SIFT 로 맞춤) ·
          가까운 윗팔 = 남색 소매 + 팔꿈치 맨살(은색 어깨갑 조각 밑) · 먼 어깨갑·소매 = 상체 · 크림 앞자락 = 골반(seg30) · 공격 상체 따로 없음(torsoAtk 안 씀)
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
M = json.load(open(os.path.join(HERE, 'measure30.json'))); PLAN = json.load(open(os.path.join(HERE, 'review', 'plan_alt30.json')))
YY, XX = np.mgrid[0:512, 0:512]
V = lambda p: np.array(p, float)
def desp(a):
    a = a.astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None); a[..., 0] -= m; a[..., 2] -= m; return np.clip(a, 0, 255).astype(np.uint8)
def sheet(n): return desp(np.array(Image.open(os.path.join(PC, n + '.png')).convert('RGBA')))
def art(mask): a = RA.copy(); a[..., 3] = np.where(mask, a[..., 3], 0); return a
def dil(m, r): return cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
CUT = {}
OFF = {}
def despeck(a, minpx=14):   # 조각에서 떨어진 작은 점(라벨 경계에 남은 외곽선 부스러기) 지움
    n, cc, st, _ = cv2.connectedComponentsWithStats((a[..., 3] > 0).astype(np.uint8), 8); a = a.copy()
    for i in range(1, n):
        if st[i, 4] < minpx: a[cc == i] = 0
    return a
def save(name, a, pad=2):
    if name in ('head', 'torso', 'hips', 'pauldron', 'headB', 'torsoB', 'pauldronB', 'hipsB', 'ponyB', 'armU', 'armF', 'armL', 'foreF', 'pony', 'tailA'):
        d_ = despeck(a); a = d_ if (d_[..., 3] > 0).any() else a
    ys, xs = np.nonzero(a[..., 3] > 0); x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad); x1, y1 = min(a.shape[1], xs.max() + 1 + pad), min(a.shape[0], ys.max() + 1 + pad)
    Image.fromarray(a[y0:y1, x0:x1]).save(os.path.join(PARTS, name + '.png')); OFF[name] = (x0, y0); return np.array([x0, y0], float)
def under(a, b, where):
    out = a.copy(); w = where & (b[..., 3] > 0) & (a[..., 3] < 250); fa = a[..., 3:4] / 255.0; fb = b[..., 3:4] / 255.0
    col = a[..., :3] * fa + b[..., :3] * fb * (1 - fa); al = fa + fb * (1 - fa)
    out[w, :3] = np.clip(col[w] / np.maximum(al[w], 1e-3), 0, 255).astype(np.uint8); out[w, 3] = np.clip(al[w, 0] * 255, 0, 255).astype(np.uint8); return out
def col_match(im, ref_m, k=1.0):
    im = im.astype(np.float32); m = im[..., 3] > 200; R = RA[..., :3].astype(np.float32)[ref_m & (RA[..., 3] > 200)]
    for c in range(3):
        v = im[..., c][m]; im[..., c] = np.where(im[..., 3] > 0, (im[..., c] - v.mean()) / max(1.0, v.std()) * R[:, c].std() + R[:, c].mean(), im[..., c])
    im[..., :3] *= k; return np.clip(im, 0, 255).astype(np.uint8)
# ---------------- 관절 ----------------
N_, F_ = M['near'], M['far']
SOLE = float(M['sole_y']); HIP = V(M['hip']); NECK = V(M['neck'])
LEG = {sd: {k: V(v) for k, v in M['legs'][sd].items() if k != 'len'} for sd in ('near', 'far')}
O = V([(LEG['near']['ankle'][0] + LEG['far']['ankle'][0]) / 2, SOLE])
SH_N, EL_N, WR_N, FI_N, BL_N = V(N_['SH']), V(N_['EL']), V(N_['WR']), V(N_['fist']), V(N_['head'])
SH_F, EL_F, WR_F, FI_F, BL_F = V(F_['SH']), V(F_['EL']), V(F_['WR']), V(F_['fist']), V(F_['head'])
PONY = V(M['pony'])
UN = (BL_N - FI_N) / np.linalg.norm(BL_N - FI_N); UF = (BL_F - FI_F) / np.linalg.norm(BL_F - FI_F)
SC = 2.0
# ---------------- 가려진 곳 = '팔·철퇴만 지운 원화'(프롬프트 2·3) — 10 v1.1 과 같은 reveal ----------------
DRAW_IDLE = ['pony', 'tailA', 'legFar', 'legNear', 'armF', 'foreF', 'skirt', 'torso', 'armU', 'pauldron', 'weapon', 'fistF', 'head', 'axeN', 'armL', 'fistN']
BONE_OF = {'head': 'head', 'pony': 'pony', 'scarf': 'tailA', 'torso': 'torso', 'hips': 'skirt', 'legN': 'legNear', 'legF': 'legFar', 'pauldN': 'pauldron', 'upperN': 'armU', 'foreN': 'armL', 'fistN': 'fistN',
           'axeN': 'axeN', 'upperF': 'armF', 'foreF': 'foreF', 'fistF': 'fistF', 'axeF': 'weapon'}
NONEAR = np.array(Image.open(os.path.join(HERE, 'sheets', 'nonear_1806.png')).convert('RGBA'))
NOFAR = np.array(Image.open(os.path.join(HERE, 'sheets', 'nofar_1819.png')).convert('RGBA'))
def clean(IMG):   # 지운 원화의 떨어진 작은 섬(< 40px — 18:19 그림 귀 옆 머리 가닥 끝 외곽선 36px) 지움
    n, cc, st, _ = cv2.connectedComponentsWithStats((IMG[..., 3] > 0).astype(np.uint8), 8); IMG = IMG.copy()
    for i in range(1, n):
        if st[i, 4] < 40: IMG[cc == i] = 0
    return IMG
NONEAR, NOFAR = clean(NONEAR), clean(NOFAR)
ADD, BACK = {}, {}
def reveal(IMG, rem_names, tag):
    R = lab(*rem_names); BG = len(NAMES) + 1; mk = np.zeros((512, 512), np.int32)
    for n in NAMES:
        if n not in rem_names: mk[(LAB == LID[n]) & ~R] = LID[n]
    mk[(LAB == 0) & ~R] = BG; mk[R & (IMG[..., 3] < 24)] = BG
    al = IMG[..., 3:4] / 255.0; rgb = np.ascontiguousarray((IMG[..., :3] * al + 52 * (1 - al)).astype(np.uint8))
    ws = cv2.watershed(rgb, mk.copy())
    for y, x in zip(*np.nonzero((ws <= 0) & R)):
        nb = ws[max(0, y - 1):y + 2, max(0, x - 1):x + 2].ravel(); nb = nb[nb > 0]; ws[y, x] = np.bincount(nb).argmax() if len(nb) else BG
    rep = {}
    for n in NAMES:
        if n in rem_names: continue
        m = R & (ws == LID[n]) & (IMG[..., 3] > 0)
        if not m.any(): continue
        for p in rem_names:
            mp = m & (LAB == LID[p])
            if not mp.any(): continue
            back = DRAW_IDLE.index(BONE_OF[n]) > DRAW_IDLE.index(BONE_OF[p])
            (BACK if back else ADD).setdefault(n, []).append((IMG, mp)); rep[f"{n}{'(뒤)' if back else ''}←{p}"] = int(mp.sum())
    print(f'  {tag}: 지운 곳 {int(R.sum())} px · 뒤 그림 {int((R & (IMG[..., 3] > 0)).sum())} px →', rep)
REM_N, REM_F = ['upperN', 'foreN', 'fistN', 'axeN'], ['upperF', 'foreF', 'fistF', 'axeF']
reveal(NONEAR, REM_N, 'nonear(가까운 팔·도끼 지움)')
reveal(NOFAR, REM_F, 'nofar(먼 팔·도끼 지움)')
# 지운 원화는 팔이 나오던 짧은 검은 소매 토막(입구 구멍)을 어깨갑 밑에 남겨 그림 — 이 리그는 소매 끝·띠가 윗팔 조각에 붙어 같이 돌므로,
#   토막을 상체·어깨갑에 남기면 팔이 비킬 때 '빈 소매'가 따로 보임(첫 v1 공격 .267 확대) → 몸 실루엣 밖(가까운 x < 200 · 먼 x > 296)의 토막 픽셀은 뺌(투명)
def drop(tbl, names, where):
    for n in names:
        if n in tbl: tbl[n] = [(IMG, m & ~where) for IMG, m in tbl[n] if (m & ~where).any()]
        if n in tbl and not tbl[n]: del tbl[n]
SLEEVE_N = lab('upperN') & (XX >= 168) & (YY >= 312) & (YY <= 346)   # 지운 원화의 빈 남색 소매 토막(18:06 — 어깨갑 왼쪽 아래)
for T_ in (ADD, BACK): drop(T_, ['torso', 'head', 'pauldN'], SLEEVE_N); drop(T_, ['torso'], lab('upperF') & (XX > 306)); drop(T_, ['pauldN'], lab('foreN') | lab('upperN'))   # 팔 뒤가 어깨갑 몫이 되면 팔이 비킬 때 어깨갑에 남색 천이 붙어 다님 → 빼고 포니테일 메움이 받침
# 지운 원화가 어깨갑 몫으로 다시 그린 곳(어깨갑 왼쪽 외곽선 — 원화에선 윗팔 소매 위 끝이 겸함)은 어깨갑 조각 앞에(뒤 조각 아님): 팔이 비켜도 어깨갑 가장자리가 깨끗
if 'pauldN' in BACK: ADD.setdefault('pauldN', []).extend(BACK.pop('pauldN'))
print('  소매 토막 뺀 뒤:', {('뒤 ' if T_ is BACK else '') + k: int(sum(m.sum() for _, m in v)) for T_ in (ADD, BACK) for k, v in T_.items()})
REPL, FRONT_ADD = {}, {}
def unmix_edges(IMG, rem_names, tag, band_r=3, T=20):
    fr = [f for f in rem_names if f in ('upperN', 'foreN', 'fistN', 'axeN', 'fistF', 'axeF')]   # 대기에 뒤 부품보다 나중에 그려지는 앞 부품
    dist = np.stack([cv2.distanceTransform((~lab(f)).astype(np.uint8), cv2.DIST_L2, 3) for f in fr]); own = dist.argmin(0); dmin = dist.min(0)
    p = RA[..., :3].astype(np.float32); h = IMG[..., :3].astype(np.float32)
    cand = (dmin <= band_r) & ~lab(*rem_names) & (LAB > 0) & (RA[..., 3] > 200) & (IMG[..., 3] > 200) & (np.abs(p - h).max(-1) > T)
    bgc = (dmin <= band_r) & ~lab(*rem_names) & (LAB > 0) & (RA[..., 3] > 0) & (IMG[..., 3] < 30)
    rep = {}
    for i, f in enumerate(fr):
        om = lab(f) & (RA[..., :3].astype(int).mean(-1) < 50)
        if not om.any(): continue
        oc = np.median(RA[om][:, :3], 0).astype(np.float32)
        for b in NAMES:
            if b in rem_names or DRAW_IDLE.index(BONE_OF[b]) > DRAW_IDLE.index(BONE_OF[f]): continue
            m = cand & (own == i) & (LAB == LID[b]); mb = bgc & (own == i) & (LAB == LID[b])
            if not (m.any() or mb.any()): continue
            lay = FRONT_ADD.setdefault(f, np.zeros((512, 512, 4), np.float32))
            if m.any():
                dv = oc - h[m]; a = np.clip(((p[m] - h[m]) * dv).sum(-1) / np.maximum((dv * dv).sum(-1), 1e-3), 0, 1)
                res = np.abs(p[m] - (h[m] + a[:, None] * dv)).max(-1); full = res >= 18
                pm = RA[m]; hs = cv2.cvtColor(pm[None, :, :3], cv2.COLOR_RGB2HSV)[0]
                armlike = (b in ('head', 'pony')) & ((hs[:, 1] > 50) | (pm[:, :3].astype(int).mean(-1) < 60))
                keep = full & ~armlike; mm = m.copy(); mm[np.nonzero(m)[0][keep], np.nonzero(m)[1][keep]] = False
                ys, xs = np.nonzero(m); sel = ~keep
                lay[ys[sel], xs[sel], :3] = np.where(full[sel][:, None], p[m][sel], oc); lay[ys[sel], xs[sel], 3] = np.where(full[sel], 255, a[sel] * 255)
                REPL.setdefault(b, []).append((IMG, mm)); rep[f'{b}→{f}'] = (int(mm.sum()), int((full & armlike).sum()), int(keep.sum()))
            if mb.any():
                ys, xs = np.nonzero(mb); lay[ys, xs] = RA[mb].astype(np.float32); REPL.setdefault(b, []).append((np.zeros_like(RA), mb)); rep[f'{b}→{f}(배경)'] = int(mb.sum())
    print(f'  {tag} 가장자리 풀기 (옮김, 통째, 원화 그대로)', rep)
unmix_edges(NONEAR, REM_N, 'nonear', band_r=5)
unmix_edges(NOFAR, REM_F, 'nofar')
# 윗팔 바로 둘레(4px)인데 대기에 윗팔보다 나중에 그리는 라벨(머리숱·어깨갑)에 남은 팔 외곽선·살 조각: 지운 원화에서 배경(투명)이면 팔 조각으로 옮김
#   (첫 v1 공격 .267: 팔이 비키면 어깨갑 왼쪽에 검은 선·주황 갈고리가 떠 있었음) — 대기 합성은 그대로(팔 조각이 그 자리를 그림)
def move_over(IMG, f, backs, r=4):
    near = (cv2.distanceTransform((~lab(f)).astype(np.uint8), cv2.DIST_L2, 3) <= r) & (IMG[..., 3] < 30) & (RA[..., 3] > 0)
    lay = FRONT_ADD.setdefault(f, np.zeros((512, 512, 4), np.float32)); rep = {}
    for b in backs:
        m = near & (LAB == LID[b])
        if not m.any(): continue
        lay[m] = RA[m].astype(np.float32); REPL.setdefault(b, []).append((np.zeros_like(RA), m)); rep[b] = int(m.sum())
    print(f'  {f} 둘레 앞 라벨 조각 → {f}', rep)
move_over(NONEAR, 'upperN', ['head', 'pauldN', 'pony', 'scarf']); move_over(NOFAR, 'upperF', ['torso'])
# 윗팔 위를 덮던 머리 가닥 끝(팔에서 잘린 끝): 지운 원화가 이어 그린 가닥으로(팔 둘레 6px, 지운 원화가 칠해진 곳) — 팔이 비키면 가닥 끝이 점처럼 떠 보였음
_hn = (cv2.distanceTransform((~lab('upperN')).astype(np.uint8), cv2.DIST_L2, 3) <= 6) & (LAB == LID['head']) & (NONEAR[..., 3] > 200)
REPL.setdefault('head', []).append((NONEAR, _hn)); print('  머리 가닥 끝 → 지운 원화', int(_hn.sum()), 'px')
# 윗팔과 맞닿는 조각(어깨갑·상체·머리숱)의 경계 외곽선: 라벨 경계가 외곽선 가운데를 지나 팔이 비키면 어깨갑·상체 가장자리가 톱니(첫 v1 .267)
#   → 윗팔 라벨의 어두운 경계 픽셀(밝기 < 80, 이웃 라벨 2px 안)을 이웃 조각에도 복사(팔 조각에도 남김) — 대기 합성 그대로
COPY = {}
LUMI = RA[..., :3].astype(int).mean(-1)
for f_, backs_ in (('upperN', ('pauldN', 'torso')), ('upperF', ('torso',))):
    for b_ in backs_:
        m_ = lab(f_) & dil(lab(b_), 2) & (LUMI < 80) & (RA[..., 3] > 200)
        if m_.any(): COPY.setdefault(b_, []).append(m_)
print('  경계 외곽선 복사 px', {k: int(sum(x.sum() for x in v)) for k, v in COPY.items()})
def front_with(n, a):
    if n not in FRONT_ADD: return a
    lay = FRONT_ADD[n]; o = a.astype(np.float32); w = lay[..., 3] > 0; o[w] = lay[w]; return np.clip(o, 0, 255).astype(np.uint8)
def with_reveal(n):
    a = art(lab(n))
    for IMG, m in REPL.get(n, []): a[m] = IMG[m]
    for m in COPY.get(n, []): a[m] = RA[m]
    for IMG, m in ADD.get(n, []): a = under(a, IMG, m)
    return a
# ---------------- 도끼: 원화 + 주먹 밑·아래 자루 끝 = 시트 13번 도끼(도끼 머리 SIFT 로 원화 도끼에 맞춤) ----------------
SM = sheet('axe'); _sift = cv2.SIFT_create(4000)
def _gr(a): al_ = a[..., 3:4] / 255.0; return cv2.cvtColor((a[..., :3] * al_ + 128 * (1 - al_)).astype(np.uint8), cv2.COLOR_RGB2GRAY)
def axe_fit(lm, fist, head, U):   # 시트 도끼 → 원화 도끼(닮음 변환): 도끼 머리 둘레 SIFT
    k1, d1 = _sift.detectAndCompute(_gr(SM), ((SM[..., 3] > 128) * 255).astype(np.uint8))
    reg = lm & (((XX - head[0]) ** 2 + (YY - head[1]) ** 2) <= 80 ** 2); k2, d2 = _sift.detectAndCompute(_gr(RA), (reg * 255).astype(np.uint8))
    mm = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < .75 * b.distance]
    T, inl = cv2.estimateAffinePartial2D(np.float32([k1[a.queryIdx].pt for a in mm]), np.float32([k2[a.trainIdx].pt for a in mm]), ransacReprojThreshold=2.0)
    return T, int(inl.sum()), float(np.hypot(T[0, 0], T[1, 0])), math.degrees(math.atan2(T[1, 0], T[0, 0]))
def axe_img(name, fist, head, U, lm):
    a = art(lm); T, ni, sc, rot = axe_fit(lm, fist, head, U)
    ws = cv2.warpAffine(SM, T, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
    nv = np.array([-U[1], U[0]]); u = (XX - fist[0]) * U[0] + (YY - fist[1]) * U[1]; v = (XX - fist[0]) * nv[0] + (YY - fist[1]) * nv[1]
    pom = float(-u[lm & (RA[..., 3] > 128)].min())   # 원화 자루 끝(금 마개)까지 — 그보다 아래는 대기에 없던 자루라 안 씀(대기 = 원화)
    where = (u < 22) & (u >= -pom) & (np.abs(v) < 16) & dil(RA[..., 3] > 128, 1)   # 원화 실루엣 안(주먹에 가려진 자루)만 — 밖이면 시트 자루 폭이 주먹 옆에 갈색 테로 보였음
    out = under(a, ws, where); ys, xs = np.nonzero(where & (ws[..., 3] > 128)); umin = float(u[ys, xs].min()) if len(ys) else 0.0
    print(f'  {name}: 시트 도끼 SIFT {ni}점 ×{sc:.3f} 회전 {rot:+.1f}° · 주먹 밑·자루 끝 {int((where & (ws[..., 3] > 0) & (a[..., 3] < 250)).sum())} px · 자루 끝 = 주먹 아래 {-umin:.0f}px')
    return out, -umin
mcN, POM_N = axe_img('axeN', FI_N, BL_N, UN, lab('axeN')); mcN = front_with('axeN', mcN)
mcF, POM_F = axe_img('axeF', FI_F, BL_F, UF, lab('axeF')); mcF = front_with('axeF', mcF)
save('axeN', mcN)
UPS = 2; ang_tip = math.atan2(UF[1], UF[0]); rot_deg = math.degrees(-math.pi / 2 - ang_tip)
sw2 = cv2.resize(mcF, None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LANCZOS4); sw2[..., 3] = np.clip(cv2.resize(mcF[..., 3], None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LINEAR), 0, 255)
Rm = cv2.getRotationMatrix2D((float(FI_F[0] * UPS), float(FI_F[1] * UPS)), -rot_deg, 1.0); WS, HS = 700, 1000; Rm[0, 2] += WS / 2 - FI_F[0] * UPS; Rm[1, 2] += 720 - FI_F[1] * UPS
swv = cv2.warpAffine(sw2, Rm, (WS, HS), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
ys, xs = np.nonzero(swv[..., 3] > 0); assert xs.min() > 0 and ys.min() > 0 and xs.max() < WS - 1 and ys.max() < HS - 1, '도끼 그림이 캔버스 밖'
x0, y0 = max(0, xs.min() - 2), max(0, ys.min() - 2); swv = swv[y0:ys.max() + 3, x0:xs.max() + 3]; Image.fromarray(swv).save(os.path.join(PARTS, 'weapon.png'))
vpt = lambda p: (Rm[:, :2] @ (np.array(p, float) * UPS) + Rm[:, 2]) - np.array([x0, y0])
W_PIV = vpt(FI_F); W_HEAD = vpt(BL_F); ysw, xsw = np.nonzero(swv[..., 3] > 128); W_TIP = np.array([float(W_PIV[0]), float(ysw.min())]); W_POM = np.array([float(W_PIV[0]), float(ysw.max())])
print('  far axe vertical: pivot', np.round(W_PIV, 1), 'top', np.round(W_TIP, 1), 'pommel', np.round(W_POM, 1), 'rot', round(rot_deg, 1))
# ---------------- 머리·상체·골반·어깨갑 + 이음 밑 4px ----------------
def underlay(a, back_m, front_m, r=4):
    band = front_m & dil(back_m, r) & (RA[..., 3] >= 250) & (a[..., 3] == 0); a = a.copy(); a[band] = RA[band]; return a, int(band.sum())
head_m = lab('head'); hd = with_reveal('head')
RIM = np.zeros((512, 512), bool)
o_head = save('head', hd)
_p, _n1 = underlay(with_reveal('pony'), lab('pony'), head_m)
#   가까운 소매 뒤(빈 소매 토막을 뺀 자리) = 포니테일 머리카락으로 메움 — 팔을 들면 어깨갑 왼쪽 아래에 배경이 비쳤음(v1 첫 렌더 .28). 포니테일은 맨 뒤라 대기엔 소매가 덮음
_hole = dil(lab('upperN') | SLEEVE_N, 4) & (_p[..., 3] < 200) & (XX < 204) & (YY >= 300) & (YY <= 352) & ~lab('scarf')
_rgb_p = np.ascontiguousarray(_p[..., :3]); _ip = cv2.inpaint(_rgb_p, (((_p[..., 3] < 200) & dil(_hole, 6)) * 255).astype(np.uint8), 5, cv2.INPAINT_TELEA)
_p = _p.copy(); _p[_hole, :3] = _ip[_hole]; _p[_hole, 3] = 255; print('  포니테일 소매 뒤 메움', int(_hole.sum()), 'px')
o_pony = save('pony', _p); print('  포니테일 이음 밑(머리 밑)', _n1)
_sc = with_reveal('scarf'); o_sc = save('tailA', _sc)
_sm = (np.array(Image.open(os.path.join(PARTS, 'tailA.png')))[..., 3] > 128); _sy, _sx = np.nonzero(_sm)
_rx = int(_sx.max()); _ry = float(np.mean(_sy[_sx >= _rx - 3])); SCARF_ROOT = np.array([OFF['tailA'][0] + _rx - 2, OFF['tailA'][1] + _ry])
print('  스카프 꼬리 tailA: 뿌리(오른쪽 끝)', np.round(SCARF_ROOT, 1), '· 길이', int(_sx.max() - _sx.min()), 'px')
tr, _n2 = underlay(with_reveal('torso'), lab('torso'), head_m | lab('pauldN') | lab('pony') | lab('scarf'))
o_tor = save('torso', tr)
_hp, _n3 = underlay(with_reveal('hips'), lab('hips'), lab('torso'))
for _x, _y in CUT.items():   # 바지를 가로지른 골반 아래 끝 2줄 옅게(대기엔 같은 원화 다리 위라 그대로, 달리면 시트 허벅지 위로 부드럽게)
    _hp[_y, _x, 3] = (_hp[_y, _x, 3] * 0.45).astype(np.uint8); _hp[_y - 1, _x, 3] = (_hp[_y - 1, _x, 3] * 0.8).astype(np.uint8)
# 허리띠 조각(belt — 상체와 한 몸, 서기·달리기 모두) · 서 있을 땐 그 밑 바지(hips, 골반 뼈), 달리기 다리 그림이면 바지 대신 시트 허벅지 + 가랑이 메움(hipsU)
#   DHL 11:59 '치마를 없애는 것이 좋을 것 같아요 · 러스트 브루노처럼 깔끔하게 허리띠만 나오도록' — v1.5~1.9 치마 대신:
#   원화 골반 칸에서 허리띠·쌈지·버클·끈·금빛 병(바지 천이 아닌 색) + 그 둘레 원화 외곽선만 남기고 바지 천은 뺌 → 허리띠 아래 = 시트 허벅지(바지)
#   허리띠 밑 가랑이 사이는 다리 뒤 조각 hipsU(바지 천 색, 다리보다 먼저 그림)가 메움 — 허벅지 윗끝 둥근 끝 사이로 배경이 안 보이게
def belt_run():   # 30: 허리띠(버클·쌈지 — 골반 칸 y ≤ 383) + 크림 앞자락 두 장(크림 + 둘레 외곽선, 속 구멍 메움) — 그 밖 남색 바지는 hips
    base, _ = underlay(with_reveal('hips'), lab('hips'), lab('torso')); Hm = lab('hips') & (base[..., 3] > 0)
    lum = RA[..., :3].astype(int).mean(-1); sat = RA[..., :3].max(-1).astype(int) - RA[..., :3].min(-1)
    band = Hm & (YY <= 383)
    cream = Hm & (lum > 150) & (sat >= 22) & (YY > 376)
    nc, cc = cv2.connectedComponents(cream.astype(np.uint8), 8); cr2 = np.zeros_like(cream)
    for i_ in range(1, nc):
        if (cc == i_).sum() >= 30: cr2 |= cc == i_
    flap = cv2.morphologyEx(cr2.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0   # 금 리벳·주름 선 = 속 구멍 메움
    flap = (flap | (dil(flap, 2) & (lum < 70))) & Hm
    keep = band | flap
    ff = keep.astype(np.uint8).copy(); cv2.floodFill(ff, None, (0, 0), 2); keep |= (ff == 0) & Hm
    out = base.copy(); out[~keep, 3] = 0
    print('  허리띠 조각 belt:', int(keep.sum()), 'px (허리띠', int(band.sum()), '· 앞자락', int((flap & ~band).sum()), ') · 원화 골반', int((base[..., 3] > 0).sum()), 'px')
    return out, keep
_belt, BELT = belt_run()
o_belt = save('belt', _belt)
#   허리띠는 상체와 한 몸(belt 뼈 = torso 자식) — DHL 12:16 '탄띠 위치를 이동시키지 않으면 탄띠·아래 다리 쪽 잔상도 안 남을 것':
#   상체가 기울 때 재킷 밑단과 허리띠·쌈지가 따로 움직여 쌈지 위에 재킷 끝이 떠 보였음 → 허리띠는 상체를 따라, 그 밑 바지(hips)는 다리 쪽(골반 뼈)에.
#   바지 조각엔 허리띠 픽셀을 빼고(겹쳐 그리면 두 겹 잔상) 허리띠 밑 허리 안쪽을 바지 천 색으로 채움 — 허리띠가 기울어 들려도 배경·잔상 대신 바지
_lum = RA[..., :3].astype(int).mean(-1); _sat = RA[..., :3].max(-1).astype(int) - RA[..., :3].min(-1); _Hm = lab('hips')
_rgb = RA[..., :3].astype(int); _PANTS = (_lum >= 28) & (_lum <= 95) & (_rgb[..., 2] - _rgb[..., 0] > 12)
_pc = np.median(RA[_Hm & (RA[..., 3] >= 250) & _PANTS][:, :3], 0)
_wp = np.stack(np.nonzero((lab('torso') & (YY >= 348) & (YY <= 362)) | (_Hm & _PANTS & (YY >= 380)))[::-1], 1).astype(np.int32)
_waist = np.zeros((512, 512), np.uint8); cv2.fillConvexPoly(_waist, cv2.convexHull(_wp), 1); _waist = (_waist > 0) & (YY >= 354)
_F = BELT & (_waist | (YY >= 378))   # 허리띠·앞자락 밑 = 바지 천(앞자락이 상체를 따라 들려도 구멍 대신 바지)
_hp[BELT & ~_F, 3] = 0; _hp[_F, :3] = (_pc * (1 - 0.12 * np.clip((YY[_F] - 362) / 24.0, 0, 1))[:, None]).astype(np.uint8); _hp[_F, 3] = 255
print('  바지 조각 hips: 허리띠 픽셀 뺌', int((BELT & ~_F).sum()), '· 허리띠 밑 허리 바지 천', int(_F.sum()), '· 색', _pc.astype(int).tolist())
_spk = _Hm & ~BELT & (_lum > 110) & (_hp[..., 3] > 0)   # 허리띠 조각에 못 들어간 크림 앞자락 부스러기(허리띠가 상체를 따라 기울면 바지 위에 흰 점으로 남았음) → 바지 천
_hp[_spk, :3] = _pc.astype(np.uint8); print('  바지 조각 크림 부스러기 → 바지 천', int(_spk.sum()))
o_hips = save('hips', _hp)
#   hipsU — 허리띠 밑 가랑이 메움(다리 뒤): 두 다리 뿌리 사이 아래로 둥근 바지 천(원화 바지 색 + 아래 둥근 끝 외곽선). 서 있을 땐 원화 골반·다리에 다 덮임
def hips_under(K=4):
    Hm = lab('hips'); lum = RA[..., :3].astype(int).mean(-1); sat = RA[..., :3].max(-1).astype(int) - RA[..., :3].min(-1)
    rgb_ = RA[..., :3].astype(int); pc = np.median(RA[Hm & (RA[..., 3] >= 250) & (lum >= 28) & (lum <= 95) & (rgb_[..., 2] - rgb_[..., 0] > 12)][:, :3], 0).astype(float)
    oc = np.median(RA[Hm & (RA[..., 3] >= 250) & (lum < 30)][:, :3], 0).astype(float)
    from PIL import ImageDraw as _D
    hx = sorted([LEG['near']['hip'][0], LEG['far']['hip'][0]]); hy = max(LEG['near']['hip'][1], LEG['far']['hip'][1])
    x0, x1, yt, yb = hx[0] - HU_W, hx[1] + HU_W, 366, hy + HU_D; rr = HU_R   # 위 끝은 허리띠 밑까지(허리띠가 상체를 따라 기울어 들려도 배경 안 보이게)
    def ss(fn):
        im = Image.new('L', (512 * K, 512 * K), 0); fn(_D.Draw(im)); return np.array(im.resize((512, 512), Image.BOX)).astype(float) / 255.0
    body = ss(lambda d: d.rounded_rectangle([x0 * K, yt * K, x1 * K, yb * K], radius=int(rr * K), fill=255))
    inner = ss(lambda d: d.rounded_rectangle([(x0 + 2) * K, yt * K, (x1 - 2) * K, (yb - 2) * K], radius=int(max(1, rr - 2) * K), fill=255))
    line = np.clip(body - inner, 0, 1) * (YY > yt + 6)
    shade = 1.0 - 0.18 * np.clip((YY - yt) / max(1.0, yb - yt), 0, 1)
    col = np.clip(pc[None, None, :] * shade[..., None], 0, 255); col = col * (1 - line[..., None]) + oc[None, None, :] * line[..., None]
    a = np.zeros_like(RA); a[..., :3] = col.astype(np.uint8); a[..., 3] = np.clip(body * 255, 0, 255).astype(np.uint8)
    print('  가랑이 메움 hipsU: x', x0, '~', x1, '· y', yt, '~', yb, '· 바지 색', pc.astype(int).tolist())
    return a
HU_D = float(os.environ.get('HU_D', 10)); HU_W = float(os.environ.get('HU_W', 22)); HU_R = float(os.environ.get('HU_R', 10))   # 다리 뿌리 아래로 몇 px · 뿌리 밖으로 몇 px · 모서리 반지름 — 허벅지 윗끝 둥근 끝 둘레가 배경 대신 바지 천
o_hipsU = save('hipsU', hips_under())
_pd = with_reveal('pauldN'); _pd[RIM] = RA[RIM]   # 밝은 테(머리에서 옮김)
_pd, _nu = underlay(_pd, lab('pauldN'), head_m | lab('pony'), r=3)   # 어깨갑 위 끝 밑 머리 3px(머리 밑에 그려져 대기엔 안 보임)
print('  어깨갑: 위 끝 밑 머리', _nu)
o_pd = save('pauldron', _pd)
print('  이음 밑 덧칠 px: 상체←머리·어깨갑', _n2, '· 골반←상체', _n3)
BACKB = {}
_PAR = {'head': ('head', NECK), 'torso': ('torso', HIP), 'hips': ('skirt', HIP), 'pauldN': ('pauldron', SH_N), 'pony': ('pony', PONY), 'scarf': ('tailA', None)}
for n, lst in BACK.items():
    assert n in _PAR, f'뒤 조각 부모 없음: {n}'
    a = np.zeros_like(RA)
    for IMG, m in lst: a = under(a, IMG, m)
    nm = {'hips': 'hips', 'pauldN': 'pauldron'}.get(n, _PAR[n][0]) + 'B'; save(nm, a); BACKB[nm] = _PAR[n]
print('  뒤 조각', {k: v[0] for k, v in BACKB.items()})
# ---------------- 팔: 원화 윗팔·팔뚝·주먹 — 윗팔 위 끝 = 어깨(어깨갑 밑) 둘레 원(반지름 12, 띠 색)으로 이음 ----------------
def upper_img(nm, lm, S, cover):
    a = front_with(nm, art(lm)); disk = (XX - S[0]) ** 2 + (YY - S[1]) ** 2 <= 12 ** 2
    hull = cv2.convexHull(np.stack(np.nonzero(dil(lm, 1) & (np.hypot(XX - S[0], YY - S[1]) < 26))[::-1], 1).astype(np.int32))
    hm = np.zeros((512, 512), np.uint8); cv2.fillConvexPoly(hm, hull, 1); fill = (disk | ((hm > 0) & cover)) & ~lm
    band = lm & (np.hypot(XX - S[0], YY - S[1]) < 30) & (RA[..., 3] > 200); col = np.median(RA[band][:, :3], 0)
    f = np.zeros_like(RA); f[fill, :3] = col.astype(np.uint8); f[fill, 3] = 255
    print(f'  {nm}: 어깨 밑 이음 {int((fill & (a[..., 3] < 250)).sum())} px (색 {col.astype(int).tolist()})')
    return under(a, f, fill)
# 팔꿈치: 라벨 경계가 토시 밑 테·팔꿈치 살을 가로질러 팔뚝이 돌면 잘린 면(톱니)이 보였음(첫 v1 .217) →
#   윗팔 = 어깨→팔꿈치 캡슐(반지름 16) + 팔꿈치 원(11) 안만, 그 밖 조각(토시 외곽선 갈고리)은 팔뚝으로 · 팔뚝 = 팔뚝 라벨 + 팔꿈치 원(10, 원화 팔꿈치 살) — 팔뚝이 위에 그려져 관절을 덮음
def capm(p, q, r):
    p, q = V(p), V(q); d = q - p; L2 = max(d @ d, 1e-9); t = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + t * d[0])) ** 2 + (YY - (p[1] + t * d[1])) ** 2 <= r * r
def elbow_split(up, fo, S, E):
    u_ = (E - S) / np.linalg.norm(E - S); keep = capm(S, E - 7 * u_, 16) | capm(E, E, 9); out = up & ~keep & (cv2.distanceTransform((~fo).astype(np.uint8), cv2.DIST_L2, 3) <= 14)
    return up & ~out, fo | out | (up & capm(E, E, 10)), int(out.sum())
UPN, FON, _m1 = elbow_split(lab('upperN'), lab('foreN'), SH_N, EL_N); UPF, FOF, _m2 = elbow_split(lab('upperF'), lab('foreF'), SH_F, EL_F)
print('  팔꿈치 나눔: 윗팔 → 팔뚝 옮김 px 가까운', _m1, '· 먼', _m2)
o_aU = save('armU', upper_img('upperN', UPN, SH_N, lab('pauldN')))
o_aF = save('armF', upper_img('upperF', UPF, SH_F, lab('torso')))
o_aL = save('armL', front_with('foreN', art(FON)))
o_fN = save('fistN', front_with('fistN', art(lab('fistN'))))
o_fF = save('foreF', art(FOF))
o_fiF = save('fistF', front_with('fistF', art(lab('fistF'))))
# ---------------- 다리: 서 있을 땐 원화 다리 통째(발목 핀), 달리면 시트 허벅지·정강이·부츠 ----------------
def sole_pts(m, ankle, ground=None):
    ys, xs = np.nonzero(m); xl, xr = xs.min(), xs.max(); bot = {x: ys[xs == x].max() for x in range(xl, xr + 1) if (xs == x).any()}
    xlow = max(bot, key=lambda x: bot[x]); cols_ = sorted(set([int(round(xl + (xr - xl) * f)) for f in (0.02, 0.2, 0.8, 0.98)] + [xlow]))
    lift = 0.0 if ground is None else float(ground - bot[xlow]); return [[float(x - ankle[0]), float(bot[x] - ankle[1] + lift)] for x in cols_ if x in bot]
o_lN = save('bootStandN', underlay(art(lab('legN')), lab('legN'), lab('hips'))[0]); o_lF = save('bootStandF', underlay(art(lab('legF')), lab('legF'), lab('hips'))[0])
BOOT_UP = float(os.environ.get('BOOT_UP', 0) or 0)
RUNLOCK = None if os.environ.get('RUNLOCK') == 'off' else 0.0   # 달리기 다리 그림(시트 정강이·부츠)이면 발목 고정 — 부츠 = 정강이와 한 줄(엔진 opt-in boot.runLock). DHL v1.1 검수: 달리기·달리다 공격 때 정강이 아래 끝이 부츠 목 옆으로 튀어나옴 · 무릎·골반 움직임으로 충분해 두 발목 모두 고정. 서 있는 원화 다리 그림은 원래 범위(대기 = 원화)   # 실험용 — 0 = 원화 발목 높이
def run_boot(nm, lm, sd):   # 발목 점 높이 = 원화 발목(부츠 목 가운데)~밑창 거리(가까운 31 · 먼 29) — v1 은 16 이라 부츠 목이 정강이 2/3 를 덮어 달릴 때 다리가 짧고 무릎판이 부츠 위에 붙어 보였음(DHL v1 검수)
    up = BOOT_UP or (SOLE - LEG[sd]['ankle'][1])
    b = sheet(nm); ys, xs = np.nonzero(b[..., 3] > 128); piv = (float(xs.min() + (xs.max() - xs.min()) * 0.32), ys.max() - up)
    Image.fromarray(b).save(os.path.join(PARTS, f'{nm}Run.png')); bot = {x: ys[xs == x].max() for x in range(xs.min(), xs.max() + 1) if (xs == x).any()}; xl, xr = min(bot), max(bot)
    return piv, [[round(float(x - piv[0]), 1), round(float(bot[x] - piv[1]), 1)] for x in sorted(set(int(round(xl + (xr - xl) * f)) for f in (0.03, 0.25, 0.5, 0.75, 0.97)))]
RB = {'near': run_boot('bootN', lab('legN'), 'near'), 'far': run_boot('bootF', lab('legF'), 'far')}
def limb_piece(nm, lm, top_pad, bot_pad, ref):
    p = sheet(nm); Image.fromarray(p).save(os.path.join(PARTS, nm + '.png'))   # 색 맞춤 안 함 — 원화 띠·무릎판·금 리벳이 섞여 허벅지가 청록으로 바뀜(첫 v1 달리기), 시트 색이 원화와 비슷
    ys, xs = np.nonzero(p[..., 3] > 128); cx = float((xs.min() + xs.max()) / 2); return {'part': nm, 'a': [round(cx, 1), float(ys.min() + top_pad)], 'b': [round(cx, 1), float(ys.max() - bot_pad)], 'w': 1.0}
_thR = (YY >= 386) & (YY <= 418); _shR = (YY >= 410) & (YY <= 460)
# 관절 점(a·b) = 둥근 끝 안쪽 몇 px — 허벅지 위 끝은 골반 밑, 아래 끝은 정강이 무릎판 밑으로 숨음. a-b ≈ 원화 뼈 길이(허벅지 44.4 · 정강이 48.1)라 엔진 배율 ≈ 2(시트 = 원화 1:1, 늘이지 않음 — 52번)
#   뼈 길이 = 두 다리 중 긴 쪽(먼 다리: 엉덩이→발목 94.3 이 평균 허벅지+정강이 92.5 보다 길어, 평균을 쓰면 대기에 골반이 3.2px 내려앉음 — idlediff20)
TH = {'near': limb_piece('thighN', lab('legN'), 27, 0, _thR), 'far': limb_piece('thighF', lab('legF'), 39, 0, _thR)}   # 아래 둥근 끝 = 무릎(b) — 허벅지가 무릎판 위쪽 반을 덮음(DHL 19:19 '무릎 보호대가 반만 보이면'), 위 끝은 골반 밑이라 크게 잡아 a-b ≈ 41   # 시트 허벅지가 골반 밑까지 길게 옴(68·80 / 선 40) — 둥근 끝 안쪽을 크게 잡아 a-b ≈ 42
SHN = {'near': limb_piece('shinN', lab('legN'), 10, 0, _shR), 'far': limb_piece('shinF', lab('legF'), 11, 0, _shR)}
# 굵기(DHL 19:01 '달릴 때 다리가 너무 얇음'): 시트 다리 굵기 × 길이 배율이 원화 다리보다 얇음(허벅지 26.5·23.6 · 정강이 19.9·25.2 / 원화 약 30 · 32~38 art px)
#   → 조각마다 굵기 배율 w = 목표 굵기 ÷ 지금 굵기(허벅지 30 · 정강이 32 art px) — 길이는 그대로(52번: 늘이지 않음은 길이 이야기, 굵기는 원화에 맞춤 — 13 v1.1 교훈)
LEG_W = {'thigh': float(os.environ.get('THIGH_W', 34)), 'shin': float(os.environ.get('SHIN_W', 36))}   # DHL 19:10 '살짝 더 두껍게' — 30·32 → 34·36
# 무릎 보호대 조각(DHL 19:30 '달리는 양쪽 무릎에 딱 표시한 대로' — 원화 먼 무릎: 은색 무릎판 + 금 리벳 + 아래 갈색 끈 + 크림 감기 윗단) — 원화 그대로 오려 달릴 때 두 무릎 위에(엔진 opt-in kneeImg)
def knee_piece():
    lum = RA[..., :3].astype(int).mean(-1); rgb = RA[..., :3].astype(int); navy = (rgb[..., 2] - rgb[..., 0] > 12) & (lum > 28) & (lum < 95)
    reg = (XX >= 286) & (XX <= 328) & (YY >= 396) & (YY <= 441) & lab('legF') & (RA[..., 3] > 0)
    core = reg & ~navy
    nc, cc = cv2.connectedComponents(core.astype(np.uint8), 8); k = np.zeros_like(core)
    for i_ in range(1, nc):
        if (cc == i_).sum() >= 25: k |= cc == i_
    k = cv2.morphologyEx(k.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
    k |= dil(k, 2) & reg & (lum < 45)                                         # 둘레 외곽선
    a = art(k); print('  무릎 보호대 조각 knee:', int(k.sum()), 'px'); return a
o_knee = save('knee', knee_piece())
L_TH = float(max(np.linalg.norm(LEG[s]['knee'] - LEG[s]['hip']) for s in LEG)); L_SH = float(max(np.linalg.norm(LEG[s]['ankle'] - LEG[s]['knee']) for s in LEG))
def _setw(img, bone, kind):
    p = np.array(Image.open(os.path.join(PARTS, img['part'] + '.png')))[..., 3] > 128; ab = float(np.hypot(*(np.subtract(img['b'], img['a']))))
    mid = int(p[int((img['a'][1] + img['b'][1]) / 2)].sum()); now = mid * (SC * bone / ab) / SC; img['w'] = round(LEG_W[kind] / max(1.0, now), 3); return round(now, 1), img['w']
print('  달리는 다리 굵기(원화 px, 지금 → w)', {f'{k}_{sd}': _setw(d[sd], L, k) for k, d, L in (('thigh', TH, L_TH), ('shin', SHN, L_SH)) for sd in ('near', 'far')})
print('  leg lengths thigh', round(L_TH, 1), 'shin', round(L_SH, 1), '· sheet a-b', {k: round(float(np.hypot(*(np.subtract(v['b'], v['a'])))), 1) for k, v in {**{f'th_{s}': TH[s] for s in TH}, **{f'sh_{s}': SHN[s] for s in SHN}}.items()})
# ---------------- 표정·깜빡임: 시트 머리 → 원화 머리 자리(SIFT), 무표정과 다른 곳 + 5px 만 ----------------
sift = cv2.SIFT_create()
def gray(a): al = a[..., 3:4] / 255.0; return cv2.cvtColor((a[..., :3] * al + 128 * (1 - al)).astype(np.uint8), cv2.COLOR_RGB2GRAY)
def up(a, k): return cv2.resize(a, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
kA, dA = sift.detectAndCompute(up(gray(RA), 2), (up((head_m * 255).astype(np.uint8), 2) > 0).astype(np.uint8) * 255)
neu_s = sheet('face_neutral'); kS, dS = sift.detectAndCompute(up(gray(neu_s), 2), (up(neu_s[..., 3], 2) > 20).astype(np.uint8) * 255)
mt = cv2.BFMatcher().knnMatch(dS, dA, k=2); good = [a for a, b in mt if a.distance < .75 * b.distance]
MF, inl = cv2.estimateAffinePartial2D(np.float32([kS[a.queryIdx].pt for a in good]) / 2, np.float32([kA[a.trainIdx].pt for a in good]) / 2, ransacReprojThreshold=2.0)
print('  face SIFT', int(inl.sum()), 'scale', round(float(np.hypot(MF[0, 0], MF[1, 0])), 4), 'rot', round(math.degrees(math.atan2(MF[1, 0], MF[0, 0])), 2))
FACE_N = ['happy', 'angry', 'focus', 'shout', 'effort']; BLINK_N = ['half', 'closed']
SRCF = {'happy': 'face_happy', 'angry': 'face_angry', 'focus': 'face_focus', 'shout': 'face_shout', 'effort': 'face_effort', 'half': 'blink_half', 'closed': 'blink_closed'}
neu = neu_s.astype(np.int16); U_ = np.zeros(neu.shape[:2], bool)
for n in FACE_N + BLINK_N:
    s_ = sheet(SRCF[n]).astype(np.int16)
    if s_.shape != neu.shape: s_ = cv2.resize(s_.astype(np.uint8), (neu.shape[1], neu.shape[0]), interpolation=cv2.INTER_AREA).astype(np.int16)
    U_ |= np.abs(s_ - neu).max(2) > 40
reg = cv2.dilate(U_.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
# 시트 머리 9장은 머리카락 결이 장마다 조금씩 달라(다시 그린 그림) 다른 곳 전체를 붙이면 머리숱까지 바뀜 → 눈·눈썹·안경·입 둘레 타원 안만
FACE_EL = (((XX - 289) / 38.0) ** 2 + ((YY - 280) / 22.0) ** 2) <= 1   # 눈·눈썹 둘레(복면 위)
face = (cv2.warpAffine(reg, MF, (512, 512), flags=cv2.INTER_NEAREST) > 0) & head_m & FACE_EL
fm = np.clip(cv2.GaussianBlur(cv2.erode(face.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (5, 5), 1.0) * 1.15, 0, 1)
hb = np.array(Image.open(os.path.join(PARTS, 'head.png'))); hx0, hy0 = OFF['head']; hh, hw = hb.shape[:2]
wn = cv2.warpAffine(neu_s, MF, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)).astype(np.float32); cm = face & (wn[..., 3] > 200) & (RA[..., 3] > 200)
CA = [(RA[..., c][cm].astype(np.float32).std() / max(1.0, wn[..., c][cm].std()), 0.0) for c in range(3)]
CA = [(a, float(RA[..., c][cm].mean() - a * wn[..., c][cm].mean())) for c, (a, _) in enumerate(CA)]
FACE_FIT = {}
for n in FACE_N + BLINK_N:
    sp = sheet(SRCF[n])
    # 표정마다 시트 자리가 1~2px 다름(check_sheet20 — 외침 회전 +2.8°) → 무표정 변환 MF 에 그 표정 ↔ 무표정 SIFT 를 곱함
    k2, d2 = sift.detectAndCompute(up(gray(sp), 2), (up(sp[..., 3], 2) > 20).astype(np.uint8) * 255)
    mm = [a for a, b in cv2.BFMatcher().knnMatch(d2, dS, k=2) if a.distance < .7 * b.distance]
    Mrel = None
    if len(mm) >= 12:
        Mrel, inr = cv2.estimateAffinePartial2D(np.float32([k2[a.queryIdx].pt for a in mm]) / 2, np.float32([kS[a.trainIdx].pt for a in mm]) / 2, ransacReprojThreshold=1.5)
    Mn = MF if Mrel is None else (np.vstack([MF, [0, 0, 1]]) @ np.vstack([Mrel, [0, 0, 1]]))[:2]
    FACE_FIT[n] = None if Mrel is None else [round(float(np.hypot(Mrel[0, 0], Mrel[1, 0])), 4), round(float(Mrel[0, 2]), 1), round(float(Mrel[1, 2]), 1)]
    wf = cv2.warpAffine(sp, Mn, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)).astype(np.float32)
    for c in range(3): wf[..., c] = np.clip(wf[..., c] * CA[c][0] + CA[c][1], 0, 255)
    al = fm * (wf[..., 3] / 255.0); o_ = np.zeros((512, 512, 4), np.float32); o_[hy0:hy0 + hh, hx0:hx0 + hw] = hb
    o_[..., :3] = o_[..., :3] * (1 - al[..., None]) + wf[..., :3] * al[..., None]
    fc = o_[hy0:hy0 + hh, hx0:hx0 + hw].astype(np.uint8); fc[..., 3] = hb[..., 3]
    Image.fromarray(fc).save(os.path.join(PARTS, f'face_{n}.png'))
print('  face patch px', int(face.sum()), 'colour fit', [(round(a, 3), round(b, 1)) for a, b in CA], 'per-face fit', FACE_FIT)
# ---------------- 뼈·조각 ----------------
def piv(name, p): o = np.array(OFF[name], float); q = np.array(p, float) - o; return [round(float(q[0]), 1), round(float(q[1]), 1)]
parts = {}
def P_(name, at, **kw): parts[name] = dict({'src': f'parts/{name}.png', 'pivot': piv(name, at), 'scale': SC}, **kw)
P_('knee', LEG['far']['knee']); P_('torso', HIP); P_('hips', HIP); P_('belt', HIP); P_('hipsU', HIP); P_('head', NECK); P_('pauldron', SH_N); P_('pony', PONY); P_('tailA', SCARF_ROOT, mesh={'cols': 8, 'rows': 2})
for _nm, (_par, _pt) in BACKB.items(): P_(_nm, _pt if _pt is not None else SCARF_ROOT)
P_('armU', SH_N, elbow=piv('armU', EL_N)); P_('armF', SH_F, elbow=piv('armF', EL_F))
P_('armL', EL_N, fist=piv('armL', FI_N)); P_('fistN', FI_N); P_('axeN', FI_N)
P_('foreF', EL_F); P_('fistF', WR_F)
parts['weapon'] = {'src': 'parts/weapon.png', 'pivot': [round(float(W_PIV[0]), 1), round(float(W_PIV[1]), 1)], 'scale': SC / UPS,
                   'tip': [round(float(W_TIP[0]), 1), round(float(W_TIP[1]), 1)], 'tips': [[round(float(W_TIP[0]) - 100, 1), round(float(W_TIP[1]) + 100, 1)], [round(float(W_TIP[0]) + 100, 1), round(float(W_TIP[1]) + 100, 1)]],
                   'guard': [round(float(W_HEAD[0]), 1), round(float(W_HEAD[1]) + 110, 1)], 'pommel': [round(float(W_POM[0]), 1), round(float(W_POM[1]), 1)]}
for n in FACE_N + BLINK_N: parts[f'face_{n}'] = {'src': f'parts/face_{n}.png', 'pivot': parts['head']['pivot'], 'scale': SC}
for nm, sd in [('bootStandN', 'near'), ('bootStandF', 'far')]: P_(nm, LEG[sd]['ankle'])
for _sd, _nm in (('near', 'bootNRun'), ('far', 'bootFRun')): parts[_nm] = {'src': f'parts/{_nm}.png', 'pivot': [round(RB[_sd][0][0], 1), round(RB[_sd][0][1], 1)], 'scale': SC}
for nm in ('thighN', 'thighF', 'shinN', 'shinF'): parts[nm] = {'src': f'parts/{nm}.png', 'pivot': [0, 0], 'scale': 1}
WEAPON_ANG = math.atan2(UF[1], UF[0]) + math.pi / 2
ARML_REST = 0.3   # 엔진이 서 있을 때 자유 팔뚝을 −0.3 rad 굽힘 → 뼈 rot +0.3(그 자식 철퇴·주먹도) → 대기 = 원화(10 과 같음)
world = {'root': (O, 0.0), 'hip': (HIP, 0.0), 'skirt': (HIP, 0.0), 'cape': (NECK, 0.0), 'scarf': (NECK, 0.0), 'pouch': (HIP, 0.0), 'pauldron': (SH_N, 0.0), 'pauldronF': (SH_F, 0.0), 'torso': (HIP, 0.0), 'head': (NECK, 0.0),
         'armU': (SH_N, 0.0), 'armL': (EL_N, ARML_REST), 'axeN': (FI_N, ARML_REST), 'fistN': (FI_N, ARML_REST), 'pony': (PONY, 0.0), 'tailA': (SCARF_ROOT, 0.0),
         'armF': (SH_F, 0.0), 'foreF': (EL_F, 0.0), 'fistF': (WR_F, 0.0), 'weapon': (FI_F, WEAPON_ANG), 'foreFb': (WR_F, 0.0), 'belt': (HIP, 0.0), 'hipsU': (HIP, 0.0)}
for _nm, (_par, _pt) in BACKB.items(): world[_nm] = (_pt if _pt is not None else SCARF_ROOT, 0.0)
BONES = [('root', None), ('hip', 'root'), ('skirt', 'hip'), ('torso', 'hip'), ('head', 'torso'), ('pony', 'head'), ('tailA', 'torso'), ('armF', 'torso'), ('foreF', 'armF'), ('fistF', 'foreF'), ('weapon', 'fistF'),
         ('armU', 'torso'), ('armL', 'armU'), ('axeN', 'armL'), ('fistN', 'armL'), ('foreFb', 'torso'),
         ('cape', 'torso'), ('scarf', 'torso'), ('pouch', 'hip'), ('pauldron', 'torso'), ('pauldronF', 'torso'), ('belt', 'torso'), ('hipsU', 'skirt')]
BONES += [(_nm, _par) for _nm, (_par, _pt) in BACKB.items()]
WANG = {'armL': ARML_REST, 'axeN': ARML_REST, 'fistN': ARML_REST, 'weapon': WEAPON_ANG}
bones = []
for name, parent in BONES:
    if parent is None: bones.append({'name': 'root', 'parent': None, 'pos': [0, 0]}); continue
    pw_, pa, cw_, ca = world[parent][0], WANG.get(parent, 0.0), world[name][0], WANG.get(name, 0.0)
    if parent == 'armL': pa, ca = 0.0, 0.0
    dv = (cw_ - pw_) * SC; c, s = math.cos(-pa), math.sin(-pa)
    b = {'name': name, 'parent': parent, 'pos': [round(c * dv[0] - s * dv[1], 1), round(s * dv[0] + c * dv[1], 1)]}
    if abs(ca - pa) > 1e-4: b['rot'] = round(ca - pa, 4)
    if name in parts: b['part'] = name
    if name == 'skirt': b['part'] = 'hips'   # 서 있을 땐 원화 골반(허리띠 + 바지 윗부분)
    bones.append(b)
# ---------------- 다리 정의(10 v1.1 구조: x = 서 있는 발 자리 · hipX = 다리 뿌리 · runX = 달리는 줄) ----------------
THIGH_FIRST = os.environ.get('THIGH_FIRST', '0') == '1'   # DHL 19:10 '무릎 보호대를 달릴 때도' — 허벅지를 먼저 그려 정강이 위 끝 은색 무릎판이 허벅지 아래 둥근 끝 위로(엔진 opt-in legs.thighFirst)
_kL = LEG['far']; _at = math.atan2(*(_kL['knee'] - _kL['hip'])[::-1]); _as = math.atan2(*(_kL['ankle'] - _kL['knee'])[::-1])
KNEE_ROT = -(_at + ((_as - _at + math.pi) % (2 * math.pi) - math.pi) * .5 - math.pi / 2)   # 원화 무릎 그림의 다리 축 기울기만큼 되돌림(엔진은 허벅지·정강이 가운데 각으로 돌림)
KNEE_IMG = {'part': 'knee', 'mix': .5, 'rot': round(KNEE_ROT, 4)}
legs = {'hip': [0, round(SC * (float(np.mean([LEG[s]['hip'][1] for s in LEG])) - HIP[1]), 1)], 'thigh': round(SC * L_TH, 1), 'shin': round(SC * L_SH, 1),
        'thighImg': TH['near'], 'shinImg': SHN['near'], 'kneeImg': KNEE_IMG, 'boot': {'part': 'bootNRun', 'sole': RB['near'][1], 'ankleRange': [-1.2, 1.4], **({} if RUNLOCK is None else {'runLock': RUNLOCK})}, **({'thighFirst': True} if THIGH_FIRST else {})}
for sd, nm, lm in [('near', 'bootStandN', lab('legN')), ('far', 'bootStandF', lab('legF'))]:
    hide = {'part': TH[sd]['part'], 'a': TH[sd]['a'], 'b': TH[sd]['b'], 'w': 0.001}
    _root = round(SC * (LEG[sd]['hip'][0] - HIP[0]), 1); _rest = round(SC * (LEG[sd]['ankle'][0] - HIP[0]), 1)
    legs[sd] = {'x': _rest, 'hipX': _root, 'runX': _root, 'shade': 0, 'thighImg': TH[sd], 'shinImg': SHN[sd], 'runBoot': 'bootNRun' if sd == 'near' else 'bootFRun',
                'stand': {'fade': [0.05, 0.1], 'thighImg': hide, 'shinImg': dict(hide, part=SHN[sd]['part'], a=SHN[sd]['a'], b=SHN[sd]['b']), 'boot': {'part': nm, 'sole': sole_pts(lm, LEG[sd]['ankle'], SOLE)}}}
idle = {sd: legs[sd]['x'] for sd in ('near', 'far')}
# ---------------- 그리는 순서(뒤 → 앞): 다리 · 뒤 조각 · 먼 윗팔·팔뚝 · 골반 · 상체 · 가까운 윗팔 · 어깨갑 · 먼 철퇴·주먹 · 머리 · 가까운 철퇴 · 팔뚝 · 주먹 ----------------
draw = ['pony', 'tailA', 'hipsU', 'legFar', 'legNear'] + list(BACKB) + DRAW_IDLE[4:]   # hipsU = 다리 뒤 가랑이 메움
draw.insert(draw.index('skirt') + 1, 'belt')   # 허리띠 = 바지 앞 · 상체 뒤(상체와 한 몸)
rig = {'name': 'bruno-sky', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': parts, 'bones': bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': {n: f'face_{n}' for n in FACE_N},
       'blinkFaces': {'half': 'face_half', 'closed': 'face_closed'},
       'gait': {'stance': 0.26, 'strideBase': 40, 'strideK': 0.12, 'hipBase': 6, 'bob': 8, 'lean': 0.1, 'headBob': 3, 'kneeLift': 0.7, 'heelKick': 0.5, 'dropCap': 16,   # 10 러스트 · 20 네온 브루노와 같은 걸음
                'swingReach': 0.05, 'landAng': -0.04, 'elbowRun': 0.12, 'armSwing': 0.06, 'armBias': 0.0, 'headRun': 0.05},
       'carrySwing': 0.15, 'wristRange': 0.2, 'dropLift': 8, 'ponySway': 0.8, 'bounce': [],
       'streamers': [{'bone': 'tailA', 'part': 'tailA', 'len': round(float(2 * (_sx.max() - _sx.min())), 1), 'amp': 7, 'freq': 6.2, 'phase': 0, 'droop': 0.0, 'sag': 4, 'wind': 0.6, 'lag': 0.4}],
       'metrics': {'bodyHeight': round(2 * (SOLE - M['hairTop'][1])), 'note': f"rig units; 포니테일 위(y{M['hairTop'][1]})~발바닥({SOLE:.0f}) ×2, 도끼 제외"},
       'ui': {'attack': 'smash', 'touch': 'hop'}, 'standSwap': [['skirt', 'hipsU']]}   # 서 있는 원화 다리 그림이면 바지(hips)·원화 상체, 달리기 다리면 가랑이 메움(hipsU)·torsoAtk (허리띠는 늘, 공격 중 상체는 tPiece torsoAtk)
# ---------------- 공격: 번갈아 내려찍기(tools/plan_alt20.py 키 그대로) ----------------
fo_off = np.array(OFF['foreF'], float); fi_off = np.array(OFF['fistF'], float)
ipt = lambda off, p: [round(float(p[0] - off[0]), 1), round(float(p[1] - off[1]), 1)]
ud = (EL_F - WR_F) / np.linalg.norm(EL_F - WR_F)
parts['gF'] = {'src': 'parts/fistF.png', 'pivot': ipt(fi_off, WR_F), 'grip': ipt(fi_off, FI_F), 'elbow': ipt(fi_off, WR_F), 'wrist': ipt(fi_off, WR_F), 'scale': SC,
               'shaftDir': [round(float(UF[0]), 4), round(float(UF[1]), 4)], 'fore': 'foreFa', 'foreBone': 'foreFb', 'foreDir': [round(float(ud[0]), 4), round(float(ud[1]), 4)]}
parts['foreFa'] = {'src': 'parts/foreF.png', 'pivot': ipt(fo_off, WR_F), 'elbow': ipt(fo_off, EL_F), 'scale': SC}
rig['swordGrip'] = {'tipDepth': 6, 'near': {'upper': 'armF', 'carry': 'gF', 'pieces': []}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': 0}, 'stretchMax': 1.05, 'shoulderPush': 0}
rig['drawA'] = ['pony', 'tailA', 'hipsU', 'legFar', 'legNear'] + list(BACKB) + ['armF', 'foreFb', 'skirt', 'belt', 'torso', 'armU', 'pauldron', 'weapon', 'foreF', 'head', 'axeN', 'armL', 'fistN']
# 2타(먼 도끼) 구간 = 먼 도끼·먼 주먹이 몸(골반·허리띠·상체·어깨) 뒤 — DHL 19:19 '2번째 공격하는 도끼와 손이 몸 뒤로'. 다리 앞·머리 뒤는 그대로. 바뀌는 시각 = 겹침이 가장 적은 때(ORDER_T)
rig['drawB'] = ['pony', 'tailA', 'hipsU', 'legFar', 'legNear'] + list(BACKB) + ['armF', 'foreFb', 'weapon', 'foreF', 'skirt', 'belt', 'torso', 'armU', 'pauldron', 'head', 'axeN', 'armL', 'fistN']
ORDER_T = [float(x) for x in os.environ.get('ORDER_T', '0.30,0.90').split(',')]
E = PLAN['engine']
trk = lambda f: [[e[0], round(f(e), 4), 'io'] for e in E]
HIPY_K = float(os.environ.get('HIPY_K', 0))   # 공격 골반 내림 배율 — 0: 골반(허리띠·바지) 높이 고정(DHL 12:16 — 서 있는 원화 다리는 발목에 고정된 한 장이라 골반이 12px 내려앉으면 바지 아래 끝이 다리 위로 미끄러져 잔상). 철퇴 쥔 자리(gy)는 골반 기준이라 몸과 같이 그대로
act = {'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': 1.0, 'hitAt': PLAN['summary']['hits'][0], 'hitStop': 0.05, 'cancelAt': 0.8,
       'w': [[0, 1]], 'reach': [[0, 0]], 'nPiece': [[0, 'gF']], 'nUpper': [[0, 'armF']], 'armIK': [[0, 1]], 'ikSideK': {'N': [[0, 1]]},
      
       'gx': trk(lambda e: SC * e[1]), 'gy': trk(lambda e: SC * (e[2] - e[5])), 'sa': trk(lambda e: math.radians(e[3])),
       'lean': trk(lambda e: e[4]), 'hipY': trk(lambda e: SC * e[5] * HIPY_K),
       'head': [[0, 0], [0.1, -0.05, 'io'], [0.28, 0.06, 'io'], [0.4, -0.03, 'io'], [0.54, 0.07, 'io'], [0.8, 0]],
       'freeArm': True, 'fuA': trk(lambda e: e[6]), 'flA': trk(lambda e: e[7]),
       'face': [[0, 'angry'], [0.24, 'shout'], [0.38, 'angry'], [0.5, 'shout'], [0.7, 'focus'], [0.9, None]],   # 공격 중 눈 뜸(10 DHL 23:57 — 같은 인물), 시트 표정 6장 모두 눈 뜸
       'order': [[0, 'drawA'], [ORDER_T[0], 'drawB'], [ORDER_T[1], 'drawA']],
       'nearLift': [[0, 0], [0.03, 0, 'io'], [0.09, 10, 'io'], [0.15, 0]], 'farLift': [[0, 0], [0.17, 0, 'io'], [0.23, 10, 'io'], [0.29, 0]],
       'aDamp': 9, 'standStep': True}
rig['actions'] = {'smash': act}
rig['cutHold'] = 0.1   # (20 값 — 게임 넣을 때 30 으로 다시 잼) 20: 스킬 컷인 멈춤(10-21 게임 넣기): 후보 .10·.17·.20·.28 을 게임 컷인(PC 1440×900, 혼자·7 루시아와 둘)으로 잼(cutpair) — 리그 맨 위 .10 혼자 칸 안 7px · 둘 −1 / .17 −9·−19 / .20 −1·−11 / .28 −5·−13 → .10 예비(가까운 철퇴를 뒤로 젖히고 먼 철퇴 듦 — 두 철퇴 V 자)
_a = np.array(Image.open(os.path.join(HERE, '..', '..', '..', 'art', 'characters', 'char_0030.png')).convert('RGBA').resize((160, 160), Image.BOX))[..., 3]
_ys, _xs = np.nonzero(_a > 40); FIT_CX = round(float(((_xs.min() + _xs.max() + 1) / 2 + _xs.mean() + .5) / 2 / 160 * 512), 1)
rig['gameRef'] = {'refOrigin': [round(float(O[0] - (HIP[0] - FIT_CX)), 1), float(O[1])], 'refScale': 2.0, 'refLift': 0,
                  'note': f'게임 그림 char_0030.png(512) = 0번 합격 원화(ref512, DHL 10-21 17:44). x = 도감 칸(fitArt 중심 {FIT_CX}, index.html measureBox 와 같은 계산)에서 골반(hip x {HIP[0]:.0f})이 가운데'}
rig['note'] = '30 스카이 브루노 v1(대기·달리기·번갈아 내려찍기). 20 네온 브루노 v2.1 구조 + 포니테일(pony)·스카프 꼬리(streamers). 조각 = 원화를 부품별로 나눔(seg30.py) + 가려진 곳 = 팔·도끼만 지운 원화(프롬프트 2·3: sheets/nonear_1806·nofar_1819), 시트 = 표정·깜빡임·포니테일·스카프·달리는 다리·부츠·도끼 자루 끝'
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(PARTS)): _h.update(fn.encode()); _h.update(open(os.path.join(PARTS, fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_bruno30.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};window.MR_RIG_DEFS['bruno-sky']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(parts), 'parts, version', rig['version'], 'idle', idle, 'legs', legs['thigh'], legs['shin'], 'hip', legs['hip'], 'FIT_CX', FIT_CX)
