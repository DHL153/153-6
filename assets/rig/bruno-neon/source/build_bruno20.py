"""20 네온 브루노 리그 조립 v2.1(달리기 부츠 발목 점 = 원화 발목 높이 · 달리기 다리일 때 발목 고정 boot.runLock · 골반 아래 끝 다듬기 · 허리띠 belt = 상체와 한 몸 · 그 밑 = 서 있을 땐 바지 hips(허리띠 밑 바지 천 채움), 달릴 땐 시트 허벅지 + 다리 뒤 가랑이 메움 hipsU(standSwap, 치마 없앰) · 공격 골반 높이 고정 · 달리기·공격 상체 torsoAtk(standSwap + 공격 tPiece) · 어깨갑 왼쪽 위 다듬기) — 10 러스트 브루노 v1.2(build_bruno10) 구조, 공격 = 번갈아 내려찍기(tools/plan_alt20.py)
입력: ref512.png(0번 합격 원화 = 게임 char_0020) · sheets/nonear_0614.png·nofar_0623.png(팔·철퇴만 지운 원화) · work/labels.npy(seg20.py) · pieces/(조각 시트 19칸, cut20.py) · measure20.json · review/plan_alt20.json
출력: ../rig.json · ../rig.def.js · ../parts/*.png
실행: cd source && python3 -I cut20.py && python3 -I seg20.py && python3 -I tools/plan_alt20.py && python3 -I build_bruno20.py
원칙(DHL): 대기 = 원화 · 철퇴 크기 그대로 · 팔다리 길이 고정 · 팔꿈치(팔뚝)가 어깨(윗팔)보다 앞 · 먼 팔은 몸 뒤, 주먹·철퇴만 앞 · 공격 중 눈 뜸
10 과 다른 곳: 포니테일 없음 · 가까운 윗팔 = 원화 맨살 팔(상체 앞, 어깨갑 pauldron 조각 밑) — 위 끝은 어깨갑 밑 둥근 원(어느 각에서도 덮임) · 먼 윗팔도 원화(상체 뒤, 먼 어깨갑 밑)
          철퇴 주먹 밑·아래 자루 끝 = 시트 13번 철퇴(원화 공에 맞춘 축·배율) · 표정 happy = 시트 5번 · angry = 4번(시트에서 웃는 입이 5번에 옴)
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
M = json.load(open(os.path.join(HERE, 'measure20.json'))); PLAN = json.load(open(os.path.join(HERE, 'review', 'plan_alt20.json')))
YY, XX = np.mgrid[0:512, 0:512]
V = lambda p: np.array(p, float)
def desp(a):
    a = a.astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None); a[..., 0] -= m; a[..., 2] -= m; return np.clip(a, 0, 255).astype(np.uint8)
def sheet(n): return desp(np.array(Image.open(os.path.join(PC, n + '.png')).convert('RGBA')))
def art(mask): a = RA.copy(); a[..., 3] = np.where(mask, a[..., 3], 0); return a
def dil(m, r): return cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
# ---------------- 골반 아래 끝 다듬기 (DHL v1.2 검수: 달릴 때 골반 아래가 덜 잘림) ----------------
#   골반 라벨 아래 끝이 가까운 무릎판 테 윗부분(회색 + 밝은 윗가장자리)과 먼 허리 금빛 병 윗부분을 가로질러, 달리면 골반에 회색 쐐기·밝은 점선·금 줄이 남았음
#   ① 가까운 무릎판 테: 골반 라벨의 회색(밝기 ≥ 80 · 채도 < 30, x < 240 · y ≥ 388) → 가까운 다리, 그 칸 아래(테 윗선 밑)도 다리로 — 테 윗선 위 어두운 외곽선은 골반에 남아 골반 아래 끝 선이 됨
#   ② 먼 허리 금빛 병(허리띠에 달린 것): 금빛 덩어리 + 둘레 어두운 외곽선 → 골반 통째(달리면 허리에 매달림)
def _fix_hips():
    lum = RA[..., :3].astype(int).mean(-1); sat = RA[..., :3].max(-1).astype(int) - RA[..., :3].min(-1); H, N_, F_ = LID['hips'], LID['legN'], LID['legF']
    g = (LAB == H) & (lum >= 80) & (sat < 30) & (XX < 240) & (YY >= 388) & (RA[..., 3] > 128)
    n1 = int(g.sum()); LAB[g] = N_; n2 = 0
    for x in range(180, 240):
        ys_ = np.nonzero(g[:, x])[0]
        if len(ys_): col = (LAB[:, x] == H) & (np.arange(512) > ys_.min()); n2 += int(col.sum()); LAB[col, x] = N_
    gold = (RA[..., 0] > 140) & (RA[..., 1] > 60) & (RA[..., 2] < 70) & (RA[..., 0].astype(int) - RA[..., 2] > 100) & (XX >= 278) & (XX <= 310) & (YY >= 378) & (YY <= 412)
    nc, cc = cv2.connectedComponents(gold.astype(np.uint8), 8); big = np.zeros_like(gold)
    for i in range(1, nc):
        if (cc == i).sum() >= 30: big |= cc == i
    vial = (big | (dil(big, 2) & (lum < 60))) & ((LAB == F_) | (LAB == H)); n3 = int((vial & (LAB != H)).sum()); LAB[vial] = H
    # ③ 골반 아래 끝 = 정한 선 c(x)(그 위 = 골반, 아래 = 다리): 가까운 쪽은 무릎판 테 윗선(원화 외곽선이 골반 아래 끝 선) · 가랑이는 원화 실루엣 아래 끝(가랑이 V 외곽선까지) ·
    #    그 사이(가까운 테 오른쪽 ~ 가랑이, 가랑이 ~ 먼 허벅지)는 곧은 선 — 바지를 가로지르는 곳이라 2줄 옅게(달리면 시트 허벅지 위에 부드럽게)
    op = RA[..., 3] >= 128; gr = (lum >= 80) & (sat < 30) & (RA[..., 3] > 200)
    def gtop(x): ys_ = np.nonzero(gr[386:410, x])[0]; return 386 + int(ys_.min()) if len(ys_) else None
    def sil(x): ys_ = np.nonzero(~op[390:425, x])[0]; return 390 + int(ys_.min()) if len(ys_) else None
    c = {}
    for x in range(190, 200): c[x] = 396
    for x in range(200, 232): g_ = gtop(x); c[x] = g_ if g_ is not None and g_ < 402 else 398
    for x in range(232, 246): c[x] = 398 + (x - 232) * (405 - 398) / 14.0
    for x in range(246, 259): c[x] = float(min(sil(x) or 405, 405))   # 가랑이 V 꼭짓점 외곽선까지만(V 팔 외곽선은 다리)
    for x in range(259, 285): c[x] = 406 + (x - 259) * (391 - 406) / 25.0
    n4 = n5 = 0; col = np.arange(512)
    for x, v in c.items():
        yb = int(np.ceil(v)) - 1   # yb 까지 골반
        dn = (LAB[:, x] == H) & (col > yb) & (col <= 415); LAB[dn, x] = N_ if x < 252 else F_; n4 += int(dn.sum())
        up = ((LAB[:, x] == N_) | (LAB[:, x] == F_)) & (col <= yb) & (col >= 372) & ~gr[:, x] & (RA[:, x, 3] > 0); LAB[up, x] = H; n5 += int(up.sum())
        if 232 <= x < 246 or 259 <= x < 285: CUT[x] = yb
    # ④ 골반 아래쪽(y ≥ 388)의 가는 외곽선 꼬리(폭 ≤ 2px — 테 왼쪽 끝·가랑이 V 팔·먼 허벅지 바깥 선 토막) → 다리
    Hm = (LAB == H).astype(np.uint8); opn = cv2.morphologyEx(Hm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
    tail = (LAB == H) & ~opn & (YY >= 388) & (XX >= 186) & (XX <= 312) & ~(dil(big, 1))
    tail |= (LAB == H) & (XX <= 203) & (YY >= 393) & (YY <= 402)   # 쌈지 왼쪽 아래 = 무릎판 테 왼쪽 모서리 윗선(달리면 쌈지 밑 갈고리)
    n6 = int(tail.sum()); LAB[tail & (XX < 252)] = N_; LAB[tail & (XX >= 252)] = F_
    for x in list(CUT):
        ys_ = np.nonzero(LAB[:, x] == H)[0]; ys_ = ys_[ys_ >= 380]
        if len(ys_): CUT[x] = int(ys_.max())
        else: CUT.pop(x)
    print('  골반 다듬기: 무릎판 테 회색 → 다리', n1, '· 테 밑 칸', n2, '· 금빛 병 → 골반', n3, '· 아래 끝 선 골반→다리', n4, '다리→골반', n5, '· 가는 꼬리 → 다리', n6, '· 옅게 열', len(CUT))
CUT = {}
_fix_hips()
OFF = {}
def despeck(a, minpx=14):   # 조각에서 떨어진 작은 점(라벨 경계에 남은 외곽선 부스러기) 지움
    n, cc, st, _ = cv2.connectedComponentsWithStats((a[..., 3] > 0).astype(np.uint8), 8); a = a.copy()
    for i in range(1, n):
        if st[i, 4] < minpx: a[cc == i] = 0
    return a
def save(name, a, pad=2):
    if name in ('head', 'torso', 'torsoAtk', 'hips', 'pauldron', 'headB', 'torsoB', 'pauldronB', 'hipsB', 'armU', 'armF', 'armL', 'foreF'):
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
SH_N, EL_N, WR_N, FI_N, BL_N = V(N_['SH']), V(N_['EL']), V(N_['WR']), V(N_['fist']), V(N_['ball'])
SH_F, EL_F, WR_F, FI_F, BL_F = V(F_['SH']), V(F_['EL']), V(F_['WR']), V(F_['fist']), V(F_['ball'])
UN = (BL_N - FI_N) / np.linalg.norm(BL_N - FI_N); UF = (BL_F - FI_F) / np.linalg.norm(BL_F - FI_F)
SC = 2.0
# ---------------- 가려진 곳 = '팔·철퇴만 지운 원화'(프롬프트 2·3) — 10 v1.1 과 같은 reveal ----------------
DRAW_IDLE = ['legFar', 'legNear', 'armF', 'foreF', 'skirt', 'torso', 'armU', 'pauldron', 'weapon', 'fistF', 'head', 'maceN', 'armL', 'fistN']
BONE_OF = {'head': 'head', 'torso': 'torso', 'hips': 'skirt', 'legN': 'legNear', 'legF': 'legFar', 'pauldN': 'pauldron', 'upperN': 'armU', 'foreN': 'armL', 'fistN': 'fistN',
           'maceN': 'maceN', 'upperF': 'armF', 'foreF': 'foreF', 'fistF': 'fistF', 'maceF': 'weapon'}
NONEAR = np.array(Image.open(os.path.join(HERE, 'sheets', 'nonear_0614.png')).convert('RGBA'))
NOFAR = np.array(Image.open(os.path.join(HERE, 'sheets', 'nofar_0623.png')).convert('RGBA'))
def clean(IMG):   # 지운 원화의 떨어진 작은 섬(< 6px — 06:14 그림 (130,270) 점) 지움
    n, cc, st, _ = cv2.connectedComponentsWithStats((IMG[..., 3] > 0).astype(np.uint8), 8); IMG = IMG.copy()
    for i in range(1, n):
        if st[i, 4] < 6: IMG[cc == i] = 0
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
REM_N, REM_F = ['upperN', 'foreN', 'fistN', 'maceN'], ['upperF', 'foreF', 'fistF', 'maceF']
reveal(NONEAR, REM_N, 'nonear(가까운 팔·철퇴 지움)')
reveal(NOFAR, REM_F, 'nofar(먼 팔·철퇴 지움)')
# 지운 원화는 팔이 나오던 짧은 검은 소매 토막(입구 구멍)을 어깨갑 밑에 남겨 그림 — 이 리그는 소매 끝·띠가 윗팔 조각에 붙어 같이 돌므로,
#   토막을 상체·어깨갑에 남기면 팔이 비킬 때 '빈 소매'가 따로 보임(첫 v1 공격 .267 확대) → 몸 실루엣 밖(가까운 x < 200 · 먼 x > 296)의 토막 픽셀은 뺌(투명)
def drop(tbl, names, where):
    for n in names:
        if n in tbl: tbl[n] = [(IMG, m & ~where) for IMG, m in tbl[n] if (m & ~where).any()]
        if n in tbl and not tbl[n]: del tbl[n]
for T_ in (ADD, BACK): drop(T_, ['torso', 'head'], lab('upperN') & (XX < 200)); drop(T_, ['torso'], lab('upperF') & (XX > 296))
# 지운 원화가 어깨갑 몫으로 다시 그린 곳(어깨갑 왼쪽 외곽선 — 원화에선 윗팔 소매 위 끝이 겸함)은 어깨갑 조각 앞에(뒤 조각 아님): 팔이 비켜도 어깨갑 가장자리가 깨끗
if 'pauldN' in BACK: ADD.setdefault('pauldN', []).extend(BACK.pop('pauldN'))
print('  소매 토막 뺀 뒤:', {('뒤 ' if T_ is BACK else '') + k: int(sum(m.sum() for _, m in v)) for T_ in (ADD, BACK) for k, v in T_.items()})
REPL, FRONT_ADD = {}, {}
def unmix_edges(IMG, rem_names, tag, band_r=3, T=20):
    fr = [f for f in rem_names if f in ('upperN', 'foreN', 'fistN', 'maceN', 'fistF', 'maceF')]   # 대기에 뒤 부품보다 나중에 그려지는 앞 부품
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
                armlike = (b == 'head') & ((hs[:, 1] > 50) | (pm[:, :3].astype(int).mean(-1) < 60))
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
move_over(NONEAR, 'upperN', ['head', 'pauldN']); move_over(NOFAR, 'upperF', ['torso'])
# 윗팔 위를 덮던 머리 가닥 끝(팔에서 잘린 끝): 지운 원화가 이어 그린 가닥으로(팔 둘레 6px, 지운 원화가 칠해진 곳) — 팔이 비키면 가닥 끝이 점처럼 떠 보였음
_hn = (cv2.distanceTransform((~lab('upperN')).astype(np.uint8), cv2.DIST_L2, 3) <= 6) & (LAB == LID['head']) & (NONEAR[..., 3] > 200)
REPL.setdefault('head', []).append((NONEAR, _hn)); print('  머리 가닥 끝 → 지운 원화', int(_hn.sum()), 'px')
# 윗팔과 맞닿는 조각(어깨갑·상체·머리숱)의 경계 외곽선: 라벨 경계가 외곽선 가운데를 지나 팔이 비키면 어깨갑·상체 가장자리가 톱니(첫 v1 .267)
#   → 윗팔 라벨의 어두운 경계 픽셀(밝기 < 80, 이웃 라벨 2px 안)을 이웃 조각에도 복사(팔 조각에도 남김) — 대기 합성 그대로
COPY = {}
LUMI = RA[..., :3].astype(int).mean(-1)
for f_, backs_ in (('upperN', ('pauldN', 'head')), ('upperF', ('torso',))):
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
# ---------------- 철퇴: 원화 + 주먹 밑·아래 자루 끝 = 시트 13번 철퇴(공 가운데·축·배율을 원화에 맞춤) ----------------
SM = sheet('mace'); _sa = SM[..., 3] > 128; _w = _sa.sum(1); _rows = np.nonzero(_w > 0.6 * _w.max())[0]
S_BALL = np.array([float(np.nonzero(_sa[_rows].any(0))[0].mean()), float((_rows.min() + _rows.max()) / 2)])
_low = np.arange(int(0.75 * SM.shape[0]), SM.shape[0] - 4); S_AX = np.array([float(np.median([np.nonzero(_sa[y])[0].mean() for y in _low if _sa[y].any()])), float(_low.mean())])
K_MACE = 1 / 1.0256   # check_sheet20: 시트 철퇴 ↔ 원화 먼 철퇴 공 SIFT 배율
def mace_img(name, fist, ball, U, lm, lf):
    a = art(lm); su = (S_BALL - S_AX) / np.linalg.norm(S_BALL - S_AX)          # 시트 축(아래 → 공)
    th = math.atan2(U[1], U[0]) - math.atan2(su[1], su[0]); c, s = math.cos(th) * K_MACE, math.sin(th) * K_MACE
    Mx = np.array([[c, -s, 0], [s, c, 0]], float); Mx[:, 2] = ball - Mx[:, :2] @ S_BALL
    ws = cv2.warpAffine(SM, Mx, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
    nv = np.array([-U[1], U[0]]); u = (XX - fist[0]) * U[0] + (YY - fist[1]) * U[1]; v = (XX - fist[0]) * nv[0] + (YY - fist[1]) * nv[1]
    ws = col_match(ws, lm & (u > 25) & (u < 70) & (np.abs(v) < 10)) if False else ws
    where = (u < 22) & (np.abs(v) < 16)
    out = under(a, ws, where); ys, xs = np.nonzero(where & (ws[..., 3] > 128)); umin = float(u[ys, xs].min()) if len(ys) else 0.0
    print(f'  {name}: 시트 철퇴로 주먹 밑·자루 끝 {int((where & (ws[..., 3] > 0) & (a[..., 3] < 250)).sum())} px · 자루 끝 = 주먹 아래 {-umin:.0f}px')
    return out, -umin
mcN, POM_N = mace_img('maceN', FI_N, BL_N, UN, lab('maceN'), lab('fistN')); mcN = front_with('maceN', mcN)
mcF, POM_F = mace_img('maceF', FI_F, BL_F, UF, lab('maceF'), lab('fistF')); mcF = front_with('maceF', mcF)
save('maceN', mcN)
UPS = 2; ang_tip = math.atan2(UF[1], UF[0]); rot_deg = math.degrees(-math.pi / 2 - ang_tip)
sw2 = cv2.resize(mcF, None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LANCZOS4); sw2[..., 3] = np.clip(cv2.resize(mcF[..., 3], None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LINEAR), 0, 255)
Rm = cv2.getRotationMatrix2D((float(FI_F[0] * UPS), float(FI_F[1] * UPS)), -rot_deg, 1.0); WS, HS = 700, 1000; Rm[0, 2] += WS / 2 - FI_F[0] * UPS; Rm[1, 2] += 720 - FI_F[1] * UPS
swv = cv2.warpAffine(sw2, Rm, (WS, HS), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
ys, xs = np.nonzero(swv[..., 3] > 0); assert xs.min() > 0 and ys.min() > 0 and xs.max() < WS - 1 and ys.max() < HS - 1, '철퇴 그림이 캔버스 밖'
x0, y0 = max(0, xs.min() - 2), max(0, ys.min() - 2); swv = swv[y0:ys.max() + 3, x0:xs.max() + 3]; Image.fromarray(swv).save(os.path.join(PARTS, 'weapon.png'))
vpt = lambda p: (Rm[:, :2] @ (np.array(p, float) * UPS) + Rm[:, 2]) - np.array([x0, y0])
W_PIV = vpt(FI_F); W_HEAD = vpt(BL_F); ysw, xsw = np.nonzero(swv[..., 3] > 128); W_TIP = np.array([float(W_PIV[0]), float(ysw.min())]); W_POM = np.array([float(W_PIV[0]), float(ysw.max())])
print('  far mace vertical: pivot', np.round(W_PIV, 1), 'top', np.round(W_TIP, 1), 'pommel', np.round(W_POM, 1), 'rot', round(rot_deg, 1))
# ---------------- 머리·상체·골반·어깨갑 + 이음 밑 4px ----------------
def underlay(a, back_m, front_m, r=4):
    band = front_m & dil(back_m, r) & (RA[..., 3] >= 250) & (a[..., 3] == 0); a = a.copy(); a[band] = RA[band]; return a, int(band.sum())
head_m = lab('head'); hd = with_reveal('head')
def _thin_off(a, reg):   # 가는 가닥(폭 ≤ 2px) 지움 — DHL 10:37 '공격할 때 표시한 부분이 지저분' 어깨갑 왼쪽 위 머리 가닥 끝
    m = (a[..., 3] > 40) & reg; op_ = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0; th = m & ~op_; a = a.copy(); a[th, 3] = 0; return a, int(th.sum())
hd, _nth = _thin_off(hd, (XX < 196) & (YY >= 286) & (YY <= 326)); print('  머리 어깨 왼쪽 가는 가닥 지움', _nth)
#   어깨갑 위 끝 바로 위 밝은 테(원화 1px 빛 줄 — 머리 칸에 들어 있어 머리가 움직이면 어깨갑에서 떨어져 점선처럼 보임) → 어깨갑 조각으로
_lum_ = RA[..., :3].astype(int).mean(-1); RIM = (hd[..., 3] > 0) & (_lum_ > 95) & dil(lab('pauldN'), 3) & ~lab('pauldN') & (YY >= 286) & (YY <= 312) & (XX >= 186) & (XX <= 222)
hd = hd.copy(); hd[RIM, 3] = 0; print('  어깨갑 위 밝은 테 머리 → 어깨갑', int(RIM.sum()))
o_head = save('head', hd)
tr, _n2 = underlay(with_reveal('torso'), lab('torso'), head_m | lab('pauldN'))
#   머리 ↔ 어깨갑 이음 뒤(상체, 둘보다 먼저 그림)에 머리카락 색 받침 — 공격·숨쉬기로 머리와 어깨갑이 따로 움직여 벌어진 틈에 배경 대신 머리카락 색(대기엔 위 조각에 다 덮임)
SEAM = (dil(RIM, 2) | (head_m & dil(lab('pauldN'), 3))) & (YY >= 284) & (YY <= 312) & (XX >= 184) & (XX <= 224) & (tr[..., 3] == 0)
_hc = np.median(RA[head_m & (RA[..., 3] >= 250) & (RA[..., :3].astype(int).mean(-1) < 40)][:, :3], 0).astype(np.uint8)
tr[SEAM, :3] = _hc; tr[SEAM, 3] = 255; print('  상체 머리·어깨갑 이음 받침', int(SEAM.sum()), 'px', _hc.tolist())
o_tor = save('torso', tr)
#   torsoAtk(엔진 opt-in standSwap — 서 있을 땐 원화 상체, 달리기·공격엔 이 조각): 가까운 팔 밑 상체 왼쪽 뾰족한 검은 자락(x 176~198)은 대기엔 팔 밑으로 이어지는 재킷이지만
#   팔을 들면 위가 끊겨 떨어진 깃발처럼 보임(DHL 10:37) → 몸 옆선(어깨갑 왼쪽 아래 → 허리띠 왼쪽) 밖을 자르고 잘린 끝에 외곽선
TA_LINE = [(318, 203.0), (330, 200.0), (346, 198.5), (362, 198.0)]
def torso_atk():
    a = tr.copy(); cl = np.interp(YY, [p[0] for p in TA_LINE], [p[1] for p in TA_LINE]); cut = (XX < cl - 0.5) & (YY >= 318) & (YY <= 362) & (a[..., 3] > 0)
    n_ = int(cut.sum()); a[cut, 3] = 0
    oc = np.array([18, 16, 20], float); edge = (a[..., 3] > 0) & (YY >= 318) & (YY <= 362) & (XX < cl + 1.5) & (XX >= cl - 0.5)
    a[edge, :3] = (0.35 * a[edge, :3] + 0.65 * oc).astype(np.uint8)
    print('  torsoAtk: 팔 밑 검은 자락 자름', n_, 'px'); return a
o_torA = save('torsoAtk', torso_atk())
_hp, _n3 = underlay(with_reveal('hips'), lab('hips'), lab('torso'))
for _x, _y in CUT.items():   # 바지를 가로지른 골반 아래 끝 2줄 옅게(대기엔 같은 원화 다리 위라 그대로, 달리면 시트 허벅지 위로 부드럽게)
    _hp[_y, _x, 3] = (_hp[_y, _x, 3] * 0.45).astype(np.uint8); _hp[_y - 1, _x, 3] = (_hp[_y - 1, _x, 3] * 0.8).astype(np.uint8)
# 허리띠 조각(belt — 상체와 한 몸, 서기·달리기 모두) · 서 있을 땐 그 밑 바지(hips, 골반 뼈), 달리기 다리 그림이면 바지 대신 시트 허벅지 + 가랑이 메움(hipsU)
#   DHL 11:59 '치마를 없애는 것이 좋을 것 같아요 · 러스트 브루노처럼 깔끔하게 허리띠만 나오도록' — v1.5~1.9 치마 대신:
#   원화 골반 칸에서 허리띠·쌈지·버클·끈·금빛 병(바지 천이 아닌 색) + 그 둘레 원화 외곽선만 남기고 바지 천은 뺌 → 허리띠 아래 = 시트 허벅지(바지)
#   허리띠 밑 가랑이 사이는 다리 뒤 조각 hipsU(바지 천 색, 다리보다 먼저 그림)가 메움 — 허벅지 윗끝 둥근 끝 사이로 배경이 안 보이게
def belt_run():
    base, _ = underlay(with_reveal('hips'), lab('hips'), lab('torso')); Hm = lab('hips')
    lum = RA[..., :3].astype(int).mean(-1); sat = RA[..., :3].max(-1).astype(int) - RA[..., :3].min(-1)
    pants = (lum >= 32) & (lum <= 85) & (sat < 20); dark = lum < 32
    stuff = Hm & (RA[..., 3] > 128) & ~pants & ~dark                      # 허리띠·쌈지·버클·끈·금빛 병
    nc, cc = cv2.connectedComponents(stuff.astype(np.uint8), 8); st2 = np.zeros_like(stuff)
    for i_ in range(1, nc):
        if (cc == i_).sum() >= 12: st2 |= cc == i_                       # 바지 주름 빛 부스러기 뺌
    keep = st2 | (Hm & dark & dil(st2, 2)) | (Hm & (YY < 379))            # 그 둘레 외곽선 2px · 허리띠 윗부분은 통째
    keep = cv2.morphologyEx(keep.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
    keep &= Hm | (base[..., 3] > 0)
    nc, cc = cv2.connectedComponents(keep.astype(np.uint8), 8); k2 = np.zeros_like(keep)
    for i_ in range(1, nc):
        if (cc == i_).sum() >= 40: k2 |= cc == i_
    out = base.copy(); out[~k2, 3] = 0
    print('  허리띠 조각 belt:', int(k2.sum()), 'px · 원화 골반', int((base[..., 3] > 0).sum()), 'px')
    return out, k2
_belt, BELT = belt_run()
o_belt = save('belt', _belt)
#   허리띠는 상체와 한 몸(belt 뼈 = torso 자식) — DHL 12:16 '탄띠 위치를 이동시키지 않으면 탄띠·아래 다리 쪽 잔상도 안 남을 것':
#   상체가 기울 때 재킷 밑단과 허리띠·쌈지가 따로 움직여 쌈지 위에 재킷 끝이 떠 보였음 → 허리띠는 상체를 따라, 그 밑 바지(hips)는 다리 쪽(골반 뼈)에.
#   바지 조각엔 허리띠 픽셀을 빼고(겹쳐 그리면 두 겹 잔상) 허리띠 밑 허리 안쪽을 바지 천 색으로 채움 — 허리띠가 기울어 들려도 배경·잔상 대신 바지
_lum = RA[..., :3].astype(int).mean(-1); _sat = RA[..., :3].max(-1).astype(int) - RA[..., :3].min(-1); _Hm = lab('hips')
_pc = np.median(RA[_Hm & (RA[..., 3] >= 250) & (_lum >= 45) & (_lum <= 75) & (_sat < 15)][:, :3], 0)
_wp = np.stack(np.nonzero((lab('torso') & (YY >= 352) & (YY <= 368)) | (_Hm & (_lum >= 32) & (_lum <= 85) & (_sat < 20) & (YY >= 384)))[::-1], 1).astype(np.int32)
_waist = np.zeros((512, 512), np.uint8); cv2.fillConvexPoly(_waist, cv2.convexHull(_wp), 1); _waist = (_waist > 0) & (YY >= 358)
_F = BELT & _waist
_hp[BELT & ~_F, 3] = 0; _hp[_F, :3] = (_pc * (1 - 0.12 * np.clip((YY[_F] - 366) / 24.0, 0, 1))[:, None]).astype(np.uint8); _hp[_F, 3] = 255
print('  바지 조각 hips: 허리띠 픽셀 뺌', int((BELT & ~_F).sum()), '· 허리띠 밑 허리 바지 천', int(_F.sum()), '· 색', _pc.astype(int).tolist())
o_hips = save('hips', _hp)
#   hipsU — 허리띠 밑 가랑이 메움(다리 뒤): 두 다리 뿌리 사이 아래로 둥근 바지 천(원화 바지 색 + 아래 둥근 끝 외곽선). 서 있을 땐 원화 골반·다리에 다 덮임
def hips_under(K=4):
    Hm = lab('hips'); lum = RA[..., :3].astype(int).mean(-1); sat = RA[..., :3].max(-1).astype(int) - RA[..., :3].min(-1)
    pc = np.median(RA[Hm & (RA[..., 3] >= 250) & (lum >= 45) & (lum <= 75) & (sat < 15)][:, :3], 0).astype(float)
    oc = np.median(RA[Hm & (RA[..., 3] >= 250) & (lum < 30)][:, :3], 0).astype(float)
    from PIL import ImageDraw as _D
    hx = sorted([LEG['near']['hip'][0], LEG['far']['hip'][0]]); hy = max(LEG['near']['hip'][1], LEG['far']['hip'][1])
    x0, x1, yt, yb = hx[0] - HU_W, hx[1] + HU_W, 368, hy + HU_D; rr = HU_R   # 위 끝은 허리띠 밑까지(허리띠가 상체를 따라 기울어 들려도 배경 안 보이게)
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
_mr = (_pd[..., 3] > 0) & (_pd[..., 0].astype(int) > 80) & (_pd[..., 0].astype(int) - _pd[..., 1] > 40) & (_pd[..., 0].astype(int) - _pd[..., 2] > 30) & (_pd[..., 1] < 100) & (XX < 200)
_pd[_mr, 3] = 0   # 윗팔 자줏빛 띠 조각(대기엔 밑의 윗팔 그림이 같은 픽셀) — 팔이 비키면 어깨갑 왼쪽 안에 붉은 줄
_pd, _nu = underlay(_pd, lab('pauldN'), head_m, r=3)   # 어깨갑 위 끝 밑 머리 3px(머리 밑에 그려져 대기엔 안 보임)
#   어깨갑 두 날개 사이 오목한 곳(원화 = 윗팔의 검은 소매 띠)을 어깨갑에 원화 픽셀 그대로 — 팔을 들면 어깨갑 사이가 비어 윗팔 위 끝 원(갈색, 톱니 가장자리)이 비쳤음(DHL 10:37)
_pm = lab('pauldN').astype(np.uint8); _hull = np.zeros((512, 512), np.uint8); cv2.fillConvexPoly(_hull, cv2.convexHull(np.stack(np.nonzero(_pm)[::-1], 1).astype(np.int32)), 1)
_gap = (_hull > 0) & lab('upperN') & (RA[..., 3] >= 250) & (RA[..., :3].astype(int).mean(-1) < 60) & (_pd[..., 3] == 0)
_pd[_gap] = RA[_gap]; print('  어깨갑 두 날개 사이 검은 소매 띠 → 어깨갑', int(_gap.sum()))
print('  어깨갑: 자줏빛 띠 조각 지움', int(_mr.sum()), '· 위 끝 밑 머리', _nu)
o_pd = save('pauldron', _pd)
print('  이음 밑 덧칠 px: 상체←머리·어깨갑', _n2, '· 골반←상체', _n3)
BACKB = {}
_PAR = {'head': ('head', NECK), 'torso': ('torso', HIP), 'hips': ('skirt', HIP), 'pauldN': ('pauldron', SH_N)}
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
TH = {'near': limb_piece('thighN', lab('legN'), 5, 5, _thR), 'far': limb_piece('thighF', lab('legF'), 8, 8, _thR)}
SHN = {'near': limb_piece('shinN', lab('legN'), 10, 0, _shR), 'far': limb_piece('shinF', lab('legF'), 11, 0, _shR)}
L_TH = float(max(np.linalg.norm(LEG[s]['knee'] - LEG[s]['hip']) for s in LEG)); L_SH = float(max(np.linalg.norm(LEG[s]['ankle'] - LEG[s]['knee']) for s in LEG))
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
SRCF = {'happy': 'face_angry', 'angry': 'face_happy', 'focus': 'face_focus', 'shout': 'face_shout', 'effort': 'face_effort', 'half': 'blink_half', 'closed': 'blink_closed'}   # 시트 4·5번 바뀜(웃는 입 = 5번)
neu = neu_s.astype(np.int16); U_ = np.zeros(neu.shape[:2], bool)
for n in FACE_N + BLINK_N:
    s_ = sheet(SRCF[n]).astype(np.int16)
    if s_.shape != neu.shape: s_ = cv2.resize(s_.astype(np.uint8), (neu.shape[1], neu.shape[0]), interpolation=cv2.INTER_AREA).astype(np.int16)
    U_ |= np.abs(s_ - neu).max(2) > 40
reg = cv2.dilate(U_.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
# 시트 머리 9장은 머리카락 결이 장마다 조금씩 달라(다시 그린 그림) 다른 곳 전체를 붙이면 머리숱까지 바뀜 → 눈·눈썹·안경·입 둘레 타원 안만
FACE_EL = (((XX - 272) / 42.0) ** 2 + ((YY - 286) / 38.0) ** 2) <= 1
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
P_('torso', HIP); P_('torsoAtk', HIP); P_('hips', HIP); P_('belt', HIP); P_('hipsU', HIP); P_('head', NECK); P_('pauldron', SH_N)
for _nm, (_par, _pt) in BACKB.items(): P_(_nm, _pt)
P_('armU', SH_N, elbow=piv('armU', EL_N)); P_('armF', SH_F, elbow=piv('armF', EL_F))
P_('armL', EL_N, fist=piv('armL', FI_N)); P_('fistN', FI_N); P_('maceN', FI_N)
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
         'armU': (SH_N, 0.0), 'armL': (EL_N, ARML_REST), 'maceN': (FI_N, ARML_REST), 'fistN': (FI_N, ARML_REST),
         'armF': (SH_F, 0.0), 'foreF': (EL_F, 0.0), 'fistF': (WR_F, 0.0), 'weapon': (FI_F, WEAPON_ANG), 'foreFb': (WR_F, 0.0), 'torsoAtk': (HIP, 0.0), 'belt': (HIP, 0.0), 'hipsU': (HIP, 0.0)}
for _nm, (_par, _pt) in BACKB.items(): world[_nm] = (_pt, 0.0)
BONES = [('root', None), ('hip', 'root'), ('skirt', 'hip'), ('torso', 'hip'), ('head', 'torso'), ('armF', 'torso'), ('foreF', 'armF'), ('fistF', 'foreF'), ('weapon', 'fistF'),
         ('armU', 'torso'), ('armL', 'armU'), ('maceN', 'armL'), ('fistN', 'armL'), ('foreFb', 'torso'),
         ('cape', 'torso'), ('scarf', 'torso'), ('pouch', 'hip'), ('pauldron', 'torso'), ('pauldronF', 'torso'), ('torsoAtk', 'torso'), ('belt', 'torso'), ('hipsU', 'skirt')]
BONES += [(_nm, _par) for _nm, (_par, _pt) in BACKB.items()]
WANG = {'armL': ARML_REST, 'maceN': ARML_REST, 'fistN': ARML_REST, 'weapon': WEAPON_ANG}
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
legs = {'hip': [0, round(SC * (float(np.mean([LEG[s]['hip'][1] for s in LEG])) - HIP[1]), 1)], 'thigh': round(SC * L_TH, 1), 'shin': round(SC * L_SH, 1),
        'thighImg': TH['near'], 'shinImg': SHN['near'], 'boot': {'part': 'bootNRun', 'sole': RB['near'][1], 'ankleRange': [-1.2, 1.4], **({} if RUNLOCK is None else {'runLock': RUNLOCK})}}
for sd, nm, lm in [('near', 'bootStandN', lab('legN')), ('far', 'bootStandF', lab('legF'))]:
    hide = {'part': TH[sd]['part'], 'a': TH[sd]['a'], 'b': TH[sd]['b'], 'w': 0.001}
    _root = round(SC * (LEG[sd]['hip'][0] - HIP[0]), 1); _rest = round(SC * (LEG[sd]['ankle'][0] - HIP[0]), 1)
    legs[sd] = {'x': _rest, 'hipX': _root, 'runX': _root, 'shade': 0, 'thighImg': TH[sd], 'shinImg': SHN[sd], 'runBoot': 'bootNRun' if sd == 'near' else 'bootFRun',
                'stand': {'fade': [0.05, 0.1], 'thighImg': hide, 'shinImg': dict(hide, part=SHN[sd]['part'], a=SHN[sd]['a'], b=SHN[sd]['b']), 'boot': {'part': nm, 'sole': sole_pts(lm, LEG[sd]['ankle'], SOLE)}}}
idle = {sd: legs[sd]['x'] for sd in ('near', 'far')}
# ---------------- 그리는 순서(뒤 → 앞): 다리 · 뒤 조각 · 먼 윗팔·팔뚝 · 골반 · 상체 · 가까운 윗팔 · 어깨갑 · 먼 철퇴·주먹 · 머리 · 가까운 철퇴 · 팔뚝 · 주먹 ----------------
draw = ['hipsU', 'legFar', 'legNear'] + list(BACKB) + DRAW_IDLE[2:]   # hipsU = 다리 뒤 가랑이 메움
draw.insert(draw.index('skirt') + 1, 'belt')   # 허리띠 = 바지 앞 · 상체 뒤(상체와 한 몸)
draw.insert(draw.index('torso') + 1, 'torsoAtk')   # 달리기·공격 상체(standSwap)
rig = {'name': 'bruno-neon', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': parts, 'bones': bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': {n: f'face_{n}' for n in FACE_N},
       'blinkFaces': {'half': 'face_half', 'closed': 'face_closed'},
       'gait': {'stance': 0.26, 'strideBase': 40, 'strideK': 0.12, 'hipBase': 6, 'bob': 8, 'lean': 0.1, 'headBob': 3, 'kneeLift': 0.7, 'heelKick': 0.5, 'dropCap': 16,   # 10 러스트 브루노와 같은 걸음(치마 안 종종걸음 v1.6~1.9 는 치마를 없애며 되돌림 — DHL 11:59)
                'swingReach': 0.05, 'landAng': -0.04, 'elbowRun': 0.12, 'armSwing': 0.06, 'armBias': 0.0, 'headRun': 0.05},
       'carrySwing': 0.15, 'wristRange': 0.2, 'dropLift': 8, 'bounce': [],
       'metrics': {'bodyHeight': round(2 * (SOLE - M['hairTop'][1])), 'note': f"rig units; 상투 위(y{M['hairTop'][1]})~발바닥({SOLE:.0f}) ×2, 철퇴 제외"},
       'ui': {'attack': 'smash', 'touch': 'hop'}, 'standSwap': [['skirt', 'hipsU'], ['torso', 'torsoAtk']]}   # 서 있는 원화 다리 그림이면 바지(hips)·원화 상체, 달리기 다리면 가랑이 메움(hipsU)·torsoAtk (허리띠는 늘, 공격 중 상체는 tPiece torsoAtk)
# ---------------- 공격: 번갈아 내려찍기(tools/plan_alt20.py 키 그대로) ----------------
fo_off = np.array(OFF['foreF'], float); fi_off = np.array(OFF['fistF'], float)
ipt = lambda off, p: [round(float(p[0] - off[0]), 1), round(float(p[1] - off[1]), 1)]
ud = (EL_F - WR_F) / np.linalg.norm(EL_F - WR_F)
parts['gF'] = {'src': 'parts/fistF.png', 'pivot': ipt(fi_off, WR_F), 'grip': ipt(fi_off, FI_F), 'elbow': ipt(fi_off, WR_F), 'wrist': ipt(fi_off, WR_F), 'scale': SC,
               'shaftDir': [round(float(UF[0]), 4), round(float(UF[1]), 4)], 'fore': 'foreFa', 'foreBone': 'foreFb', 'foreDir': [round(float(ud[0]), 4), round(float(ud[1]), 4)]}
parts['foreFa'] = {'src': 'parts/foreF.png', 'pivot': ipt(fo_off, WR_F), 'elbow': ipt(fo_off, EL_F), 'scale': SC}
rig['swordGrip'] = {'tipDepth': 6, 'near': {'upper': 'armF', 'carry': 'gF', 'pieces': []}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': 0}, 'stretchMax': 1.05, 'shoulderPush': 0}
rig['drawA'] = ['hipsU', 'legFar', 'legNear'] + list(BACKB) + ['armF', 'foreFb', 'skirt', 'belt', 'torso', 'torsoAtk', 'armU', 'pauldron', 'weapon', 'foreF', 'head', 'maceN', 'armL', 'fistN']
E = PLAN['engine']
trk = lambda f: [[e[0], round(f(e), 4), 'io'] for e in E]
HIPY_K = float(os.environ.get('HIPY_K', 0))   # 공격 골반 내림 배율 — 0: 골반(허리띠·바지) 높이 고정(DHL 12:16 — 서 있는 원화 다리는 발목에 고정된 한 장이라 골반이 12px 내려앉으면 바지 아래 끝이 다리 위로 미끄러져 잔상). 철퇴 쥔 자리(gy)는 골반 기준이라 몸과 같이 그대로
act = {'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': 1.0, 'hitAt': PLAN['summary']['hits'][0], 'hitStop': 0.05, 'cancelAt': 0.8,
       'w': [[0, 1]], 'reach': [[0, 0]], 'nPiece': [[0, 'gF']], 'nUpper': [[0, 'armF']], 'armIK': [[0, 1]], 'ikSideK': {'N': [[0, 1]]}, 'tPiece': [[0, 'torsoAtk']],   # 공격 내내 상체 = torsoAtk(팔 밑 자락 자름 — DHL 10:37), 서 있는 원화 다리 그림이어도
      
       'gx': trk(lambda e: SC * e[1]), 'gy': trk(lambda e: SC * (e[2] - e[5])), 'sa': trk(lambda e: math.radians(e[3])),
       'lean': trk(lambda e: e[4]), 'hipY': trk(lambda e: SC * e[5] * HIPY_K),
       'head': [[0, 0], [0.1, -0.05, 'io'], [0.28, 0.06, 'io'], [0.4, -0.03, 'io'], [0.54, 0.07, 'io'], [0.8, 0]],
       'freeArm': True, 'fuA': trk(lambda e: e[6]), 'flA': trk(lambda e: e[7]),
       'face': [[0, 'angry'], [0.24, 'shout'], [0.38, 'angry'], [0.5, 'shout'], [0.7, 'focus'], [0.9, None]],   # 공격 중 눈 뜸(10 DHL 23:57 — 같은 인물), 시트 표정 6장 모두 눈 뜸
       'order': [[0, 'drawA']],
       'nearLift': [[0, 0], [0.03, 0, 'io'], [0.09, 10, 'io'], [0.15, 0]], 'farLift': [[0, 0], [0.17, 0, 'io'], [0.23, 10, 'io'], [0.29, 0]],
       'aDamp': 9, 'standStep': True}
rig['actions'] = {'smash': act}
rig['cutHold'] = 0.1   # 스킬 컷인 멈춤(10-21 게임 넣기): 후보 .10·.17·.20·.28 을 게임 컷인(PC 1440×900, 혼자·7 루시아와 둘)으로 잼(cutpair) — 리그 맨 위 .10 혼자 칸 안 7px · 둘 −1 / .17 −9·−19 / .20 −1·−11 / .28 −5·−13 → .10 예비(가까운 철퇴를 뒤로 젖히고 먼 철퇴 듦 — 두 철퇴 V 자)
_a = np.array(Image.open(os.path.join(HERE, '..', '..', '..', 'art', 'characters', 'char_0020.png')).convert('RGBA').resize((160, 160), Image.BOX))[..., 3]
_ys, _xs = np.nonzero(_a > 40); FIT_CX = round(float(((_xs.min() + _xs.max() + 1) / 2 + _xs.mean() + .5) / 2 / 160 * 512), 1)
rig['gameRef'] = {'refOrigin': [round(float(O[0] - (HIP[0] - FIT_CX)), 1), float(O[1])], 'refScale': 2.0, 'refLift': 0,
                  'note': f'게임 그림 char_0020.png(512) = 0번 합격 원화(ref512, 치마 없앰 — DHL 10-21 11:59). x = 도감 칸(fitArt 중심 {FIT_CX}, index.html measureBox 와 같은 계산)에서 골반(hip x {HIP[0]:.0f})이 가운데'}
rig['note'] = '20 네온 브루노 v1(대기·달리기·번갈아 내려찍기). 10 러스트 브루노 v1.2 구조. 조각 = 원화를 부품별로 나눔(seg20.py) + 가려진 곳 = 팔·철퇴만 지운 원화(프롬프트 2·3: sheets/nonear_0614·nofar_0623), 시트 = 표정·깜빡임·달리는 다리·부츠·철퇴 자루 끝'
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(PARTS)): _h.update(fn.encode()); _h.update(open(os.path.join(PARTS, fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_bruno20.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};window.MR_RIG_DEFS['bruno-neon']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(parts), 'parts, version', rig['version'], 'idle', idle, 'legs', legs['thigh'], legs['shin'], 'hip', legs['hip'], 'FIT_CX', FIT_CX)
