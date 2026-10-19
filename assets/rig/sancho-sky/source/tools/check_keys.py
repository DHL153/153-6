"""23 스카이아크 산초 올려베기 키 검사 (13 check_keys.py 그대로 — joints.json eyes 에 입은 mouth 로: 마스크 대신 입, 여유 0 이상) (조립 전에도 돎 — 원화 관절·칼 모양만으로).
실행: cd source && python3 -I tools/check_keys.py [attack_keys.json]
키마다: 두 팔 닿음(관 팔 길이 고정, 1.00 넘으면 늘어남) · 눈·마스크 가림 여유(px, 음수 = 칼·팔뚝·주먹이 덮음) · 칼끝-땅(px) · 팔꿈치 자리
  러스트 산초 ik5 와 같은 기준: 칼 그림까지 −14, 팔뚝 선 −24, 주먹 가운데 −34. 칼 그림 = 원화 칼(날 행 측정 + 날밑·손잡이·폼멜 다각형)
  얼굴 앞을 지나는 0.17~0.255(빠르게 내려침)는 러스트와 같이 가림 허용 — 표에 '지나감'
"""
import json, math, os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = json.load(open(os.path.join(HERE, 'joints.json'), encoding='utf-8'))
A = lambda v: np.array(v, float)
HIP = A(J['HIP']); rel = lambda p: ((p[0] - HIP[0]) * 2, (p[1] - HIP[1]) * 2)
HJ = J['handle']; COL, POM = A(HJ['collar']), A(HJ['pommel']); HD = (POM - COL) / np.linalg.norm(POM - COL)
onh = lambda y: COL + HD * ((y - COL[1]) / HD[1])
GU_art, GL_art = onh(HJ['G_U_y']), onh(HJ['G_L_y']); SA0 = math.atan2(-HD[1], -HD[0])
SFL = float(np.linalg.norm(GL_art - GU_art)) * 2
SN, SF, NECK, GU0 = rel(J['SH_N']), rel(J['SH_F']), rel(J['NECK']), rel(GU_art)
T = J['tubes']; L1N, L2N, L1F, L2F = T['upperN'], T['foreN'], T['upperF'], T['foreF']
FEAT = {k: rel(v) for k, v in J['eyes'].items() if not k.startswith('_')}
BL = J['blade']; TIP = A(BL['tip'])
BLADE_OFF = math.atan2(TIP[1] - GU_art[1], TIP[0] - GU_art[0]) - SA0   # 날끝 방향 − 손잡이 축(원화 그림 꺾임)
TIPd = float(np.linalg.norm(TIP - GU_art)) * 2
def sword_mask():
    """23: 원화 칼 자리 — build_sky.py 가 남긴 work/swm.png 가 있으면 그것, 없으면 날 두 직선(날밑 윗선 위) + 날밑·폼멜 금색 + 손잡이 띠"""
    f = os.path.join(HERE, 'work', 'swm.png')
    if os.path.exists(f): return np.array(Image.open(f)) > 127
    RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA')); al = RA[..., 3] > 100
    la, lk, _ = BL['left']; ra, rk, _ = BL['right']; GT = J['guardTop']; g0, g1 = A(GT['p0']), A(GT['p1'])
    yy, xx = np.mgrid[0:512, 0:512]; gtop = g0[1] + (xx - g0[0]) * (g1[1] - g0[1]) / (g1[0] - g0[0])
    m = al & (xx >= la + lk * yy - 1) & (xx <= ra + rk * yy + 1) & (yy < gtop + 4) & (yy < 280)
    r, g, b = [RA[..., i].astype(int) for i in range(3)]; gold = al & (r > 150) & (g > 100) & (b < 120) & (r - b > 70) & (r >= g)
    gold &= ((xx > 180) & (xx < 266) & (yy > 236) & (yy < 302)) | ((xx > 244) & (xx < 283) & (yy > 354) & (yy < 385))
    m |= cv2.dilate(gold.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    pp = np.array([HD[1], -HD[0]]) * 8; im = Image.new('L', (512, 512), 0); ImageDraw.Draw(im).polygon([tuple(COL + pp), tuple(POM + pp), tuple(POM - pp), tuple(COL - pp)], fill=255)
    return m | (np.array(im) > 0)
SWM = sword_mask(); DT = cv2.distanceTransform((~SWM).astype(np.uint8), cv2.DIST_L2, 5)
def bdist(p, G, sa):
    th = sa - SA0; c, s = math.cos(-th), math.sin(-th); dx, dy = (p[0] - G[0]) / 2, (p[1] - G[1]) / 2
    x = GU_art[0] + dx * c - dy * s; y = GU_art[1] + dx * s + dy * c; xi, yi = int(round(x)), int(round(y))
    if 0 <= xi < 512 and 0 <= yi < 512: return -1.0 if SWM[yi, xi] else float(DT[yi, xi]) * 2
    return 999.0
def ik(S, W, L1, L2, side):
    dx, dy = W[0] - S[0], W[1] - S[1]; dd = math.hypot(dx, dy); base = math.atan2(dy, dx)
    if dd >= L1 + L2: return (S[0] + dx / dd * L1, S[1] + dy / dd * L1), dd / (L1 + L2)
    if dd < abs(L1 - L2): return None, dd / (L1 + L2)
    al = math.acos(max(-1, min(1, (L1 * L1 + dd * dd - L2 * L2) / (2 * L1 * dd)))); a = base + al if side > 0 else base - al
    return (S[0] + math.cos(a) * L1, S[1] + math.sin(a) * L1), dd / (L1 + L2)
def dseg(p, a, b):
    ax, ay = b[0] - a[0], b[1] - a[1]; t = max(0, min(1, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / (ax * ax + ay * ay + 1e-9))); return math.hypot(p[0] - a[0] - t * ax, p[1] - a[1] - t * ay)
def headrot(p, phi):
    x, y = p[0] - NECK[0], p[1] - NECK[1]; c, s = math.cos(phi), math.sin(phi); return (NECK[0] + x * c - y * s, NECK[1] + x * s + y * c)
def check(G, sa, phi=0, shN=(0, 0), shF=(0, 0), sN=1, sF=-1, hipY=0):
    """shN = 가까운 어깨 이동(엔진 shFx·shFy), shF = 먼 어깨 이동(엔진 shNx·shNy) — 산초는 이름이 반대"""
    U_ = (math.cos(sa), math.sin(sa)); GF = (G[0] - SFL * U_[0], G[1] - SFL * U_[1]); sn = (SN[0] + shN[0], SN[1] + shN[1]); sf = (SF[0] + shF[0], SF[1] + shF[1])
    EN, rN = ik(sn, G, L1N, L2N, sN); EF, rF = ik(sf, GF, L1F, L2F, sF); per = {}
    for k, p in FEAT.items():
        p = headrot(p, phi); v = [bdist(p, G, sa) - 14, math.hypot(p[0] - G[0], p[1] - G[1]) - 34, math.hypot(p[0] - GF[0], p[1] - GF[1]) - 34]
        if EN: v += [dseg(p, EN, G) - 24, dseg(p, sn, EN) - 24]
        if EF: v.append(dseg(p, EF, GF) - 24)
        per[k] = round(min(v), 1)
    tip = (G[0] + TIPd * math.cos(sa + BLADE_OFF), G[1] + TIPd * math.sin(sa + BLADE_OFF)); gnd = (J['O'][1] - HIP[1]) * 2 - hipY
    return dict(rN=round(rN, 3), rF=round(rF, 3), face=per, tipGnd=round(gnd - tip[1] - 6, 1), EN=EN and tuple(round(v) for v in EN), EF=EF and tuple(round(v) for v in EF))
def track(K, t):
    if not K: return 0
    if t <= K[0][0]: return K[0][1]
    for a, b in zip(K, K[1:]):
        if a[0] <= t <= b[0]: u = (t - a[0]) / (b[0] - a[0]) if b[0] > a[0] else 0; return a[1] + (b[1] - a[1]) * u
    return K[-1][1]
if __name__ == '__main__':
    print('G_U', np.round(GU_art, 1).tolist(), 'G_L', np.round(GL_art, 1).tolist(), 'sF', round(-SFL, 1), 'sa0', round(SA0, 4), f'({math.degrees(SA0):.1f}°)', 'G_U rig', np.round(GU0, 1).tolist(),
          'blade off', f'{math.degrees(BLADE_OFF):.1f}°', 'tip dist', round(TIPd), '| SN', SN, 'SF', SF, 'tubes', {k: v for k, v in T.items() if not k.startswith('_')})
    print('대기 닿음 N', round(math.dist(SN, GU0) / (L1N + L2N), 3), 'F', round(math.dist(SF, rel(GL_art)) / (L1F + L2F), 3))
    kf = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'attack_keys.json')
    if os.path.exists(kf):
        K = json.load(open(kf, encoding='utf-8')); act = K['action']; side = act.get('ikSide', {'N': 1, 'F': -1})
        for t, gx, gy, sa, *e in K['grip']:
            G = GU0 if gx == 'idle' else (gx, gy); sa = SA0 if sa == 'idle' else sa
            tr = lambda n: track(act.get(n), t)
            sk = act.get('ikSideK', {}); stp = lambda KK, d: ([v for tt, v in KK if t >= tt] or [d])[-1]
            sN_, sF_ = stp(sk.get('N', []), side['N']), stp(sk.get('F', []), side['F'])
            c = check(G, sa, tr('head'), (tr('shFx'), tr('shFy')), (tr('shNx'), tr('shNy')), sN_, sF_, tr('hipY'))
            f = c['face']; passing = 0.15 < t < 0.27; bad = [k for k, v in f.items() if v < (0 if k in ('mask', 'mouth') else 6)]
            flag = ('지나감' if passing and bad else ('X 가림 ' + ','.join(bad) if bad else '')) + (' X 늘어남' if max(c['rN'], c['rF']) > 1.02 else '') + (' X 땅' if c['tipGnd'] < 20 else '')
            print(f"t{t:5.3f} G({G[0]:6.1f},{G[1]:6.1f}) sa{math.degrees(sa):7.1f}° 닿음 N{c['rN']:.2f} F{c['rF']:.2f} 얼굴 {f} 칼끝-땅 {c['tipGnd']:7.1f} 팔꿈치 N{c['EN']}({sN_:+d}) F{c['EF']} {flag}")
