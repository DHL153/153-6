"""2 러스트 둘시네 — 두 손 내려찍기 v4 (2026-10-19 17:45~18:55, build_dulcinea.py 가 exec)
DHL 14:24 '팔이 꼬임·늘어남' → 15:31 '팔이 어깨에서 빠짐 · 얼굴 뒤로 숨음'(두 손 머리 위) → 17:45 '표시한 팔들이 관절을 무시 · 팔이 늘어나는 것 절대 금지 · 양손 모두'
  원화 팔이 짧고(어깨→주먹 가운데 약 190~200, 키의 0.27) 머리가 커서(키의 0.46) 두 손을 머리 위로 올리면 팔이 어깨에서 빠지거나 얼굴 뒤로 숨음(v2),
  한 손으로 앞으로 뻗으면 먼 팔이 곧게 펴져 관절 없는 관처럼 보임(v3).
  → v4: 두 손은 늘 턱 아래(가슴~배 앞)에서 자루를 쥠. 망치는 머리 뒤로 세웠다가(예비) 손을 축으로 머리 옆을 지나 앞 땅으로 내려침.
  · 먼 팔꿈치는 대기 원화처럼 늘 몸통(재킷) 뒤(ikSide N +1, 한 번도 안 뒤집힘) — 먼 어깨(몸 뒤라 안 보임)를 가운데로 −70~−120 옮겨 팔이 굽은 채 닿게.
  · 가까운 팔꿈치는 잡기~휘두름 아래(+1), 타격 직전 가장 빠른 한 프레임(0.3805~0.389)에 앞 위(−1)로 — 타격·버팀에서 두 주먹이 다 보이게
    (그 한 프레임만 자루 따라 쥔 주먹 gNh, 나머지는 원화 장갑 gNart2 하나).
  자세(G·각도·두 손 사이)는 엔진 그대로 돌리는 풀이(tools/pose_search.py)로 고름. 프레임 검사 tools/frame_table.py:
    늘임 1.00 · 손목 ±47° · 펴짐 ≤ 0.92 · 가까운 윗팔 35~160°(어깨갑 밑에서 아래로) · 먼 윗팔 0~175° · 팔꿈치 얼굴 밖.
  손 순서: 자루 끝 쪽 = 먼 손(G), 쇠 머리 쪽 = 가까운 손(sF 48, 쥐는 동안 그대로 — 손 미끄러짐 없음).
  키는 attack/keys_v4.json (POSE · ikSideK · nPiece · fPiece · 어깨 · 몸 · reach · fade · order).
  엔진 'near' 쪽 = 둘시네 먼 팔(armF 윗팔 · foreF 주먹 · foreFf 팔뚝), 'far' 쪽 = 가까운 팔(armU 윗팔 · armL 주먹 · armLf 팔뚝).
입력 전역: def_parts, bones, O_, pc, HIP, SH_N, EL_N, SH_F, EL_F, WR_F, G, HU, OUT, W, HERE, json, np, os, cv2, Image, ImageDraw
출력: SMASH(rig 에 합칠 dict)"""
def unit(v): v = np.array(v, float); return [round(float(x), 4) for x in v / np.linalg.norm(v)]
# ---- 공 손목(3 러스트 산초 v2 '공 손목 관 팔' 방식): 주먹 = 장갑만, 손목 키 = 쥔 점(주먹 가운데) — 팔뚝 끝을 장갑 밑 가운데까지 이어 그려서
#      팔뚝이 어느 각도로 들어와도 장갑 밑으로 들어감(손목이 꺾인 '팔 없는' 모양이 안 생김). 팔 길이 = 원화 어깨→팔꿈치→주먹 가운데 그대로.
def capsule(a, o, p0, p1, col):   # 원화 좌표 p0→p1 을 a(틀 o) 안에 팔뚝 굵기로 이어 그림 — 이미 불투명한 곳은 그대로
    ax = (p1 - p0) / np.linalg.norm(p1 - p0); hh, ww = a.shape[:2]; yy, xx = np.mgrid[0:hh, 0:ww]; X, Y = xx + o[0], yy + o[1]
    near0 = (np.abs((X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]) < 4) & (a[..., 3] > 200)
    hw = max(6.0, float(np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])[near0].max()) - 1.5)   # 손목 굵기의 반(외곽선 안쪽)
    t = (X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]; d = np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])
    m = (t >= -2) & (t <= np.linalg.norm(p1 - p0) + 2) & (d <= hw) & ~(a[..., 3] > 200)
    a[..., :3][m] = col; a[..., 3][m] = 255; return a, round(hw, 1)
