"""12 네온 둘시네 — 한 손 내려찍기 (2 러스트 둘시네 v6.4 attack/smash_one.py 를 그대로 옮김, 10-20 08:43 기록, 시험판 p1). build_neon12.py 가 exec.
바꾼 곳: ①대기 자리(첫·끝 키 gx·gy·sa) = 네온 원화 쥔 점·자루 각 ②gFh(휘두를 때 자루 따라 쥔 먼 손) = 네온 시트 21칸(10-20 08:43, attack/pieces/gFh.png — 손목이 자루와 약 65°, 러스트 33°)
  ③그리는 순서에서 포니테일·천자락·허리띠 뺌. 나머지 키·시간표는 러스트 그대로 — 시험판으로 1/60 표를 뽑아 네온 몸에서 걸리는 곳을 찾는 것이 목적.
--- 아래는 러스트 원본 설명 ---
2 러스트 둘시네 — 한 손 내려찍기 v3 (2026-10-19 15:40~, build_dulcinea.py 가 exec)
10-19 21:36 DHL '전에 한 손으로 망치 치던 버전이 좋았는데요, 그걸로' → 커밋 6167bd7 그대로 되살림(동작·키 같음). 더한 것: 공격 중 망치 모서리 정리(weaponA)
DHL 14:24 '팔이 꼬임·늘어남 — 기존의 팔이 움직이도록' → 15:31 '팔이 어깨에서 빠져 없어지고, 다른 한쪽은 얼굴 뒤로 숨음' → 15:36 '다른 것 연구해서 해봐요, 그럼 쉬울 수 있어요'
  원화 팔이 짧고(어깨→주먹 가운데 약 190~200, 키의 0.27) 머리가 커서(키의 0.46) 두 손을 머리 위로 올리면 ①가까운 팔은 어깨갑 밖으로 빠져 보이고
  ②먼 팔은 얼굴을 가로질러야 함(앞에 그리면 얼굴을 가리고 뒤에 그리면 팔이 사라짐) → 큰 무기 꼬마 캐릭터에 흔한 '한 손 내려찍기'(못 박는 망치질 궤적)로 바꿈.
  먼 손(원화에서 망치를 쥔 손)만 망치를 쥔 채 얼굴 오른쪽 위로 들어 올림(쇠 머리가 머리 위 뒤로 넘어감) → 멈칫 → 팔꿈치를 축으로 팔뚝이 앞으로 돌며 내려찍음
  (주먹 그림 그대로 자루가 팔뚝과 거의 직각 = 망치질 손목) → 타격(손 배 오른쪽 앞, 쇠 머리 앞 땅) → 버팀 → 대기. 가까운 팔은 원화 팔 그대로 반대로 흔듦(예비 앞 · 타격 뒤).
  팔은 원화만: 먼 팔 = 원화 주먹(gFart) + 원화 팔뚝을 주먹 가운데까지 이은 것(afFart, 공 손목) + 원화 길이 윗팔(auFart, 몸 뒤). 길이 고정 2관절 IK(엔진 _swordRigid 손목 마디).
  먼 팔꿈치는 늘 얼굴 오른쪽 바깥(풀이로 고름), 먼 팔뚝은 움직이는 동안 머리·몸 앞에 그림.
입력 전역: def_parts, bones, O_, pc, HIP, SH_N, EL_N, SH_F, EL_F, WR_F, G, HU, OUT, W, HERE, json, np, os, cv2, Image, ImageDraw
출력: SMASH(rig 에 합칠 dict)"""
def unit(v): v = np.array(v, float); return [round(float(x), 4) for x in v / np.linalg.norm(v)]
# ---- 공 손목(3 러스트 산초 v2 '공 손목 관 팔' 방식): 주먹 = 장갑만, 손목 키 = 쥔 점(주먹 가운데) — 팔뚝 끝을 장갑 밑 가운데까지 이어 그려서
#      팔뚝이 어느 각도로 들어와도 장갑 밑으로 들어감(손목이 꺾인 '팔 없는' 모양이 안 생김). 팔 길이 = 원화 어깨→팔꿈치→주먹 가운데 그대로.
def capsule(a, o, p0, p1, col, hwmax=None):   # 원화 좌표 p0→p1 을 a(틀 o) 안에 팔뚝 굵기로 이어 그림 — 이미 불투명한 곳은 그대로
    ax = (p1 - p0) / np.linalg.norm(p1 - p0); hh, ww = a.shape[:2]; yy, xx = np.mgrid[0:hh, 0:ww]; X, Y = xx + o[0], yy + o[1]
    near0 = (np.abs((X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]) < 4) & (a[..., 3] > 200)
    hw = max(6.0, float(np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])[near0].max()) - 1.5)   # 손목 굵기의 반(외곽선 안쪽)
    if hwmax: hw = min(hw, hwmax)   # (12 네온) 손목 = 흰 보호대 끝이라 재면 장갑 테두리까지 19px — 주먹 밖으로 삐져나오지 않게 보호대 반지름으로
    t = (X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]; d = np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])
    m = (t >= -2) & (t <= np.linalg.norm(p1 - p0) + 2) & (d <= hw) & ~(a[..., 3] > 200)
    a[..., :3][m] = col; a[..., 3][m] = 255; return a, round(hw, 1)
