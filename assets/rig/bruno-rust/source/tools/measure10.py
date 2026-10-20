"""10 러스트 브루노 — 원화 측정(두 도끼 축·손 순서·관절 점) — 리소스(프롬프트 0 결과) 오기 전 연구용, 새 원화가 오면 같은 도구로 다시 잼
입력: 원화 512(기본 = 저장소 게임 그림 char_0010 — 받은 그림(ref_dhl_2118)과 무릎 위가 같고 발이 정상)
출력: source/measure10.json · source/review/measure10.png
실행: python3 -I measure10.py [원화.png]
관절 점(어깨·팔꿈치·손목·골반·목·발목)은 확대 격자 그림(눈)으로 읽은 값 — 도끼 축만 그림에서 계산(손잡이 채도 높은 픽셀의 줄별 가운데 → 직선 맞춤)
"""
import json, os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.abspath(os.path.join(HERE, '..')); REPO = os.path.abspath(os.path.join(SRC, '..', '..', '..', '..'))
ART = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, 'assets', 'art', 'characters', 'char_0010.png')
RA = np.array(Image.open(ART).convert('RGBA')); A = RA[..., 3] > 40
hsv = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV); SAT = hsv[..., 1].astype(int); VAL = hsv[..., 2].astype(int)
def axis(y0, y1, x0, x1):   # 손잡이(붕대 크림·갈색 = 채도 있음, 머리카락 회색 = 채도 없음) 줄별 가운데 → x = a·y + b
    pts = []
    for y in range(y0, y1):
        xs = np.nonzero(A[y, x0:x1] & (SAT[y, x0:x1] > 45) & (VAL[y, x0:x1] > 60))[0] + x0
        if len(xs) >= 8 and xs.max() - xs.min() < 34: pts.append((y, (xs.min() + xs.max()) / 2))
    P = np.array(pts); a, b = np.polyfit(P[:, 0], P[:, 1], 1); res = P[:, 1] - (a * P[:, 0] + b)
    return float(a), float(b), len(P), float(np.abs(res).mean())
aN, bN, nN, eN = axis(100, 232, 95, 165)     # 가까운 도끼(화면 왼쪽 위, 오른손): 머리 아래 ~ 주먹 위
aF, bF, nF, eF = axis(160, 270, 340, 430)    # 먼 도끼(화면 오른쪽, 왼손)
deg = lambda a: float(np.degrees(np.arctan(a)))   # 세로에서 기운 각(+ = 위가 왼쪽으로)
ys, xs = np.nonzero(A); sole = int(ys.max())
M = {
  'art': os.path.basename(ART), 'sole_y': sole, 'top_y': int(ys.min()),
  'hairTop': [240, 166], 'neck': [252, 300], 'hip': [250, 372],
  'near': {'note': '화면 왼쪽 = 오른손(가까운 팔) — 머리 위로 든 도끼, 팔꿈치가 아래로 접힘(윗팔은 재킷 어깨 밑)',
           'SH': [190, 315], 'EL': [158, 328], 'WR': [141, 265], 'fist': [146, 250], 'pommel': [158, 278],
           'axis': {'a': aN, 'b': bN, 'deg_from_vertical': deg(aN), 'rows': nN, 'fit_err_px': eN}, 'head': [95, 75], 'edge': '오른쪽(앞)', 'top': [128, 8]},
  'far': {'note': '화면 오른쪽 = 왼손(먼 팔) — 몸 앞 오른쪽으로 든 도끼',
          'SH': [288, 325], 'EL': [306, 350], 'WR': [336, 320], 'fist': [350, 294], 'pommel': [338, 318],
          'axis': {'a': aF, 'b': bF, 'deg_from_vertical': deg(aF), 'rows': nF, 'fit_err_px': eF}, 'head': [440, 145], 'edge': '오른쪽(앞)', 'top': [430, 115]},
  'legs_note': '다리 점 = 0번 합격 원화 4배 격자에서 읽음(무릎 = 무릎 쇠판 가운데, 발목 = 부츠 목)', 'legs': {'near': {'hip': [228, 388], 'knee': [204, 418], 'ankle': [186, 464]}, 'far': {'hip': [262, 388], 'knee': [290, 418], 'ankle': [300, 462]}},
  'ponytail': {'root': [175, 250], 'tie': [100, 395], 'tip': [70, 430]},
}
for sd in ('near', 'far'):   # 도끼 머리 가운데 = 축 위(눈으로 찍은 y 에서 축의 x)
    s = M[sd]; s['head'] = [round(s['axis']['a'] * s['head'][1] + s['axis']['b'], 1), s['head'][1]]