# 가까운 팔: 원화 armL 그림을 같은 틀(같은 크기·같은 자리)로 장갑 주먹(gNart)·팔뚝(afNart) 둘로 — 같은 틀이라 reachW 잡기 시작(reach 0) = 원화 그대로
_A = np.array(Image.open(os.path.join(W, 'armLArt.png')).convert('RGBA')); oL = O_['armL']; _h, _w = _A.shape[:2]
_pm = Image.new('L', (_w, _h), 0)
ImageDraw.Draw(_pm).polygon([(x - oL[0], y - oL[1]) for x, y in [(98, 297), (126, 297), (130, 306), (138, 314), (150, 311), (160, 318), (162, 345), (150, 360), (120, 364), (98, 350)]], fill=255)
_hv = cv2.cvtColor(np.ascontiguousarray(_A[..., :3]), cv2.COLOR_RGB2HSV); _band = (_hv[..., 1] < 70) & (_hv[..., 2] > 140)   # 손목 붕대(크림) = 팔뚝 쪽
_fist = (np.array(_pm) > 0) & ~_band & (_A[..., 3] > 0)
_n, _lb, _st, _ = cv2.connectedComponentsWithStats(_fist.astype(np.uint8), 8); _fist = _lb == (1 + int(np.argmax(_st[1:, cv2.CC_STAT_AREA])))   # 장갑 덩어리 하나만(붕대 부스러기 빼기)
_fore = (_A[..., 3] > 0) & ~_fist
WR2 = np.array([133.0, 309.0]); GRIP_N = np.array([130.0, 332.0])   # 손목(붕대·장갑 사이) · 쥔 점(주먹 가운데 = 공 손목)
_F = _A.copy(); _F[..., 3] = np.where(_fist, _A[..., 3], 0)
_R = _A.copy(); _R[..., 3] = np.where(_fore, _A[..., 3], 0)
_R, _hwN = capsule(_R, oL, WR2, GRIP_N, np.median(_A[..., :3][_band & _fore], 0).astype(np.uint8))
Image.fromarray(_F).save(os.path.join(OUT, 'parts', 'gNart.png')); Image.fromarray(_R).save(os.path.join(OUT, 'parts', 'afNart.png'))
def_parts['gNart'] = dict(src='parts/gNart.png', pivot=pc(GRIP_N, oL), scale=2.0, grip=pc(GRIP_N, oL), wrist=pc(GRIP_N, oL), elbow=pc(GRIP_N, oL),
                          shaftDir=unit([-(EL_N - WR2)[1], (EL_N - WR2)[0]]), fore='afNart', foreBone='armLf', foreDir=unit(EL_N - GRIP_N))   # 자루 = 손목→팔꿈치 방향을 시계 방향 90°