# 먼 팔: 원화 주먹(fistF, 망치를 쥔 그대로) · 원화 팔뚝(foreF)을 주먹 가운데(G)까지 이어 그린 것 — 대기 = 원화 그대로(이은 곳은 주먹·자루 밑)
oF, oA = O_['fistF'], O_['foreF']
_fa = np.array(Image.open(os.path.join(W, 'foreFArt.png')).convert('RGBA')); _cv = np.zeros((512, 512, 4), np.uint8); _cv[int(oA[1]):int(oA[1]) + _fa.shape[0], int(oA[0]):int(oA[0]) + _fa.shape[1]] = _fa
_wr = (np.hypot(*(np.mgrid[0:512, 0:512][::-1] - WR_F[:, None, None])) < 7) & (_cv[..., 3] > 200)
_gd = (np.hypot(*(np.mgrid[0:512, 0:512][::-1] - WR_F[:, None, None])) < 14) & (_cv[..., 3] > 200) & (_cv[..., :3].min(-1) > 170)   # (12 네온) 흰 손목 보호대 색
_cv, _hwF = capsule(_cv, np.zeros(2), WR_F, G, np.median(_cv[..., :3][_gd if _gd.sum() > 10 else _wr], 0).astype(np.uint8), hwmax=float(os.environ.get('HW_WRIST', 12)))
# 공격용 팔뚝 afFart2: 팔꿈치 쪽 끝의 어두운 재킷 소매 끝(원화에선 몸통 옆 재킷 밑)을 살색 둥근 팔꿈치로 — 팔을 들면 몸통 밖으로 나와 얼굴·배 옆에 검은 덩어리로 보였음(10-19 15:45)
_ax = (WR_F - EL_F) / np.linalg.norm(WR_F - EL_F); _yy, _xx = np.mgrid[0:512, 0:512].astype(np.float32)
_t = (_xx - EL_F[0]) * _ax[0] + (_yy - EL_F[1]) * _ax[1]; _dp = (_xx - EL_F[0]) * -_ax[1] + (_yy - EL_F[1]) * _ax[0]
_h2 = cv2.cvtColor(np.ascontiguousarray(_cv[..., :3]), cv2.COLOR_RGB2HSV).astype(int); _op = _cv[..., 3] > 200
_sk = _op & (_h2[..., 0] >= 6) & (_h2[..., 0] <= 18) & (_h2[..., 1] > 120) & (_h2[..., 2] > 150) & (_t < float(np.linalg.norm(WR_F - EL_F)) - 4)   # 원화 팔뚝 살(붕대·이어 그린 곳 빼고)
_t0 = float(np.percentile(_t[_sk], 3)) + 1.0                       # 살이 시작되는 곳(팔꿈치 쪽)
_band = _op & (_t > _t0 + 1) & (_t < _t0 + 5); _d0, _d1 = float(_dp[_band].min()), float(_dp[_band].max())
_hw = max((_d1 - _d0) / 2 - .8, float(os.environ.get('HW_FAR', 10.5))); _dc = (_d0 + _d1) / 2;   # (12 네온) 팔꿈치·윗팔 굵기 반 = 원화 먼 팔뚝 살 폭 20 + 외곽선 → 10.5 (가는 막대로 보였음)
_hwm = _hw; _cen = EL_F + _ax * (_t0 + 1.5) + np.array([-_ax[1], _ax[0]]) * _dc
_cv2 = _cv.copy(); _cv2[..., 3][_t < _t0 + 1.5] = 0
_cap = (np.hypot(_xx - _cen[0], _yy - _cen[1]) <= _hw) & (_t < _t0 + 3)
_cv2[..., :3][_cap] = np.median(_cv[..., :3][_sk], 0).astype(np.uint8); _cv2[..., 3][_cap] = 255
_rim = _cap & (np.hypot(_xx - _cen[0], _yy - _cen[1]) > _hw - 1.8) & (_t < _t0 + 1.5)   # 둥근 끝 외곽선(원화 선 굵기)
_cv2[..., :3][_rim] = np.array([34, 26, 22], np.uint8)
# (12 네온 10-20 DHL 11:45 타격 0.40 '이상함' 표시) 공격 팔뚝 가장자리 정리 — 원화 팔뚝은 몸통 밑에서 오린 그림이라 ①윗선이 계단처럼 꺾이고 살 부스러기가 붙어 있었고
#   ②흰 손목 보호대 아래로 원화 장갑·자루의 검은 조각이 매달려 있었음(타격 때 주먹 왼쪽 아래에 보임) → 팔뚝 살 부분 = 팔꿈치→손목 축의 곧은 관(위 −9.8→−11.5 · 아래 9.8→12.5, 원화에서 잰 폭)
#   = 둥근 팔꿈치 + 곧은 관 밖은 지우고, 안의 빈칸·잘린 선 조각은 살색(원화 살 색 그대로 둔 곳은 그대로), 가장자리 1.7px 는 원화 선 색 · 보호대 구간은 아래 17.5 밖(매달린 조각)만 지움. 그림·길이·굵기 그대로
def _tidy_fore(a):
    _u = (WR_F - EL_F) / np.linalg.norm(WR_F - EL_F); _n = np.array([-_u[1], _u[0]])
    _T = (_xx - EL_F[0]) * _u[0] + (_yy - EL_F[1]) * _u[1]; _D = (_xx - EL_F[0]) * _n[0] + (_yy - EL_F[1]) * _n[1]
    _tc = _t0 + 1.5; _k = np.clip(_T / 21.0, 0, 1); _top = -10.3 - 1.2 * _k; _bot = 10.3 + 2.2 * _k
    _tube = (((_T >= _tc) & (_D >= _top) & (_D <= _bot)) | (np.hypot(_T - _tc, _D) <= 10.3)) & (_T < 22.5)   # 둥근 팔꿈치 + 곧은 관(손목 보호대 앞까지)
    _zs = (_T < 22.5) & (_T > _tc - 12)
    a[..., 3][(_zs & ~_tube) | ((_T >= 22.5) & (_T <= 47) & (_D > 17.5))] = 0
    _dist = cv2.distanceTransform(np.ascontiguousarray(_tube.astype(np.uint8)), cv2.DIST_L2, 3)
    _inner = _tube & (_dist > 1.7); _sk = _inner & (a[..., 3] > 200) & (a[..., 0] > 150) & (a[..., :3].max(-1) > 110)
    _fix = _inner & ((a[..., 3] < 200) | (a[..., :3].max(-1) < 110))   # 빈칸·안쪽에 남은 잘린 선 → 살색
    a[..., :3][_fix] = np.median(a[..., :3][_sk], 0).astype(np.uint8); a[..., 3][_fix] = 255
    _edge = _tube & (_dist <= 1.7) & ~((_T > 21.0) & (a[..., :3].min(-1) > 150)); a[..., :3][_edge] = np.array([34, 26, 22], np.uint8); a[..., 3][_edge] = 255
    _ge = (_T >= 22.5) & (_T <= 47) & (_D > 16) & (_D <= 17.5) & (a[..., 3] > 128); a[..., :3][_ge] = np.array([22, 20, 24], np.uint8)
    return a
