# 키 맞춤 시험: python3 tune.py 출력접두어 [tune.json]  — 동작 시트 m09~m13 시각에서 리그 vs 시트 (각도표 + 겹침 IoU + 비교 그림)
import sys, json, math, threading, functools, http.server, socketserver, base64, io, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from playwright.sync_api import sync_playwright
ROOT = '/home/claude/153-6'; HERE = os.path.dirname(os.path.abspath(__file__))
OUTP = sys.argv[1]; TUNE = sys.argv[2] if len(sys.argv) > 2 else None
SHEET = os.path.join(HERE, '..', 'sheets', 'motion_v1.png'); K = 2.8
# 동작 시트 관절점(시트 px, 손으로 찍음 — 3배 격자 그림 g_m11/g_m12 에서). back = 화면 왼쪽 다리 = 리그 near
PTS = {k: v for k, v in json.load(open(os.path.join(HERE, 'sheet_pts.json'), encoding='utf-8')).items() if not k.startswith('_')}
TS = {k: v['t'] for k, v in PTS.items()}
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
keys = list(PTS.keys()); ts = ','.join(str(TS[k]) for k in keys)
q = f'ts={ts}' + (f'&tune={os.path.relpath(TUNE, HERE)}' if TUNE else '')
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto(f'http://127.0.0.1:{port}/assets/rig/alonso-neon/source/tools/tunev.html?' + q)
    pg.wait_for_function("document.title==='done'||document.title.startsWith('ERR')", timeout=30000)
    if pg.title() != 'done': print(pg.title()); sys.exit(1)
    R = pg.evaluate('R'); d = pg.evaluate("document.getElementById('c').toDataURL('image/png')"); b.close()
srv.shutdown()
canvas = Image.open(io.BytesIO(base64.b64decode(d.split(',')[1]))).convert('RGBA')
S = np.asarray(Image.open(SHEET).convert('RGB')).astype(int)
def ang(a, b): return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
def dang(a, b): return (a - b + 180) % 360 - 180
SEG = [('torso', 'pelvis', 'neck'), ('backThigh', 'hipB', 'kneeB'), ('backShin', 'kneeB', 'ankleB'), ('frontThigh', 'hipF', 'kneeF'), ('frontShin', 'kneeF', 'ankleF'),
       ('nearUpper', 'shoulderN', 'elbowN'), ('nearFore', 'elbowN', 'grip')]
rows = []; panels = []
REF = None
if 'm13' in keys:
    _r = R[keys.index('m13')]; REF = {'s': ang(PTS['m13']['pelvis'], PTS['m13']['neck']), 'g': ang(_r['pelvis'], _r['neck'])}
for k, r in zip(keys, R):
    sp = PTS[k]; ox = 416; oy = 972   # 리그 root → 캔버스
    rg = {'pelvis': r['pelvis'], 'neck': r['neck'], 'hipB': r['hipN'], 'kneeB': r['kneeN'], 'ankleB': r['ankleN'], 'hipF': r['hipF'], 'kneeF': r['kneeF'], 'ankleF': r['ankleF'],
          'shoulderN': r['SF'], 'elbowN': r['EF'], 'grip': r['grip']}
    line = [k, f"t={r['t']}"]; errs = []
    for nm, a, bb in SEG:
        if a in sp and bb in sp:
            s_ = ang(sp[a], sp[bb]); g_ = ang(rg[a], rg[bb])
            if nm == 'torso' and REF:   # 몸통: 목·골반 점 잡는 법이 시트·리그가 달라 '대기 대비 변화량'으로 비교
                s_ -= REF['s']; g_ -= REF['g']
            e = dang(g_, s_); errs.append(abs(e)); line.append(f'{nm} {s_:.0f}/{g_:.0f}({e:+.0f})')
    if 'swordDeg' in sp: g_ = math.degrees(r['sa']); line.append(f"sword {sp['swordDeg']:.0f}/{g_:.0f}"); 
    # 높이(땅 기준, 대기 대비 비율): 골반
    sg = sp['ground']; line.append(f"pelvisH {(sg - sp['pelvis'][1]) * K:.0f}/{-r['pelvis'][1]} drop {r['hipDrop']} lr {r['legRun']}")
    rows.append(' | '.join(line) + f'  || mean|e| {np.mean(errs):.1f}°')
    # 겹침: 시트 프레임을 골반 x·땅에 맞춤
    x0, x1 = sp['box']; c = S[400:793, x0:x1]; fg = c.min(2) < 240
    fg = ndimage.binary_fill_holes(ndimage.binary_closing(fg, iterations=2)); lab, n = ndimage.label(fg); sz = ndimage.sum(fg, lab, range(1, n + 1)); fg = lab == (1 + int(np.argmax(sz)))
    sh = Image.fromarray(np.dstack([c, fg * 255]).astype(np.uint8), 'RGBA'); sh = sh.resize((int(sh.width * K), int(sh.height * K)), Image.LANCZOS)
    i = keys.index(k); rgim = canvas.crop((1024 * i, 0, 1024 * (i + 1), 1100))
    dx = ox + r['pelvis'][0] - (sp['pelvis'][0] - x0) * K; dy = oy - (sg - 400) * K
    W, H = 1024, 1100; A_ = np.zeros((H, W), bool); sa_ = np.asarray(sh)[:, :, 3] > 40
    X0, Y0 = int(round(dx)), int(round(dy)); ys, xs = np.nonzero(sa_); ys = ys + Y0; xs = xs + X0; ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W); A_[ys[ok], xs[ok]] = True
    B_ = np.asarray(rgim)[:, :, 3] > 40; iou = (A_ & B_).sum() / max(1, (A_ | B_).sum()); rows[-1] += f'  IoU {iou:.2f}'
    pan = Image.new('RGBA', (W * 2, H), (255, 255, 255, 255)); pan.alpha_composite(sh, (X0, Y0)); pan.alpha_composite(rgim, (W, 0))
    ov = Image.new('RGBA', (W, H), (255, 255, 255, 255))
    def tint(im, col):
        a = np.asarray(im).astype(float); o = a.copy(); g = a[:, :, :3].mean(2, keepdims=True); o[:, :, :3] = g * .45 + np.array(col) * .55; o[:, :, 3] = a[:, :, 3] * .55; return Image.fromarray(o.astype(np.uint8), 'RGBA')
    ov.alpha_composite(tint(sh, (255, 40, 40)), (X0, Y0)); ov.alpha_composite(tint(rgim, (0, 140, 255)), (0, 0))
    full = Image.new('RGBA', (W * 3, H), (255, 255, 255, 255)); full.alpha_composite(pan, (0, 0)); full.alpha_composite(ov, (2 * W, 0))
    dr = ImageDraw.Draw(full); dr.text((10, 10), f'{k} sheet', fill=(0, 0, 0)); dr.text((W + 10, 10), f"rig t={r['t']}", fill=(0, 0, 0)); dr.text((2 * W + 10, 10), f'IoU {iou:.2f}', fill=(0, 0, 0))
    panels.append(full.crop((0, 120, W * 3, H)).convert('RGB').resize((W * 3 // 3, (H - 120) // 3), Image.LANCZOS))
out = Image.new('RGB', (panels[0].width, sum(p.height for p in panels)), 'white'); y = 0
for p_ in panels: out.paste(p_, (0, y)); y += p_.height
out.save(OUTP + '.png'); open(OUTP + '.txt', 'w').write('\n'.join(rows) + '\n'); print('\n'.join(rows))