def_parts['afNart'] = dict(src='parts/afNart.png', pivot=pc(GRIP_N, oL), scale=2.0, elbow=pc(EL_N, oL))
# 공격용 가까운 팔뚝 afNart2: 팔꿈치 쪽 끝(원화에선 찢긴 소매 밑에 잘린 살)을 살색 둥근 팔꿈치로 — 팔뚝이 윗팔(소매)보다 앞이라 굽히면 잘린 끝이 보임
_axN = (GRIP_N - EL_N) / np.linalg.norm(GRIP_N - EL_N); _yyN, _xxN = np.mgrid[0:_h, 0:_w].astype(np.float32); _xxN += oL[0]; _yyN += oL[1]
_tN = (_xxN - EL_N[0]) * _axN[0] + (_yyN - EL_N[1]) * _axN[1]; _dN = (_xxN - EL_N[0]) * -_axN[1] + (_yyN - EL_N[1]) * _axN[0]
_hN = cv2.cvtColor(np.ascontiguousarray(_R[..., :3]), cv2.COLOR_RGB2HSV).astype(int); _opN = _R[..., 3] > 200
_skN = _opN & (_hN[..., 0] >= 5) & (_hN[..., 0] <= 18) & (_hN[..., 1] > 110) & (_hN[..., 2] > 140) & (_tN < 8)
_t0N = float(np.percentile(_tN[_skN], 3)) + 1.0 if _skN.any() else -12.0
_bN = _opN & (_tN > _t0N + 1) & (_tN < _t0N + 5); _d0N, _d1N = float(_dN[_bN].min()), float(_dN[_bN].max())
_hwN2 = (_d1N - _d0N) / 2 - .8; _cN = EL_N + _axN * (_t0N + 1.5) + np.array([-_axN[1], _axN[0]]) * ((_d0N + _d1N) / 2)
_R2 = _R.copy(); _R2[..., 3][_tN < _t0N + 1.5] = 0
_capN = (np.hypot(_xxN - _cN[0], _yyN - _cN[1]) <= _hwN2) & (_tN < _t0N + 3)
_R2[..., :3][_capN] = np.median(_R[..., :3][_skN], 0).astype(np.uint8); _R2[..., 3][_capN] = 255
_R2[..., :3][_capN & (np.hypot(_xxN - _cN[0], _yyN - _cN[1]) > _hwN2 - 1.8) & (_tN < _t0N + 1.5)] = np.array([34, 26, 22], np.uint8)
Image.fromarray(_R2).save(os.path.join(OUT, 'parts', 'afNart2.png'))
def_parts['afNart2'] = dict(def_parts['afNart'], src='parts/afNart2.png')
def_parts['gNart2'] = dict(def_parts['gNart'], fore='afNart2')
bones.append(dict(name='armLf', parent='torso', pos=[0, 0], part='afNart'))
print('  smash afNart2 살 시작 t', round(_t0N, 1), '팔꿈치 반지름', round(_hwN2, 1), '(원화 px)')
# 먼 팔: 원화 주먹(fistF, 망치를 쥔 그대로) · 원화 팔뚝(foreF)을 주먹 가운데(G)까지 이어 그린 것 — 대기 = 원화 그대로(이은 곳은 주먹·자루 밑)
oF, oA = O_['fistF'], O_['foreF']
_fa = np.array(Image.open(os.path.join(W, 'foreFArt.png')).convert('RGBA')); _cv = np.zeros((512, 512, 4), np.uint8); _cv[int(oA[1]):int(oA[1]) + _fa.shape[0], int(oA[0]):int(oA[0]) + _fa.shape[1]] = _fa
_wr = (np.hypot(*(np.mgrid[0:512, 0:512][::-1] - WR_F[:, None, None])) < 7) & (_cv[..., 3] > 200)
_cv, _hwF = capsule(_cv, np.zeros(2), WR_F, G, np.median(_cv[..., :3][_wr], 0).astype(np.uint8))
_ys, _xs = np.nonzero(_cv[..., 3] > 0); oA2 = np.array([_xs.min() - 2, _ys.min() - 2], float)
# 공격용 팔뚝 afFart2: 팔꿈치 쪽 끝의 어두운 재킷 소매 끝(원화에선 몸통 옆 재킷 밑)을 살색 둥근 팔꿈치로 — 팔을 들면 몸통 밖으로 나와 얼굴·배 옆에 검은 덩어리로 보였음(10-19 15:45)
_ax = (WR_F - EL_F) / np.linalg.norm(WR_F - EL_F); _yy, _xx = np.mgrid[0:512, 0:512].astype(np.float32)
_t = (_xx - EL_F[0]) * _ax[0] + (_yy - EL_F[1]) * _ax[1]; _dp = (_xx - EL_F[0]) * -_ax[1] + (_yy - EL_F[1]) * _ax[0]
_h2 = cv2.cvtColor(np.ascontiguousarray(_cv[..., :3]), cv2.COLOR_RGB2HSV).astype(int); _op = _cv[..., 3] > 200
_sk = _op & (_h2[..., 0] >= 6) & (_h2[..., 0] <= 18) & (_h2[..., 1] > 120) & (_h2[..., 2] > 150) & (_t < float(np.linalg.norm(WR_F - EL_F)) - 4)   # 원화 팔뚝 살(붕대·이어 그린 곳 빼고)
_t0 = float(np.percentile(_t[_sk], 3)) + 1.0                       # 살이 시작되는 곳(팔꿈치 쪽)
_band = _op & (_t > _t0 + 1) & (_t < _t0 + 5); _d0, _d1 = float(_dp[_band].min()), float(_dp[_band].max())
_hw = (_d1 - _d0) / 2 - .8; _dc = (_d0 + _d1) / 2; _cen = EL_F + _ax * (_t0 + 1.5) + np.array([-_ax[1], _ax[0]]) * _dc
_cv2 = _cv.copy(); _cv2[..., 3][_t < _t0 + 1.5] = 0
_cap = (np.hypot(_xx - _cen[0], _yy - _cen[1]) <= _hw) & (_t < _t0 + 3)
_cv2[..., :3][_cap] = np.median(_cv[..., :3][_sk], 0).astype(np.uint8); _cv2[..., 3][_cap] = 255
_rim = _cap & (np.hypot(_xx - _cen[0], _yy - _cen[1]) > _hw - 1.8) & (_t < _t0 + 1.5)   # 둥근 끝 외곽선(원화 선 굵기)
_cv2[..., :3][_rim] = np.array([34, 26, 22], np.uint8)
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
_au[..., :3][_in & (_dd > _r - 1.8)] = np.array([34, 26, 22], np.uint8)
Image.fromarray(_au).save(os.path.join(OUT, 'parts', 'auFart.png'))
def_parts['auFart'] = dict(src='parts/auFart.png', pivot=[round(float(_p0[0]), 1), round(float(_p0[1]), 1)], scale=2.0, elbow=[round(float(_p1[0]), 1), round(float(_p1[1]), 1)])
bones.append(dict(name='foreFf', parent='torso', pos=[0, 0], part='afFart'))
# 쥔 손 시트(3번 2줄, 1차에서 오려 둔 attack/pieces) — 자루 세로·가로 손: 원화 주먹은 '팔뚝 = 자루에서 시계 반대 97°(가까운)·125°(먼)'로만 쥐어서
#   망치를 세우거나 어깨 뒤로 젖히면 손목이 꺾임(엔진 표 손목 각 80~180°). 먼 손 세로(gFv)는 팔뚝이 오른쪽(먼 어깨 쪽)에서 들어옴.
#   팔·팔뚝은 원화 것 그대로(공 손목: 팔뚝 끝이 장갑 밑 쥔 점까지) — 시트 팔은 안 씀(원화의 2배 길이)
AD = os.path.join(HERE, 'attack'); AP = json.load(open(os.path.join(AD, 'pieces.json')))
for _n in ('gNh', 'gFh'):   # 시트 주먹 중 v4 가 쓰는 둘(자루 따라 쥔 손) — gNv·gFv 는 v4 에서 안 씀
    _j = AP[_n]; _near = _n[1] == 'N'; shutil.copy(os.path.join(AD, 'pieces', _n + '.png'), os.path.join(OUT, 'parts', _n + '.png'))
    _g = [round(float(_j['grip'][0]), 1), round(float(_j['grip'][1]), 1)]
    def_parts[_n] = dict(src=f'parts/{_n}.png', pivot=_g, scale=_j['scale'], grip=_g, wrist=_g, elbow=_g, shaftDir=[float(v) for v in _j['shaftDir']],
                         fore='afNart2' if _near else 'afFart2', foreBone='armLf' if _near else 'foreFf', foreDir=unit(np.array(_j['wrist']) - np.array(_j['grip'])))