_cv2 = _tidy_fore(_cv2); _cv = _tidy_fore(_cv)
_ys, _xs = np.nonzero((_cv[..., 3] > 0) | (_cv2[..., 3] > 0)); oA2 = np.array([_xs.min() - 2, _ys.min() - 2], float)   # (12 네온) 둥근 팔꿈치 끝이 원래 팔뚝 그림 밖까지 나와서 틀(bbox)을 둘 다로 — 잘려 네모 끝이 됐었음
Image.fromarray(_cv2[int(oA2[1]):_ys.max() + 3, int(oA2[0]):_xs.max() + 3]).save(os.path.join(OUT, 'parts', 'afFart2.png'))
print('  smash afFart2 살 시작 t', round(_t0, 1), '팔꿈치 반지름', round(_hw, 1))
Image.fromarray(_cv[int(oA2[1]):_ys.max() + 3, int(oA2[0]):_xs.max() + 3]).save(os.path.join(OUT, 'parts', 'afFart.png'))
def_parts['gFart'] = dict(src='parts/fistF.png', pivot=pc(G, oF), scale=2.0, grip=pc(G, oF), wrist=pc(G, oF), elbow=pc(G, oF),
                          shaftDir=[round(float(HU[0]), 4), round(float(HU[1]), 4)], fore='afFart', foreBone='foreFf', foreDir=unit(EL_F - G))
