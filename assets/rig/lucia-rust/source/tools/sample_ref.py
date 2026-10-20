# 기준 리그(둘시네 2·12·22) 공격을 엔진으로 1/60 씩 재서 JSON 으로: 먼 어깨 S · 쥔 점 G · 상체 각 th · 골반 위치 · 자루 각 sa · 실루엣 꼭대기(발바닥 위, 리그 px)
#   python3 -I tools/sample_ref.py → work/ref_samples.json   (presim7.py 가 읽음)
import sys, time, socket, subprocess, os, json
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); root = os.path.abspath(os.path.join(SRC, '..', '..'))
IDS = ['dulcinea-neon', 'dulcinea-rust', 'dulcinea-sky']
srcs = ''.join(f'<script src="{i}/rig.def.js?x={time.time()}"></script>' for i in IDS)
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script>{srcs}<script>
const load=async id=>{{const d=MR_RIG_DEFS[id];const ims=await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src=p.src.startsWith('data:')?p.src:id+'/'+p.src}})));return [d,Object.fromEntries(ims)]}};
window.run=async(id,vx)=>{{const [d,IM]=await load(id);const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<240;i++)an.update(1/120,{{vx,stepHz:2.22}});an.attack('smash');an.update(1/6000,{{vx}});
 const c=document.createElement('canvas');c.width=1400;c.height=1400;const g=c.getContext('2d',{{willReadFrequently:true}});const out=[];const sd=d.parts.weapon.shaftDir||[0,-1];let n=0;
 for(let f=0;f<=62;f++){{const T=f/60;while(an.act&&an.act.t<T-1e-6&&n<20000){{an.update(1/600,{{vx:vx*Math.max(0,1-an.act.t*8)}});n++}}if(!an.act)break;
  const S=rig.by.armF.wm||rig.by.armF.m,Tm=rig.by.torso.m,H=rig.by.hip.m,Wm=rig.by.weapon.m;
  const wx=Wm[0]*sd[0]+Wm[2]*sd[1],wy=Wm[1]*sd[0]+Wm[3]*sd[1];
  g.clearRect(0,0,1400,1400);rig.draw(g,600,1100,1,1);const D=g.getImageData(0,0,1400,1400).data;let top=-1;for(let y=0;y<1400&&top<0;y++)for(let x=0;x<1400;x++)if(D[(y*1400+x)*4+3]>40){{top=y;break}}
  out.push({{t:an.act.t,S:[S[4],S[5]],G:an.swordG,th:Math.atan2(Tm[1],Tm[0]),hip:[H[4],H[5]],sa:Math.atan2(wy,wx),top:1100-top}})}}
 return {{bodyH:d.metrics.bodyHeight,frames:out}}}};window.ready=1</script>'''
fn = os.path.join(root, '_sref.html'); open(fn, 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
OUT = {}
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(f'http://127.0.0.1:{port}/_sref.html'); pg.wait_for_function('window.ready', timeout=30000)
        for i in IDS:
            OUT[i] = pg.evaluate('([i,v])=>run(i,v)', [i, 0])
            fr = OUT[i]['frames']; mx = max(fr, key=lambda r: r['top'])
            print(f"{i}: frames {len(fr)} bodyH {OUT[i]['bodyH']} · 꼭대기 최대 {mx['top']:.0f} @ {mx['t']:.3f} = 몸 키 ×{mx['top'] / OUT[i]['bodyH']:.3f} · 대기 ×{fr[0]['top'] / OUT[i]['bodyH']:.3f}")
        b.close()
        if errs: print('errors', errs[:3])
finally:
    srv.terminate(); os.remove(fn)
json.dump(OUT, open(os.path.join(SRC, 'work', 'ref_samples.json'), 'w'))
