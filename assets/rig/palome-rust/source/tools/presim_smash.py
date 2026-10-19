#!/usr/bin/env python3
"""9 러스트 팔로메 한 손 내려찍기 — 조각 시트 오기 전 미리 보기 (2026-10-19 21:35, DHL 21:29 '한손 내려찍기')

원화(512px) 좌표, 골반 기준(+x 앞, +y 아래). 먼 팔 = 칼 메는 팔(왼손), 손 그림 = 원화 손(cArt) 그대로라
손 + 칼은 한 덩어리로 돌고, 팔뚝은 어깨→팔꿈치→손목 2관절 IK(길이 고정).
검사:
  1) 팔 늘어남 = 어깨~손 거리 / (윗팔+팔뚝) ≤ 0.98 (닿음)
  2) 손목 꺾임 = (칼 방향 − 팔뚝 방향) − 원화 값(−48°) 이 ±40° 안 (21 교훈: 손 그림의 손목 방향 ±40°)
  3) 칼끝 높이: 전투 칸 위 여유(원화 틀 위 약 225px, 21 게임 화면에서 잼) 안, 땅(발바닥) 밑으로 안 들어감
  4) 칼 크기 = 그대로 (그림만 돌림)
python3 -I presim_smash.py [키.json]  → review/presim_smash.png + 표
값(관절·팔 길이)은 1차 추정(measure/joints_est.json) — 조각 시트 오면 measure 값으로 다시 돌림.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
J = json.load(open(os.path.join(SRC, 'measure', 'joints_est.json')))
HIP = J['HIP']; SOLE = max(J['sole'].values())
SH0 = (J['farArm']['SH'][0] - HIP[0], J['farArm']['SH'][1] - HIP[1])       # 먼 어깨(골반 기준)
G0 = (J['farArm']['grip'][0] - HIP[0], J['farArm']['grip'][1] - HIP[1])     # 원화 쥔 점
EL0 = (J['farArm']['EL'][0] - HIP[0], J['farArm']['EL'][1] - HIP[1])
UP = math.dist(J['farArm']['SH'], J['farArm']['EL']); FO = math.dist(J['farArm']['EL'], J['farArm']['grip'])   # 윗팔·팔뚝 = 원화 추정 관절 거리(대기 = 원화). 시트 18·19번으로 다시
BLADE0 = -147.5                         # 원화 칼날 방향(손 → 칼끝, 도) — 원화 칼 마스크 축 맞춤
TIP_L, POM_L = 434.0, 86.0              # 쥔 점 → 칼끝 / 폼멜 (원화 칼 축 위 거리)
HEADROOM = -225                         # 원화 틀 위 여유(전투, 추정) — 칼끝 y ≥ 이 값
GROUND = SOLE - HIP[1]                  # 골반 기준 땅 y
FORE0 = math.degrees(math.atan2(G0[1] - EL0[1], G0[0] - EL0[0]))
REL0 = BLADE0 - FORE0                   # 원화 손목 각(칼 − 팔뚝)

# 키: t, 쥔 점 x, y(골반 기준), 칼 각도(도), 몸 기울기(도, +앞), 골반 내림(px)
KEYS = [
    [0.00, G0[0], G0[1], BLADE0, 0, 0],
    [0.12, 110, -178, -140, -4, 5],      # 준비: 살짝 웅크리며 칼을 어깨에서 띄움
    [0.28, 92, -206, -122, -9, 0],       # 젖힘 꼭대기: 손은 머리 오른쪽 이마 높이, 칼은 뒤로 눕힘(세우지 않음)
    [0.36, 134, -190, -97, -4, 2],       # 넘김: 칼이 수직을 지나는 순간 손을 낮게 → 칼끝이 칸 안
    [0.41, 196, -104, -50, 6, 8],        # 휘두름
    [0.45, 187, 8, 7, 14, 12],        # 타격: 팔을 앞 아래로 쭉(늘어남 ~.95), 칼은 얕게 → 칼끝이 앞 땅에 닿음
    [0.60, 185, 6, 7, 13, 11],        # 버팀(컷인 유지 자세 후보)
    [0.66, 188, -92, -52, 6, 7],       # 칼을 땅에서 뽑아 올림(팔이 먼저, 칼이 따라옴)
    [0.74, 140, -182, -100, -2, 2],       # 들어 올림: 칼을 다시 세우며 어깨로
    [0.86, G0[0], G0[1], BLADE0, 0, 0],  # 대기(원화)
]
if len(sys.argv) > 1: KEYS = json.load(open(sys.argv[1]))
# B안(손 하나 더): 휘두름~버팀(HANDB 구간) 동안 '내려친 손' — 같은 쇠 장갑, 칼이 팔뚝 줄보다 약 18° 아래(손목을 반대로 꺾음). 빠르게 휘두르는 순간 바꿈
HANDB = os.environ.get('HANDB') == '1'; REL_S = 18.0; B_ON = (0.38, 0.68)
if HANDB:
    KEYS = [k for k in KEYS if not (0.36 < k[0] < 0.7)] + [
        [0.41, 190, -150, -40, 6, 6],        # 휘두름(손을 어깨 높이 앞으로 뻗으며)
        [0.45, 218, -60, 18, 12, 10],        # 타격: 팔은 어깨 높이에서 앞으로 쭉, 칼은 약 20° 아래로 → 칼끝이 앞 땅
        [0.60, 216, -58, 18, 11, 9],
        [0.66, 196, -118, -50, 6, 7]]
    KEYS.sort(key=lambda k: k[0])

def rot(p, deg, o=(0, 0)):
    a = math.radians(deg); x, y = p[0] - o[0], p[1] - o[1]
    return (o[0] + x * math.cos(a) - y * math.sin(a), o[1] + x * math.sin(a) + y * math.cos(a))

def ik(S, G, side):
    dx, dy = G[0] - S[0], G[1] - S[1]; d = math.hypot(dx, dy); dd = min(d, (UP + FO) * 0.999)
    a = math.atan2(dy, dx); c = (UP * UP + dd * dd - FO * FO) / (2 * UP * dd); c = max(-1, min(1, c))
    e = a + side * math.acos(c); E = (S[0] + UP * math.cos(e), S[1] + UP * math.sin(e))
    return E, d / (UP + FO)

def ease(u): return u * u * (3 - 2 * u)

def at(t):
    for k0, k1 in zip(KEYS, KEYS[1:]):
        if k0[0] <= t <= k1[0]:
            u = ease((t - k0[0]) / max(1e-6, k1[0] - k0[0])); return [k0[i] + (k1[i] - k0[i]) * u for i in range(1, 6)]
    return KEYS[-1][1:6]

# 원화 팔꿈치 쪽(대기와 같은 쪽으로만 굽힘): 원화에서 어깨→손 선의 어느 쪽에 팔꿈치가 있나
SIDE = min((1, -1), key=lambda sd: math.dist(ik(SH0, G0, sd)[0], EL0))   # 원화 팔꿈치에 가까운 해 쪽

def pose(t):
    gx, gy, ba, lean, hd = at(t)
    S = rot(SH0, lean); S = (S[0], S[1] + hd)                  # 상체 기울기는 골반에서 돎, 골반 내림
    G = (gx, gy); E, st = ik(S, G, SIDE)
    fore = math.degrees(math.atan2(G[1] - E[1], G[0] - E[0])); r0 = REL_S if (HANDB and B_ON[0] <= t < B_ON[1]) else REL0; rel = (ba - fore - r0 + 180) % 360 - 180
    tip = (G[0] + TIP_L * math.cos(math.radians(ba)), G[1] + TIP_L * math.sin(math.radians(ba)))
    pom = (G[0] - POM_L * math.cos(math.radians(ba)), G[1] - POM_L * math.sin(math.radians(ba)))
    return dict(t=t, S=S, E=E, G=G, tip=tip, pom=pom, stretch=st, wrist=rel, ba=ba, lean=lean, hd=hd)

def check():
    bad = []; rows = []
    for i in range(0, 87):
        p = pose(i / 100)
        ok_s = p['stretch'] <= 0.98; ok_w = abs(p['wrist']) <= 40; ok_top = p['tip'][1] >= HEADROOM - HIP[1]
        ok_g = max(p['tip'][1], p['pom'][1]) <= GROUND - 2
        rows.append((p['t'], p['stretch'], p['wrist'], p['tip'][1] + HIP[1], ok_s and ok_w and ok_top and ok_g))
        if not (ok_s and ok_w and ok_top and ok_g): bad.append((round(p['t'], 2), round(p['stretch'], 2), round(p['wrist']), round(p['tip'][1] + HIP[1])))
    return rows, bad

def draw(path, cols=5):
    from PIL import ImageFont
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30)
    except Exception: font = None
    art = Image.open(os.path.join(SRC, 'refs', 'ref_art_char0009.png')).convert('RGBA')
    ts = [k[0] for k in KEYS] + [0.20, 0.32, 0.39, 0.43]; ts = sorted(set(round(t, 2) for t in ts))
    W, H, ox, oy = 1120, 820, 30, 260
    rows = (len(ts) + cols - 1) // cols
    out = Image.new('RGB', (W * cols, H * rows), (238, 238, 238))
    for i, t in enumerate(ts):
        p = pose(t); cv = Image.new('RGBA', (W, H), (238, 238, 238, 255))
        ghost = art.copy(); ghost.putalpha(ghost.getchannel('A').point(lambda v: v * 0.30))
        cv.alpha_composite(ghost, (ox, oy))
        d = ImageDraw.Draw(cv); H0 = (ox + HIP[0], oy + HIP[1])
        P = lambda q: (H0[0] + q[0], H0[1] + q[1])
        d.line([0, oy + HEADROOM, W, oy + HEADROOM], fill=(255, 80, 80), width=3)      # 전투 칸 위 끝(추정)
        d.line([0, oy + SOLE, W, oy + SOLE], fill=(120, 90, 60), width=3)              # 땅
        ba = math.radians(p['ba']); u = (math.cos(ba), math.sin(ba)); n = (-u[1], u[0])
        g = P(p['G']); tip = P(p['tip']); pom = P(p['pom']); gd = (g[0] + u[0] * 105, g[1] + u[1] * 105)
        poly = [(gd[0] + n[0] * 20, gd[1] + n[1] * 20), (tip[0] + n[0] * 14, tip[1] + n[1] * 14), tip, (gd[0] - n[0] * 20, gd[1] - n[1] * 20)]
        d.polygon(poly, fill=(120, 120, 125), outline=(30, 30, 30))
        d.line([pom, gd], fill=(110, 70, 40), width=14)
        d.line([(gd[0] + n[0] * 30, gd[1] + n[1] * 30), (gd[0] - n[0] * 30, gd[1] - n[1] * 30)], fill=(80, 80, 80), width=10)
        s, e = P(p['S']), P(p['E'])
        col = (0, 90, 220) if abs(p['wrist']) <= 40 and p['stretch'] <= .98 else (230, 0, 0)
        d.line([s, e], fill=col, width=14); d.line([e, g], fill=col, width=14); d.ellipse([g[0] - 15, g[1] - 15, g[0] + 15, g[1] + 15], fill=(90, 80, 75))
        d.text((14, 10), f"t {t:.2f}  reach {p['stretch']:.2f}  wrist {p['wrist']:+.0f}  tip y {p['tip'][1] + HIP[1]:.0f}  lean {p['lean']:+.0f}", fill=(0, 0, 0), font=font)
        d.rectangle([0, 0, W - 1, H - 1], outline=(180, 180, 180), width=2)
        out.paste(cv.convert('RGB'), (W * (i % cols), H * (i // cols)))
    sc = 0.4; out.resize((int(out.width * sc), int(out.height * sc)), Image.LANCZOS).save(path)

if __name__ == '__main__':
    print('원화 손목 각 REL0', round(REL0, 1), '· 팔꿈치 쪽', SIDE, '· 어깨', SH0, '· 쥔 점', G0, '· 땅 y', GROUND)
    rows, bad = check()
    for t, s, w, ty, ok in rows[::5]: print(f'{t:.2f} 늘어남 {s:.2f} 손목 {w:+5.0f} 칼끝y {ty:6.0f} {"OK" if ok else "××"}')
    print('불합격 프레임', len(bad), bad[:12])
    draw(os.path.join(SRC, 'review', 'presim_smash_B.png' if HANDB else 'presim_smash.png'))
