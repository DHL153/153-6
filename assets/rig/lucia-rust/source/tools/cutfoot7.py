# 컷인 유지 자세(게임과 같은 cutHold + 1.3/60)에서 '가장 낮은 불투명 점'(지금 컷인 발 맞춤 기준) vs '발(다리만 그린 가장 낮은 점)' — 리그마다 (10-21 DHL 루시아 컷인 높음)
#   python3 -I tools/cutfoot7.py   → 리그 px(배율 1) 차이 · 몸 높이 대비 %
import os, sys
exec(open(os.path.dirname(os.path.abspath(__file__)) + '/game_base.py').read())
JS = r"""async ()=>{
  const out=[];
  for(const [n,id] of Object.entries(MRRig.registry)){
    const def=window.MR_RIG_DEFS[id];if(!def){out.push([n,id,'nodef']);continue;}
    const base='assets/rig/'+id+'/',images={};
    await Promise.all(Object.entries(def.parts).map(([k,p])=>new Promise(res=>{const im=new Image();im.onload=()=>{images[k]=im;res()};im.onerror=()=>res();im.src=(String(p.src).startsWith('data:')?'':base)+p.src+(def.version&&!String(p.src).startsWith('data:')?'?v='+def.version:'');})));
    const atk=def.ui?.attack||'thrust',AT=def.actions?.[atk],spear=AT&&(AT.kind==='spear'||def.ui?.stillSame||!!def.ui?.stillReady);
    const other=atk!=='thrust'&&!spear;
    const rig=new CharacterRig(def,images),an=new RunAnimator(rig,{runSpeed:620});
    let T=0;
    if(other){an.attack(atk);T=(def.cutHold||.62)+1.3/60;for(let i=0;i<400&&an.act&&an.act.t<T;i++){if(an.act.freeze>0)an.act.freeze=0;an.update(Math.min(1/60,T-an.act.t+1e-4),{vx:0,facing:1});}}
    else{out.push([+n,id,'찌르기 컷인(guard 자세) — 건너뜀']);continue;}
    const N=2400,meas=(order)=>{const c=document.createElement('canvas');c.width=c.height=N;const g=c.getContext('2d',{willReadFrequently:true});
      const keep=rig.drawOrder;if(order)rig.drawOrder=order;rig.draw(g,N/2,N*.8,1,1);rig.drawOrder=keep;
      const d=g.getImageData(0,0,N,N).data;let t=N,b=-1,l=N,r=-1;for(let y=0;y<N;y+=2)for(let x=0;x<N;x+=2)if(d[(y*N+x)*4+3]>40){if(y<t)t=y;if(y>b)b=y;if(x<l)l=x;if(x>r)r=x;}
      return {top:t-N*.8,bottom:b-N*.8,l:l-N/2,r:r-N/2};};
    const all=meas(null),cur=rig.drawOrder||def.draw,legs=meas(cur.filter(x=>x==='legFar'||x==='legNear'));
    out.push([+n,id,other?'cutHold '+T:'guard',Math.round(all.bottom),Math.round(legs.bottom),Math.round(all.bottom-legs.bottom),def.metrics?.bodyHeight,Math.round(all.top)]);
  }
  return out;}"""
with sync_playwright() as p:
    b, pg, errs = boot(p, 1440, 900)
    rows = pg.evaluate(JS)
    print('번호 id 자세 | 전체 맨 아래 · 발 맨 아래 · 차이(리그px) · 몸 높이 · 차이/몸높이%')
    for r in sorted(rows, key=lambda r: r[0] if isinstance(r[0], int) else 99):
        if len(r) < 8: print(r); continue
        print(r[0], r[1], r[2], '|', r[3], r[4], r[5], r[6], f'{100*r[5]/r[6]:.1f}%')
    print('errs', [e for e in errs if 'handleAsset' not in e][:5]); b.close()
srv.shutdown()
