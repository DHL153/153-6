"""19 네온 팔로메 — 게임 정지 그림(char_0019.png: 카드·필살기 컷신 얼굴·리그 받기 전 그림)의 칼날을 리그 v1.3 처럼 좌우 반전 — 2026-10-20 21:03
  DHL 21:01 '네, 뒤집어 주세요'. 리그 대기와 같은 그림이 되게:
  ① 대기 때 보이는 칼(work/sword_idle_art.png — 원화 칼 픽셀 + 머리 뒤 이은 칼날, build_neon19.py 가 저장)을
     세운 그림 공간(work/sword_flip.json 의 Rm)에서 날밑 위 칼날만 칼날 가운데 세로선으로 거울 → 원화 공간에 한 번에 다시 샘플(흐림 1번)
  ② 옛 칼 자리(칼 라벨 + 2px, 앞 부품·먼 토시 빼고) = '칼·먼 주먹·먼 토시만 지운 원화'(sheets/nosword_2019.png — 원화와 0px)
  ③ 그 위에 새 칼 — 리그 대기 그리는 순서처럼 머리·수염·먼 주먹·가까운 팔·어깨갑(앞 부품) 밑, 상체·치마·먼 토시 위
입력: ../ref512.png(원화 = 리그 원본, 바꾸지 않음) · work/labels.npy · work/label_names.json · work/sword_idle_art.png · work/sword_flip.json · sheets/nosword_2019.png
출력: python3 -I art_flip19.py 출력.png  (기본 = 저장소 assets/art/characters/char_0019.png) + review/v1_3_art_flip.png(원화 · 새 그림 · 바뀐 곳)
"""
import json, os, sys
import numpy as np, cv2
from PIL import Image
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REPO = os.path.abspath(os.path.join(S, '..', '..', '..', '..'))
OUTP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, 'assets', 'art', 'characters', 'char_0019.png')
RA = np.array(Image.open(os.path.join(S, 'ref512.png')).convert('RGBA'))
NS = np.array(Image.open(os.path.join(S, 'sheets', 'nosword_2019.png')).convert('RGBA').resize((512, 512), Image.LANCZOS))
lab = np.load(os.path.join(S, 'work', 'labels.npy')); NAMES = json.load(open(os.path.join(S, 'work', 'label_names.json')))
L = lambda *ns: np.logical_or.reduce([lab == NAMES.index(n) + 1 for n in ns])
SWI = np.array(Image.open(os.path.join(S, 'work', 'sword_idle_art.png')).convert('RGBA')).astype(np.float32)
F = json.load(open(os.path.join(S, 'work', 'sword_flip.json'))); Rm = np.array(F['Rm']); UPS = F['UPS']; off = np.array([F['x0'], F['y0']], float)
assert F['BCX'] is not None, 'build_neon19.py FLIP_BLADE 가 꺼져 있음'
# 원화 p → 세운 그림 q = Rm·(UPS·p) − off ; 거울 q' = (2·BCX − qx, qy) (qy < YCUT, XL ≤ qx ≤ XR) ; 다시 원화 p' = Rm⁻¹(q' + off)/UPS
A = Rm[:, :2] * UPS; Ainv = np.linalg.inv(A); t = Rm[:, 2] - off
YY, XX = np.mgrid[0:512, 0:512].astype(np.float64)
qx = A[0, 0] * XX + A[0, 1] * YY + t[0]; qy = A[1, 0] * XX + A[1, 1] * YY + t[1]
reg = (qy < F['YCUT']) & (qx >= F['XL']) & (qx <= F['XR'])
qsx = np.where(reg, 2 * F['BCX'] - qx, qx); dx, dy = qsx - t[0], qy - t[1]
px = (Ainv[0, 0] * dx + Ainv[0, 1] * dy).astype(np.float32); py = (Ainv[1, 0] * dx + Ainv[1, 1] * dy).astype(np.float32)
pm = np.dstack([SWI[..., :3] * SWI[..., 3:4] / 255, SWI[..., 3:4]])   # 미리 곱한 알파로 샘플(가장자리 검은 테 방지)
sm = cv2.remap(pm, px, py, cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0)); sm[..., 3] = np.clip(sm[..., 3], 0, 255)
a = sm[..., 3:4] / 255.0; NEW = np.dstack([np.where(a > 0, sm[..., :3] / np.maximum(a, 1e-6), 0), sm[..., 3:4]]).clip(0, 255)
# ② 옛 칼 지우기: 칼 라벨 + 2px, 앞 부품(머리·수염·먼 주먹·가까운 팔·어깨갑)·먼 토시는 원화 그대로
FRONT = L('head', 'handF', 'upperN', 'foreN', 'pauldron')
OLD = (cv2.dilate(L('sword').astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & ~FRONT & ~L('foreF')
base = RA.astype(np.float32).copy(); base[OLD] = NS[OLD]
# ③ 새 칼(앞 부품 밑): 앞 부품 자리엔 그리지 않음
na = NEW[..., 3:4] / 255.0 * (~FRONT)[..., None]
ba = base[..., 3:4] / 255.0; oa = na + ba * (1 - na)
oc = (NEW[..., :3] * na + base[..., :3] * ba * (1 - na)) / np.maximum(oa, 1e-6)
out = np.dstack([oc, oa * 255]).clip(0, 255).round().astype(np.uint8); out[oa[..., 0] <= 0] = 0
Image.fromarray(out).save(OUTP, optimize=True)
d = np.abs(out.astype(int) - RA.astype(int)).max(-1); ch = d > 24
print('저장', OUTP, '· 바뀐 px(>24)', int(ch.sum()), '· 앞 부품 바뀐 px', int((ch & FRONT).sum()), '· 다리·몸 아래(y>330) 바뀐 px', int((ch[330:]).sum()))
# 검수 그림: 원화 · 새 그림 · 바뀐 곳(빨강), 어두운 배경 2배
def onbg(im):
    b = Image.new('RGBA', (512, 512), (52, 52, 62, 255)); b.alpha_composite(Image.fromarray(im)); return b.convert('RGB')
diff = onbg(RA); dv = np.array(diff); dv[ch] = (dv[ch] * .3 + np.array([255, 40, 40]) * .7).astype(np.uint8)
row = Image.new('RGB', (512 * 3 + 20, 512), (255, 255, 255)); row.paste(onbg(RA), (0, 0)); row.paste(onbg(out), (522, 0)); row.paste(Image.fromarray(dv), (1044, 0))
row.crop((0, 0, row.width, 360)).resize((row.width * 2 // 2, 360)).save(os.path.join(S, 'review', 'v1_3_art_flip.png'))
