# 9 팔로메 한 손 내려찍기 키 맞추기 — 엔진 _swordRigid + 손목 마디(wristArm)와 같은 계산 (2026-10-19 22:40)
#   주먹(원화 손)은 칼에 붙어 같이 돎 → 손목 점 W = G + 회전(칼 각 − 원화 칼 각)·(원화 손목 − 원화 쥔 점)
#   팔꿈치 = 어깨 원(윗팔 L1) ∩ 손목 원(팔뚝 L2), 원화 팔뚝 방향(손과 같이 돈 것)에 가까운 쪽 · 손목 꺾임 = 그 방향과 실제 팔뚝 각 차
#   키: [t, gx, gy(원화 px, 서 있는 골반 기준), 칼끝 방향(도), 몸 기울기(도, +앞), 골반 내림(px)]
#   python3 -I presim2.py [keys.json] → 표 + review/presim2.png
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
S_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = dict(HIP=(288, 405), SH=(358, 303), EL=(424, 336), WR=(404, 288), G=(398.0, 261.4), SA0=-146.13, TIP=434.0, POM=95.0, GROUND=501, TOP=float(os.environ.get('TOP', -50)))   # TOP: 전투 칸 위 끝(원화 y) — 10-20 게임에서 잼: PC −64 · 폰 −60 (−225 는 알론소 배율로 잘못 추정)
HIP = np.array(J['HIP'], float); SH0 = np.array(J['SH'], float) - HIP; EL0 = np.array(J['EL'], float) - HIP; WR0 = np.array(J['WR'], float) - HIP; G0 = np.array(J['G']) - HIP
L1 = float(np.linalg.norm(EL0 - SH0)); L2 = float(np.linalg.norm(EL0 - WR0))
rot = lambda v, d: np.array([v[0] * math.cos(math.radians(d)) - v[1] * math.sin(math.radians(d)), v[0] * math.sin(math.radians(d)) + v[1] * math.cos(math.radians(d))])
EASE = {'io': lambda u: u * u * (3 - 2 * u), 'lin': lambda u: u, 'i': lambda u: u * u, 'o': lambda u: 1 - (1 - u) ** 2}
KEYS = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else json.load(open(os.path.join(S_, 'attack_keys.json')))['keys']
def at(t):
    for k0, k1 in zip(KEYS, KEYS[1:]):
        if k0[0] <= t <= k1[0]:
            e = EASE[k0[6] if len(k0) > 6 else 'io']; u = e((t - k0[0]) / max(1e-6, k1[0] - k0[0])); return [k0[i] + (k1[i] - k0[i]) * u for i in range(1, 6)]
    return KEYS[-1][1:6]
def pose(t, side=None):
    gx, gy, sa, lean, hd = at(t); G = np.array([gx, gy]); d = sa - J['SA0']
    W = G + rot(WR0 - G0, d); E0 = W + rot(EL0 - WR0, d)
    S = rot(SH0, lean) + np.array([0, hd]); v = W - S; dd = float(np.linalg.norm(v)); b = math.atan2(v[1], v[0])
    if dd >= L1 + L2: E = S + v / dd * L1; ok = False
    else:
        al = math.acos(max(-1, min(1, (L1 * L1 + dd * dd - L2 * L2) / (2 * L1 * dd)))); e1 = S + L1 * np.array([math.cos(b - al), math.sin(b - al)]); e2 = S + L1 * np.array([math.cos(b + al), math.sin(b + al)])
        E = (e2 if side > 0 else e1) if side else (e1 if np.linalg.norm(e1 - E0) <= np.linalg.norm(e2 - E0) else e2); ok = True
    bend = (math.degrees(math.atan2(*(E - W)[::-1]) - math.atan2(*(E0 - W)[::-1])) + 180) % 360 - 180
    U = np.array([math.cos(math.radians(sa)), math.sin(math.radians(sa))]); tip = G + U * J['TIP']; pom = G - U * J['POM']
    return dict(t=t, G=G, W=W, E=E, S=S, E0=E0, reach=dd / (L1 + L2), bend=bend, tip=tip, pom=pom, sa=sa, lean=lean, hd=hd, ok=ok)
