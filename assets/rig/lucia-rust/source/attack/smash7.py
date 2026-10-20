"""7 러스트 루시아 — 한 손 도끼 내려찍기 (22 스카이 둘시네 attack/smash22.py = 12 네온 v1.4 구조를 옮김, 10-20 21:xx v1). build_lucia7.py 가 exec.
같은 것: 시간표(들어 올림 .18 · 예비 .27 · 휘두름 .32·.36 · 타격 .40 · 버팀 .58 · 돌아옴 .68·.82)·얼굴·도끼 바꿈(weapon→weaponA)·공격 내내 한 순서(drawA)
바꾼 것: ①쥔 점·자루 각·골반·숙임 키 = attack/keys7.json(tools/keyfit7.py 로 잼 — 루시아 팔: 주먹 = 쥔 점, 팔뚝 = 쥔 점→팔꿈치)
  — 타격·버팀: 날 앞 끝이 땅에 닿게(도끼가 몸 키보다 커서 12 키 그대로면 날이 땅속으로 들어감 — 연구 10-20 20:3x), 손목 꺾임 ±40° 안
  ②먼 팔 조각: 윗팔 = 원화 걷은 갈색 소매 upF(v1.2 — v1 은 민무늬 관 auFart) + 들어 올림~휘두름만 같은 무늬 곧은 관 upFs · 팔뚝 afFart = 원화 살 팔뚝 + 손목 띠 + 주먹 가운데(G)까지 띠 색 관 + 둥근 팔꿈치 끝
  ③먼 주먹 = 내내 원화 주먹(gFart·gFart2 — v1.3, v1.2 까지 휘두름~버팀은 시트 19칸 gFh) ④가까운 팔 = 방패(자유 팔 fuA 를 follow 로 12% 따라 돎)
입력 전역: def_parts, bones, O_, pc, HIP, SH_F, EL_F, WR_F, G, HU, OUT, W, HERE, json, np, os, cv2, Image, own, RA, LUM, SKIN, BLADE_LO, TIPU
출력: SMASH(rig 에 합칠 dict)"""
def unit(v): v = np.array(v, float); return [round(float(x), 4) for x in v / np.linalg.norm(v)]
def capsule(a, o, p0, p1, col, hwmax=None):   # 원화 좌표 p0→p1 을 a(틀 o) 안에 팔뚝 굵기로 이어 그림 — 이미 불투명한 곳은 그대로
    ax = (p1 - p0) / np.linalg.norm(p1 - p0); hh, ww = a.shape[:2]; yy_, xx_ = np.mgrid[0:hh, 0:ww]; X, Y = xx_ + o[0], yy_ + o[1]
    near0 = (np.abs((X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]) < 4) & (a[..., 3] > 200)
    hw = max(6.0, float(np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])[near0].max()) - 1.5) if near0.any() else 8.0
    if hwmax: hw = min(hw, hwmax)
    t = (X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]; d = np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])
    m = (t >= -2) & (t <= np.linalg.norm(p1 - p0) + 2) & (d <= hw) & ~(a[..., 3] > 200)
    a[..., :3][m] = col; a[..., 3][m] = 255; return a, round(hw, 1)
