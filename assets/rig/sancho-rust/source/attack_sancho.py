# 3 러스트 산초 올려베기 (2026-10-19) — build_sancho.py 끝에서 exec (rig, def_parts, bones, np, math, json, os, HERE, PC, OUT, img 사용)
#  rigid 칼(칼 먼저, 쥔 팔 조각이 칼에 붙음) + armIK(윗팔·팔뚝 길이 고정 두 관절) — 11 네온 알론소 v5.4 방식, 키는 attack_keys.json
#  · 엔진 이름: near(armF→foreF) = 위 주먹·가까운 팔 · far(armU→armL) = 아래 주먹·먼 팔 + 어깨갑
#  · 엔진 트랙 shNx·shNy 는 armU(= 산초 먼 어깨 + 어깨갑)를, shFx·shFy 는 armF(= 산초 가까운 어깨)를 옮김 (이름이 21 기준이라 반대)
ATK = json.load(open(os.path.join(HERE, 'attack_keys.json'), encoding='utf-8'))
#  · 먼 팔은 손목 마디(armL 주먹 + armLf 팔뚝, 엔진 wristArm) — 칼이 한 바퀴 돌아도 조각 바꾸기 없음
# ---------------- 공격 팔 (10-19 08:12 DHL '한쪽 팔이 떨어졌다 붙었다 — 신체구조 무시' · '칼 잡은 손 레이어가 가장 앞') ----------------
#  원화 팔은 짧게 겹친(앞으로 뻗은) 그림이라 팔을 펴면 주먹과 소매가 떨어져 보였음 → 공격 동안은 어깨→윗팔(소매 관)→팔꿈치→팔뚝(붕대 관)→주먹이 늘 이어지는 사슬:
#  · 윗팔·팔뚝 = 조각 시트 관(upperA·foreA 가까운, upperB·foreB 먼), 주먹 = 원화 장갑만(손목 붕대 뺌) — 손목 마디는 주먹 가운데(쥔 점, 공 관절): 팔뚝이 어느 쪽에서 들어와도 장갑 밑
#  · 대기 원화 팔과는 겹쳐 바꿈: 공격 처음 원화 팔 사본(armF0·foreF0·armU0·armL0·armLf0)이 위에 있다가 사라지고, 끝에 다시 나타난 뒤 원화 팔로(사라졌다 나타나는 조각 없음)
AR = ATK['arms']; K_ACROSS = AR['across']
def _desp(a):
    a = a.astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None); a[..., 0] -= m; a[..., 2] -= m; return np.clip(a, 0, 255).astype(np.uint8)
def tube(nm, src, y0, y1, L, rep=None):
    """시트 관 그림 → 리그 그림(scale 1). y0 = pivot 끝(관 가운데 줄), y1 = elbow 끝. rep = (a, b): 이 줄들을 되풀이해 길이를 맞춤(붕대 무늬가 늘어나 보이지 않게)"""
    a = _desp(np.array(img(os.path.join(PC, src + '.png'))))
    if rep:
        ra, rb = rep; n = 0
        while True:
            seg = np.concatenate([a[:ra]] + [a[ra:rb]] * n + [a[rb:]], 0); yy1 = y1 + (rb - ra) * n if y1 > rb else y1; yy0 = y0 + (rb - ra) * n if y0 > rb else y0
            if abs(yy1 - yy0) * K_ACROSS >= L * 0.97 or n > 12: break
            n += 1
        a, y0, y1 = seg, yy0, yy1
    kL = L / abs(y1 - y0); H, Wd = a.shape[:2]
    im = Image.fromarray(a).resize((round(Wd * K_ACROSS), round(H * kL)), Image.LANCZOS); cx = (Wd / 2) * K_ACROSS
    im.save(os.path.join(OUT, 'parts', nm + '.png')); def_parts[nm] = dict(src=f'parts/{nm}.png', pivot=[round(cx, 1), round((y0 + .5) * kL, 1)], elbow=[round(cx, 1), round((y1 + .5) * kL, 1)], scale=1.0)
    print('  tube', nm, im.size, 'len', L, 'kL', round(kL, 2), 'rep', rep)
