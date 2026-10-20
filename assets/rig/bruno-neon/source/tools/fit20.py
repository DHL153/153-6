"""20 네온 브루노 — 새 원화(10 러스트 브루노 자세) 요청 전 '철퇴 맞춤' 그림 (실수 39: 프롬프트 쓰기 전에 무기를 그 자세에 겹쳐 봄) — 2026-10-21 00:40
  기준 자세 = 10 러스트 브루노 원화(char_0010 — 리그 원본, 공격 키가 이 자세·이 쥔 점으로 짜여 있음)
  철퇴 = 20 네온 원화(char_0020) 의 철퇴 — 공 = 가까운 철퇴 공(가려진 곳 없음), 자루 = 먼 철퇴 자루(공~주먹 사이)
  크기 규칙(B — 12 네온 둘시네와 같은 판단): 주먹 → 공 가운데 = 러스트 도끼 주먹 → 도끼 머리 가운데(가까운 183.7 · 먼 173.5) — 공격 키·땅·게임 칸 그대로
            공 지름 = 네온 원화 공 × K(머리 크기 비 — 러스트 머리 134 / 네온 머리 162 ≈ .83 보다 조금 작게 .75, 러스트 도끼 날 폭과 비슷)
  출력: ../refs/ref_mace_fit20.png(첨부 3 — 흐린 러스트 자세 + 진한 철퇴 두 개 + 주먹) · 숫자(공 위 끝·좌우 끝, 캔버스 안인지)
실행: python3 -I fit20.py
"""
import json, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); REPO = os.path.abspath(os.path.join(SRC, '..', '..', '..', '..'))
NEON = np.array(Image.open(os.path.join(REPO, 'assets', 'art', 'characters', 'char_0020.png')).convert('RGBA'))
RUST = np.array(Image.open(os.path.join(REPO, 'assets', 'art', 'characters', 'char_0010.png')).convert('RGBA'))
M = json.load(open(os.path.join(REPO, 'assets', 'rig', 'bruno-rust', 'source', 'measure10.json')))
LAB = np.load(os.path.join(REPO, 'assets', 'rig', 'bruno-rust', 'source', 'work', 'labels.npy'))
NAMES = json.load(open(os.path.join(REPO, 'assets', 'rig', 'bruno-rust', 'source', 'work', 'label_names.json')))
lab = lambda *ns: np.logical_or.reduce([LAB == NAMES.index(n) + 1 for n in ns])
V = lambda p: np.array(p, float)
YY, XX = np.mgrid[0:512, 0:512].astype(float)
K = 0.75
# ---- 네온 철퇴 조각 (네온 원화 px) ----
BALL_C, BALL_R = V([90, 390]), 64                      # 가까운 철퇴 공(가시 끝까지)
SH_A, SH_B, SH_W = V([282, 100]), V([428, 202]), 10    # 먼 철퇴 자루: 공 아래 끝 → 주먹 바로 위(가운데 줄 ±10)
def band(p, q, w):
    d = q - p; L = np.linalg.norm(d); u = d / L; n = np.array([-u[1], u[0]])
    s = (XX - p[0]) * u[0] + (YY - p[1]) * u[1]; t = (XX - p[0]) * n[0] + (YY - p[1]) * n[1]
    return (s >= 0) & (s <= L) & (np.abs(t) <= w), u, n, L
