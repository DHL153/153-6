# 12 네온 둘시네 선 연구(10-20 07:30): 네온 망치 길이로 러스트 둘시네 한 손 내려찍기(v6.4 키)를 돌려 보면 어디가 걸리나
#   새 원화가 오기 전 — 지금 원화(char_0012) 망치를 러스트 몸 크기로 줄여(머리카락 위~발바닥 395 → 365) 러스트 리그 망치 자리에 끼움
#   A = 지금 원화 길이 그대로 · B = 쇠 머리 그대로, 길이만 러스트 망치와 같게 · R = 러스트 망치(기준)
#   잼(엔진 그대로, 1/60초, 서서·달리다): 망치 가장 높은 점(땅 위, 몸 키 배수 — 전투 칸 위 끝 = 1.81 배, game_top 으로 잰 PC·폰 값) · 가장 낮은 점(땅 아래면 −) · 컷인 자세(.32~.34) 높이
#   python3 -I tools/fit12.py → 표 + OUT/fit12_<변형>_<t>.png
import os, sys, json, math, time, socket, subprocess
import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..')); RIG = os.path.join(REPO, 'assets', 'rig')
OUT = os.environ.get('OUT', '/tmp/claude-0/-home-claude/68d7ec04-d283-5e5f-8529-136e76cd93e3/scratchpad/neon/fit')
os.makedirs(OUT, exist_ok=True)
a = np.array(Image.open(os.path.join(REPO, 'assets/art/characters/char_0012.png')).convert('RGBA'))
A = a[..., 3] > 20; yy, xx = np.mgrid[0:512, 0:512]
C1 = np.array([175.1, 153.0]); C2 = np.array([468.7, 305.7]); U = (C2 - C1) / np.linalg.norm(C2 - C1); N = np.array([-U[1], U[0]])   # 자루 축(쇠 머리 → 마개)
HEAD = A & (xx < 212) & (yy < 245); CAP = A & (xx > 440) & (yy > 262) & (yy < 340); G = np.array([390.0, 262.0])   # 지금 원화 먼 손 쥔 점
K = 365 / 395   # 네온 몸(머리카락 위 97 ~ 발바닥 492) → 러스트 몸(120 ~ 485)
def proxy(dh, dc):
    """쇠 머리를 자루 쪽으로 dh, 마개를 쥔 점 쪽으로 dc(원화 px) 옮긴 망치 → 세운 그림(쇠 머리 위, 2배·러스트 몸 크기) + 쥔 점·쇠 머리 가운데·마개"""
    im = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    H = np.zeros((512, 512, 4), np.uint8); H[HEAD] = a[HEAD]; Cc = np.zeros((512, 512, 4), np.uint8); Cc[CAP] = a[CAP]
    Hi = Image.fromarray(H).transform((512, 512), Image.AFFINE, (1, 0, -U[0] * dh, 0, 1, -U[1] * dh), resample=Image.BICUBIC)
    Ci = Image.fromarray(Cc).transform((512, 512), Image.AFFINE, (1, 0, U[0] * dc, 0, 1, U[1] * dc), resample=Image.BICUBIC)
    d = ImageDraw.Draw(im); p0 = C1 + U * (10 + dh); p1 = C2 - U * (20 + dc)
    for w, col in [(30, (25, 25, 30, 255)), (24, (78, 80, 88, 255))]: d.line([tuple(p0), tuple(p1)], fill=col, width=w)
    im.alpha_composite(Ci); im.alpha_composite(Hi)
    m = np.array(im)[..., 3] > 40; pts = np.stack(np.nonzero(m)[::-1], 1).astype(float)
    pu = (pts - G) @ U; top = pu.min(); bot = pu.max()                         # 축 위 위치(쥔 점 기준, + = 마개 쪽)
    hm = np.array(Hi)[..., 3] > 40; hp = np.stack(np.nonzero(hm)[::-1], 1).astype(float); tipu = float(((hp - G) @ U).mean())   # 쇠 머리 가운데
    S = 2 * K; ang = math.degrees(math.atan2(U[1], U[0])) - 90   # 축을 아래(+y)로 세움 → 쇠 머리 위
    big = im.resize((int(512 * S), int(512 * S)), Image.LANCZOS); pad = 700
    can = Image.new('RGBA', (big.width + 2 * pad, big.height + 2 * pad), (0, 0, 0, 0)); can.paste(big, (pad, pad)); Gc = G * S + pad
    r = can.rotate(ang, resample=Image.BICUBIC, center=tuple(Gc)); bb = r.getbbox(); r = r.crop(bb); Gc = Gc - np.array(bb[:2])
    return r, [round(float(Gc[0]), 1), round(float(Gc[1]), 1)], {'top': top * K, 'butt': bot * K, 'tip': tipu * K}