SIDE = 1   # 원화 팔꿈치 쪽(대기) = e2 — 엔진 ikSideK N [[0, 1]] 로 고정
def check(step=0.01, T=None):
    T = T or KEYS[-1][0]; bad = []; rows = []
    for i in range(int(T / step) + 1):
        p = pose(i * step, SIDE); ty = p['tip'][1] + HIP[1]; py = p['pom'][1] + HIP[1]
        fl = [] if p['ok'] else ['닿지않음']
        if abs(p['bend']) > 40: fl.append('손목')
        if ty < J['TOP']: fl.append('칸위')
        if max(ty, py) > J['GROUND'] - 2: fl.append('땅밑')
        rows.append((round(p['t'], 2), round(p['reach'], 2), round(p['bend']), round(ty), fl))
        if fl: bad.append(rows[-1])
    return rows, bad
def draw(path, ts=None):
    art = Image.open(os.path.join(S_, 'ref512.png')).convert('RGBA'); ts = ts or sorted(set([k[0] for k in KEYS] + [0.2, 0.33, 0.39, 0.43]))
    Wc, Hc, ox, oy, cols = 1120, 820, 30, 260, 5; rows = (len(ts) + cols - 1) // cols; out = Image.new('RGB', (Wc * cols, Hc * rows), (238, 238, 238))
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30)
    except Exception: font = None
    for i, t in enumerate(ts):
        p = pose(t, SIDE); cv = Image.new('RGBA', (Wc, Hc), (238, 238, 238, 255)); gh = art.copy(); gh.putalpha(gh.getchannel('A').point(lambda v: v * .28)); cv.alpha_composite(gh, (ox, oy)); d = ImageDraw.Draw(cv)
        P = lambda q: (ox + HIP[0] + q[0], oy + HIP[1] + q[1])
        d.line([0, oy + J['TOP'], Wc, oy + J['TOP']], fill=(255, 80, 80), width=3); d.line([0, oy + J['GROUND'], Wc, oy + J['GROUND']], fill=(120, 90, 60), width=3)
        u = np.array([math.cos(math.radians(p['sa'])), math.sin(math.radians(p['sa']))]); n = np.array([-u[1], u[0]]); g = np.array(P(p['G'])); gd = g + u * 120; tip = np.array(P(p['tip'])); pom = np.array(P(p['pom']))
        d.polygon([tuple(gd + n * 26), tuple(tip + n * 16), tuple(tip), tuple(gd - n * 26)], fill=(120, 120, 125), outline=(30, 30, 30)); d.line([tuple(pom), tuple(gd)], fill=(110, 70, 40), width=14)
        d.line([tuple(gd + n * 32), tuple(gd - n * 32)], fill=(80, 80, 80), width=10)
        col = (0, 90, 220) if abs(p['bend']) <= 40 and p['ok'] else (230, 0, 0)
        d.line([P(p['S']), P(p['E'])], fill=col, width=14); d.line([P(p['E']), P(p['W'])], fill=(0, 160, 255), width=12); d.ellipse([g[0] - 16, g[1] - 16, g[0] + 16, g[1] + 16], fill=(90, 80, 75))
        d.text((14, 10), f"t {t:.2f} reach {p['reach']:.2f} wrist {p['bend']:+.0f} tip y {p['tip'][1] + HIP[1]:.0f} lean {p['lean']:+.0f}", fill=(0, 0, 0), font=font)
        out.paste(cv.convert('RGB'), (Wc * (i % cols), Hc * (i // cols)))
    out.resize((int(out.width * .4), int(out.height * .4)), Image.LANCZOS).save(path)
if __name__ == '__main__':
    print('L1', round(L1, 1), 'L2', round(L2, 1), 'keys', len(KEYS))
    rows, bad = check()
    for r in rows[::4]: print(r)
    print('불합격', len(bad), bad[:10])
    draw(os.path.join(S_, 'review', 'presim2.png'))