print('  smash 공 손목 팔뚝 굵기 반(원화 px): far', _hwF)
_L = lambda *p: round(float(sum(np.linalg.norm(p[i + 1] - p[i]) for i in range(len(p) - 1)) * 2), 1)
print('  smash 원화 먼 팔 길이(리그, 어깨→팔꿈치→주먹 가운데):', _L(SH_F, EL_F, G))

# ---- 시간표 (애니 초) ----
#   잡기: 먼 손이 망치를 가슴 앞으로 세우고 가까운 손이 올라와 쇠 머리 쪽을 잡음 → 예비: 두 손을 가까운 어깨 앞으로, 망치를 어깨 위 뒤로 젖힘(멈칫)
#   → 휘두름: 두 손이 가슴 앞 → 배 앞으로 내려오며 망치가 머리 위를 지나 앞으로 → 타격(쇠 머리 앞 땅) → 버팀 → 들어 올려 가까운 손 놓음 → 대기
GRAB0, GRAB, WIND0, WIND, SW1, SW2, HIT, HOLD, REL0, REL, END = .05, .16, .24, .30, .34, .37, .40, .58, .66, .76, 1.0
k = lambda *kv: [list(x) for x in kv]
_KF = os.environ.get('SMASH_KF', 'keys_v6.json')   # v6(10-19 21:00) — v5 = keys_v5.json, v4 = keys_v4.json
_kv = json.load(open(os.path.join(HERE, 'attack', _KF))) if os.path.exists(os.path.join(HERE, 'attack', _KF)) else {}
#        (시각, gx, gy, 자루 각도, sF(가까운 손 = 먼 손에서 쇠 머리 쪽으로), 보간)   — 먼 손 쥔 점 G(골반 기준 리그 px) · 쇠 머리 방향(라디안, −π/2 = 위)
POSE = _kv.get('POSE') or [(0, 164.6, -10, -.96, 82, 'io'), (GRAB, 40, -60, -1.9, 48, 'io'), (WIND0, 14, -52, -2.2, 48, 'io'), (WIND, 10, -50, -2.3, 48, 'i'),
        (SW1, 40, -80, -1.6, 48, None), (SW2, 90, -60, -.6, 46, 'o'), (HIT, 90, -10, .45, 44, 'o'), (HOLD, 90, -8, .47, 44, 'io'), (REL0, 120, -40, -.3, 44, 'io'), (END - .03, 164.6, -10, -.96, 82, None)]
