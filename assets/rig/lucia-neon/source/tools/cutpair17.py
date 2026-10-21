# (17 네온 루시아용 — 7 러스트 cutpair7 복사, HOLD7 = lucia-neon cutHold 시험)
# 여러 명 스킬 컷인(두 명) 간격 확인 (10-21 00:51 DHL '다중 인원 컷인 때 두 캐릭터가 너무 붙어 있다') + 혼자 컷인 발 높이
#   python3 -I tools/cutpair7.py 가로 세로 이름 '팀1;팀2;...'   팀 = 번호,번호[,번호] (첫 번호 = 주 캐릭터)
#   각 팀: battleTeam 직접 → 두 명 컷인(Math.random 고정) → 유지 자세 1.05초 → 칸 그림 + 캐릭터마다 리그 불투명 범위(칸 기준 px)
import os, sys
exec(open(os.path.dirname(os.path.abspath(__file__)) + '/game_base.py').read())
W = int(sys.argv[1]); H = int(sys.argv[2]); tag = sys.argv[3]
HOLDS7 = [h for h in os.environ.get('HOLD7', '').split(',') if h]   # 시험: 7 루시아 cutHold 바꿔 보기(예 .32,.40 — 값마다 모든 팀)
TEAMS = [[int(x) for x in t.split(',')] for t in (sys.argv[4] if len(sys.argv) > 4 else '7,2;9,7;1,3;7').split(';')]
SET = r"""(ids)=>{for(const i of ids)battleCharInventory[i]=Object.assign({},Object.values(battleCharInventory)[0]||{},{count:1});
  battleTeam=[ids[0],ids[1]??null,ids[2]??null];selectedBattleTeamSlot=0;commitBattleTeamLive(0);return [...activeBattleTeam];}"""
CUT = r"""(pair)=>{const R=Math.random;if(pair)Math.random=()=>.95;try{clearBattleTeamSkill?.();startBattleTeamSkill({kind:'slash',duration:6000});}finally{Math.random=R;}}"""
MEASURE = r"""()=>{const st=document.querySelector('#battle-stage').getBoundingClientRect(),res=[];
  for(const img of document.querySelectorAll('#skill-cinematic img.team-cut-in')){
    const e=MRRig.stills.get(img),c=e?.canvas;const ir=img.getBoundingClientRect();
    const row={num:img.dataset.battleCharacter,id:e?.id,cutX:img.style.getPropertyValue('--cut-x'),img:[ir.left-st.left,ir.top-st.top,ir.width,ir.height].map(v=>Math.round(v))};
    if(c&&c.style.display!=='none'){const r=c.getBoundingClientRect(),g=c.getContext('2d'),d=g.getImageData(0,0,c.width,c.height).data,k=r.width/c.width;
      let l=1e9,t=1e9,RR=-1,B=-1;for(let y=0;y<c.height;y+=2)for(let x=0;x<c.width;x+=2)if(d[(y*c.width+x)*4+3]>60){if(x<l)l=x;if(x>RR)RR=x;if(y<t)t=y;if(y>B)B=y;}
      Object.assign(row,{l:Math.round(r.left+l*k-st.left),r:Math.round(r.left+RR*k-st.left),t:Math.round(r.top+t*k-st.top),b:Math.round(r.top+B*k-st.top)});
      const hip=(e.rig.def.bones||[]).find(x=>x.name==='hip');}
    res.push(row);}
  return {stage:[Math.round(st.width),Math.round(st.height)],members:res};}"""
with sync_playwright() as p:
    b, pg, errs = play(p, W, H)
    for ti, (HOLD7, team) in enumerate([(h, t) for h in (HOLDS7 or ['']) for t in TEAMS]):
        got = pg.evaluate(SET, [n - 1 for n in team]); time.sleep(3)
        name = '-'.join(f'{n:02d}' for n in team) + (f'_h{HOLD7.lstrip("0.")}' if HOLD7 else '')
        for tr in range(4):   # 컷인이 막히면(경고·다른 연출) 다시 — 칸 그림을 먼저 찍고 바로 잼(찍는 동안 컷인이 끝나지 않게)
            if HOLD7: pg.evaluate(f"()=>{{window.MR_RIG_DEFS['lucia-neon'].cutHold={HOLD7}}}")
            pg.evaluate(CUT, len(team) > 1); time.sleep(2.4)   # 6초 컷인의 40% (= 2.5초 컷인 1.0초와 같은 단계) — 찍는 데 오래 걸려도 컷인 안
            pg.locator('#battle-stage').screenshot(path=O + f'{tag}_pair_{name}.png')
            m = pg.evaluate(MEASURE)
            on = pg.evaluate("()=>document.getElementById('skill-cinematic')?.classList.contains('on')")
            if on and m['members'] and all('l' in x for x in m['members']): break
            time.sleep(3)
        print(name, 'team', got, json.dumps(m, ensure_ascii=False), flush=True)
        time.sleep(4.5)
    print('errs', [e for e in errs if 'handleAsset' not in e][:5]); b.close()
srv.shutdown()