def_parts['afFart'] = dict(src='parts/afFart.png', pivot=pc(G, oA2), scale=2.0, elbow=pc(EL_F, oA2))
def_parts['afFart2'] = dict(src='parts/afFart2.png', pivot=pc(G, oA2), scale=2.0, elbow=pc(EL_F, oA2))
def_parts['gFart2'] = dict(def_parts['gFart'], fore='afFart2')   # 같은 원화 주먹, 팔뚝만 공격용(살색 팔꿈치)
# 먼 윗팔 auFart: 원화에선 몸통 뒤라 그림이 없음 → 살색 관(둥근 두 끝 + 원화 굵기 외곽선), 길이 = 원화 어깨→팔꿈치. 굵기 = 공격용 팔뚝 팔꿈치와 같게
#   (가까운 팔의 찢긴 소매 그림을 빌려 쓰면 팔을 들 때 몸통 옆에 올리브 천 조각이 떠 보였음, 10-19 15:50)
_LU = float(np.linalg.norm(EL_F - SH_F)); _r = _hw; _Wd, _Hd = int(_LU + 2 * _r + 6), int(2 * _r + 6)
_uy, _ux = np.mgrid[0:_Hd, 0:_Wd].astype(np.float32); _p0 = np.array([_r + 3, _r + 3]); _p1 = _p0 + np.array([_LU, 0])
_tt = np.clip((_ux - _p0[0]) / _LU, 0, 1); _dd = np.hypot(_ux - (_p0[0] + _tt * _LU), _uy - _p0[1])
_au = np.zeros((_Hd, _Wd, 4), np.uint8); _in = _dd <= _r
_au[..., :3][_in] = np.median(_cv[..., :3][_sk], 0).astype(np.uint8); _au[..., 3][_in] = 255
_sh = _in & (_uy > _p0[1] + _r * .35); _au[..., :3][_sh] = (_au[..., :3][_sh] * .86).astype(np.uint8)   # 아래쪽 그늘
_sl = _in & (_ux < _p0[0] + _LU * .34)   # (12 네온) 어깨 쪽 1/3 = 크롭 탑 남색 짧은 소매(원화 먼 어깨 옆 소매 색) + 소매 끝 선
_au[..., :3][_sl] = (75, 79, 90); _au[..., :3][_sl & (_uy > _p0[1] + _r * .35)] = (60, 63, 73)
_au[..., :3][_in & (np.abs(_ux - (_p0[0] + _LU * .34)) < 1.3)] = (28, 26, 30)
_au[..., :3][_in & (_dd > _r - 1.8)] = np.array([34, 26, 22], np.uint8)
Image.fromarray(_au).save(os.path.join(OUT, 'parts', 'auFart.png'))
def_parts['auFart'] = dict(src='parts/auFart.png', pivot=[round(float(_p0[0]), 1), round(float(_p0[1]), 1)], scale=2.0, elbow=[round(float(_p1[0]), 1), round(float(_p1[1]), 1)])
bones.append(dict(name='foreFf', parent='torso', pos=[0, 0], part='afFart'))
print('  smash 공 손목 팔뚝 굵기 반(원화 px): far', _hwF)
_L = lambda *p: round(float(sum(np.linalg.norm(p[i + 1] - p[i]) for i in range(len(p) - 1)) * 2), 1)
print('  smash 원화 먼 팔 길이(리그, 어깨→팔꿈치→주먹 가운데):', _L(SH_F, EL_F, G))

