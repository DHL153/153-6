# 22 스카이 둘시네 휘두름 검사(10-20 DHL 10:37 '0.35초 팔 길이가 이상' — 먼 어깨가 몸 밖 허공으로 나가 윗팔 관·남색 소매 끝이 보이고 팔이 거의 다 펴짐 .96)
#   python3 -I tools/swing12.py [t0=.25] [t1=.45] [vx=0]   (env SMASH_KEYS=패치.json 이면 그 키로 다시 빌드 — 끝나면 원래대로 다시 빌드하지 않음, 직접 빌드)
#   표: t · 펴짐(≤.90) · 손목 · 어깨 S · 팔꿈치 E · 쥔 점 G(골반 기준) · 어깨 끝 보임 px(S 둘레 26 안 윗팔 — 0 이어야 몸 뒤) · 윗팔 전체 보임 · 팔꿈치 얼굴 · 맨 위(몸 키 배, 칸 1.81)
import sys, time, socket, subprocess, os, json, math
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); root = os.path.abspath(os.path.join(SRC, '..', '..'))
T0 = float(sys.argv[1]) if len(sys.argv) > 1 else .25; T1 = float(sys.argv[2]) if len(sys.argv) > 2 else .45; VX = float(sys.argv[3]) if len(sys.argv) > 3 else 0
if os.environ.get('SMASH_KEYS') or os.environ.get('BUILD'):
    subprocess.run([sys.executable, '-I', 'build_neon12.py'], cwd=SRC, env=os.environ.copy(), check=True, stdout=subprocess.DEVNULL)