VARS = {'A': (0, 0), 'B': (120 / K, 50 / K)}
ART = os.environ.get('ART')   # 새 원화(러스트 자세·러스트 몸 크기)로 돌릴 때: ART=work/art0_v1.png GN=298,316 UN=.6,-.8 (쥔 점·자루 방향 위) — seg12 의 work/labels.npy 필요
def art_hammer(fn):
    """새 원화의 망치(쇠 머리 = seg hammer + 머리 칸 중 x≥305·y≤245, 자루 = 축 ±12 띠) → 세운 그림 + 쥔 점·쇠 머리 가운데·마개"""
    b = np.array(Image.open(fn).convert('RGBA')); Ab = b[..., 3] > 40; lab = np.load(os.path.join(HERE, 'work', 'labels.npy'))
    Gn = np.array([float(v) for v in os.environ.get('GN', '298,316').split(',')]); Un = np.array([float(v) for v in os.environ.get('UN', '.6,-.8').split(',')]); Un = -Un / np.linalg.norm(Un)  # 축(쇠 머리 → 마개)
    Nn = np.array([-Un[1], Un[0]]); pu = (xx - Gn[0]) * Un[0] + (yy - Gn[1]) * Un[1]; pn = (xx - Gn[0]) * Nn[0] + (yy - Gn[1]) * Nn[1]
    Hm = ((lab == 2) | ((lab == 1) & (xx >= 305) & (yy <= 245))) & (pu <= -20); Sm = Ab & (np.abs(pn) <= 12) & (pu > -60) & (pu < 75)
    m = Hm | Sm; im = np.zeros_like(b); im[m] = b[m]; im = Image.fromarray(im)
    Kn = 365 / (int(np.nonzero(Ab.any(1))[0].max()) - int(np.nonzero(Ab[:, :300].any(1))[0].min()))
    top = pu[m].min(); bot = pu[m].max(); tipu = float(pu[Hm].mean())
    S = 2 * Kn; ang = math.degrees(math.atan2(Un[1], Un[0])) - 90
    big = im.resize((int(512 * S), int(512 * S)), Image.LANCZOS); pad = 700
    can = Image.new('RGBA', (big.width + 2 * pad, big.height + 2 * pad), (0, 0, 0, 0)); can.paste(big, (pad, pad)); Gc = Gn * S + pad
    r = can.rotate(ang, resample=Image.BICUBIC, center=tuple(Gc)); bb = r.getbbox(); r = r.crop(bb); Gc = Gc - np.array(bb[:2])
    return r, [round(float(Gc[0]), 1), round(float(Gc[1]), 1)], {'top': top * Kn, 'butt': bot * Kn, 'tip': tipu * Kn}
os.makedirs(os.path.join(OUT, 'px'), exist_ok=True); PARTS = {}
for k, (dh, dc) in list(VARS.items()) + ([('N', (0, 0))] if ART else []):
    r, pv, inf = art_hammer(ART) if k == 'N' else proxy(dh, dc); fn = os.path.join(OUT, 'px', f'hammer{k}.png'); r.save(fn)
    tip = [pv[0], round(pv[1] + inf['tip'] * 2, 1)]; pom = [pv[0], round(pv[1] + inf['butt'] * 2, 1)]
    PARTS[k] = dict(src=f'../px/hammer{k}.png', pivot=pv, scale=1.0, tip=tip, pommel=pom, tips=[[tip[0] - 12, tip[1]], [tip[0] + 12, tip[1]]], shaftDir=[0.0, -1.0])
    print(k, '쥔 점→위 끝 %.0f · →마개 %.0f · →쇠 머리 가운데 %.0f (원화 px, 러스트 몸 크기) — 러스트 225 · 58 · 170' % (-inf['top'], inf['butt'], -inf['tip']))