# (21:42 DHL 타격 0.40 먼 팔 표시 '이 부분만 · 원래 팔로 구부리지 말고') 휘두름~버팀 먼 손 = 시트 '자루 따라 쥔 손'(gFh, 3번 시트 2줄 먼 손) —
#   원화 주먹(gFart)은 팔뚝이 자루에서 125° 라 망치가 앞 아래(4시)면 팔뚝이 위로 서서 팔꿈치가 턱 옆으로 솟았음. gFh 는 팔뚝이 자루를 따라 몸 쪽으로 →
#   팔꿈치는 대기처럼 재킷 뒤(ikSide +1), 보이는 건 원화 팔뚝(붕대) + 주먹
AD = os.environ.get('GFH_DIR') or os.path.join(HERE, 'attack'); AP = json.load(open(os.path.join(AD, 'pieces.json'))); import shutil as _shu
_j = AP['gFh']; _shu.copy(os.path.join(AD, 'pieces', 'gFh.png'), os.path.join(OUT, 'parts', 'gFh.png')); _g = [round(float(_j['grip'][0]), 1), round(float(_j['grip'][1]), 1)]
def_parts['gFh'] = dict(src='parts/gFh.png', pivot=_g, scale=_j['scale'], grip=_g, wrist=_g, elbow=_g, shaftDir=[float(v) for v in _j['shaftDir']],
                        fore='afFart2', foreBone='foreFf', foreDir=unit(np.array(_j['wrist']) - np.array(_j['grip'])))

# ---- 시간표 (애니 초) ----
#   들어 올림(먼 손 얼굴 오른쪽 위, 쇠 머리 머리 위 뒤) 0~0.18 → 멈칫 ~0.27 → 휘두름(팔꿈치 축으로 팔뚝이 앞으로 돌며 내려옴) 0.27~0.40 → 타격 0.40 → 버팀 ~0.58 → 대기 ~0.97
LIFT, WIND, SW1, SW2, HIT, HOLD, RET1, RET, END = .18, .27, .32, .36, .40, .58, .68, .82, 1.0
k = lambda *kv: [list(x) for x in kv]
#        (시각, gx, gy, 자루 각도 — 먼 손 쥔 점 G 골반 기준 리그 px, 쇠 머리 방향 라디안: −π/2 = 위, 보간)
_g0 = (G - HIP) * 2; _a0 = math.atan2(HU[1], HU[0]); _g0x, _g0y = round(float(_g0[0]), 1), round(float(_g0[1]), 1); _a0 = round(_a0, 3)   # 네온 대기 쥔 점·자루 각
POSE = [(0, _g0x, _g0y, _a0, 'io'), (LIFT, 190, -268, -2.6, 'io'), (WIND, 186, -272, -2.65, 'i'), (SW1, 260, -212, -1.8, None), (SW2, 328, -132, -1.1, 'o'),
        (HIT, 216, 0, .4, 'o'), (HOLD, 214, 2, .42, 'io'), (RET1, 313, -23, -.2, 'io'), (RET, 175, -60, -.5, 'io'), (END - .03, _g0x, _g0y, _a0, None)]
