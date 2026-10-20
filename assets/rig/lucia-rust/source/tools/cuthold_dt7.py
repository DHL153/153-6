# 컷인 유지 자세: 정한 시각(cutHold) vs 화면에 실제로 그려지는 시각(cutHold + dt×1.3 — drawStill 이 고정한 뒤 한 프레임 더 감) 자세 차이 — 리그마다
#   python3 -I tools/cuthold_dt7.py → 상자(폭·위·아래·가운데) 리그 px, 몸 높이 대비 %
import os, sys
exec(open(os.path.dirname(os.path.abspath(__file__)) + '/game_base.py').read())
JS = r"""async ()=>{const out=[];
  for(const [n,id] of Object.entries(MRRig.registry)){const def=window.MR_RIG_DEFS[id];if(!def)continue;
    const atk=def.ui?.attack||'thrust',AT=def.actions?.[atk],spear=AT&&(AT.kind==='spear'||def.ui?.stillSame||!!def.ui?.stillReady);if(atk==='thrust'||spear)continue;
    const base='assets/rig/'+id+'/',images={};
    await Promise.all(Object.entries(def.parts).map(([k,p])=>new Promise(res=>{const im=new Image();im.onload=()=>{images[k]=im;res()};im.onerror=()=>res();const d=String(p.src).startsWith('data:');im.src=(d?'':base)+p.src+(def.version&&!d?'?v='+def.version:'');})));
    const box=T=>{const rig=new CharacterRig(def,images),an=new RunAnimator(rig,{runSpeed:620});an.attack(atk);
      for(let i=0;i<400&&an.act&&an.act.t<T;i++){if(an.act.freeze>0)an.act.freeze=0;an.update(Math.min(1/60,T-an.act.t+1e-4),{vx:0,facing:1});}
      const N=2400,c=document.createElement('canvas');c.width=c.height=N;const g=c.getContext('2d',{willReadFrequently:true});rig.draw(g,N/2,N*.8,1,1);
      const d=g.getImageData(0,0,N,N).data;let l=N,t=N,r=-1,b=-1;for(let y=0;y<N;y+=3)for(let x=0;x<N;x+=3)if(d[(y*N+x)*4+3]>40){if(x<l)l=x;if(x>r)r=x;if(y<t)t=y;if(y>b)b=y;}
      return [r-l,t-N*.8,b-N*.8,(l+r)/2-N/2];};
    const T=def.cutHold||.62,a=box(T),b=box(T+1.3/60),c=box(T+2.6/60),bh=def.metrics?.bodyHeight||718;
    out.push([+n,id,T,a.map(Math.round),b.map(Math.round),c.map(Math.round),Math.round(100*Math.max(...a.map((v,i)=>Math.abs(v-b[i]))) /bh)]);}
  return out;}"""
with sync_playwright() as p:
    b, pg, errs = boot(p, 1440, 900)
    rows = pg.evaluate(JS)
    print('번호 id cutHold | 상자[폭,위,아래,가운데] T · T+1프레임 · T+2프레임 | 1프레임 최대 차이 %몸높이')
    for r in sorted(rows): print(*r)
    b.close()
srv.shutdown()
