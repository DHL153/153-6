# 둘시네 공격 1/60초 표: 팔 늘임(stN·stF) · 손목 꺾임(wrN·wrF) · 쓰는 조각 · 손·팔꿈치·망치 머리 자리 튐(프레임 사이 이동) — python3 tools/table_atk.py [out.json]
#  엔진 'N' = 둘시네 먼 팔(armF·foreF·foreFf), 'F' = 가까운 팔(armU·armL·armLf)
import sys, time, socket, subprocess, os, json
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ID = 'dulcinea-rust'
ACT = open(os.environ['ACT']).read() if os.environ.get('ACT') else '{}'
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const def=MR_RIG_DEFS['{ID}'];Object.assign(def.actions.smash,{ACT});const ims=await Promise.all(Object.entries(def.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src}})));
const IM=Object.fromEntries(ims);
window.run=()=>{{const rig=new CharacterRig(def,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<60;i++)an.update(1/120,{{vx:0}});an.attack('smash');const out=[];
 const P=(b,x,y)=>{{const m=rig.by[b].wm||rig.by[b].m;return [m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]]}};
 const pt=(b)=>{{if(!rig.by[b])return null;const pn=rig.swap[b]||rig.by[b].part, p=def.parts[pn]; if(!p)return null; const q=p.grip||p.fist||p.pivot, k=p.scale||1; return P(b,(q[0]-p.pivot[0])*k,(q[1]-p.pivot[1])*k)}};
 const el=(b)=>{{if(!rig.by[b])return null;const pn=rig.swap[b]||rig.by[b].part, p=def.parts[pn]; if(!p||!p.elbow)return null; const k=p.scale||1; return P(b,(p.elbow[0]-p.pivot[0])*k,(p.elbow[1]-p.pivot[1])*k)}};
 while(an.act){{const t=an.act.t;an.update(1/60,{{vx:0}});if(!an.act)break;
  const tipP=rig.partPoint('weapon',...def.parts.weapon.tip);
  out.push({{t:an.act.t,fz:an.act.freeze||0,stN:an.stN||0,stF:an.stF||0,wrN:an.wrN||0,wrF:an.wrF||0,reach:an._tr('reach'),gN:an.gapN||0,gF:an.gapF||0,
   sw:{{foreF:rig.swap.foreF||null,armL:rig.swap.armL||null,armF:rig.swap.armF||null,armU:rig.swap.armU||null,foreFf:rig.swap.foreFf||null,armLf:rig.swap.armLf||null}},
   SN:rig.by.armF.wm?[rig.by.armF.wm[4],rig.by.armF.wm[5]]:null,SF:rig.by.armU.wm?[rig.by.armU.wm[4],rig.by.armU.wm[5]]:null,HM:rig.by.hip.m.slice(),G:an.swordG,A:an.swordA,head:[rig.by.head.m[4],rig.by.head.m[5]],fN:pt('foreF'),fF:pt('armL'),eN:el('foreFf'),eF:el('armLf'),tip:tipP,ord:rig.drawOrder?'A':'-'}})}}
 return out}};window.ready=1}})()</script>'''
open(os.path.join(root, '_tab.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(f'http://127.0.0.1:{port}/_tab.html'); pg.wait_for_function('window.ready', timeout=30000)
        R = pg.evaluate('run()'); b.close()
        if errs: print('errors', errs[:5])
finally:
    srv.terminate(); os.remove(os.path.join(root, '_tab.html'))
import math
D = lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1]) if a and b else 0
bad = []
for i, r in enumerate(R):
    pr = R[i - 1] if i else r
    r['jN'] = D(r['fN'], pr['fN']); r['jF'] = D(r['fF'], pr['fF']); r['jT'] = D(r['tip'], pr['tip'])
    flags = []
    if r['stN'] and not .95 <= r['stN'] <= 1.05: flags.append(f"stN {r['stN']:.2f}")
    if r['stF'] and r['reach'] > .985 and not .95 <= r['stF'] <= 1.05: flags.append(f"stF {r['stF']:.2f}")
    if abs(math.degrees(r['wrN'])) > 40: flags.append(f"wrN {math.degrees(r['wrN']):.0f}")
    if r['reach'] > .985 and abs(math.degrees(r['wrF'])) > 40: flags.append(f"wrF {math.degrees(r['wrF']):.0f}")
    if r['gN'] > .5: flags.append(f"gapN {r['gN']:.0f}")
    if r['gF'] > .5 and r['reach'] > 0: flags.append(f"gapF {r['gF']:.0f}")
    if flags: bad.append((round(r['t'], 3), flags))
print('frames', len(R)); print('flags', len(bad))
for b_ in bad[:60]: print(' ', b_)
print('max jumps per frame (rig px): fistN', round(max(r['jN'] for r in R), 1), 'fistF', round(max(r['jF'] for r in R), 1), 'hammer head', round(max(r['jT'] for r in R), 1))
for r in R:
    if r['jN'] > 60 or r['jF'] > 60: print('  jump t', round(r['t'], 3), 'N', round(r['jN'], 1), 'F', round(r['jF'], 1), r['sw'])
if os.environ.get('ROWS'):
    for r in R[::int(os.environ['ROWS'])]: print(f"  t {r['t']:.3f} reach {r['reach']:.2f} stN {r['stN']:.2f} stF {r['stF']:.2f} wrN {math.degrees(r['wrN']):5.0f} wrF {math.degrees(r['wrF']):5.0f} gapN {r['gN']:4.0f} gapF {r['gF']:4.0f}")
if len(sys.argv) > 1: json.dump(R, open(sys.argv[1], 'w'))
