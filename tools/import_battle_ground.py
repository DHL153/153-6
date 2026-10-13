#!/usr/bin/env python3
"""전투 배경(땅 레이어) 가져오기 — 연두 배경 제거 + 잘린 아랫단 복구 + 게임 크기로 저장.

사용법:
    python3 tools/import_battle_ground.py <그림 10장이 든 폴더> <시작 번호>
    예) python3 tools/import_battle_ground.py ~/neon 11   → bg_battle_0011 ~ 0020

규격 (2026-10-14, 전투 배경 2레이어):
  - 받는 그림: 2048x1024, 지평선 위는 연두 단색(#00FF00), 아래는 달리기 길
  - 저장: assets/art/backgrounds/battle/bg_battle_NNNN.png, 1536x768 투명 PNG
  - 폴더 안 PNG는 파일 이름 순서대로 번호를 붙임 (01_..., 02_... 형태 권장)

잘린 그림 처리:
  압축 파일로 받은 큰 그림은 아랫부분이 잘려 검게 오는 경우가 있음.
  같은 묶음의 그림들은 아랫길(달리기 길 띠)이 거의 같으므로,
  잘린 줄 바로 위 80줄이 가장 비슷한 다른 그림에서 아랫단을 가져와 8줄 겹쳐 이어 붙인다.
  복구한 그림은 끝에 목록으로 알려 주니, 원본을 다시 받으면 교체할 것.
"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageFile, ImageFilter

ImageFile.LOAD_TRUNCATED_IMAGES = True  # 잘린 그림도 읽을 수 있는 데까지 읽기

OUT_SIZE = (1536, 768)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, 'assets', 'art', 'backgrounds', 'battle')


def last_filled_row(a):
    """검게 비지 않은 마지막 줄 번호 (잘린 그림 판별용)."""
    rows = np.where(a.reshape(a.shape[0], -1).any(1))[0]
    return int(rows.max()) if len(rows) else -1


def repair(images):
    """잘린 그림의 아랫단을 가장 비슷한 온전한 그림에서 가져와 복구. 복구 목록을 돌려줌."""
    h = images[0].shape[0]
    last = [last_filled_row(a) for a in images]
    whole = [i for i, l in enumerate(last) if l >= h - 1]
    fixed = []
    for i, l in enumerate(last):
        if l >= h - 1:
            continue
        if not whole:
            raise SystemExit(f'{i + 1}번째 그림이 잘렸는데 복구에 쓸 온전한 그림이 없습니다.')
        ref = images[i][max(0, l - 80):l]
        donor = min(whole, key=lambda d: np.abs(images[d][max(0, l - 80):l] - ref).mean())
        a, d, blend = images[i], images[donor], 8
        for k in range(blend):  # 이음 자국이 안 보이게 8줄 섞기
            t = (k + 1) / (blend + 1)
            r = l - blend + 1 + k
            a[r] = (1 - t) * a[r] + t * d[r]
        a[l + 1:] = d[l + 1:]
        fixed.append((i, donor, round(100 * (h - 1 - l) / h, 1)))
    return fixed


def key_green(a):
    """연두(#00FF00) 배경을 투명하게, 가장자리 초록 번짐 제거."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    greenness = g - np.maximum(r, b)
    alpha = np.clip((150 - greenness) / 90, 0, 1)   # 150 이상 = 완전 투명, 60 이하 = 불투명
    g2 = np.where(greenness > 0, np.minimum(g, np.maximum(r, b)), g)  # 초록 번짐 제거
    im = Image.fromarray(np.dstack([r, g2, b, alpha * 255]).clip(0, 255).astype('uint8'), 'RGBA')
    # 하늘 자리에 남은 작은 점 지우기
    al = im.getchannel('A')
    opened = al.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    im.putalpha(Image.fromarray(np.minimum(np.asarray(opened), np.asarray(al))))
    return im


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src_dir, start = sys.argv[1], int(sys.argv[2])
    files = sorted(glob.glob(os.path.join(src_dir, '**', '*.png'), recursive=True))
    if not files:
        raise SystemExit(f'PNG가 없습니다: {src_dir}')
    images = []
    for f in files:
        try:
            images.append(np.asarray(Image.open(f).convert('RGB')).astype(float))
        except Exception as e:  # 읽을 수 없는 파일은 중단하고 알림
            raise SystemExit(f'그림을 읽을 수 없습니다: {f} ({e})')
    if len({a.shape for a in images}) != 1:
        raise SystemExit('그림 크기가 서로 다릅니다: ' + ', '.join(f'{os.path.basename(f)} {a.shape[1]}x{a.shape[0]}' for f, a in zip(files, images)))

    fixed = repair(images)
    os.makedirs(OUT_DIR, exist_ok=True)
    for k, (f, a) in enumerate(zip(files, images)):
        out = os.path.join(OUT_DIR, f'bg_battle_{start + k:04d}.png')
        key_green(a).resize(OUT_SIZE, Image.LANCZOS).save(out, optimize=True)
        print(f'{os.path.basename(f)} -> {os.path.relpath(out, REPO)} ({os.path.getsize(out) / 1e6:.2f} MB)')
    for i, donor, pct in fixed:
        print(f'⚠ 복구: {os.path.basename(files[i])} 아랫단 {pct}% 잘림 → {os.path.basename(files[donor])}의 아랫길로 이어 붙임')


if __name__ == '__main__':
    main()