al = NEON[..., 3] > 0
ball = al & (((XX - BALL_C[0]) ** 2 + (YY - BALL_C[1]) ** 2) <= BALL_R ** 2) & (XX < 150)   # 오른쪽 자루 쪽은 뺌
shaft_m, U_sh, N_sh, L_sh = band(SH_A, SH_B, SH_W); shaft_m &= al
# 자루 띠를 '축 좌표' 그림으로 펴기(길이 방향 반복해 쓸 수 있게): 가로 = 축(공 → 주먹), 세로 = 폭
SW = int(L_sh); SH_img = np.zeros((2 * SH_W + 1, SW, 4), np.float32)
for i in range(SW):
    for j in range(-SH_W, SH_W + 1):
        x, y = SH_A + U_sh * i + N_sh * j
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < 512 and 0 <= yi < 512 and shaft_m[yi, xi]: SH_img[j + SH_W, i] = NEON[yi, xi]
CLEAN_I = int(20 + np.argmax([(SH_img[:, i, 3] > 200).sum() * 1000 - SH_img[:, i, :3].mean() for i in range(20, SW - 20)]))
BALL_DIR = math.degrees(math.atan2(345 - BALL_C[1], 190 - BALL_C[0]))   # 네온 가까운 철퇴: 공 → 주먹 방향(공의 자루 꽂는 곳이 이쪽)
def place_mace(canvas, fist, head, pom_len):
    """주먹 → 공 가운데 축에 철퇴: 공(×K) + 자루(×K 굵기, 길이는 주먹 −pom_len ~ 공 가장자리, 무늬는 네온 자루 그대로 늘이지 않고 잘라 씀)"""
    u = (head - fist) / np.linalg.norm(head - fist); n = np.array([-u[1], u[0]]); Lh = np.linalg.norm(head - fist)
    r = BALL_R * K; s_end = Lh - r * .55; s0 = -pom_len
    # 자루: 축 좌표 s(주먹 0 → 공 쪽 +), 폭 t — 네온 자루 그림에서 공 쪽 끝을 맞춰 뒤로 읽음(넘치면 맨 끝 줄 반복)
    out = canvas.copy().astype(np.float32)
    s = (XX - fist[0]) * u[0] + (YY - fist[1]) * u[1]; t = (XX - fist[0]) * n[0] + (YY - fist[1]) * n[1]
    m = (s >= s0) & (s <= s_end) & (np.abs(t) <= SH_W * K)
    # 자루 = 네온 자루에서 가장 깨끗한(불투명이 가장 많은) 단면 한 줄을 길이 방향으로 이어 붙임 — 띠를 그대로 쓰면 머리카락·틈이 섞여 얼룩
    src_j = np.clip(np.round(t / K).astype(int) + SH_W, 0, 2 * SH_W)
    px = SH_img[src_j, CLEAN_I]; a = px[..., 3:4] / 255.0 * m[..., None]
    out[..., :3] = px[..., :3] * a + out[..., :3] * (1 - a); out[..., 3:4] = np.maximum(out[..., 3:4], a * 255)
    # 공: 네온 공을 ×K, 가운데 = head
    want = math.degrees(math.atan2(fist[1] - head[1], fist[0] - head[0]))   # 공 → 주먹 방향에 자루 꽂는 곳을 맞춤
    Mb = cv2.getRotationMatrix2D((float(BALL_C[0]), float(BALL_C[1])), BALL_DIR - want, K); Mb[:, 2] += head - BALL_C
    bimg = NEON.copy(); bimg[~ball] = 0
    wb = cv2.warpAffine(bimg.astype(np.float32), Mb, (512, 512), flags=cv2.INTER_AREA, borderValue=(0, 0, 0, 0))
    a = wb[..., 3:4] / 255.0; out[..., :3] = wb[..., :3] * a + out[..., :3] * (1 - a); out[..., 3:4] = np.maximum(out[..., 3:4], wb[..., 3:4])
    ys, xs = np.nonzero(wb[..., 3] > 60); return out, (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())), r
N_, F_ = M['near'], M['far']
ghost = RUST.copy().astype(np.float32); ghost[lab('axeN', 'axeF')] = 0; ghost[..., 3] *= .32       # 흐린 러스트 자세(도끼 지움)
can = np.zeros((512, 512, 4), np.float32)
can, boxN, r = place_mace(can, V(N_['fist']), V(N_['head']), 30)
can, boxF, _ = place_mace(can, V(F_['fist']), V(F_['head']), 26)
fists = RUST.copy().astype(np.float32); fists[~lab('fistN', 'fistF')] = 0                          # 쥔 자리 = 러스트 주먹(진하게)
def over(dst, src):
    a = src[..., 3:4] / 255.0; o = dst.copy(); o[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a); o[..., 3:4] = np.maximum(dst[..., 3:4], src[..., 3:4]); return o
img = over(over(ghost, can), fists)
print('공 반지름(가시 끝)', round(r, 1), '· 가까운 철퇴 공 상자 x', boxN[:2], 'y', boxN[2:], '· 먼 철퇴 공 상자 x', boxF[:2], 'y', boxF[2:])
print('캔버스 안:', all(0 <= v < 512 for v in boxN + boxF), '· 러스트 도끼 위 끝 y', N_['top'][1], '→ 철퇴 공 위 끝 y', min(boxN[2], boxF[2]))
W = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); W.alpha_composite(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)))
W = W.convert('RGB').resize((1024, 1024), Image.LANCZOS)
BH = 112; out = Image.new('RGB', (1024, 1024 + BH), (255, 255, 255)); out.paste(W, (0, BH)); d = ImageDraw.Draw(out)
f = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 30)
d.text((20, 14), '진한 철퇴 두 개 = 자리·각도·크기 (흐린 그림은 자세 참고)', fill=(170, 0, 0), font=f)
d.text((20, 56), '주먹이 자루를 쥔 자리 = 진한 주먹, 공은 자루 끝', fill=(30, 30, 30), font=f)
d.line([(0, BH - 2), (1024, BH - 2)], fill=(200, 200, 200), width=2)
out.save(os.path.join(SRC, 'refs', 'ref_mace_fit20.png')); print('저장 refs/ref_mace_fit20.png')