# 서버 뿌리: OUT 아래에 rig.js·dulcinea-rust 를 이어 붙임(px/ 와 같은 뿌리)
root = os.path.join(OUT, 'root'); os.makedirs(root, exist_ok=True)
for n in ['rig.js', 'dulcinea-rust']:
    p = os.path.join(root, n)
    if not os.path.exists(p): os.symlink(os.path.join(RIG, n), p)
pxl = os.path.join(root, 'px')
if not os.path.exists(pxl): os.symlink(os.path.join(OUT, 'px'), pxl)
ID = 'dulcinea-rust'
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
const D0=MR_RIG_DEFS['{ID}'];const PARTS={json.dumps(PARTS)};
async function loadDef(v){{const def=JSON.parse(JSON.stringify(D0));if(v!=='R'){{def.parts.weapon=Object.assign({{}},PARTS[v]);def.parts.weaponA=Object.assign({{}},PARTS[v])}}
 const ims=await Promise.all(Object.entries(def.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src}})));return [def,Object.fromEntries(ims)]}}
const LISTS=['draw','drawA','drawA0','drawP','drawU','drawM','drawL'];
window.run=async(v,vx,TS,only)=>{{const [D,IM]=await loadDef(v);const out=[];
 for(const T of TS){{const def=JSON.parse(JSON.stringify(D));if(only)for(const L of LISTS)if(def[L])def[L]=only;
  const rig=new CharacterRig(def,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<240;i++)an.update(1/120,{{vx}});an.attack('smash');let n=0;
  while(an.act&&an.act.t<T-1e-6&&n<4000){{an.update(1/240,{{vx}});n++}}
  const c=document.createElement('canvas');c.width=1000;c.height=1000;const g=c.getContext('2d');rig.draw(g,500,880,.5,1);const d=g.getImageData(0,0,1000,1000).data;
  let y0=-1,y1=-1;for(let y=0;y<1000&&y0<0;y++)for(let x=0;x<1000;x++)if(d[(y*1000+x)*4+3]>40){{y0=y;break}}
  for(let y=999;y>=0&&y1<0;y--)for(let x=0;x<1000;x++)if(d[(y*1000+x)*4+3]>40){{y1=y;break}}
  out.push([T,(880-y0)/.5,(880-y1)/.5,only?null:c.toDataURL()])}}return out}};window.ready=1</script>'''
open(os.path.join(root, '_fit.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
BH = 730.0; LIM = 1.807
TS = [round(i / 60, 4) for i in range(0, 61)]
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(f'http://127.0.0.1:{port}/_fit.html'); pg.wait_for_function('window.ready', timeout=30000)
        print('\n변형  달리기 | 망치 최고(몸 키 배)  그때 t | 컷인 .32/.333 높이 | 타격 .40~.58 가장 낮은 점(리그 px, 땅 0, −=땅 아래)')
        for v in (['R', 'B', 'N'] if ART else ['R', 'B', 'A']):
            for vx in [0, 620]:
                R = pg.evaluate('([v,vx,T,o])=>run(v,vx,T,o)', [v, vx, TS, ['weapon', 'weaponA']])
                mx = max(R, key=lambda r: r[1]); cut = [r[1] / BH for r in R if abs(r[0] - .3167) < .02 or abs(r[0] - .3333) < .01]
                low = min(r[2] for r in R if .399 <= r[0] <= .58)
                print(f'  {v}    {vx:4d}  |  {mx[1] / BH:.2f}{" ✗" if mx[1] / BH > LIM - .05 else ""}  t {mx[0]:.3f}  |  {" / ".join(f"{c:.2f}" for c in cut)}  |  {low:.0f}')
            if v != 'R':
                for t, (r) in zip([.18, .27, .32, .40], pg.evaluate('([v,vx,T])=>run(v,vx,T,null)', [v, 0, [.18, .27, .32, .40]])):
                    import base64, io
                    Image.open(io.BytesIO(base64.b64decode(r[3].split(',')[1]))).save(os.path.join(OUT, f'fit12_{v}_{t:.2f}.png'))
        b.close()
        if errs: print('errors', errs[:3])
finally:
    srv.terminate(); os.remove(os.path.join(root, '_fit.html'))
print(f'전투 칸 위 끝 = 땅 위 {LIM} × 몸 키(PC·폰 같음, 러스트 game_top 으로 잼). 러스트 v6.4 최고 1.36 → 칸 위에서 PC 31px')