tube('armFt', 'upperA', 6, 31, AR['upperN']); tube('armUt', 'upperB', 6, 31, AR['upperF'])
tube('foreFt', 'foreA', 29, 4, AR['foreN'], rep=(9, 23)); tube('armLft', 'foreB', 32, 4, AR['foreF'], rep=(9, 24))
def glove(nm, src_png, origin, poly, grip_art, fore, fbone):
    a = np.array(Image.open(src_png)); m = Image.new('L', (a.shape[1], a.shape[0]), 0); ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
    m = cv2.GaussianBlur(np.array(m).astype(np.float32), (3, 3), 0.7) / 255; a = a.copy(); a[..., 3] = (a[..., 3] * m).astype(np.uint8)
    Image.fromarray(a).save(os.path.join(OUT, 'parts', nm + '.png')); gp = pc(grip_art, origin)
    def_parts[nm] = dict(src=f'parts/{nm}.png', pivot=gp, elbow=gp, grip=gp, wrist=gp, shaftDir=SD, scale=2.0, fore=fore, foreBone=fbone, foreDir=[0.0, 1.0])
glove('foreFk', os.path.join(W, 'nForeArt.png'), o_nF, AR['gloveN'], G_U, 'foreFt', 'foreFf')
glove('armLk', os.path.join(W, 'fForeArt.png'), o_fF, AR['gloveF'], G_L, 'armLft', 'armLf')
bones.append(dict(name='foreFf', parent='armF', pos=[0, 0], part='foreFt'))
# 원화 팔 사본(대기 자리 그대로, 상체에 붙음) — 공격 처음·끝 겹쳐 바꾸기용
bone('armF0', 'torso', SH_N, HIP, 'armF'); bone('foreF0', 'armF0', EL_N, SH_N, 'foreF')
bone('armU0', 'torso', SH_F, HIP, 'armU'); bone('armL0', 'armU0', EL_F, SH_F, 'armL'); bone('armLf0', 'armU0', WR_F, SH_F, 'armLf')
rig['hidden'] = rig.get('hidden', []) + ['armF0', 'foreF0', 'armU0', 'armL0', 'armLf0']
act = dict(ATK['action']); act.update({'kind': 'sword', 'rigid': True, 'frame': 'torso', 'orderAlways': True})
gx, gy, sa = [], [], []
for t, X, Y, A, *e in ATK['grip']:
    ee = e[0] if e else 'io'; gx.append([t, X, ee]); gy.append([t, Y, ee]); sa.append([t, A, ee])
act.update({'gx': gx, 'gy': gy, 'sa': sa})
for k, L in ATK.get('orders', {}).items(): rig[k] = L
if ATK.get('weaponFront'):   # 칼 앞 사본(weaponF·weaponHF): 올려베기·끝·돌아옴 동안 칼은 머리 뒤(얼굴을 안 가림) → 대기 순서(칼이 머리카락 앞)로 돌아가기 전 앞 사본이 서서히 나타남(순서 바뀜 튐 없음)
    bones.append(dict(name='weaponF', parent='weapon', pos=[0, 0], part='weapon')); bones.append(dict(name='weaponHF', parent='weaponH', pos=[0, 0], part='weaponH'))
    rig['hidden'] = rig.get('hidden', []) + ['weaponF', 'weaponHF']
rig['actions'] = {'upslash': act}
rig['ui']['attack'] = 'upslash'
rig['cutHold'] = ATK.get('cutHold', .5)
if ATK.get('torsoTwist'):   # (DHL 10-19 09:32 '어깨가 있어야 할 자리에') 가까운 어깨를 shFx 만큼 앞으로 옮길 때 상체 그림의 가까운 어깨 쪽도 같이 옮김 — 몸을 튼 것처럼(엔진 torsoTwist, 메시 상체 torsoTw = 같은 그림, shFx 0 이면 원래 상체 그대로)
    shutil.copy(os.path.join(OUT, 'parts', 'torso.png'), os.path.join(OUT, 'parts', 'torsoTw.png'))
    def_parts['torsoTw'] = dict(def_parts['torso'], src='parts/torsoTw.png', mesh={'cols': 12, 'rows': 10})
    _TT = ATK['torsoTwist']; rig['torsoTwist'] = dict(bone='torso', part='torsoTw', sx=round(float(SH_N[0] - HIP[0]) * 2, 1), sy=round(float(SH_N[1] - HIP[1]) * 2, 1), ax=_TT['ax'], by=_TT['by'], p=_TT.get('p', 1))
