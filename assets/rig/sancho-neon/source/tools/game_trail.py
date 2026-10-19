# 공격 트레일 방향 확인: 전투 무대(배경+리그+효과)를 페이지 안에서 rAF 마다 합성해 찍음 — python3 game_trail.py 가로 세로 이름 [전투인덱스]
import os
exec(open(os.path.dirname(os.path.abspath(__file__)) + '/game_base.py').read())
import base64, io
from PIL import Image
W = int(sys.argv[1]); H = int(sys.argv[2]); tag = sys.argv[3]; IDX = int(sys.argv[4]) if len(sys.argv) > 4 else 12
with sync_playwright() as p:
    b, pg, errs = play(p, W, H)
    pg.evaluate(f"()=>{{battleCharInventory[{IDX}]=Object.assign({{}},Object.values(battleCharInventory)[0]||{{}},{{count:1}});assignBattleTeamCharacter({IDX});}}")
    time.sleep(3)
    shots = pg.evaluate("""()=>new Promise(res=>{let el=null,slot=null;for(const [s,e] of MRRig.live){slot=s;el=e.el?.id;break}
      MRRig.onState('attack',slot);MRBattleFX.attack(el);const out=[],t0=performance.now();
      const rig=document.getElementById('battle-rig-canvas'),fx=document.getElementById('mr-battle-fx-canvas');
      const step=()=>{const t=performance.now()-t0;const c=document.createElement('canvas');c.width=rig.width;c.height=rig.height;const g=c.getContext('2d');g.fillStyle='#556';g.fillRect(0,0,c.width,c.height);
        g.drawImage(rig,0,0);if(fx&&!fx.hidden)g.drawImage(fx,0,0,c.width,c.height);out.push([Math.round(t),c.toDataURL('image/png')]);
        if(t<700)requestAnimationFrame(step);else res(out)};requestAnimationFrame(step)})""")
    keep = [s for s in shots]
    ims = [Image.open(io.BytesIO(base64.b64decode(d.split(',')[1]))).convert('RGB') for _, d in keep]
    # 트레일이 보이는 구간만 골라 6장
    print('frames', len(ims), 'sizes', ims[0].size, 'times', [t for t, _ in keep][:5], '...')
    w, h = ims[0].size; sel = list(range(0, len(ims), max(1, len(ims) // 18)))[:18]
    o = Image.new('RGB', (w * 3, h * 6), 'black')
    for k, i in enumerate(sel): o.paste(ims[i], ((k % 3) * w, (k // 3) * h))
    o.thumbnail((1800, 2400)); o.save(O + f'{tag}_trail.png'); print('times', [keep[i][0] for i in sel]); b.close()
srv.shutdown()