L = lambda p, q: float(np.hypot(p[0] - q[0], p[1] - q[1]))
for sd in ('near', 'far'):
    s = M[sd]; s['len'] = {'upper': L(s['SH'], s['EL']), 'fore_to_wrist': L(s['EL'], s['WR']), 'fore_to_fist': L(s['EL'], s['fist']), 'fist_to_head': L(s['fist'], s['head']), 'fist_to_top': L(s['fist'], s['top'])}
body = sole - M['hairTop'][1]; M['bodyH'] = body
M['gameTop_est'] = {'note': '게임 전투 칸 위 끝 ≈ 땅 − 1.81 × 몸 키(머리카락 위~발바닥, 9·19 팔로메 game_top 실측 비율) — 공격 키 짜기 전에 game_top.py 로 직접 다시 잼(실수 36)', 'y': round(sole - 1.81 * body, 1),
                    'idle_margin_px': round(min(M['near']['top'][1], M['far']['top'][1]) - (sole - 1.81 * body), 1)}
M['arm_over_body'] = round((M['near']['len']['upper'] + M['near']['len']['fore_to_fist']) / body, 3)
json.dump(M, open(os.path.join(SRC, 'measure10.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: M[k] for k in ('sole_y', 'bodyH', 'gameTop_est', 'arm_over_body')}, ensure_ascii=False))
for sd in ('near', 'far'): print(sd, {k: round(v, 1) for k, v in M[sd]['len'].items()}, 'axis', round(M[sd]['axis']['deg_from_vertical'], 1), '° err', round(M[sd]['axis']['fit_err_px'], 2), 'rows', M[sd]['axis']['rows'])
# 그림
K = 2; W = Image.new('RGBA', (512 * K, 512 * K), (255, 255, 255, 255)); W.alpha_composite(Image.fromarray(RA).resize((512 * K, 512 * K), Image.LANCZOS)); d = ImageDraw.Draw(W)
P = lambda p: (p[0] * K, p[1] * K)
for sd, c in (('near', (230, 40, 40)), ('far', (30, 110, 230))):
    s = M[sd]; d.line([P(s['SH']), P(s['EL'])], fill=c, width=6); d.line([P(s['EL']), P(s['fist'])], fill=c, width=4)
    a, b = s['axis']['a'], s['axis']['b']; ytop = s['head'][1] - 20; ybot = s['pommel'][1] + 10
    d.line([P((a * ytop + b, ytop)), P((a * ybot + b, ybot))], fill=(20, 160, 40), width=3)
    for p in (s['SH'], s['EL'], s['fist'], s['head']): x, y = P(p); d.ellipse([x - 7, y - 7, x + 7, y + 7], outline=(0, 0, 0), width=3)
for sd in ('near', 'far'):
    g = M['legs'][sd]; d.line([P(g['hip']), P(g['knee']), P(g['ankle'])], fill=(150, 60, 200), width=4)
yt = M['gameTop_est']['y']
f = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 24)
d.text((12, 12), f"빨강 = 가까운 팔(오른손) · 파랑 = 먼 팔(왼손) · 초록 = 도끼 축 · 보라 = 다리   게임 칸 위 끝 추정 y {yt:.0f}(그림 밖 위)", fill=(30, 30, 30), font=f)
W.convert('RGB').save(os.path.join(SRC, 'review', 'measure10.png')); print('saved review/measure10.png')
