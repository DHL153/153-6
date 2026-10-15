#!/usr/bin/env python3
"""UI 버튼 그림에 '살짝 녹슨' 질감을 입혀 *_rust.webp 로 저장 (2026-10-15).

원본(ui_btn.webp 등)은 그대로 두고 옆에 새 파일을 만든다 → CSS에서 새 파일을 씀.
사용: python3 tools/rustify_ui_buttons.py [강도 0~1, 기본 1.2]
  - 황동 테두리: 얼룩덜룩한 녹(주황·갈색) + 작은 녹 점
  - 가운데 에나멜 판: 테두리 쪽에만 아주 옅은 녹물 얼룩 (글씨 대비 유지)
  - 같은 씨앗값이라 다시 돌려도 같은 결과
"""
import sys, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'ui', 'theme')
FILES = {  # 파일: 강도 배율 (강조 버튼·눌림은 조금 약하게)
    'ui_btn': 1.0, 'ui_btn_pressed': 1.0,
    'ui_btn_primary': 0.6, 'ui_btn_primary_pressed': 0.6,
    'ui_tab': 0.8, 'ui_tab_active': 0.55,
}


def noise(h, w, rng, octaves=4, base=6):
    """여러 크기의 무작위 격자를 겹친 부드러운 얼룩 (0~1)."""
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = base * 2 ** o // 2 + 2, base * 2 ** o + 2
        g = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += np.asarray(im, np.float32) / 255 * amp
        tot += amp
        amp *= 0.5
    return out / tot


def rustify(name, k, seed):
    path = os.path.join(ROOT, name + '.webp')
    im = Image.open(path).convert('RGBA')
    a = np.asarray(im, np.float32)
    rgb, al = a[..., :3], a[..., 3:4]
    h, w = rgb.shape[:2]
    rng = np.random.default_rng(seed)

    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    brass = np.clip(((r - b) - 40) / 80, 0, 1) * (r > g * 0.95)          # 금색 테두리
    enamel = np.clip(((b - r) - 10) / 60, 0, 1)                            # 남색 판
    # 가장자리까지 거리 (0=가장자리, 1=가운데) → 판의 녹물은 가장자리 쪽만
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = np.minimum(np.minimum(xx, w - 1 - xx) / (w * 0.5), np.minimum(yy, h - 1 - yy) / (h * 0.5))
    near_edge = np.clip(1 - edge / 0.45, 0, 1)

    rim = np.clip(1 - (edge - 0.22) / 0.12, 0, 1)                          # 테두리 띠 (강조 버튼 주황 판 제외)
    brass = brass * rim
    n = noise(h, w, rng, octaves=5, base=5)
    blot = np.clip((n - 0.42) / 0.2, 0, 1) ** 1.1                         # 녹 얼룩
    speck = (rng.random((h, w)) > 0.975).astype(np.float32)               # 작은 녹 점
    speck = np.asarray(Image.fromarray((speck * 255).astype(np.uint8)).resize((w, h)), np.float32) / 255

    rust_col = np.empty_like(rgb)
    t = noise(h, w, rng, octaves=3, base=10)[..., None]                    # 주황 ↔ 짙은 갈색 섞기
    rust_col[:] = (1 - t) * np.array([168, 74, 26], np.float32) + t * np.array([84, 38, 18], np.float32)

    m_brass = brass * np.clip(blot * 0.9 + speck * 0.7, 0, 1) * k
    m_enamel = enamel * near_edge * blot * 0.25 * k
    m = np.clip(m_brass + m_enamel, 0, 0.9)[..., None]

    # 녹은 빛을 덜 반사 → 밝기를 살짝 낮춰서 섞음 (원래 명암은 유지)
    lum = (0.3 * r + 0.59 * g + 0.11 * b)[..., None] / 255
    out = rgb * (1 - m) + rust_col * (0.55 + 0.6 * lum) * m
    res = np.concatenate([np.clip(out, 0, 255), al], -1).astype(np.uint8)
    dst = os.path.join(ROOT, name + '_rust.webp')
    Image.fromarray(res, 'RGBA').save(dst, 'WEBP', quality=90, method=6)
    print('saved', os.path.relpath(dst))


if __name__ == '__main__':
    k = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
    for i, (n, mul) in enumerate(FILES.items()):
        rustify(n, k * mul, seed=153 + i)
