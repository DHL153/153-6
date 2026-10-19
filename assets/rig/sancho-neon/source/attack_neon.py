# 13 네온 산초 올려베기 (2026-10-19) — build_neon.py 끝에서 exec (rig, def_parts, bones, np, math, json, os, HERE, PC, OUT, img, JT 사용)
#  3 러스트 산초 attack_sancho.py 와 같은 구조: rigid 칼(칼 먼저, 쥔 팔 조각이 칼에 붙음) + 공 손목 관 팔(윗팔·팔뚝 길이 고정) — 키는 attack_keys.json(tools/gen_keys.py)
#  · 엔진 이름: near(armF→foreF) = 위 주먹·가까운 팔 · far(armU→armL) = 아래 주먹·먼 팔 + 먼 어깨 보호대
#  · 엔진 트랙 shNx·shNy 는 armU(= 산초 먼 어깨 + 보호대)를, shFx·shFy 는 armF(= 산초 가까운 어깨)를 옮김 (이름이 21 기준이라 반대)
#  · 가까운 팔꿈치 쪽 ikSideK: 대기 −1(팔꿈치 왼쪽 아래 = 원화) → 두 손이 어깨 앞에서 팔이 다 접힌 순간(0.17) +1 → 돌아올 때 접힌 순간(0.76) −1 — 접힌 자리에선 두 쪽 팔꿈치가 같은 점(튐 없음)
ATK = json.load(open(os.path.join(HERE, 'attack_keys.json'), encoding='utf-8'))
TB = JT['tubes']; K_ACROSS = 2.2   # 시트 팔 조각 폭 25~28 ×2.2 = 55~62 리그 ≈ 원화 팔 굵기 28~30
def tube(nm, src, y_piv, y_el, L, k=None):
    """시트 관 그림 → 리그 그림(scale 1). y_piv = pivot 끝(관 가운데 줄), y_el = elbow 끝. k(리그/시트 px, 세로): 주면 pivot 줄을 그림 밖까지 옮겨 길이를 맞춤
    — 손목·어깨 끝은 주먹·어깨 보호대 밑이라 그림을 덜 늘임(갑옷 판이 늘어나 보이지 않게)"""
    a, _ = desp(np.array(img(os.path.join(PC, src + '.png'))))
    if k: y_piv = y_el + (L / k) * (1 if y_piv > y_el else -1)
    kL = L / abs(y_el - y_piv); H, Wd = a.shape[:2]
    im = Image.fromarray(a).resize((round(Wd * K_ACROSS), round(H * kL)), Image.LANCZOS); cx = (Wd / 2) * K_ACROSS
    im.save(os.path.join(OUT, 'parts', nm + '.png')); def_parts[nm] = dict(src=f'parts/{nm}.png', pivot=[round(cx, 1), round((y_piv + .5) * kL, 1)], elbow=[round(cx, 1), round((y_el + .5) * kL, 1)], scale=1.0)
    print('  tube', nm, src, im.size, 'len', L, 'kL', round(kL, 2), 'pivot row', round(y_piv, 1))
