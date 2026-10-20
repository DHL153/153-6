"""17 네온 루시아 — 새 원화(7 러스트 루시아 자세) 요청 전 '도끼·방패 맞춤' 그림 (실수 39: 프롬프트 쓰기 전에 무기를 그 자세에 겹쳐 봄) — 2026-10-21 06:51
  기준 자세 = 7 러스트 루시아 원화(char_0007 = lucia-rust/source/ref512 — 리그 원본, 공격 키가 이 자세·이 쥔 점으로 짜여 있음)
  손 바꿈: 네온 원화는 도끼 = 가까운 손(화면 왼쪽, 머리 위로 듦) · 방패 = 먼 손(화면 오른쪽) → 러스트 자세 = 방패 가까운 손 · 도끼 먼 손
  도끼 크기 규칙(B — 12·20 네온과 같은 판단): 쥔 점 → 자루 축 따라 가장 먼 점 = 러스트 도끼(공격 키·땅·게임 칸·컷인 그대로), 날 모양·무늬·색 = 네온
  방패: 네온 방패 모양 그대로(가로세로 비 유지) · 높이 = 러스트 방패 높이 · 아래 끝 = 러스트 방패 아래 끝 · 가로 가운데 = 러스트 방패 가운데
  출력: ../refs/ref_weapon_fit17.png(첨부 3) · 숫자
실행: python3 -I fit17.py
"""
import json, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); REPO = os.path.abspath(os.path.join(SRC, '..', '..', '..', '..'))
NEON = np.array(Image.open(os.path.join(REPO, 'assets', 'art', 'characters', 'char_0017.png')).convert('RGBA')).astype(np.float32)
RUST = np.array(Image.open(os.path.join(REPO, 'assets', 'art', 'characters', 'char_0007.png')).convert('RGBA')).astype(np.float32)
RS = os.path.join(REPO, 'assets', 'rig', 'lucia-rust', 'source')
J = json.load(open(os.path.join(RS, 'joints7.json')))
LAB = np.load(os.path.join(RS, 'work', 'labels.npy')); NAMES = json.load(open(os.path.join(RS, 'work', 'label_names.json')))
lab = lambda *ns: np.logical_or.reduce([LAB == NAMES.index(n) + 1 for n in ns])
YY, XX = np.mgrid[0:512, 0:512].astype(float)
V = lambda p: np.array(p, float)
al = NEON[..., 3] > 60                                  # 원화 둘레 거의 투명한 점(α ≤ 60)은 뺌 — 날 오른쪽 위에 흩어진 점이 있어 길이를 잘못 잼
# ---- 네온 도끼 (네온 원화 px — 격자 4배 눈대중) ----
N_GRIP = V([92, 232])                                  # 가까운 주먹 가운데 = 자루 축 위 쥔 점
N_AX_DIR = math.atan2(198 - 272, 150 - 30)             # 자루 축: 자루 끝 마개 (30,272) → 주먹 위 (150,198) ≈ −31.7°
axe = al & (((XX < 60) & (YY > 230) & (YY < 300)) | ((XX >= 118) & (XX < 200) & (YY < 215)) | ((XX >= 200) & (YY < 182)))
# 주먹 밑 자루(가려진 곳): 자루 끝 쪽 깨끗한 단면 색으로 띠를 이어 그림(그림 확인용)
u = np.array([math.cos(N_AX_DIR), math.sin(N_AX_DIR)]); n = np.array([-u[1], u[0]])
s = (XX - N_GRIP[0]) * u[0] + (YY - N_GRIP[1]) * u[1]; t = (XX - N_GRIP[0]) * n[0] + (YY - N_GRIP[1]) * n[1]
gap = (s > -48) & (s < 40) & (np.abs(t) <= 8.5) & ~axe
AXE = NEON.copy(); AXE[~axe] = 0
AXE[gap] = [58, 60, 66, 255]; AXE[gap & (np.abs(t) > 6.5)] = [16, 16, 18, 255]
axe_all = axe | gap
# ---- 러스트 도끼 ----
R_G = V(J['G']); pm, co = V(J['AXE']['pommel']), V(J['AXE']['collar']); R_DIR = math.atan2(co[1] - pm[1], co[0] - pm[0])
r_axe = lab('axe')
ur = np.array([math.cos(R_DIR), math.sin(R_DIR)])
r_far = ((XX - R_G[0]) * ur[0] + (YY - R_G[1]) * ur[1])[r_axe].max()
n_far = s[axe].max(); n_back = -s[axe].min()
K = r_far / n_far
print(f'러스트 도끼: 쥔 점 {R_G.tolist()} 자루 축 {math.degrees(R_DIR):.1f}° · 쥔 점→가장 먼 점 {r_far:.1f}')
print(f'네온 도끼: 쥔 점 {N_GRIP.tolist()} 자루 축 {math.degrees(N_AX_DIR):.1f}° · 쥔 점→가장 먼 점 {n_far:.1f} · 쥔 점→자루 끝 {n_back:.1f}  → 배율 K {K:.3f}')
ang = math.degrees(N_AX_DIR - R_DIR)           # cv2 각도(+ = 반시계, y 아래 좌표에서)
M = cv2.getRotationMatrix2D((float(N_GRIP[0]), float(N_GRIP[1])), ang, K); M[:, 2] += R_G - N_GRIP
axe_w = cv2.warpAffine(AXE, M, (512, 512), flags=cv2.INTER_AREA, borderValue=(0, 0, 0, 0))
ys, xs = np.nonzero(axe_w[..., 3] > 60)
print(f'맞춘 도끼 상자 x {xs.min()}–{xs.max()} · y {ys.min()}–{ys.max()} (러스트 도끼 위 끝 y {J["AXE"]["top_y"]}) · 자루 끝(쥔 점 아래) {n_back * K:.0f}px')
# ---- 방패 ----
shield = al & (XX >= 352) & (YY >= 195) & ~((XX < 365) & (YY > 430))   # 방패 왼쪽 옆 죔쇠 덩어리(x 322–351)는 먼 팔 쪽과 섞여 있어 뺌 — 자른 면은 외곽선으로
cut_edge = shield & (XX <= 354)
ys0, xs0 = np.nonzero(shield); nb = (xs0.min(), ys0.min(), xs0.max(), ys0.max())
rb = np.nonzero(lab('shield')); r_box = (rb[1].min(), rb[0].min(), rb[1].max(), rb[0].max())
Ks = (r_box[3] - r_box[1]) / (nb[3] - nb[1])
cx_r = (r_box[0] + r_box[2]) / 2; cx_n = (nb[0] + nb[2]) / 2
Ms = np.array([[Ks, 0, cx_r - Ks * cx_n], [0, Ks, r_box[3] - Ks * nb[3]]], np.float32)
SH = NEON.copy(); SH[~shield] = 0; SH[cut_edge] = [18, 18, 20, 255]
sh_w = cv2.warpAffine(SH, Ms, (512, 512), flags=cv2.INTER_AREA, borderValue=(0, 0, 0, 0))
ys, xs = np.nonzero(sh_w[..., 3] > 60)
print(f'네온 방패 상자 {nb} (가로 {nb[2]-nb[0]} · 세로 {nb[3]-nb[1]}) · 러스트 방패 {tuple(int(v) for v in r_box)} (가로 {r_box[2]-r_box[0]} · 세로 {r_box[3]-r_box[1]})')
print(f'맞춘 방패 배율 {Ks:.3f} → x {xs.min()}–{xs.max()} · y {ys.min()}–{ys.max()}')
# ---- 그림 ----
ghost = RUST.copy(); ghost[lab('axe', 'shield')] = 0; ghost[..., 3] *= .30
fists = RUST.copy(); fists[~lab('handF', 'handN')] = 0
def over(dst, src):
    a = src[..., 3:4] / 255.0; o = dst.copy(); o[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a); o[..., 3:4] = np.maximum(dst[..., 3:4], src[..., 3:4]); return o
img = over(over(over(ghost, sh_w), axe_w), fists)
W = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); W.alpha_composite(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)))
W = W.convert('RGB').resize((1024, 1024), Image.LANCZOS)
BH = 112; out = Image.new('RGB', (1024, 1024 + BH), (255, 255, 255)); out.paste(W, (0, BH)); d = ImageDraw.Draw(out)
f = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 30)
d.text((20, 14), '진한 도끼·방패 = 자리·각도·크기 (흐린 그림은 자세 참고)', fill=(170, 0, 0), font=f)
d.text((20, 56), '방패 = 가까운 손(화면 왼쪽) · 도끼 = 먼 손(화면 오른쪽), 진한 주먹 = 쥔 자리', fill=(30, 30, 30), font=f)
d.line([(0, BH - 2), (1024, BH - 2)], fill=(200, 200, 200), width=2)
out.save(os.path.join(SRC, 'refs', 'ref_weapon_fit17.png')); print('저장 refs/ref_weapon_fit17.png')
