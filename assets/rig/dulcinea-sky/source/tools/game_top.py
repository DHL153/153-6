# 전투 칸 위 잘림 재기: 공격 동안 rAF 마다 리그 캔버스에서 가장 위 불투명 점(무대 위 끝 기준 CSS px) — python3 game_top.py 가로 세로 번호
import os
exec(open(os.path.dirname(os.path.abspath(__file__)) + '/game_base.py').read())
W = int(sys.argv[1]); H = int(sys.argv[2]); IDX = int(sys.argv[3]) - 1
with sync_playwright() as p:
    b, pg, errs = play(p, W, H)
    pg.evaluate(f"()=>{{battleCharInventory[{IDX}]=Object.assign({{}},Object.values(battleCharInventory)[0]||{{}},{{count:1}});assignBattleTeamCharacter({IDX});}}")
    time.sleep(3)
    r = pg.evaluate("""()=>new Promise(res=>{let el=null,slot=null,E=null;for(const [s,e] of MRRig.live){if(e.rig){slot=s;el=e.el?.id;E=e;break}}
      const cv=E.cv,st=document.getElementById('battle-stage');const cr=cv.getBoundingClientRect(),sr=st.getBoundingClientRect();
      const k=cr.height/cv.height,g=cv.getContext('2d');MRRig.onState('attack',slot);const out=[],t0=performance.now();
      const scan=()=>{const d=g.getImageData(0,0,cv.width,cv.height).data;for(let y=0;y<cv.height;y++){for(let x=0;x<cv.width;x+=1)if(d[(y*cv.width+x)*4+3]>30)return y;}return -1};
      const step=()=>{const t=performance.now()-t0;const a=E.anim.act;out.push([Math.round(t),a?Math.round(a.t*1000)/1000:null,Math.round((cr.top+scan()*k-sr.top)*10)/10]);
        if(t<900)requestAnimationFrame(step);else res({id:E.id,scale:E.scale,canvasTop:cr.top-sr.top,canvasH:cr.height,stageH:sr.height,info:MRRig.info,out})};requestAnimationFrame(step)})""")
    mn = min(o[2] for o in r['out']); print(r['id'], 'scale', round(r['scale'], 4), 'canvasTop', r['canvasTop'], 'canvasH', r['canvasH'], 'stageH', r['stageH'], 'info', r['info'])
    print('min top y (stage px)', mn, [o for o in r['out'] if o[2] < mn + 6][:8])
    print('idle top', r['out'][0])
    print('errs', [e for e in errs if 'handleAsset' not in e][:5]); b.close()
srv.shutdown()
