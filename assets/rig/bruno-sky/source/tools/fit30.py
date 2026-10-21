"""30 스카이 브루노 — 새 원화(10 러스트 브루노 자세) 요청 전 '도끼 맞춤' 그림 (실수 39: 프롬프트 쓰기 전에 무기를 그 자세에 겹쳐 봄)
  기준 자세 = 10 러스트 브루노 원화(char_0010 — 리그 원본, 공격 키가 이 자세·이 쥔 점으로 짜여 있음)
  도끼 = 30 스카이 원화(char_0030) 의 먼 도끼(머리 위로 든 것 — 가려진 곳 없음): 머리(날·소켓·뒤 작은 날) + 자루(소켓 밑 ~ 주먹 위)
  크기 규칙 B(20 네온과 같음): 주먹 → 도끼 머리 가운데(소켓) = 러스트 도끼 길이(가까운 183.7 · 먼 173.5) — 공격 키·땅·게임 칸 그대로
            도끼 머리 = 스카이 도끼 × K(머리 크기 비 — 러스트 / 스카이 ≈ .95, 눈 사이·머리카락~눈 평균)
  자루 = 스카이 자루(소켓 밑 ~ 주먹 위, 가죽 감기 무늬)를 길이 방향으로 이어 붙임(늘이지 않음)
  출력: ../refs/ref_axe_fit30.png(첨부 3 — 흐린 러스트 자세 + 진한 도끼 두 자루 + 러스트 주먹) · 숫자(날 위 끝·좌우 끝, 캔버스 안인지)
실행: python3 -I fit30.py
"""
import json, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); REPO = os.path.abspath(os.path.join(SRC, '..', '..', '..', '..'))
SKY = np.array(Image.open(os.path.join(SRC, 'refs', 'ref_design_char0030.png')).convert('RGBA')).astype(np.float32)
RUST = np.array(Image.open(os.path.join(REPO, 'assets', 'art', 'characters', 'char_0010.png')).convert('RGBA'))
BR = os.path.join(REPO, 'assets', 'rig', 'bruno-rust', 'source')
M = json.load(open(os.path.join(BR, 'measure10.json')))
LAB = np.load(os.path.join(BR, 'work', 'labels.npy')); NAMES = json.load(open(os.path.join(BR, 'work', 'label_names.json')))
lab = lambda *ns: np.logical_or.reduce([LAB == NAMES.index(n) + 1 for n in ns])
V = lambda p: np.array(p, float)
YY, XX = np.mgrid[0:512, 0:512].astype(float)
K = 0.95
# ---- 스카이 먼 도끼 (스카이 원화 px — 줄마다 자루 불투명 띠 가운데로 잰 축: y150 x425 · y222 x453) ----
HEAD_C = V([409, 108])                    # 소켓(크림 네모) 가운데 = 도끼 머리 가운데
FIST_C = V([464, 248])                    # 주먹 가운데(축 위)
U_S = (HEAD_C - FIST_C) / np.linalg.norm(HEAD_C - FIST_C); N_S = np.array([-U_S[1], U_S[0]])
SIG0, SIG1, SH_W = 43.0, 124.0, 10        # 자루 띠: 머리 가운데에서 주먹 쪽으로 43(소켓 밑) ~ 124(주먹 위), 폭 ±10(외곽선 포함 — 줄마다 21px 폭 × cos 21°)
al = SKY[..., 3] > 0
head_m = al & (((YY <= 146) & (XX >= 352)) | ((YY > 146) & (YY <= 184) & (XX >= 466)))
_n, _cc, _st, _ = cv2.connectedComponentsWithStats(head_m.astype(np.uint8), connectivity=8)
head_m = _cc == 1 + int(np.argmax(_st[1:, cv2.CC_STAT_AREA]))     # 가장 큰 덩어리만(머리카락 끝 부스러기 뺌)
# 자루 띠를 축 좌표 그림으로 폄: 가로 = σ(머리 → 주먹), 세로 = 폭
SW = int(SIG1 - SIG0); STRIP = np.zeros((2 * SH_W + 1, SW, 4), np.float32)
for i in range(SW):
    for j in range(-SH_W, SH_W + 1):
        x, y = HEAD_C - U_S * (SIG0 + i) + N_S * j
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < 512 and 0 <= yi < 512 and al[yi, xi]: STRIP[j + SH_W, i] = SKY[yi, xi]
def over(dst, src):
    a = src[..., 3:4] / 255.0; o = dst.copy(); o[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a); o[..., 3:4] = np.maximum(dst[..., 3:4], src[..., 3:4]); return o