PT = lambda i: [[p[0], p[i]] + ([p[5]] if p[5] else []) for p in POSE]
smash = {
    'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': END, 'hitAt': HIT, 'hitStop': .10, 'cancelAt': .78, 'reachW': True,
    'aDamp': 30, 'standStep': True,   # 달리다 공격(게임 전투는 늘 달리다 공격): 발을 0.1초 안에 딛고, 달리기 다리 그림 → 원화 다리 그림은 한 프레임 계단(반투명 겹침 없음)
    'ankleRange': [-.45, 1.1], 'legRun': k((0, 0), (SW1 - .01, 0, 'lin'), (SW1 + .02, 1), (HOLD + .04, 1, 'io'), (REL + .045, .12, 'lin'), (REL + .055, 0)),
    'w': k((0, 0, 'io'), (GRAB0 + .04, 1), (END - .03, 1, 'io'), (END, 0)),
    'reach': k((0, 0), (GRAB0, 0, 'io'), (GRAB, 1), (REL0, 1, 'io'), (REL, 0)),
    'sN': k((0, 0)), 'sF': PT(4),
    'nPiece': k((0, 'gFart'), (GRAB0, 'gFart2'), (REL + .06, 'gFart')), 'nUpper': k((0, 'auFart')),   # 먼 팔뚝: 움직이는 동안 살색 둥근 팔꿈치
    'fPiece': k((0, 'gNart'), (GRAB0, 'gNart2'), (REL - .002, 'gNart')), 'fUpper': k((0, 'armU')),   # 가까운 팔뚝: 잡고 있는 동안 살색 둥근 팔꿈치
    'armIK': k((0, 1)), 'ikSideK': _kv.get('ikSideK') or {'N': [[0, 0]], 'F': [[0, 0]]},
    'gx': PT(1), 'gy': PT(2), 'sa': PT(3),
    'shNx': _kv.get('shNx') or k((0, 0)), 'shNy': _kv.get('shNy') or k((0, 0)),   # 가까운 어깨(armU + 어깨갑)
    'shFx': _kv.get('shFx') or k((0, 0)), 'shFy': _kv.get('shFy') or k((0, 0)),   # 먼 어깨(armF, 몸 뒤)
    'hipX': k((0, 0, 'io'), (GRAB, -6, 'io'), (WIND, -12, 'i'), (SW2, 25, 'o'), (HIT, 56, 'o'), (HOLD, 60, 'io'), (REL + .08, 0)),
    'hipY': k((0, 0, 'io'), (GRAB, 8, 'io'), (WIND, 16, 'i'), (SW2, 24, 'o'), (HIT, 40, 'o'), (HIT + .05, 46, 'io'), (HOLD, 44, 'io'), (REL + .08, 0)),
    'lean': k((0, 0, 'io'), (GRAB, -.05, 'io'), (WIND, -.12, 'i'), (SW1, -.02), (SW2, .14, 'o'), (HIT, .30, 'o'), (HOLD, .32, 'io'), (REL + .08, 0)),
    'head': k((0, 0, 'io'), (GRAB, -.02, 'io'), (WIND, -.04, 'i'), (HIT, -.08, 'o'), (HOLD, -.06, 'io'), (REL + .08, 0)),
    'nearDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, -80), (HOLD, -82, 'io'), (REL + .06, 0)),
    'farDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, 85), (HOLD, 85, 'io'), (REL + .06, 0)),
    'farLift': k((0, 0), (SW1, 0, 'io'), (SW2, 14, 'io'), (HIT, 0), (HOLD, 0, 'io'), (HOLD + .06, 10, 'io'), (REL + .06, 0)),
    'shake': k((0, 0), (HIT, 0, 'lin'), (HIT + .01, 1), (HIT + .12, 0)),
    'face': [[0, 'focus'], [GRAB0, 'effort'], [WIND0, 'shout'], [HIT + .14, 'focus'], [REL + .08, None]],
    'fade': {'armLf': k((0, 0), (GRAB0, 0, 'lin'), (GRAB0 + .001, 1), (REL - .001, 1, 'lin'), (REL, 0))},
    'order': _kv.get('order') or [[0, 'drawA'], [.03, 'drawB'], [SW1, 'drawF'], [.86, 'drawA']],
}
for _k, _v in _kv.items():   # keys_v4.json 이 정한 트랙은 그대로 씀(POSE 는 위에서 gx·gy·sa·sF 로 풂)
    if _k != 'POSE' and not _k.startswith('_'): smash[_k] = _v
