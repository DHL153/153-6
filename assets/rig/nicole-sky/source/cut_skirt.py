"""치마 앞쪽 바깥 자락 잘라내기 (2026-10-17, DHL "옷이 없어야 할 부분에 있어요")
원본 그림처럼 치마 앞면이 금색 탭 달린 남색 판에서 끝나도록, 그 오른쪽의 크림 자락·좁은 띠를 잘라내고 잘린 가장자리에 잉크 선.
입력 skirt_v2_full.png → 출력 ../parts/skirt.png.  실행: python3 -I cut_skirt.py"""
import os, numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
src = Image.open(os.path.join(HERE, 'skirt_v2_full.png')).convert('RGBA'); W, H = src.size
line = [(318, 14), (352, 92), (381, 150), (405, 210), (426, 265), (432, 305)]   # 금색 탭 남색 판의 오른쪽 가장자리 (그림 픽셀)
cut = Image.new('L', (W, H), 0); ImageDraw.Draw(cut).polygon(line + [(W, H), (W, 0)], fill=255)
a = np.asarray(src).copy(); a[..., 3] = np.where(np.asarray(cut) > 0, 0, a[..., 3])
out = Image.fromarray(a); ImageDraw.Draw(out).line(line, fill=(28, 22, 26, 255), width=4, joint='curve')
oa = np.asarray(out).copy(); oa[..., 3] = np.minimum(oa[..., 3], np.asarray(src)[..., 3])
Image.fromarray(oa).save(os.path.join(HERE, '..', 'parts', 'skirt.png'))
