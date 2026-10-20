"""19 네온 팔로메 연구용 '대리 리그' (2026-10-20 18:30 DHL '리소스 오기 전에 연구 활동'):
9 러스트 팔로메 리그(같은 자세 · 같은 동작)의 칼 그림만 19 칼로 바꿔, 새 원화가 오기 전에 19 칼(날 짧고 손잡이 긺)로 대기·달리기·내려찍기를 미리 본다.
- 19 칼 = char_0019 에서 칼날·날밑은 원화 픽셀, 손잡이(두 손에 가려짐)는 갈색 가죽 감은 자루 + 폼멜 고리(원화 픽셀)
- 크기 = 19 몸 키 → 9 몸 키(×0.914, 새 원화 프롬프트 첨부 3 과 같은 배율), 리그 단위(원화 ×2)
- 쥔 점 = 19 먼 손 자리(날밑 가운데에서 손잡이 쪽 36px) — 9 쥔 점 G 에 놓임
출력: assets/rig/_proxy19/ (palome-rust 복사 + weapon.png·rig.def.js 칼 점만 바꿈, 저장소엔 안 넣음)
실행: python3 -I proxy19.py
"""
import json, math, os, shutil, re
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); RIG = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SRC = os.path.join(RIG, 'palome-rust'); DST = os.path.join(RIG, '_proxy19')
A19 = np.array(Image.open(os.path.join(HERE, '..', 'refs', 'ref_design_char0019.png')).convert('RGBA')).astype(np.float32)   # 옛 19 원화(게임 char_0019 는 새 원화로 바뀜)
G19, T19, P19 = np.array([318., 288.]), np.array([502., 10.]), np.array([230., 400.])   # 날밑 가운데 · 칼끝 · 폼멜 고리 가운데 (char_0019 격자에서 읽음)
S = 341 / 373.   # 19 몸 키 → 9 몸 키
b = (T19 - G19) / np.linalg.norm(T19 - G19); n = np.array([-b[1], b[0]])
YY, XX = np.mgrid[0:512, 0:512]; D = np.stack([XX - G19[0], YY - G19[1]], -1); t = D @ b; sd = D @ n
blade = (t >= 12) & (t <= 345) & (np.abs(sd) <= np.where(t < 75, 23.5, 27)) & (A19[..., 3] > 20)
guard = (t >= -17) & (t < 12) & (np.abs(sd) <= 50) & (A19[..., 3] > 20)
L_H = 142.0; GRIP = 36.0   # 날밑 → 폼멜 가운데 · 날밑 → 쥔 점 (19 원화 px)
P_ax = G19 - L_H * b   # 곧은 축 위 폼멜(원화 폼멜과 4° 차이 — 원화 그림이 날·손잡이가 살짝 꺾여 있음)
sw = np.zeros_like(A19); m = blade | guard; sw[m] = A19[m]
# 손잡이: 날밑 아래 ~ 폼멜 위, 반폭 7.5, 6px 마다 가죽 띠 두 색 + 외곽선
D2 = np.stack([XX - G19[0], YY - G19[1]], -1); tt = -(D2 @ b); ss = D2 @ n
hnd = (tt >= 14) & (tt <= L_H - 13) & (np.abs(ss) <= 7.5)
sw[hnd, :3] = np.where(((tt[hnd] // 6) % 2 == 0)[:, None], np.array([88, 60, 44]), np.array([66, 44, 33])); sw[hnd, 3] = 255
sw[hnd & (np.abs(ss) > 5.8), :3] = (20, 18, 18)
pm = np.hypot(XX - P19[0], YY - P19[1]) <= 17.5
pomimg = np.zeros_like(A19); pomimg[pm] = A19[pm]
Mp = np.float32([[1, 0, P_ax[0] - P19[0]], [0, 1, P_ax[1] - P19[1]]]); pw = cv2.warpAffine(pomimg, Mp, (512, 512), flags=cv2.INTER_LINEAR)
al = pw[..., 3:4] / 255.0; sw[..., :3] = pw[..., :3] * al + sw[..., :3] * (1 - al); sw[..., 3] = np.maximum(sw[..., 3], pw[..., 3])
# 세로로(칼끝 위): b → (0,−1), 배율 2·S, 쥔 점을 캔버스 아래쪽에
GP = G19 - GRIP * b
ang = math.degrees(math.atan2(b[1], b[0])); rot = -90 - ang
K = 2 * S; WS, HS = 400, 1100
Rm = cv2.getRotationMatrix2D((float(GP[0]), float(GP[1])), -rot, K); Rm[0, 2] += WS / 2 - GP[0]; Rm[1, 2] += 820 - GP[1]
v = cv2.warpAffine(sw, Rm, (WS, HS), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0)); v = np.clip(v, 0, 255)
ys, xs = np.nonzero(v[..., 3] > 0); x0, y0 = xs.min() - 2, ys.min() - 2; v = v[y0:ys.max() + 3, x0:xs.max() + 3]
vp = lambda p: (Rm[:, :2] @ np.array(p, float) + Rm[:, 2]) - np.array([x0, y0])
W_PIV, W_TIP, W_GUARD, W_POM = vp(GP), vp(T19), vp(G19), vp(P_ax)
print('19 sword vertical', v.shape[1::-1], 'pivot', np.round(W_PIV, 1), 'tip', np.round(W_TIP, 1), 'guard', np.round(W_GUARD, 1), 'pommel', np.round(W_POM, 1))
if os.path.isdir(DST): shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('review', 'measure', 'pieces', 'sheets', '__pycache__'))
Image.fromarray(v.astype(np.uint8)).save(os.path.join(DST, 'parts', 'weapon.png'))
js = open(os.path.join(DST, 'rig.def.js'), encoding='utf-8').read()
mm = re.search(r"window\.MR_RIG_DEFS\['palome-rust'\]=(\{.*\});\s*$", js, re.S); d = json.loads(mm.group(1))
r = lambda p: [round(float(p[0]), 1), round(float(p[1]), 1)]
d['parts']['weapon'].update({'pivot': r(W_PIV), 'tip': r(W_TIP), 'tips': [r(W_TIP + [-12, 20]), r(W_TIP + [28, 20])], 'guard': r(W_GUARD), 'pommel': r(W_POM)})
d['version'] = 'proxy19'; d['note'] = '연구용 대리 리그: 9 러스트 팔로메 + 19 네온 칼(×0.914)'
open(os.path.join(DST, 'rig.def.js'), 'w', encoding='utf-8').write(js[:mm.start(1)] + json.dumps(d, ensure_ascii=False) + ';\n')
json.dump(d, open(os.path.join(DST, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
print('9 weapon was', json.load(open(os.path.join(SRC, 'rig.json')))['parts']['weapon'])