_ov = os.environ.get('SMASH_KEYS')   # 맞추기용: 키 덮어쓰기 JSON
if _ov: smash.update(json.load(open(_ov)))
# 그리는 순서 — 팔뚝(팔꿈치)은 늘 윗팔·어깨갑보다 앞(DHL), 주먹 맨 앞
#   drawA = 대기(먼 팔뚝 몸 뒤) · drawB = 잡기·예비(망치가 몸통 앞·머리 뒤 = 어깨에 메듯 머리 뒤로 넘어감, 먼 팔뚝 몸 앞) · drawF = 휘두름부터(망치 머리 앞)
DRAW_ATK = ['pony', 'legFar', 'legNear', 'hips', 'flapN', 'flapC', 'belt', 'armF', 'foreFf', 'torso', 'head', 'weapon', 'foreF', 'armU', 'pauldron', 'armLf', 'armL']
DRAW_B = ['pony', 'legFar', 'legNear', 'hips', 'flapN', 'flapC', 'belt', 'armF', 'torso', 'foreFf', 'weapon', 'head', 'foreF', 'armU', 'pauldron', 'armLf', 'armL']
DRAW_F = ['pony', 'legFar', 'legNear', 'hips', 'flapN', 'flapC', 'belt', 'armF', 'torso', 'head', 'foreFf', 'weapon', 'foreF', 'armU', 'pauldron', 'armLf', 'armL']
# v6(DHL 20:58 '망치를 레이어 가장 앞으로'): 망치는 몸·머리·두 팔뚝·어깨갑보다 앞, 자루를 감싼 두 주먹만 망치 위
#   drawH0 = 먼 팔뚝이 몸통 뒤(대기와 같음, 시작·끝) · drawH = 먼 팔뚝이 몸통·머리 앞(두 손이 가슴 앞에서 쥔 동안)
DRAW_H0 = ['pony', 'legFar', 'legNear', 'hips', 'flapN', 'flapC', 'belt', 'armF', 'foreFf', 'torso', 'head', 'armU', 'pauldron', 'armLf', 'weapon', 'weaponA', 'foreF', 'armL']
DRAW_H = ['pony', 'legFar', 'legNear', 'hips', 'flapN', 'flapC', 'belt', 'armF', 'torso', 'head', 'foreFf', 'armU', 'pauldron', 'armLf', 'weapon', 'weaponA', 'foreF', 'armL']
#   weaponA = 쇠 머리 모서리를 고친 망치(원화는 흰 앞머리가 덮던 홈·앞머리 외곽선 조각) — 망치가 대기 자리를 떠난 뒤(.06)부터 돌아오기 전(.93)까지만 보임(fade 계단), 대기는 원화 망치
bones.append(dict(name='weaponA', parent='weapon', pos=[0, 0], part='weaponA'))
SMASH = {'actions': {'smash': smash}, 'drawA': DRAW_ATK, 'drawB': DRAW_B, 'drawF': DRAW_F, 'drawH0': DRAW_H0, 'drawH': DRAW_H,
         'swordGrip': {'tipDepth': -205, 'near': {'upper': 'auFart', 'carry': 'gFart'}, 'far': {'upper': 'armU', 'pieces': ['gNart'], 'sPref': 82}, 'stretchMax': 1.05, 'shoulderPush': 0},
         'swapReset': ['armL'], 'hidden': ['weaponA']}