_KF = os.path.join(HERE, 'attack', 'keys12.json')   # (10-20 08:43) tools/gen_keys12.py 가 러스트 쥔 점 키를 네온 먼 어깨·팔 길이로 옮긴 값 — 있으면 gx·gy 를 바꿈(자루 각 sa 는 러스트 그대로)
if os.path.exists(_KF) and not os.environ.get('RUST_KEYS'):
    _KG = json.load(open(_KF))['G']; POSE = [(p[0], *_KG[str(p[0])], p[3], p[4]) if str(p[0]) in _KG else p for p in POSE]
    print('  smash keys12.json 쥔 점', len(_KG), '키')
# (10-20 DHL 10:37 '0.35초 표시한 팔 길이가 이상 — 원래 리소스 유지하면서') tools/shoulder12.py: 먼 어깨를 몸(상체·머리) 실루엣 안 깊이 ≥ 20 에 두고
#   쥔 점은 러스트 방향 그대로 팔이 닿는 곳(펴짐 ≤ .86)으로 — 러스트 키는 어깨를 몸 밖 허공(목 옆)으로 밀어 윗팔 관·남색 소매 끝이 보이고 팔이 거의 다 펴졌음(.35초 .96)
#   조각 그림(원화 팔뚝·주먹·윗팔)·팔 길이는 그대로, 자세(어깨 자리·쥔 점)만 바꿈. 들어 올림·예비 = 어깨를 턱·머리카락 뒤로(얼굴 밖 팔꿈치 그대로)
_KB = os.path.join(HERE, 'attack', 'keys12b.json'); K12B = None
if os.path.exists(_KB) and not os.environ.get('RUST_KEYS') and not os.environ.get('NO_K12B'):
    K12B = json.load(open(_KB))['keys']; POSE = [(p[0], *K12B[f'{p[0]:.2f}']['G'], p[3], p[4]) if f'{p[0]:.2f}' in K12B else p for p in POSE]
    print('  smash keys12b.json 어깨·쥔 점', len(K12B), '키')
PT = lambda i: [[p[0], p[i]] + ([p[4]] if p[4] else []) for p in POSE]
SHX12 = float(os.environ.get('SHX12', 22))
def _shk(j):   # keys12b 의 어깨(상체 기준) → shFx·shFy 키(POSE 와 같은 시각·같은 보간)
    v0 = (54.0, -114.0)[j]; return [[p[0], (round(K12B[f'{p[0]:.2f}']['shL'][j] - v0, 1) if f'{p[0]:.2f}' in K12B else 0)] + ([p[4]] if p[4] else []) for p in POSE]