def place_axe(canvas, fist, head, pom_len):
    u = (head - fist) / np.linalg.norm(head - fist); n = np.array([-u[1], u[0]]); Lh = np.linalg.norm(head - fist)
    # 자루: 목표 σ'(머리 → 주먹) = 0 ~ Lh + pom_len, 원본 σ = σ'/K 를 띠 안에서 되풀이
    sig = ((XX - head[0]) * -u[0] + (YY - head[1]) * -u[1]); t = (XX - head[0]) * n[0] + (YY - head[1]) * n[1]
    m = (sig >= SIG0 * K) & (sig <= Lh + pom_len) & (np.abs(t) <= SH_W * K)
    si = (((sig / K - SIG0) % SW)).astype(int).clip(0, SW - 1); tj = np.clip(np.round(t / K).astype(int) + SH_W, 0, 2 * SH_W)
    px = STRIP[tj, si] * m[..., None]
    ol = m & (np.abs(t) / K >= 8.6)                                   # 자루 양옆 외곽선(이어 붙인 띠의 끝 들쭉날쭉 정리)
    px[ol] = (12, 8, 6, 255)
    out = over(canvas, px)
    # 머리: 스카이 도끼 머리를 회전·×K, 가운데 = head, 축 방향 U_S → u
    rot = math.degrees(math.atan2(U_S[1], U_S[0]) - math.atan2(u[1], u[0]))
    Mb = cv2.getRotationMatrix2D((float(HEAD_C[0]), float(HEAD_C[1])), rot, K); Mb[:, 2] += head - HEAD_C
    himg = SKY.copy(); himg[~head_m] = 0
    wh = cv2.warpAffine(himg, Mb, (512, 512), flags=cv2.INTER_AREA, borderValue=(0, 0, 0, 0))
    out = over(out, wh)
    ys, xs = np.nonzero(wh[..., 3] > 60); return out, (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())), round(-rot, 1)
N_, F_ = M['near'], M['far']
ghost = RUST.copy().astype(np.float32); ghost[lab('axeN', 'axeF')] = 0; ghost[..., 3] *= .32       # 흐린 러스트 자세(도끼 지움)
can = np.zeros((512, 512, 4), np.float32)
can, boxN, rN = place_axe(can, V(N_['fist']), V(N_['head']), 30)
can, boxF, rF = place_axe(can, V(F_['fist']), V(F_['head']), 26)
fists = RUST.copy().astype(np.float32); fists[~lab('fistN', 'fistF')] = 0                          # 쥔 자리 = 러스트 주먹(진하게)
img = over(over(ghost, can), fists)
src_len = float(np.linalg.norm(HEAD_C - FIST_C))
print(f'스카이 원화 도끼 주먹→머리 {src_len:.1f} → 러스트 길이 가까운 {N_["len"]["fist_to_head"]:.1f} · 먼 {F_["len"]["fist_to_head"]:.1f} (자루 ×{N_["len"]["fist_to_head"] / src_len:.2f} · ×{F_["len"]["fist_to_head"] / src_len:.2f}, 머리 ×{K})')
print('돌림(스카이 → 러스트 축)', rN, rF, '· 가까운 도끼 머리 상자 x', boxN[:2], 'y', boxN[2:], '· 먼 x', boxF[:2], 'y', boxF[2:])
print('캔버스 안:', all(0 <= v < 512 for v in boxN + boxF), '· 러스트 도끼 위 끝 y', N_['top'][1], '→ 스카이 도끼 위 끝 y', min(boxN[2], boxF[2]))
os.makedirs(os.path.join(SRC, 'review'), exist_ok=True)
Image.fromarray(np.clip(can, 0, 255).astype(np.uint8)).save(os.path.join(SRC, 'review', 'fit30_axes.png'))
W = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); W.alpha_composite(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)))
W = W.convert('RGB').resize((1024, 1024), Image.LANCZOS)
BH = 112; out = Image.new('RGB', (1024, 1024 + BH), (255, 255, 255)); out.paste(W, (0, BH)); d = ImageDraw.Draw(out)
f = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 30)
d.text((20, 14), '진한 도끼 두 자루 = 자리·각도·크기 (흐린 그림은 자세 참고)', fill=(170, 0, 0), font=f)
d.text((20, 56), '주먹이 자루를 쥔 자리 = 진한 주먹, 도끼 머리는 자루 위 끝', fill=(30, 30, 30), font=f)
d.line([(0, BH - 2), (1024, BH - 2)], fill=(200, 200, 200), width=2)
out.save(os.path.join(SRC, 'refs', 'ref_axe_fit30.png')); print('저장 refs/ref_axe_fit30.png')
