# 11 네온 알론소 내려찍기 (2026-10-18 15:30~) — build_neon.py 안에서 exec (rig, def_parts, bones, np, math, json, os, HERE, PC, OUT, img 사용)
#  rigid 칼(칼 먼저, 쥔 팔 조각이 칼에 붙음) — 21 스카이아크 알론소 방식. 키는 attack_keys.json
#  · 엔진 이름: near(armF→foreF) = 칼날 쪽 위 주먹 = 먼 팔(살색 팔뚝) · far(armU→armL) = 폼멜 쪽 아래 주먹 = 가까운 팔(은색 토시)
#  · frame 'torso': 손잡이 자리·각도가 상체 기준(대기 guard와 같음) → 시작·끝이 대기 자세와 그대로 이어짐
#  · 쥔 팔 조각 = 시트 주먹(gNv·gFv·gNh·gFh) + 시트 팔뚝(foreN 은색 토시 · foreF 살색)을 합성 — 구간마다 바꿈(nPiece·fPiece 키)
#    가까운 손(오른손) = gN*, 먼 손(왼손) = gF* 만. 좌우 뒤집기 금지(반대 손이 됨)
ATK = json.load(open(os.path.join(HERE, 'attack_keys.json'), encoding='utf-8'))
R2 = 2.0      # 합성 그림 해상도: 리그 1단위 = 2px
FS = 0.76     # 시트 주먹·팔 조각 1px = 리그 0.76 (원화 주먹 폭·토시 굵기에 맞춤)
#  grip: 칼 축이 주먹 가운데를 지나는 점 · sd: 칼끝 방향(그림 안) · wrist: 손목(토시 띠) 점 — 시트 px
FISTS = {   # stub: 지울 손잡이 토막 직사각형 [x0, y0, x1, y1] (그 안 픽셀 투명, 끝 포함) — 주먹 테두리 바로 바깥까지
    'gNv': dict(grip=(49.0, 76.0), sd=(0.0, -1.0), wrist=(6.0, 78.0), stub=[(0, 0, 85, 39), (0, 110, 85, 138)]),
    'gFv': dict(grip=(36.5, 76.0), sd=(0.0, 1.0), wrist=(80.0, 76.0), stub=[(0, 0, 85, 39), (0, 40, 28, 41), (0, 110, 85, 138)]),
    'gNh': dict(grip=(62.0, 37.0), sd=(1.0, 0.0), wrist=(6.0, 39.0), stub=[(102, 20, 139, 52)]),
    'gFh': dict(grip=(62.0, 36.0), sd=(1.0, 0.0), wrist=(6.0, 38.0), stub=[(102, 20, 138, 52)]),
}
FORES = {   # 팔뚝: 팔꿈치·손목 마디 가운데 (시트 px) · capE = 팔꿈치 덮개 끝(팔꿈치에서 축 방향 px) · wcut = 손목 쪽 띠 시작 — 그 사이(몸통)만 늘임
    'N': dict(file='foreN.png', el=(26.0, 27.0), wr=(89.0, 137.0), capE=4, wcut=110),
    'F': dict(file='foreF.png', el=(29.2, 26.7), wr=(63.6, 127.7), capE=16, wcut=90),
}
def unstub(im, spec):
    """주먹 그림에서 삐져나온 손잡이 토막 지움 — 칼 그림이 손잡이를 그림"""
    a = np.array(im).copy()
    for x0, y0, x1, y1 in spec: a[y0:y1 + 1, x0:x1 + 1, 3] = 0
    from scipy import ndimage   # 지우고 남은 부스러기: 가장 큰 덩어리만
    lab, n = ndimage.label(a[..., 3] > 0)
    if n > 1: big = 1 + int(np.argmax(ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)))); a[..., 3] = np.where(lab == big, a[..., 3], 0)
    return Image.fromarray(a)