# 먼 팔: 원화 주먹(fistF, 도끼 자루를 쥔 그대로) · 원화 팔뚝(foreF: 살 + 갈색 손목 띠)을 주먹 가운데(G)까지 띠 색으로 이어 그린 것 — 대기 = 원화 그대로(이은 곳은 주먹 밑)
oF, oA = O_['fistF'], O_['foreF']
_fa = np.array(Image.open(os.path.join(W, 'foreFArt.png')).convert('RGBA')); _cv = np.zeros((512, 512, 4), np.uint8); _cv[int(oA[1]):int(oA[1]) + _fa.shape[0], int(oA[0]):int(oA[0]) + _fa.shape[1]] = _fa
_bd = own['foreF'] & ~SKIN & (LUM > 45) & (LUM < 150) & (np.hypot(xx - WR_F[0], yy - WR_F[1]) < 22) & ((xx - WR_F[0]) * (G - WR_F)[0] + (yy - WR_F[1]) * (G - WR_F)[1] > 0)   # 손목 띠 갈색(손목 → 주먹 쪽)
_BDC = np.median(RA[..., :3][_bd], 0).astype(np.uint8) if _bd.sum() > 10 else np.array([110, 60, 40], np.uint8)
_cv, _hwF = capsule(_cv, np.zeros(2), WR_F, G, _BDC, hwmax=float(os.environ.get('HW_WRIST', 11)))
_n_, _lb_, _st_, _ = cv2.connectedComponentsWithStats((_cv[..., 3] > 10).astype(np.uint8), 8)
_cv[..., 3] = np.where(_lb_ == 1 + int(np.argmax(_st_[1:, cv2.CC_STAT_AREA])), _cv[..., 3], 0)
# 팔꿈치 쪽 끝 다듬기(v1.2, DHL 22:44 '각지지 않게'): 원화 팔뚝은 소매 끝 선·보호대에서 잘린 면이라 팔꿈치를 굽히면 모서리·톱니 틈이 보였음
#   → 팔꿈치 둘레(24px) 팔뚝 모양의 볼록 껍질 + 팔꿈치 둥근 끝(반지름 R_E) 을 살색(가까운 원화 살)으로 채우고 새 가장자리에 외곽선
_gy_ = (_cv[..., 3] > 10) & GREY & (np.hypot(xx - EL_F[0], yy - EL_F[1]) < 34); _cv[..., 3][_gy_] = 0   # 팔꿈치 쪽 회색 부스러기(보호대 가시 끝) 빼고 아래에서 살로 메움
_fm = _cv[..., 3] > 10; _er = np.hypot(xx - EL_F[0], yy - EL_F[1]) < float(os.environ.get('ELBOW_ZONE', 30))
_RE = float(os.environ.get('ELBOW_R', 11.0)); _dsc = np.hypot(xx - EL_F[0], yy - EL_F[1]) <= _RE
_hp = cv2.convexHull(np.stack(np.nonzero((_fm & _er) | _dsc)[::-1], 1).astype(np.int32)); _hm = np.zeros((512, 512), np.uint8); cv2.fillPoly(_hm, [_hp], 1)
_add = (_hm > 0) & _er & ~_fm
_skn = _fm & SKIN; _ii2 = ndimage.distance_transform_edt(~_skn, return_distances=False, return_indices=True)
_cv[..., :3][_add] = _cv[..., :3][_ii2[0][_add], _ii2[1][_add]]; _cv[..., 3][_add] = 255
_full = _cv[..., 3] > 10; _edge = _full & ~ndimage.binary_erosion(_full, iterations=2) & dil(_add, 1)
_cv[..., :3][_edge] = np.array([30, 22, 20], np.uint8)
print('  smash 팔뚝 팔꿈치 끝 메움', int(_add.sum()), 'px')
_ys, _xs = np.nonzero(_cv[..., 3] > 0); oA2 = np.array([_xs.min() - 2, _ys.min() - 2], float)
Image.fromarray(_cv[int(oA2[1]):_ys.max() + 3, int(oA2[0]):_xs.max() + 3]).save(os.path.join(OUT, 'parts', 'afFart.png'))
def_parts['gFart'] = dict(src='parts/fistF.png', pivot=pc(G, oF), scale=2.0, grip=pc(G, oF), wrist=pc(G, oF), elbow=pc(G, oF),
                          shaftDir=[round(float(HU[0]), 4), round(float(HU[1]), 4)], fore='afFart', foreBone='foreFf', foreDir=unit(EL_F - G))
