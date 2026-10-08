#!/usr/bin/env python3
"""전투 캐릭터 이미지 정규화: 모든 캐릭터를 같은 크기·같은 위치로 맞춘다.

규칙 (모든 프레임 공통)
- 캔버스: 512 x 512 투명 PNG
- 달리기 몸 높이: BODY_H px (캐릭터의 달리기 프레임 중 가장 큰 높이 기준)
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
BODY_H = 400
FEET_Y = 456
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


def normalize(item):
    runs = [open_unit(p) for p in item['runFrames']]
    rb = [bbox(im) for im in runs]
    top, bot = min(b[1] for b in rb), max(b[3] for b in rb)
    left, right = min(b[0] for b in rb), max(b[2] for b in rb)
    cx = st.median([(b[0] + b[2]) / 2 for b in rb])

    s = BODY_H / (bot - top)
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
        frames, s = normalize(item)
        for p, im in frames.items():
            im.save(os.path.join(ROOT, p), optimize=True)
        print(f'{num} {item["name"]}: x{s:.2f}, {len(frames)} files')


if __name__ == '__main__':
    main()