def compose(name, fist, fore, rel_deg, L=None, inset=8.0):
    """쥔 팔 조각: 주먹 + 팔뚝. rel_deg = 손목→팔꿈치 방향(칼끝 방향 기준, 화면 각도·시계 +).
    L = 팔꿈치~손목 길이(리그). (16:58 DHL '팔·발 중복 없이') 팔뚝 그림을 통째로 늘이면 끝의 검은 덮개·손목 띠까지 3~4배로 늘어나
    주먹 밖으로 검은 덩어리가 삐져나와 '주먹이 하나 더'처럼 보였음 → 팔꿈치 덮개·손목 띠는 그대로, 그 사이 몸통만 늘이고 손목(wr) 밖은 자름"""
    import cv2
    F, Fo = FISTS[fist], FORES[fore]
    fim = unstub(img(os.path.join(PC, fist + '.png')), F['stub']); oa = np.asarray(img(os.path.join(PC, Fo['file']))).astype(np.float32)
    k = FS * R2; sd = np.array(F['sd'], float); a_sd = math.atan2(sd[1], sd[0]); d = np.array([math.cos(a_sd + math.radians(rel_deg)), math.sin(a_sd + math.radians(rel_deg))])
    el, wr = np.array(Fo['el']), np.array(Fo['wr']); Lw = float(np.linalg.norm(wr - el)); L0 = Lw * FS; L = L or L0
    ax = (wr - el) / Lw; nx = np.array([-ax[1], ax[0]]); cE, wc = Fo['capE'], Fo['wcut']
    Lpx = L / FS; s_ = max(.3, (Lpx - cE - (Lw - wc)) / (wc - cE)); vW = cE + (wc - cE) * s_ + (Lw - wc)   # 늘인 뒤 손목 자리(= Lpx)
    U0, V0, Wd = 60, 40, 120; H = int(V0 + vW + 3)
    vv, uu = np.mgrid[0:H, 0:Wd].astype(np.float32); vo = vv - V0; uo = uu - U0
    vin = np.where(vo <= cE, vo, np.where(vo <= cE + (wc - cE) * s_, cE + (vo - cE) / s_, wc + (vo - cE - (wc - cE) * s_)))
    mx_ = (el[0] + ax[0] * vin + nx[0] * uo).astype(np.float32); my_ = (el[1] + ax[1] * vin + nx[1] * uo).astype(np.float32)
    pre = oa.copy(); pre[..., :3] *= pre[..., 3:4] / 255
    st = cv2.remap(pre, mx_, my_, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    st[..., 3] *= np.clip((V0 + vW + 2 - vv) / 2, 0, 1)   # 손목 밖은 자름(주먹이 덮는 자리)
    Wc = np.array(F['wrist']) * k; Wi = Wc - d * inset * R2; Ec = Wi + d * L * R2
    perp = np.array([d[1], -d[0]]); A = np.stack([perp * k, -d * k], 1); t = Ec - A @ np.array([U0, V0], float)
    cs = [A @ np.array(c, float) + t for c in [(0, 0), (Wd, 0), (0, H), (Wd, H)]] + [np.array([0, 0]), np.array([fim.width * k, fim.height * k])]
    mn = np.floor(np.min(cs, 0)) - 4; mx = np.ceil(np.max(cs, 0)) + 4; size = tuple((mx - mn).astype(int))
    M = np.c_[A, t - mn].astype(np.float64)
    cv_ = cv2.warpAffine(st, M, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    al = cv_[..., 3:4]; cv_[..., :3] = np.where(al > 1e-3, cv_[..., :3] / np.maximum(al, 1e-3) * 255, 0)
    canvas = Image.fromarray(np.clip(cv_, 0, 255).astype(np.uint8), 'RGBA')
    fs = fim.resize((round(fim.width * k), round(fim.height * k)), Image.LANCZOS); canvas.alpha_composite(fs, (int(-mn[0]), int(-mn[1])))
    canvas.save(os.path.join(OUT, 'parts', name + '.png'))
    g = np.array(F['grip']) * k - mn; e = Ec - mn; r = lambda v: [round(float(v[0]), 1), round(float(v[1]), 1)]
    def_parts[name] = {'src': f'parts/{name}.png', 'pivot': r(e), 'elbow': r(e), 'grip': r(g), 'wrist': r(g), 'shaftDir': [float(sd[0]), float(sd[1])], 'scale': 1 / R2}
for nm, spec in ATK['pieces'].items():
    compose(nm, *spec)
    if nm in ATK.get('pieceK', {}): def_parts[nm]['scale'] *= ATK['pieceK'][nm]   # 조각 전체 배율(주먹·팔뚝 함께 — 늘이기 아님)
# (21:40 DHL 공격 0.56초 '표시한 곳(턱 밑 ~ 손)에 팔이 들어가야') 휘두름·런지 먼 팔: v5 는 먼 주먹만 손잡이에 있고 팔이 없어
#   턱 밑 ~ 손 사이가 비었음(시트 m11·m12 는 먼 어깨(턱 밑) → 팔 → 손잡이 먼 주먹). fST2 = 시트 가로 주먹 gFh + 살색 팔뚝(compose),
#   armFst = 원화 먼 윗팔(armF)에서 팔꿈치 쪽 검은 덮개를 지운 것 — 팔꿈치 덮개는 팔뚝 조각 것 하나(17:06 '덮개 두 겹' 규칙)
if ATK.get('farUpperST'):
    _fu = ATK['farUpperST']; _p = def_parts[_fu['from']]; _u = np.array(img(os.path.join(OUT, 'parts', _fu['from'] + '.png')))
    _sh, _el = np.array(_p['pivot'], float), np.array(_p['elbow'], float); _ax = (_el - _sh) / np.linalg.norm(_el - _sh); _L = float(np.linalg.norm(_el - _sh))
    _yy, _xx = np.mgrid[0:_u.shape[0], 0:_u.shape[1]]; _t = (_xx - _sh[0]) * _ax[0] + (_yy - _sh[1]) * _ax[1]
    _u[..., 3] = (_u[..., 3] * np.clip((_L + _fu.get('cut', 0) - _t) / 2, 0, 1)).astype(np.uint8)
    Image.fromarray(_u).save(os.path.join(OUT, 'parts', 'armFst.png')); def_parts['armFst'] = dict(_p, src='parts/armFst.png', scale=_p.get('scale', 1) * _fu.get('k', 1))
# (10-19 01:54 DHL '휘두름·버팀 동안 사라지고 돌아올 때 다시 나오는 것 — 3번처럼 계속 나오게') 먼 어깨갑을 휘두름·버팀에도 보이게.
#   원화 먼 어깨갑(pauldronF)은 턱 피부 조각이 붙어 있고 오른쪽이 칼날 자리로 잘려 있음(대기 땐 칼이 덮음) → 휘두름용 pauldronFst:
#   피부·턱 외곽선 지움, 잘린 쪽은 검은 외곽선 1px. 같은 자리의 숨김 뼈 pauldronFs 로 fade 키에서 켬
if ATK.get('pauldronFst'):
    from scipy import ndimage as _nd
    _a = np.array(img(os.path.join(OUT, 'parts', 'pauldronF.png'))).astype(int); _yy, _xx = np.mgrid[0:_a.shape[0], 0:_a.shape[1]]
    _r, _g, _b, _al = _a[..., 0], _a[..., 1], _a[..., 2], _a[..., 3]
    _skin = (_r > 170) & (_g > 110) & (_b < 160) & (_r > _b + 50)
    _pad = ((_b > 150) & (_b > _r + 60)) | ((_r > 170) & (_g > 170) & (_b > 170)) | ((_r > 180) & (_g > 150) & (_b < 120) & ~_skin & (_yy > 14))
    _padF = _nd.binary_fill_holes(_nd.binary_closing(_pad, iterations=2)); _top = ATK['pauldronFst'].get('top', 11)
    _keep = (_al > 30) & ~_skin & ~(_yy < _top) & ~((_xx >= 35) & ~_padF & ~_nd.binary_dilation(_padF, iterations=1)); _keep |= _padF & (_al > 0)
    _lab, _n = _nd.label(_keep); _keep = _lab == (1 + int(np.argmax(_nd.sum(_keep, _lab, range(1, _n + 1)))))
    _o = _a.copy(); _o[..., 3] = np.where(_keep, _al, 0); _o[(_nd.binary_dilation(_keep, iterations=1) & ~_keep) & _nd.binary_dilation(_padF, iterations=1)] = [28, 28, 34, 255]
    Image.fromarray(_o.astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'parts', 'pauldronFst.png')); def_parts['pauldronFst'] = dict(def_parts['pauldronF'], src='parts/pauldronFst.png')
    bones.append(dict(next(b_ for b_ in bones if b_['name'] == 'pauldronF'), name='pauldronFs', part='pauldronFst')); rig['hidden'] = rig.get('hidden', []) + ['pauldronFs']
# 든 윗팔(시트 armNup·armFup): long_upper — 어깨 덮개 그대로, 살 부분만 미리 늘임(엔진 늘임 ≈ 1)
def long_upper(nm, src, sh, el, T, c0=-5.0, keepS=20.0, skinEnd=78.0, back=32, wk=1.0):
    """(17:40 DHL '팔뚝이 얼굴을 가로지름') 머리 위 든 윗팔을 길이 T(리그)로 미리 늘인 그림.
    엔진은 윗팔 그림을 축 방향으로 통째 늘여서 3배쯤 늘이면 어깨 쪽 검은 덮개가 긴 타원이 됐음 →
    어깨 덮개(축 c0 둘레, keepS 까지)는 그대로, 살 부분(keepS~skinEnd)만 늘이고 팔꿈치 쪽 검은 덮개(skinEnd 뒤)는 지움 —
    팔꿈치는 팔뚝 조각의 덮개 하나만(위에 그림). 그림 축 = 세로, pivot = 어깨 덮개 가운데, elbow = pivot + (0, T)"""
    import cv2
    a = np.asarray(img(os.path.join(PC, src))).astype(np.float32); pre = a.copy(); pre[..., :3] *= pre[..., 3:4] / 255
    sh, el = np.array(sh), np.array(el); ax = (el - sh) / np.linalg.norm(el - sh); ux = np.array([ax[1], -ax[0]])
    f = (T + 4 - (keepS - c0)) / (skinEnd - keepS); U0 = int(44 * wk); W = 2 * U0; H = int(back + T + 8)   # wk: 팔 굵기 배율(옆으로만) — 길게 늘인 팔이 막대처럼 가늘어 보이지 않게
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); w = yy - back; u = (xx - U0) / wk
    sv = np.where(w <= keepS - c0, w + c0, keepS + (w - (keepS - c0)) / f)
    mx = (sh[0] + ax[0] * sv + ux[0] * u).astype(np.float32); my = (sh[1] + ax[1] * sv + ux[1] * u).astype(np.float32)
    o = cv2.remap(pre, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    o[..., 3] *= np.clip((skinEnd + 1 - sv) / 1.5, 0, 1); o = np.clip(o, 0, 255)
    al = o[..., 3:4]; o[..., :3] = np.where(al > 1e-3, o[..., :3] / np.maximum(al, 1e-3) * 255, 0)
    Image.fromarray(np.clip(o, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'parts', nm + '.png'))
    def_parts[nm] = {'src': f'parts/{nm}.png', 'pivot': [U0, back], 'elbow': [U0, back + T], 'scale': ATK.get('upScale', 1.0)}
# (v5) 머리 위·휘두름 팔은 kitoh/oh_build.py — 시트1 조각 합성(compose)·미리 늘인 윗팔(long_upper)은 더 안 씀(20:15 DHL '관 팔' — 실수 기록 23)
# 공격용 칼 weaponA: 원화 칼의 손잡이·폼멜 자리(원화에서 아래 주먹이 덮어 폼멜이 조각나 있고 손잡이와 떨어져 있음)를
#   시트 칼의 손잡이·폼멜로 바꾼 그림 — 주먹 조각(gNh 등)은 원화 주먹보다 작아 공격 중에 조각난 폼멜이 보였음. 대기·달리기는 원화 칼 그대로
_wa = np.array(img(os.path.join(OUT, 'parts', 'weapon.png'))); _ss = np.array(img(os.path.join(PC, 'sword.png')))
_GB_A, _GB_S, _HX_S = 403, 215, 41.7   # 바꾸기 시작 행(원화 칼 조각 · 시트 칼 = 날밑 아래 끝 +10, 시트 날밑 아래 뾰족한 끝을 피함) · 시트 손잡이 가운데 x
_U0 = int(round(def_parts['weapon']['pivot'][0])); _wa[_GB_A:, :, 3] = 0
_part = _ss[_GB_S:]; _dx = int(round(_U0 - _HX_S)); _h = min(_part.shape[0], _wa.shape[0] - _GB_A)
_dst = _wa[_GB_A:_GB_A + _h, max(0, _dx):max(0, _dx) + _part.shape[1]]; _src = _part[:_h, :_dst.shape[1]]
_al = _src[..., 3:4].astype(float) / 255; _dst[..., :3] = (_src[..., :3] * _al + _dst[..., :3] * (1 - _al)).astype(np.uint8); _dst[..., 3] = np.maximum(_dst[..., 3], _src[..., 3])
Image.fromarray(islands(_wa, 'weaponA')).save(os.path.join(OUT, 'parts', 'weaponA.png'))   # 시트 날밑 끝 부스러기(1~2px) 지움
def_parts['weaponA'] = dict(def_parts['weapon'], src='parts/weaponA.png')
bones.append(dict(name='weaponA', parent='weapon', pos=[0, 0], part='weaponA'))
for _L in {id(rig['draw']): rig['draw'], id(rig['drawA']): rig['drawA']}.values(): _L.insert(_L.index('weapon') + 1, 'weaponA')
rig['hidden'] = rig.get('hidden', []) + ['weaponA']
for k, L in ATK.get('orders', {}).items(): rig[k] = [x for n in L for x in ([n, 'weaponA'] if n == 'weapon' else [n])]
SG = rig['swordGrip']
for k in ('shoulderN', 'shoulderF', 'stretchMax', 'shoulderPush', 'pauldronFollow'):
    if k in ATK: SG[k] = ATK[k]
act = dict(ATK['action']); act.update({'kind': 'sword', 'rigid': True, 'frame': 'torso', 'orderAlways': True})
gx, gy, sa = [], [], []
for t, X, Y, A, *e in ATK['grip']:
    ee = e[0] if e else 'io'; gx.append([t, X, ee]); gy.append([t, Y, ee]); sa.append([t, A, ee])
act.update({'gx': gx, 'gy': gy, 'sa': sa})
rig['actions'] = {'smash': act}
rig['ui']['attack'] = 'smash'
rig['cutHold'] = ATK.get('cutHold', .55)

if ATK.get('overheadKit', {}).get('on'): exec(open(os.path.join(HERE, 'kitoh', 'oh_build.py'), encoding='utf-8').read())   # 머리 위 키트(20:38 DHL 시트) 조각·키