def_parts['afFart'] = dict(src='parts/afFart.png', pivot=pc(G, oA2), scale=2.0, elbow=pc(EL_F, oA2))
def_parts['afFart2'] = dict(def_parts['afFart'])
def_parts['gFart2'] = dict(def_parts['gFart'], fore='afFart2')
# 먼 윗팔 (v1.2, DHL 10-20 22:44 '공격의 이 팔이 이상 — 각지지 않게, 원본 팔이 움직이면, 얇은 것도 이상'):
#   v1 은 공격 내내 갈색 민무늬 관(auFart, 반지름 12.5 — 원화 소매 반폭 17~19 의 0.7배)이라 타격·버팀에 보호대 밑으로 가늘고 각진 막대로 보였음
#   → 공격 윗팔 = 원화 걷은 소매 그대로(upF — 뼈 armF 의 원래 그림). 타격·버팀·돌아옴에서 원화 소매가 그대로 돌아 팔뚝으로 이어짐
#   단, 들어 올림~휘두름(팔이 앞·위)에선 원화 소매의 처진 자락·보호대 밑 메움이 팔 아래 덩어리로 드러남(v1 시험 21:5x·이번 확인)
#   → 그 구간만 upFs = 원화 소매 무늬를 뼈(어깨→팔꿈치) 따라 곧게 편 둥근 관(같은 굵기·같은 무늬 — 원화 소매 축 23° 를 뼈 54° 로 돌려 옮김)
#   upFs 는 armF 의 자식 뼈 armFs(같은 틀)라 같은 자리·같은 각, 바꿈 = 투명도 키(도끼 weapon↔weaponA 와 같은 방법)
_LU = float(np.linalg.norm(EL_F - SH_F)); _ub = (EL_F - SH_F) / _LU; _nb = np.array([-_ub[1], _ub[0]])
_slv0 = own['upF'] & ~SKIN & (RA[..., 3] > 200)                                       # 원화 소매(살 빼고)
_slv = _slv0 & ndimage.binary_erosion(own['upF'] & (RA[..., 3] > 200), iterations=2)   # 바깥 외곽선 2px 뺌(안쪽 접힌 주름 선은 그대로)
_sy, _sx = np.nonzero(_slv0); _SP = np.stack([_sx, _sy], 1).astype(float); _sc = _SP.mean(0)
_w_, _v_ = np.linalg.eigh(np.cov((_SP - _sc).T)); _as = _v_[:, 1] if _v_[0, 1] > 0 else -_v_[:, 1]; _ns = np.array([-_as[1], _as[0]])   # 소매 축(몸 → 소매 끝)
_sd = (_SP - EL_F) @ _ns; _sl, _sh_ = np.percentile(_sd, 3), np.percentile(_sd, 97); _SOFF = float((_sl + _sh_) / 2)   # 소매 가운데 줄 = 팔꿈치에서 축 옆으로 _SOFF(폭 가운데)
_RS = float(os.environ.get('UPS_R', min(16.0, (_sh_ - _sl) / 2)))                  # 관 반폭 = 원화 소매 반폭
_SMAX = float(os.environ.get('UPS_SMAX', 50.0))                                     # 원화 소매에서 가져올 범위(팔꿈치에서 50 — 그 너머는 튜닉 조각)
_PER = float(os.environ.get('UPS_PER', 16.0))                                       # 비는 곳 = 소매 축 따라 감은 주름 한 칸(16px)씩 옮겨 가져옴
_CAPE = float(os.environ.get('UPS_CAP', 8.0))                                       # 팔꿈치 쪽 끝 = 납작한 둥근 끝(축 방향 8, 팔뚝을 덜 가림)
_pad = _RS + 4; _ox, _oy = int(min(SH_F[0], EL_F[0]) - _pad), int(min(SH_F[1], EL_F[1]) - _pad); _cw, _ch = int(abs(EL_F[0] - SH_F[0]) + 2 * _pad), int(abs(EL_F[1] - SH_F[1]) + 2 * _pad)
_SS = 4                                                                             # 4배로 그려 줄임(가장자리·주름 선 계단 없게)
_Y, _X = np.mgrid[0:_ch * _SS, 0:_cw * _SS].astype(np.float32); _X = _X / _SS + _ox + .5 / _SS - .5; _Y = _Y / _SS + _oy + .5 / _SS - .5
_t = (_X - SH_F[0]) * _ub[0] + (_Y - SH_F[1]) * _ub[1]; _d = (_X - SH_F[0]) * _nb[0] + (_Y - SH_F[1]) * _nb[1]
_te = np.where(_t > _LU, (_t - _LU) * (_RS / _CAPE), np.where(_t < 0, _t, 0))       # 끝 둥글기: 팔꿈치 쪽은 타원(축 8)
_dist = np.hypot(_te, _d); _in = _dist <= _RS
_s = _LU - _t                                                                       # 팔꿈치에서 거리
_RAf = RA[..., :3].astype(np.float32); _slvf = _slv.astype(np.float32); _CRM = (LUM > 150) & _slv   # 크림 밝은 줄(원화 한 줄 — 옮겨 온 칸에선 안 씀)
_us = np.zeros(_X.shape + (3,), np.float32); _ok = np.zeros(_X.shape, bool)
for _m in [0, 1, -1, 2, -2, 3, -3]:   # 0 = 같은 자리, 그다음 주름 한 칸씩 몸 쪽·팔꿈치 쪽으로 옮겨 빈 곳 채움
    _ss = _s + _m * _PER; _QX = (EL_F[0] + _SOFF * _ns[0] - _ss * _as[0] + _d * _ns[0]).astype(np.float32); _QY = (EL_F[1] + _SOFF * _ns[1] - _ss * _as[1] + _d * _ns[1]).astype(np.float32)
    _vm = cv2.remap(_slvf, _QX, _QY, cv2.INTER_LINEAR, borderValue=0) > .99
    if _m: _vm &= cv2.remap(_CRM.astype(np.float32), _QX, _QY, cv2.INTER_LINEAR, borderValue=0) < .01
    _v = _in & ~_ok & _vm & (_ss <= _SMAX) & (_ss >= -2)
    _col = cv2.remap(_RAf, _QX, _QY, cv2.INTER_LINEAR, borderValue=0); _us[_v] = _col[_v]; _ok |= _v
