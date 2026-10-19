# 트레일 시각 vs 리그 타격 시각: rAF 마다 [ms, 리그 공격 t, 효과 캔버스 밝은 점 수] — python3 game_trail_t.py 가로 세로 [전투인덱스]
import os
exec(open(os.path.dirname(os.path.abspath(__file__)) + '/game_base.py').read())
W = int(sys.argv[1]); H = int(sys.argv[2]); IDX = int(sys.argv[3]) if len(sys.argv) > 3 else 12
with sync_playwright() as p:
    b, pg, errs = play(p, W, H)
    pg.evaluate(f"()=>{{battleCharInventory[{IDX}]=Object.assign({{}},Object.values(battleCharInventory)[0]||{{}},{{count:1}});assignBattleTeamCharacter({IDX});}}")
    time.sleep(3)
    r = pg.evaluate("""()=>new Promise(res=>{let el=null,slot=null,E=null;for(const [s,e] of MRRig.live){slot=s;el=e.el?.id;E=e;break}
      const hd=MRRig.hitDelayMs(el);MRRig.onState('attack',slot);MRBattleFX.attack(el);const out=[],t0=performance.now();
      const fx=document.getElementById('mr-battle-fx-canvas'),g=fx.getContext('2d');
      const step=()=>{const t=performance.now()-t0;let n=0;if(!fx.hidden&&fx.width){const d=g.getImageData(0,0,fx.width,fx.height).data;for(let i=0;i<d.length;i+=16)if(d[i]>150)n++;}
        const a=E.anim.action||E.anim.act||null;out.push([Math.round(t),a?Math.round((a.t??a.time??-1)*1000)/1000:null,n]);
        if(t<650)requestAnimationFrame(step);else res({hd,id:E.id,out})};requestAnimationFrame(step)})""")
    print(r['id'], 'hitDelayMs', r['hd']); print(r['out']); b.close()
srv.shutdown()
