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
- 기본 자세(Idle)도 같은 배율, 발은 같은 위치. 캔버스를 넘으면 그 프레임만 살짝 줄임

사용: python3 tools/normalize_battle_chars.py [0001 0002 ...]   (생략하면 30종 전부)
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
    '0013': 133, '0014': 56, '0015': 56, '0016': 56, '0017': 62, '0018': 75,
    '0019': 105, '0020': 72, '0021': 56, '0022': 70, '0023': 60, '0024': 78,
    '0025': 56, '0026': 70, '0027': 70, '0028': 75, '0029': 78, '0030': 75,
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


def place(im, s, dx, dy):
    """배율 s로 키운 뒤 (dx, dy)만큼 옮겨 512 캔버스에 놓는다."""
    big = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    out = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    out.paste(big, (round(dx), round(dy)))  # 빈 캔버스라 그대로 복사 (밖으로 나간 부분은 잘림)
    return out


def normalize(item, num):
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

    # 기본 자세: 같은 배율, 발 위치 동일, 가로는 자기 중심을 가운데로
    for p in {item['idle'], item['attack'], item['skill'], item['victory']}:
        if p in out:
            continue
        if not os.path.exists(os.path.join(ROOT, p)):
            print(f'  (없는 파일 건너뜀: {p})')
            continue
        im = open_unit(p)
        b = bbox(im)
        si = s
        w, h = (b[2] - b[0]) * si, (b[3] - b[1]) * si
        fit = min(1, (CANVAS - 2 * MARGIN) / w, (FEET_Y - MARGIN) / h)
        si *= fit
        icx = (b[0] + b[2]) / 2
        out[p] = place(im, si, CANVAS / 2 - icx * si, FEET_Y - b[3] * si)
    return out, s


def main():
    only = set(sys.argv[1:])
    for item in load_items():
        num = item['id'][-4:]
        if only and num not in only:
            continue
        frames, s = normalize(item, num)
        for p, im in frames.items():
            im.save(os.path.join(ROOT, p), optimize=True)
        print(f'{num} {item["name"]}: x{s:.2f}, {len(frames)} files')


if __name__ == '__main__':
    main()