_miss = _in & ~_ok
if _miss.any():   # 그래도 빈 곳 = 가까운 소매 픽셀
    _ii = ndimage.distance_transform_edt(~_ok, return_distances=False, return_indices=True); _us[_miss] = _us[_ii[0][_miss], _ii[1][_miss]]
_OLW = 2.2; _ol = np.clip((_dist - (_RS - _OLW)) / .6, 0, 1)[..., None]               # 외곽선(원화 선 색, 안쪽으로 부드럽게)
_us = _us * (1 - _ol) + np.array([30, 22, 20], np.float32) * _ol
_al = np.clip((_RS - _dist) / .6 + .5, 0, 1)
_us4 = np.dstack([_us * _al[..., None], _al * 255])                                 # 미리 곱한 알파로 줄임 → 가장자리 어둡게 안 번짐
_us4 = cv2.resize(_us4, (_cw, _ch), interpolation=cv2.INTER_AREA); _a1 = _us4[..., 3:] / 255
_us = np.dstack([np.where(_a1 > 1e-3, _us4[..., :3] / np.maximum(_a1, 1e-3), 0), _us4[..., 3:]]).clip(0, 255).astype(np.uint8)
_miss = cv2.resize(_miss.astype(np.float32), (_cw, _ch), interpolation=cv2.INTER_AREA) > .5
Image.fromarray(_us).save(os.path.join(OUT, 'parts', 'upFs.png'))
_o_us = np.array([_ox, _oy], float)
def_parts['upFs'] = dict(src='parts/upFs.png', pivot=pc(SH_F, _o_us), scale=2.0, elbow=pc(EL_F, _o_us))
bones.append(dict(name='armFs', parent='armF', pos=[0, 0], part='upFs'))
print(f'  smash 윗팔: 원화 소매(upF) + 곧은 소매 관 upFs 반폭 {_RS:.1f} · 소매 축 {np.degrees(np.arctan2(_as[1], _as[0])):.1f}° (뼈 {np.degrees(np.arctan2(_ub[1], _ub[0])):.1f}°) · 가운데 줄 {_SOFF:+.1f} · 메움 {int(_miss.sum())}px')
bones.append(dict(name='foreFf', parent='torso', pos=[0, 0], part='afFart'))
print('  smash 손목 띠 관 굵기 반(원화 px)', _hwF, '· 띠 색', _BDC.tolist())
# (v1.2 까지) 휘두름~버팀 먼 손 = 시트 19칸 '자루 따라 쥔 손'(gFh, tools/gfh7.py) — v1.3 부터 안 씀: 원화 주먹이 손목 ±40° 안에 들고, 시트 손은 펴진 손바닥(악수)처럼 보였음(DHL 23:29)
if os.environ.get('GFH') == '1':   # 비교용으로만 되살림
    AD = os.environ.get('GFH_DIR') or os.path.join(HERE, 'attack'); AP = json.load(open(os.path.join(AD, 'pieces.json')))
    _j = AP['gFh']; shutil.copy(os.path.join(AD, 'pieces', 'gFh.png'), os.path.join(OUT, 'parts', 'gFh.png')); _g = [round(float(_j['grip'][0]), 1), round(float(_j['grip'][1]), 1)]
    def_parts['gFh'] = dict(src='parts/gFh.png', pivot=_g, scale=_j['scale'], grip=_g, wrist=_g, elbow=_g, shaftDir=[float(v) for v in _j['shaftDir']],
                            fore='afFart2', foreBone='foreFf', foreDir=unit(np.array(_j['wrist']) - np.array(_j['grip'])))

