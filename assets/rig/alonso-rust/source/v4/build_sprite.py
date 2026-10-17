"""알론소 그림 넘기기(프레임 애니메이션) 데이터 만들기 — 2026-10-17 '섞어 쓰기' 결정.
입력: sheets/sheetMOTION_v4.png (달리기 8 · 내려찍기 6, 마젠타) → 조각 나누기는 split_sheet.py 결과(pieces/motion)를 씀
출력: OUT/alonso_sprite.png (프레임을 한 장에 모은 그림) + OUT/alonso_sprite.json
  frames[i] = {x,y,w,h, ax, ay}  ax·ay = 그림 안 기준점(몸통 가운데 x, 땅선 y) — 그리기: 화면 기준점에서 (-ax,-ay) 만큼 옮겨 그림
  anims = run(달리기 한 바퀴, 거리 기준 재생) · smash(시간 키, hit 프레임) · ready
실행: cd v4 && python3 -I build_sprite.py OUTDIR
"""
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
P = os.path.join(HERE, 'pieces', 'motion'); meta = {m['file'][:-4]: m for m in json.load(open(os.path.join(P, 'mmeta.json')))}
GROUND = {'run': 353, 'smash': 701}                      # 시트 줄마다 땅선 y (발바닥이 가장 많이 닿는 줄)
ROWS = {'run': ['m01', 'm02', 'm03', 'm04', 'm05', 'm08', 'm06', 'm07'], 'smash': ['m10', 'm11', 'm12', 'm09', 'm13', 'm14']}

def heel_x(im):
    """뒷발 뒤꿈치 x: 아래 12% 높이에서 가장 왼쪽 불투명 픽셀 — 공격은 뒷발을 땅에 박고 몸이 앞으로 나가야 하므로 이 점을 고정"""
    a = np.asarray(im)[..., 3] > 128; H = a.shape[0]; ys, xs = np.nonzero(a[int(H * .88):]); return float(xs.min())

def body_x(im):
    """몸통 가운데 x: 아래에서 50~62% 높이(허리·튜닉)에서 가장 긴 불투명 구간의 가운데 (칼·목도리 제외)"""
    a = np.asarray(im)[..., 3] > 128; H = a.shape[0]; xs = []
    for y in range(int(H * .50), int(H * .62)):
        c = np.nonzero(a[y])[0]
        if len(c) < 5: continue
        runs = np.split(c, np.nonzero(np.diff(c) > 1)[0] + 1); r = max(runs, key=len); xs.append((r[0] + r[-1]) / 2)
    return float(np.median(xs))

frames, names, pad = [], [], 2
for row, ns in ROWS.items():
    for n in ns:
        im = Image.open(os.path.join(P, n + '.png')).convert('RGBA'); m = meta[n]
        frames.append({'name': n, 'im': im, 'ax': round(body_x(im), 1), 'ay': GROUND[row] - m['y0'], 'heel': heel_x(im), 'row': row})
# 공격 줄: 뒷발 뒤꿈치를 준비 자세(m10)와 같은 자리에 고정 → 런지에서 몸이 앞으로 나감 (발이 미끄러지지 않음)
r0 = next(f for f in frames if f['name'] == 'm10'); off = r0['ax'] - r0['heel']
for f in frames:
    if f['row'] == 'smash': f['ax'] = round(f['heel'] + off, 1)
# 한 줄 아틀라스
W = sum(f['im'].width + pad for f in frames); H = max(f['im'].height for f in frames)
atlas = Image.new('RGBA', (W, H)); x = 0; out = []
for f in frames:
    atlas.alpha_composite(f['im'], (x, 0))
    out.append({'name': f['name'], 'x': x, 'y': 0, 'w': f['im'].width, 'h': f['im'].height, 'ax': f['ax'], 'ay': f['ay']}); x += f['im'].width + pad
atlas.save(os.path.join(OUT, 'alonso_sprite.png'), optimize=True)
idx = {f['name']: i for i, f in enumerate(out)}
# 몸 높이(머리카락 가운데~발바닥, 시트 px): 대기 프레임에서 잰 값 — 리그 bodyHeight(753)와 같은 기준이라 화면 크기를 맞출 때 씀
bodyH = 228
data = {'image': 'alonso_sprite.png', 'bodyHeight': bodyH, 'frames': out,
        'anims': {
            # 달리기: 기준 속도 620에서 12장/초, 속도에 비례
            # 임시(11:15 DHL '다리 움직임 어색'): 시트 8장 중 5·6번이 2번과 같은 '낮게' 자세라 멈칫, 3·4·8번 공중 자세가 겹쳐 깡충 뛰는 느낌 →
            # 한 발짝이 자연스럽게 이어지는 4장만 씀: 닿기(m01) → 낮게(m02) → 지나기(m06, 한 발 땅) → 높이(m07). 다리 교대 시트 오면 8장으로 교체
            'run': {'frames': [idx[n] for n in ['m01', 'm02', 'm06', 'm07']], 'fps': 10, 'refSpeed': 620},
            'ready': {'frames': [idx['m10']]},
            # 내려찍기: [프레임, 보여 주는 시간(초)] — 준비에 무게, 휘두름은 짧게, 타격 뒤 멈칫(hitStop)
            'smash': {'keys': [[idx['m11'], .09], [idx['m12'], .16], [idx['m09'], .045], [idx['m13'], .30], [idx['m14'], .16]],
                      'hit': 3, 'hitStop': .07, 'shake': 1}},
        'note': '알론소 v4 그림 넘기기 1차 — 달리기는 다리가 바뀌지 않는 시트라 임시, 추가 시트(달리기 8·내려찍기 보강 5·숨쉬기 4) 받으면 교체'}
json.dump(data, open(os.path.join(OUT, 'alonso_sprite.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'alonso_sprite.def.js'), 'w').write("window.MR_SPRITE_DEFS=window.MR_SPRITE_DEFS||{};window.MR_SPRITE_DEFS['alonso']=" + json.dumps(data, ensure_ascii=False) + ";\n")
print('atlas', atlas.size, len(out), 'frames')