ID = 'dulcinea-sky'; LN = 186.5; BH = 734.0
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const d=MR_RIG_DEFS['{ID}'];const ims=await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src+'?x={time.time()}'}})));
const IM=Object.fromEntries(ims);const red=im=>{{const c=document.createElement('canvas');c.width=im.width;c.height=im.height;const x=c.getContext('2d');x.drawImage(im,0,0);x.globalCompositeOperation='source-in';x.fillStyle='#ff0000';x.fillRect(0,0,c.width,c.height);return c}};
const IM2=Object.assign({{}},IM,{{auFart:red(IM.auFart)}});const clr=im=>{{const c=document.createElement('canvas');c.width=im.width;c.height=im.height;return c}};const BODY=['torso','hips','pauldron'];const IM3={{}};for(const k in IM)IM3[k]=BODY.includes(k)||k==='head'||k.startsWith('face')||k.startsWith('blink')?IM[k]:clr(IM[k]);
const inv=m=>{{const q=m[0]*m[3]-m[1]*m[2];return [m[3]/q,-m[1]/q,-m[2]/q,m[0]/q,(m[2]*m[5]-m[3]*m[4])/q,(m[1]*m[4]-m[0]*m[5])/q]}};const ap=(m,x,y)=>[m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]];
let FACE;{{const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<60;i++)an.update(1/120,{{vx:0}});const H=rig.by.hip.m,iH=inv(rig.by.head.m);FACE=[[-46,-400],[154,-400],[154,-140],[-46,-140]].map(p=>ap(iH,H[4]+p[0],H[5]+p[1]))}}
window.run=(vx,T0,T1)=>{{const R=[new CharacterRig(d,IM),new CharacterRig(d,IM2),new CharacterRig(d,IM3)],A=R.map(r=>new RunAnimator(r,{{runSpeed:620}}));
 for(let i=0;i<240;i++)A.forEach(a=>a.update(1/120,{{vx}}));A.forEach(a=>a.attack('smash'));const out=[];const c=document.createElement('canvas');c.width=1000;c.height=1000;const g=c.getContext('2d',{{willReadFrequently:true}});
 const X0=500,Y0=900;
 while(A[0].act){{const t=A[0].act.t;if(t>=T0-1e-9&&t<=T1+1e-9){{const rig=R[0];
   const P=(b,x,y)=>{{const m=rig.by[b].wm||rig.by[b].m;return [m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]]}};
   const pn=rig.swap.foreF||rig.by.foreF.part,pp=d.parts[pn],q=pp.grip||pp.pivot,k=pp.scale||1;const G=P('foreF',(q[0]-pp.pivot[0])*k,(q[1]-pp.pivot[1])*k);
   const fn=rig.swap.foreFf||rig.by.foreFf.part,fp=d.parts[fn];const E=fp&&fp.elbow?P('foreFf',(fp.elbow[0]-fp.pivot[0])*(fp.scale||1),(fp.elbow[1]-fp.pivot[1])*(fp.scale||1)):null;
   const Sm=rig.by.armF.wm||rig.by.armF.m,S=[Sm[4],Sm[5]],H=rig.by.hip.m;
   g.clearRect(0,0,1000,1000);R[1].draw(g,X0,Y0,1,1);let D=g.getImageData(0,0,1000,1000).data;let n=0,nc=0;
   for(let i=0;i<D.length;i+=4)if(D[i+3]>200&&D[i]>200&&D[i+1]<40&&D[i+2]<40){{n++;const p=i/4,x=p%1000-X0,y=Math.floor(p/1000)-Y0;if(Math.hypot(x-S[0],y-S[1])<26)nc++}}
   const ex=E?[E[0]-S[0],E[1]-S[1]]:[1,0],el=Math.hypot(...ex);let nb=0;for(let i=0;i<D.length;i+=4)if(D[i+3]>200&&D[i]>200&&D[i+1]<40&&D[i+2]<40){{const p=i/4,x=p%1000-X0-S[0],y=Math.floor(p/1000)-Y0-S[1];if((x*ex[0]+y*ex[1])/el<8&&Math.hypot(x,y)<30)nb++}}
   let top=1e9;for(let y=0;y<1000&&top>1e8;y++)for(let x=0;x<1000;x++)if(D[(y*1000+x)*4+3]>30){{top=y;break}}
   if(window.DBG&&Math.abs(t-window.DBG)<.009){{const c2=document.createElement('canvas');c2.width=1000;c2.height=1000;const g2=c2.getContext('2d');R[window.DBGR||0].draw(g2,X0,Y0,1,1);g2.setTransform(1,0,0,1,0,0);g2.fillStyle='#0f0';g2.beginPath();g2.arc(X0+S[0],Y0+S[1],6,0,7);g2.fill();g2.fillStyle='#00f';g2.beginPath();g2.arc(X0+E[0],Y0+E[1],6,0,7);g2.fill();g2.fillStyle='#f0f';g2.beginPath();g2.arc(X0+G[0],Y0+G[1],6,0,7);g2.fill();window.DIMG=c2.toDataURL()}}
   const top_=top;g.clearRect(0,0,1000,1000);R[2].draw(g,X0,Y0,1,1);const B=g.getImageData(0,0,1000,1000).data;let dep=0;
   for(let r=2;r<60;r+=2){{let ok=true;for(let a=0;a<24&&ok;a++){{const x=Math.round(X0+S[0]+r*Math.cos(a*Math.PI/12)),y=Math.round(Y0+S[1]+r*Math.sin(a*Math.PI/12));if(B[(y*1000+x)*4+3]<128)ok=false}}if(!ok)break;dep=r}}
   const Hd=rig.by.head.m,F=FACE.map(p=>ap(Hd,p[0],p[1]));const inF=E&&E[0]>=Math.min(...F.map(p=>p[0]))-8&&E[0]<=Math.max(...F.map(p=>p[0]))+8&&E[1]>=Math.min(...F.map(p=>p[1]))-8&&E[1]<=Math.max(...F.map(p=>p[1]))+8;
   const rel=v=>v?[Math.round(v[0]-H[4]),Math.round(v[1]-H[5])]:null;
   out.push({{t,G:rel(G),E:rel(E),S:rel(S),reach:Math.hypot(G[0]-S[0],G[1]-S[1]),wr:A[0].wrN||0,n,nc,inF,top:(Y0-top)/{BH},pn,nb,dep}})}}
  A.forEach(a=>a.update(1/60,{{vx}}))}}return out}};window.ready=1}})()</script>'''
open(os.path.join(root, '_sw.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(f'http://127.0.0.1:{port}/_sw.html'); pg.wait_for_function('window.ready', timeout=30000)
        if os.environ.get('DBG'): pg.evaluate(f"window.DBG={os.environ['DBG']};window.DBGR={os.environ.get('DBGR', 0)}")
        R = pg.evaluate('([v,a,b_])=>run(v,a,b_)', [VX, T0, T1])
        if os.environ.get('DBG'):
            import base64; open(os.environ.get('DBGOUT', '/tmp/dbg.png'), 'wb').write(base64.b64decode(pg.evaluate('window.DIMG').split(',')[1]))
        b.close()
        if errs: print('errors', errs[:3])
finally:
    srv.terminate(); os.remove(os.path.join(root, '_sw.html'))
bad = 0; last = None
for r in R:
    if last is not None and abs(r['t'] - last) < 1e-6: continue
    last = r['t']; rc = r['reach'] / LN; f = []
    if rc > .905: f.append('펴짐')
    if r['nb'] > 25: f.append('어깨끝')
    if r['inF']: f.append('팔꿈치얼굴')
    if abs(math.degrees(r['wr'])) > 47: f.append('손목')
    bad += bool(f)
    print(f"{r['t']:.3f} 펴짐 {rc:.2f} 손목 {math.degrees(r['wr']):4.0f} S {r['S']} E {r['E']} G {r['G']} 어깨끝 {r['nb']:4d} 깊이 {r['dep']:2d} 윗팔 {r['n']:5d} 맨위 {r['top']:.2f} {r['pn']:6} {'✗ ' + ' '.join(f) if f else ''}")
print('bad', bad)
