#!/usr/bin/env python3
"""전투 캐릭터 이미지 정규화: 모든 캐릭터를 같은 크기·같은 위치로 맞춘다.

규칙 (모든 프레임 공통)
- 캔버스: 512 x 512 투명 PNG
- 몸 크기: 머리 꼭대기 ~ 발끝이 BODY_H px (무기·날개처럼 머리 위로 솟은 것은 계산에서 뺌)
  · 머리 위치는 HEAD_TOP 표에 사람이 눈으로 확인해 적는다 (아래 설명)
  · 탈것(자동차·말·비행기·열기구 등)은 전체 높이를 몸으로 본다
- 발 위치: 달리기 프레임의 가장 아래가 FEET_Y px
- 가로 중심: 달리기 프레임 중심(중앙값)을 256 px에 맞춤
- 같은 캐릭터의 프레임은 같은 배율·같은 이동량 → 달리기 흔들림은 그대로 유지
- 기본 자세(Idle)는 IDLE_HEAD 표로 머리~발을 BODY_H로 맞춤, 발은 같은 위치. 캔버스를 넘으면 그 프레임만 살짝 줄임

사용: python3 tools/normalize_battle_chars.py [0001 0002 ...]   (생략하면 30종 전부)
캐릭터 그림을 새로 바꿀 때: 원본을 넣고 IDLE_HEAD는 그 캐릭터 값을 0, IDLE_FEET는 지운 뒤 한 번 돌리고,
  결과 기본 자세 그림에서 머리 꼭대기(%)·발끝(%)을 눈으로 재서 표에 적고, 원본을 다시 넣어 번호를 적어 한 번 더 돌린다.
  (표 값은 정규화된 기본 자세 그림 기준이라, 예전 값을 그대로 두면 새 그림 크기가 틀어진다)
index.html 안의 FALLBACK_ASSET_DATA(battleCharacters)에서 파일 경로를 읽는다.
"""
import json, os, sys, statistics as st
from PIL import Image

CANVAS = 512
BODY_H = 290        # 머리 꼭대기 ~ 발끝
FEET_Y = 472

# 머리 꼭대기 위치 표 (캐릭터 번호 → y 픽셀)
# 기준: 달리기 그림 전체(무기 포함)를 높이 400, 위 56 ~ 아래(발) 456 으로 맞췄을 때의 머리 꼭대기 y.
# 56 = 무기 등 솟은 것이 없음(또는 탈것 전체를 몸으로 봄). 새 캐릭터는 56으로 두고 결과를 본 뒤 고친다.
REF_TOP, REF_FEET = 56, 456
HEAD_TOP = {
    '0001': 62, '0002': 82, '0003': 178, '0004': 56, '0005': 136, '0006': 172,
    '0007': 157, '0008': 171, '0009': 171, '0010': 166, '0011': 130, '0012': 124,
    '0013': 133, '0014': 56, '0015': 56, '0016': 56, '0017': 186, '0018': 118,
    '0019': 155, '0020': 130, '0021': 112, '0022': 75, '0023': 100, '0024': 56,
    '0025': 56, '0026': 118, '0027': 140, '0028': 56, '0029': 122, '0030': 100,
}
# 기본 자세(Idle/스킬 그림) 머리 꼭대기 위치 표 (캐릭터 번호 → %)
# 기본 자세 그림(무기 포함) 맨 위를 0, 맨 아래를 100으로 볼 때 머리 꼭대기가 몇 % 아래에 있는지.
# 0 = 머리가 그림 맨 위. 이 값으로 기본 자세도 머리~발을 BODY_H로 맞춘다 (웅크린 자세가 작아 보이지 않게).
# 표에 없는 캐릭터는 예전처럼 달리기와 같은 배율을 쓴다.
IDLE_HEAD = {
    '0001': 0, '0002': 22, '0003': 40, '0004': 15, '0005': 15, '0006': 24,
    '0007': 38, '0008': 16, '0009': 19, '0010': 42, '0011': 1, '0012': 0,
    '0013': 1, '0014': 0, '0015': 0, '0016': 0, '0017': 14, '0018': 0,
    '0019': 2, '0020': 27, '0021': 23, '0022': 1, '0023': 24, '0024': 0,
    '0025': 2, '0026': 24, '0027': 23, '0028': 9, '0029': 30, '0030': 26,
}
# 기본 자세 발끝 위치 표 (%). 무기가 발보다 아래로 내려온 그림만 적는다 (없으면 100 = 그림 맨 아래가 발).
# 주의: IDLE_CLIPPED 캐릭터는 발 아래 무기 끝이 캔버스 밖으로 조금 잘려 저장됐다.
#       다시 돌리면 그림 높이가 달라지므로, 번호를 따로 적어 돌릴 때(새 그림으로 교체할 때)만 기본 자세를 다시 만든다.
IDLE_CLIPPED = {'0007', '0011', '0013', '0027'}
IDLE_FEET = {
    '0006': 95, '0007': 84, '0010': 93, '0011': 82, '0012': 91, '0013': 81,
    '0017': 94, '0027': 89,
}
MARGIN = 4          # 캔버스 가장자리 여백
ALPHA_MIN = 24      # 이보다 옅은 픽셀(빛 번짐 등)은 크기 계산에서 제외

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_items():
    s = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    key = 'const FALLBACK_ASSET_DATA = '
    i = s.index(key) + len(key)
    data, _ = json.JSONDecoder().raw_decode(s[i:])
    return data['battleCharacters']['items']