# ---- 시간표 (애니 초) — 12·22 와 같음 ----
LIFT, WIND, SW1, SW2, HIT, HOLD, RET1, RET, END = .18, .27, .32, .36, .40, .58, .68, .82, 1.0
k = lambda *kv: [list(x) for x in kv]
UPS_T = [float(v) for v in os.environ.get('UPS_T', '0.09,0.36').split(',')]   # 곧은 소매 관을 쓰는 구간(들어 올림 시작 ~ 휘두름 가장 빠른 때 .36)
KF = json.load(open(os.environ.get('KEYS7') or os.path.join(HERE, 'attack', 'keys7.json')))
KEYS = KF['keys']   # [t, gx, gy(리그 px, 골반 기준), 자루 각(도), 숙임(rad), 골반 x, 골반 y, 쥔 손(키 표 확인용), 이음]
_g0 = (G - HIP) * 2; _a0 = math.atan2(HU[1], HU[0])
assert abs(KEYS[0][1] - _g0[0]) < 1 and abs(KEYS[0][2] - _g0[1]) < 1 and abs(math.radians(KEYS[0][3]) - _a0) < .01, ('keys7 0 키 = 대기 쥔 점·자루 각이어야 함', _g0, math.degrees(_a0))
EZ = lambda r: r[8] if len(r) > 8 and r[8] else None
PT = lambda i, f=lambda v: v: [[r[0], round(f(r[i]), 4)] + ([EZ(r)] if EZ(r) else []) for r in KEYS]
smash = {
    'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': END, 'hitAt': HIT, 'hitStop': .12, 'cancelAt': .78, 'freeArm': True,
    'aDamp': 30, 'standStep': True,
    'ankleRange': [-.45, 1.1], 'legRun': k((0, 0), (SW1 - .01, 0, 'lin'), (SW1 + .02, 1), (HOLD + .04, 1, 'io'), (RET + .045, .12, 'lin'), (RET + .055, 0)),
    'w': k((0, 0, 'io'), (.12, 1), (END - .03, 1, 'io'), (END, 0)),
    'reach': k((0, 0)), 'sN': k((0, 0)),
    'nPiece': k((0, 'gFart'), (.05, 'gFart2'), (.88, 'gFart')),   # v1.3: 먼 손 = 내내 원화 주먹(gFh 바꿈 없음 — 시트 손은 악수처럼 펴져 보였음)
    'armIK': k((0, 1)), 'ikSideK': {'N': [[0, 1]]},
    'gx': PT(1), 'gy': PT(2), 'sa': PT(3, math.radians), 'lean': PT(4), 'hipX': PT(5), 'hipY': PT(6),
    'fuA': k((0, 0)),   # 자유 팔 = 방패 뒤 빈 뼈(방패는 상체 숙임을 60% 되돌려 세움 — build follow)
    'flA': k((0, 0)),
    'head': k((0, 0, 'io'), (LIFT, .05, 'io'), (WIND, .06, 'i'), (HIT, -.08, 'o'), (HOLD, -.06, 'io'), (RET + .08, 0)),
    'nearDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, 10), (HOLD, 9, 'io'), (RET + .06, 0)),
    'farDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, 10), (HOLD, 10, 'io'), (RET + .06, 0)),   # v1.5(DHL 10-21 00:10 '표시한 다리를 왼쪽으로 — 손·도끼에 걸리지 않게 살짝') 64 → 10: 먼 다리 ↔ 손·도끼 겹침 최대 2493px → 0, 가장 가까운 틈 8 리그 px(서서·달리다 같음)
    'farLift': k((0, 0), (SW1, 0, 'io'), (SW2, 11, 'io'), (HIT, 0), (HOLD, 0, 'io'), (HOLD + .06, 8, 'io'), (RET + .06, 0)),
    'shake': k((0, 0), (HIT, 0, 'lin'), (HIT + .01, 1), (HIT + .12, 0)),
    'face': [[0, 'angry'], [WIND, 'shout'], [HIT + .14, 'angry'], [RET + .08, None]],   # v1.4(DHL 23:58 '공격할때 눈 감지 않도록') — 힘줌(effort = 두 눈 꽉 감음)·집중(focus = 눈꺼풀 반 내림) 대신 화남(눈 뜸) → 외침(눈 크게) → 화남
    'fade': {'weapon': k((0, 1), (.06, 1, 'lin'), (.061, 0), (.93, 0, 'lin'), (.931, 1)), 'weaponA': k((0, 0), (.06, 0, 'lin'), (.061, 1), (.93, 1, 'lin'), (.931, 0)),
             'armF': k((0, 1), (UPS_T[0], 1, 'lin'), (UPS_T[0] + .001, 0), (UPS_T[1], 0, 'lin'), (UPS_T[1] + .001, 1)),     # 윗팔: 원화 소매 ↔ 곧은 소매 관(들어 올림~휘두름)
             'armFs': k((0, 0), (UPS_T[0], 0, 'lin'), (UPS_T[0] + .001, 1), (UPS_T[1], 1, 'lin'), (UPS_T[1] + .001, 0))},
    'order': [[0, 'drawA']],
}
for _k, _v in (KF.get('tracks') or {}).items(): smash[_k] = _v   # keys7.json 'tracks' = 트랙 통째로 바꿈(시험)
_ov = os.environ.get('SMASH_KEYS')
if _ov: smash.update(json.load(open(_ov)))
# 그리는 순서(공격 내내 한 순서): 먼 팔뚝·도끼·쥔 주먹 = 다리·골반·머리 뒤(12 v1.4) · 다리 = 상체·골반 뒤(v1.1 DHL 21:44 '다리를 옷 뒤로' — 대기 순서와 같은 규칙)
#   먼 윗팔(소매) = 상체 앞(원화: 소매가 튜닉 앞) · 보호대 · 방패 · 가까운 주먹
DRAW_ATK = ['foreFf', 'weapon', 'weaponA', 'foreF', 'legFar', 'legNear', 'torso', 'armF', 'armFs', 'hips', 'head', 'pauldronF', 'armU', 'armL', 'shield', 'fistN']
# 땅 막기(엔진: 날 가운데 점 y > tipDepth 면 자루를 세움): 타격 키 자세의 날 가운데 높이 + 여유 6 — 키대로면 안 걸림, 보간이 넘칠 때만
_hk = [r for r in KEYS if abs(r[0] - HIT) < 1e-6][0]; _Gy = (HIP[1] - O[1]) * 2 + _hk[6] + _hk[2]
TIPD = round(_Gy + math.sin(math.radians(_hk[3])) * TIPU * 2 + 6, 1)
SMASH = {'actions': {'smash': smash}, 'drawA': DRAW_ATK,
         'swordGrip': {'tipDepth': TIPD, 'near': {'upper': 'upF', 'carry': 'gFart'}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': 0}, 'stretchMax': 1.05, 'shoulderPush': 0},
         'hidden': ['weaponA', 'armFs']}
bones.append(dict(name='weaponA', parent='weapon', pos=[0, 0], part='weaponA'))
print('  smash tipDepth', TIPD, '· 키', len(KEYS))