tube('armFt', 'upperN', 7, 40, TB['upperN'])              # 가까운 윗팔: 위 = 어깨 둥근 끝, 아래 = 팔꿈치
tube('armUt', 'upperF', 6, 31, TB['upperF'], k=2.6)       # 먼 윗팔
tube('foreFt', 'foreN', 33, 6, TB['foreN'], k=2.6)        # 가까운 팔뚝: 위 = 팔꿈치, 아래 = 손목(주먹 밑)
tube('armLft', 'foreF', 54, 7, TB['foreF'], k=2.5)        # 먼 팔뚝(길게 그려진 흰 판)
GLOVE_N = [(221, 283), (231, 278), (246, 279), (254, 288), (257, 300), (255, 312), (247, 318), (232, 318), (224, 312), (219, 300)]   # 위 주먹(장갑만, 원화 px)
GLOVE_F = [(233, 317), (243, 311), (258, 312), (266, 320), (268, 334), (264, 346), (252, 351), (240, 349), (232, 340), (230, 326)]   # 아래 주먹
def glove(nm, src_png, origin, poly_art, grip_art, fore, fbone):
    a = np.array(Image.open(src_png)); m = Image.new('L', (a.shape[1], a.shape[0]), 0); ImageDraw.Draw(m).polygon([(x - origin[0], y - origin[1]) for x, y in poly_art], fill=255)
    m = cv2.GaussianBlur(np.array(m).astype(np.float32), (3, 3), 0.7) / 255; a = a.copy(); a[..., 3] = (a[..., 3] * m).astype(np.uint8)
    Image.fromarray(a).save(os.path.join(OUT, 'parts', nm + '.png')); gp = pc(grip_art, origin)
    def_parts[nm] = dict(src=f'parts/{nm}.png', pivot=gp, elbow=gp, grip=gp, wrist=gp, shaftDir=SD, scale=2.0, fore=fore, foreBone=fbone, foreDir=[0.0, 1.0])
glove('foreFk', os.path.join(W, 'nForeArt.png'), o_nF, GLOVE_N, G_U, 'foreFt', 'foreFf')
glove('armLk', os.path.join(W, 'fForeArt.png'), o_fF, GLOVE_F, G_L, 'armLft', 'armLf')
bones.append(dict(name='foreFf', parent='armF', pos=[0, 0], part='foreFt'))
# 원화 팔 사본(대기 자리 그대로, 상체에 붙음) — 공격 처음·끝 겹쳐 바꾸기용
bone('armF0', 'torso', SH_N, HIP, 'armF'); bone('foreF0', 'armF0', EL_N, SH_N, 'foreF')
bone('armU0', 'torso', SH_F, HIP, 'armU'); bone('armL0', 'armU0', EL_F, SH_F, 'armL'); bone('armLf0', 'armU0', WR_F, SH_F, 'armLf')
rig['hidden'] = rig.get('hidden', []) + ['armF0', 'foreF0', 'armU0', 'armL0', 'armLf0']
act = dict(ATK['action']); act.update({'kind': 'sword', 'rigid': True, 'frame': 'torso', 'orderAlways': True})
gx, gy, sa = [], [], []
_idle = (round(float(GX), 1), round(float(GY), 1), round(ang(U), 4))
for t, X, Y, A, *e in ATK['grip']:
    if X == 'idle': X, Y, A = _idle
    ee = e[0] if e else 'io'; gx.append([t, X, ee]); gy.append([t, Y, ee]); sa.append([t, A, ee])
act.update({'gx': gx, 'gy': gy, 'sa': sa})
for k, L in ATK.get('orders', {}).items(): rig[k] = L
rig['actions'] = {'upslash': act}
rig['ui']['attack'] = 'upslash'
rig['cutHold'] = ATK.get('cutHold', .5)
if ATK.get('torsoTwist'):   # 가까운 어깨를 shFx 만큼 앞으로 옮길 때 상체 그림의 가까운 어깨 쪽도 같이 옮김(메시 상체 torsoTw)
    shutil.copy(os.path.join(OUT, 'parts', 'torso.png'), os.path.join(OUT, 'parts', 'torsoTw.png'))
    def_parts['torsoTw'] = dict(def_parts['torso'], src='parts/torsoTw.png', mesh={'cols': 12, 'rows': 10})
    _TT = ATK['torsoTwist']; rig['torsoTwist'] = dict(bone='torso', part='torsoTw', sx=round(float(SH_N[0] - HIP[0]) * 2, 1), sy=round(float(SH_N[1] - HIP[1]) * 2, 1), ax=_TT['ax'], by=_TT['by'], p=_TT.get('p', 1))
print('  attack: idle grip', _idle, 'keys', len(gx), 'ikSideK', act.get('ikSideK'))