def open_unit(path):
    """프레임을 폭 512 기준으로 맞춰 연다 (캔버스 크기가 섞여 있어도 같은 단위)."""
    im = Image.open(os.path.join(ROOT, path)).convert('RGBA')
    if im.width != CANVAS:
        f = CANVAS / im.width
        im = im.resize((round(im.width * f), round(im.height * f)), Image.LANCZOS)
    return im


def bbox(im):
    return im.getchannel('A').point(lambda v: 255 if v >= ALPHA_MIN else 0).getbbox()


def body_center_x(im, top, bottom):
    """머리~발 사이 줄에서 보이는 픽셀의 가로 중앙값 (무기가 한쪽으로 뻗어도 몸 쪽에 가깝다)."""
    band = im.crop((0, round(top), im.width, round(bottom))).getchannel('A')
    cols = band.point(lambda v: 255 if v >= ALPHA_MIN else 0).resize((im.width, 1), Image.BOX)
    w = list(cols.tobytes())
    half, acc = sum(w) / 2, 0
    for x, v in enumerate(w):
        acc += v
        if acc >= half:
            return x + 0.5
    return im.width / 2


def place(im, s, dx, dy):
    """배율 s로 키운 뒤 (dx, dy)만큼 옮겨 512 캔버스에 놓는다."""
    big = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    out = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    out.paste(big, (round(dx), round(dy)))  # 빈 캔버스라 그대로 복사 (밖으로 나간 부분은 잘림)
    return out


def normalize(item, num, redo_idle=True):
    runs = [open_unit(p) for p in item['runFrames']]
    rb = [bbox(im) for im in runs]
    top, bot = min(b[1] for b in rb), max(b[3] for b in rb)
    left, right = min(b[0] for b in rb), max(b[2] for b in rb)
    cx = st.median([(b[0] + b[2]) / 2 for b in rb])

    s = (REF_FEET - REF_TOP) / (bot - top)                       # 1단계: 전체 높이 400 기준
    s *= BODY_H / (REF_FEET - HEAD_TOP.get(num, REF_TOP))          # 2단계: 머리~발을 BODY_H로
    # 달리기 프레임이 캔버스 밖으로 나가면 그 캐릭터 배율을 줄인다
    s = min(s, (CANVAS / 2 - MARGIN) / max(cx - left, right - cx), (FEET_Y - MARGIN) / (bot - top))
    dx, dy = CANVAS / 2 - cx * s, FEET_Y - bot * s

    out = {p: place(im, s, dx, dy) for p, im in zip(item['runFrames'], runs)}

    # 기본 자세: IDLE_HEAD·IDLE_FEET로 머리~발을 BODY_H로, 발 위치 동일, 가로는 자기 중심을 가운데로
    for p in {item['idle'], item['attack'], item['skill'], item['victory']}:
        if p in out:
            continue
        if num in IDLE_CLIPPED and not redo_idle:
            continue
        if not os.path.exists(os.path.join(ROOT, p)):
            print(f'  (없는 파일 건너뜀: {p})')
            continue
        im = open_unit(p)
        b = bbox(im)
        si = s
        feet = b[1] + (b[3] - b[1]) * IDLE_FEET.get(num, 100) / 100     # 발끝 y (무기 끝이 아님)
        if num in IDLE_HEAD:                                     # 머리~발을 BODY_H로
            si = BODY_H / (feet - (b[1] + (b[3] - b[1]) * IDLE_HEAD[num] / 100))
        w = (b[2] - b[0]) * si
        # 캔버스를 넘지 않게 (발보다 아래로 내려온 무기 끝은 잘려도 몸 크기를 우선)
        fit = min(1, (CANVAS - 2 * MARGIN) / w, (FEET_Y - MARGIN) / ((feet - b[1]) * si))
        si *= fit
        # 가로: 무기를 뺀 몸 중심을 가운데로 (컷인에서 캐릭터가 한쪽으로 치우치지 않게)
        head = b[1] + (b[3] - b[1]) * IDLE_HEAD.get(num, 0) / 100
        icx = body_center_x(im, head, feet) if num in IDLE_HEAD else (b[0] + b[2]) / 2
        dx = CANVAS / 2 - icx * si
        dx = min(max(dx, MARGIN - b[0] * si), CANVAS - MARGIN - b[2] * si)  # 무기는 캔버스 안에
        out[p] = place(im, si, dx, FEET_Y - feet * si)
    return out, s


def main():
    only = set(sys.argv[1:])
    for item in load_items():
        num = item['id'][-4:]
        if only and num not in only:
            continue
        frames, s = normalize(item, num, redo_idle=num in only)
        for p, im in frames.items():
            im.save(os.path.join(ROOT, p), optimize=True)
        print(f'{num} {item["name"]}: x{s:.2f}, {len(frames)} files')


if __name__ == '__main__':
    main()