smash = {
    'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': END, 'hitAt': HIT, 'hitStop': .12, 'cancelAt': .78, 'freeArm': True,
    'aDamp': 30, 'standStep': True,   # 달리다 공격(게임 전투는 늘 달리다 공격): 발을 0.1초 안에 딛고, 달리기 다리 그림 → 원화 다리 그림은 한 프레임 계단(반투명 겹침 없음)
    'ankleRange': [-.45, 1.1], 'legRun': k((0, 0), (SW1 - .01, 0, 'lin'), (SW1 + .02, 1), (HOLD + .04, 1, 'io'), (RET + .045, .12, 'lin'), (RET + .055, 0)),   # 서 있는 원화 다리 ↔ 시트 다리 바뀜(fade .05~.1)은 한 프레임에
    'w': k((0, 0, 'io'), (.12, 1), (END - .03, 1, 'io'), (END, 0)),
    'reach': k((0, 0)), 'sN': k((0, 0)),
    'nPiece': k((0, 'gFart'), (.05, 'gFart2'), (SW2, 'gFh'), (RET1, 'gFart2'), (.88, 'gFart')),   # 21:42 휘두름~버팀 = 자루 따라 쥔 먼 손(gFh) — 팔뚝이 몸 쪽으로 누워 팔꿈치가 재킷 옆(턱 옆으로 안 솟음)   # 움직이기 시작하면 공격용 팔뚝(살색 팔꿈치)으로, 대기 자리로 돌아온 뒤 원화 팔뚝으로 'nUpper': k((0, 'auFart')),
    'armIK': k((0, 1)), 'ikSideK': {'N': [[0, 1]]},   # 21:42 DHL '원래 팔로 구부리지 말고' — 먼 팔꿈치는 대기처럼 늘 아래·재킷 쪽(+1), 타격 때 위로 솟는 −1 없앰   # 먼 팔꿈치: 들어 올림~휘두름 = 안쪽으로 접힘(+1) · 타격·버팀 = 팔꿈치가 바깥 위(−1, 못 박는 망치질) — 바꾸는 순간(SW2·RET1)은 팔이 곧게 펴질 때(두 해가 만남)
    'gx': PT(1), 'gy': PT(2), 'sa': PT(3),
    # 먼 어깨(armF, 몸 뒤라 안 보임)를 바깥으로 — 먼 팔꿈치가 늘 얼굴 오른쪽 바깥(풀이 solve/one2.py: 팔꿈치 x ≥ 170)
    'shFx': k((0, 0, 'io'), (LIFT, 30 + SHX12, 'io'), (WIND, 32 + SHX12, 'io'), (SW1, 35 + SHX12), (SW2, 40 + SHX12, 's'), (HIT, -40 + SHX12, 'io'), (HOLD, -40 + SHX12, 'io'), (RET1, 35 + SHX12, 'io'), (RET + .06, 0)),   # (12 네온) + SHX12: 네온 먼 어깨가 러스트보다 22 안쪽(골반 기준 54 vs 76) → 움직이는 동안 러스트 자리로 — 들어 올릴 때 먼 팔꿈치가 턱 옆 머리카락 위에 왔음(표 '팔꿈치얼굴')   # 21:42 타격·버팀 먼 어깨(몸 뒤)를 안쪽 위로 — 팔뚝이 재킷 옆에서 주먹으로, 손목 꺾임 ≈ 30°
    'shFy': k((0, 0, 'io'), (LIFT, -20, 'io'), (WIND, -22, 'io'), (SW1, -10), (SW2, 0, 's'), (HIT, -20, 'io'), (HOLD, -20, 'io'), (RET1, 0, 'io'), (END, 0)),
    **({'shFx': _shk(0), 'shFy': _shk(1)} if K12B else {}),   # SW2→HIT 's'(망치와 같은 내려치기 곡선) — 휘두름 중 팔 펴짐 0.87~0.90
    # 가까운 팔(칼 안 쥔 팔, 원화 그대로): 예비 때 주먹을 앞으로(−), 타격 때 뒤로(+) — 엔진 opt-in freeArm
    'fuA': k((0, 0, 'io'), (LIFT, -.5, 'io'), (WIND, -.55, 'i'), (SW2, .1, 'o'), (HIT, .5, 'o'), (HOLD, .45, 'io'), (RET + .08, 0)),
    'flA': k((0, 0, 'io'), (LIFT, -.6, 'io'), (WIND, -.65, 'i'), (SW2, -.1, 'o'), (HIT, .15, 'o'), (HOLD, .12, 'io'), (RET + .08, 0)),
    'hipX': k((0, 0, 'io'), (LIFT, -10, 'io'), (WIND, -12, 'i'), (SW2, 25, 'o'), (HIT, 56, 'o'), (HOLD, 60, 'io'), (RET + .08, 0)),
    'hipY': k((0, 0, 'io'), (LIFT, 10, 'io'), (WIND, 14, 'i'), (SW2, 24, 'o'), (HIT, 40, 'o'), (HIT + .05, 46, 'io'), (HOLD, 44, 'io'), (RET + .08, 0)),
    'lean': k((0, 0, 'io'), (LIFT, -.12, 'io'), (WIND, -.13, 'i'), (SW1, -.02), (SW2, .14, 'o'), (HIT, .30, 'o'), (HOLD, .32, 'io'), (RET + .08, 0)),
    'head': k((0, 0, 'io'), (LIFT, .05, 'io'), (WIND, .06, 'i'), (HIT, -.08, 'o'), (HOLD, -.06, 'io'), (RET + .08, 0)),
    'nearDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, -80), (HOLD, -82, 'io'), (RET + .06, 0)),
    'farDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, 85), (HOLD, 85, 'io'), (RET + .06, 0)),
    'farLift': k((0, 0), (SW1, 0, 'io'), (SW2, 14, 'io'), (HIT, 0), (HOLD, 0, 'io'), (HOLD + .06, 10, 'io'), (RET + .06, 0)),
    'shake': k((0, 0), (HIT, 0, 'lin'), (HIT + .01, 1), (HIT + .12, 0)),
    'face': [[0, 'focus'], [.08, 'effort'], [WIND, 'shout'], [HIT + .14, 'focus'], [RET + .08, None]],
    # 공격 중 망치 = weaponA(쇠 머리 왼쪽 아래 홈·흰 앞머리 외곽선 초승달 정리, build _fix_hammer) — 대기 자리를 떠난 뒤 .061 ~ 돌아오기 전 .93 (21:40)
    'fade': {'weapon': k((0, 1), (.06, 1, 'lin'), (.061, 0), (.93, 0, 'lin'), (.931, 1)), 'weaponA': k((0, 0), (.06, 0, 'lin'), (.061, 1), (.93, 1, 'lin'), (.931, 0))},
    # 그리는 순서(10-20 12:18 DHL ②공격 = 손·망치가 머리 뒤 ③공격 = 손·망치가 다리 뒤): 공격 내내 한 순서 drawA — 먼 윗팔·팔뚝·망치·쥔 주먹 = 다리·골반·상체·머리 뒤, 가까운 팔만 앞
    #   한 순서라 바뀌는 순간이 없음(앞뒤 튐 0). 대기·달리기 draw 도 같은 앞뒤(build_neon12 draw) — 공격 시작·끝에서도 안 바뀜. 검사 tools/order12.py
    #   (전: v1.3 .36~.725 만 다리 뒤 · 들어 올림 때 주먹이 머리카락 앞 · 돌아옴 때 망치가 골반·다리 앞)
    'order': [[0, 'drawA']],
}
_ov = os.environ.get('SMASH_KEYS')   # 맞추기용: 키 덮어쓰기 JSON
if _ov: smash.update(json.load(open(_ov)))
# sideF(재킷 오른쪽 자락을 20px 늘인 조각)는 먼 팔이 올라가면 몸 옆에 네모 덩어리로 떠 보여서(10-19 15:20) 공격 순서에서 뺌
DRAW_ATK = ['armF', 'foreFf', 'weapon', 'weaponA', 'foreF', 'legFar', 'legNear', 'hips', 'torso', 'head', 'armU', 'pauldron', 'armL']   # (12 네온 10-20 12:18 DHL) 공격 내내: 먼 팔·망치·쥔 주먹 = 다리·골반·상체·머리 뒤(망치∩상체·주먹∩상체는 1/60 전체에서 거의 0 — 상체 앞/뒤는 안 보임)
#   이전 순서 기록: v1.3 drawM(.36~.725) = 이 순서 · drawP/drawU/drawA0 = 다리·골반 뒤 없음, 주먹이 머리 앞 — 12:18 에 하나로 합침
# (12 네온 10-20 DHL 11:23 '갑자기 팔이 막대처럼 나오는 것 이상 · 팔 레이어를 몸 뒤쪽으로') 먼 윗팔·팔뚝(armF·foreFf)은 공격 내내 상체·머리 뒤 — 원화 대기처럼 팔뚝이 몸 뒤에서 나와 주먹으로(그때 주먹 foreF 는 맨 앞 → 12:18 주먹·망치도 다리·머리 뒤). 러스트는 휘두름~돌아옴에 팔뚝이 몸·머리 앞이었음
SMASH = {'actions': {'smash': smash}, 'drawA': DRAW_ATK,
         'swordGrip': {'tipDepth': -205, 'near': {'upper': 'auFart', 'carry': 'gFart'}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': 0}, 'stretchMax': 1.05, 'shoulderPush': 0},
         'hidden': ['weaponA']}
bones.append(dict(name='weaponA', parent='weapon', pos=[0, 0], part='weaponA'))
