# 게임 전투에서 17 공격 1회를 rAF 마다 기록 — 공격 시각 · 서 있는 원화 다리 비율(standW, 0 = 달리기 다리 · 1 = 서 있는 다리) · A
#   + 고른 공격 시각의 리그 캔버스를 한 줄 그림으로: python3 -I game_atk17.py 가로 세로 OUT.png
#   (DHL 10-21 15:40 '공격 중 다리를 틀지 말고 이동 전에' → v1.2 legRun 0 이 게임에서도 그런지 확인)
import os
exec(open(os.path.dirname(os.path.abspath(__file__)) + '/game_base.py').read())
import base64, io
from PIL import Image, ImageDraw, ImageFont
W = int(sys.argv[1]); H = int(sys.argv[2]); OUT = sys.argv[3]
SHOT = [.0, .05, .15, .25, .31, .34, .4, .6, .8, .95]   # 공격 시각(초) — 끝(None) 뒤 첫 프레임도 한 장
with sync_playwright() as p:
    b, pg, errs = play(p, W, H)
    pg.evaluate("()=>{battleCharInventory[16]=Object.assign({},Object.values(battleCharInventory)[0]||{},{count:1});assignBattleTeamCharacter(16);}")
    time.sleep(3)
    r = pg.evaluate("""(SHOT)=>new Promise(res=>{let slot=null,E=null;for(const [s,e] of MRRig.live){if(e.id==='lucia-neon'){slot=s;E=e;break}}
      const cv=E.cv,out=[],imgs=[];let k=0,ended=0;const t0=performance.now();
      const P=()=>{const L=E.rig.legPose;return L?[L.near.standW??-1,L.far.standW??-1]:[-1,-1]};
      out.push(['before',null,P(),E.anim.A]);MRRig.onState('attack',slot);
      const step=()=>{const a=E.anim.act,t=a?a.t:null,sw=P();out.push([Math.round(performance.now()-t0),t==null?null:Math.round(t*1000)/1000,sw.map(v=>Math.round(v*100)/100),Math.round(E.anim.A*100)/100]);
        if(t!=null&&k<SHOT.length&&t>=SHOT[k]-1e-6){imgs.push([t,sw,cv.toDataURL()]);k++}
        if(t==null&&out.length>3&&!ended){ended=performance.now();imgs.push(['끝',sw,cv.toDataURL()])}
        if(ended&&performance.now()-ended>500){imgs.push(['끝+.5',sw,cv.toDataURL()]);return res({id:E.id,out,imgs})}
        if(performance.now()-t0<4000)requestAnimationFrame(step);else res({id:E.id,out,imgs})};requestAnimationFrame(step)})""", SHOT)
    b.close()
srv.shutdown()
print(r['id'], 'frames', len(r['out']), 'errs', [e for e in errs if 'handleAsset' not in e][:5])
prev = None; sw_changes = []
for o in r['out']:
    key = tuple(o[2])
    if key != prev: sw_changes.append(o); prev = key
print('서 있는 다리 비율이 바뀐 프레임(ms, 공격 시각, [가까운, 먼], A):')
for o in sw_changes: print('  ', o)
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
try: fk = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 14)
except Exception: fk = f
tiles = []
for t, sw, d in r['imgs']:
    im = Image.open(io.BytesIO(base64.b64decode(d.split(',')[1]))).convert('RGBA')
    bb = im.getbbox() or (0, 0, im.width, im.height)
    bg = Image.new('RGBA', im.size, (34, 48, 84, 255)); bg.alpha_composite(im)
    tiles.append((t, sw, bg.convert('RGB')))
# 리그 캔버스 공통 범위(불투명) — 다리가 잘 보이게 아래 60%
boxes = [Image.open(io.BytesIO(base64.b64decode(d.split(',')[1]))).getbbox() for _, _, d in r['imgs']]
bx0 = min(b_[0] for b_ in boxes if b_); by0 = min(b_[1] for b_ in boxes if b_); bx1 = max(b_[2] for b_ in boxes if b_); by1 = max(b_[3] for b_ in boxes if b_)
crops = [t[2].crop((bx0 - 4, by0 - 4, bx1 + 4, by1 + 4)) for t in tiles]
cw, ch = crops[0].size; sc = 230 / ch; cw2, ch2 = int(cw * sc), int(ch * sc); COLS = 6; ROWS = (len(crops) + COLS - 1) // COLS
G = Image.new('RGB', (cw2 * COLS, (ch2 + 40) * ROWS), 'white'); D = ImageDraw.Draw(G)
for i, ((t, sw, _), c) in enumerate(zip(tiles, crops)):
    ox, oy = (i % COLS) * cw2, (i // COLS) * (ch2 + 40)
    G.paste(c.resize((cw2, ch2), Image.LANCZOS), (ox, oy + 40))
    lab = f'{t:.2f}' if isinstance(t, float) else t
    D.text((ox + 4, oy + 2), '공격 ' + lab if isinstance(t, float) else lab, fill=(20, 20, 20), font=fk)
    D.text((ox + 4, oy + 20), '서 있는 다리' if min(sw) >= .99 else ('달리기 다리' if max(sw) <= .01 else f'섞임 {sw[0]:.2f}'), fill=(200, 60, 40) if max(sw) < .99 else (30, 120, 60), font=fk)
G.save(OUT); print(OUT, G.size)
