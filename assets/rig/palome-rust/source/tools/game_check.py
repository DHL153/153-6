# 게임 안에서 9 러스트 팔로메 확인: 전투 달리기·공격(트레일)·스킬 컷인(+끝난 뒤)·도감 2장 (필살기 컷신·시작 선택·마이룸 = game_check2.py) — python3 game_check.py 가로 세로 이름
import os
exec(open(os.path.dirname(os.path.abspath(__file__)) + '/game_base.py').read())
W = int(sys.argv[1]); H = int(sys.argv[2]); tag = sys.argv[3]; IDX = int(os.environ.get('NUM', '9')) - 1   # 캐릭터 번호(NUM=3 → 3 러스트 산초, NUM=11 → 비교용 11 네온 알론소)
with sync_playwright() as p:
    b, pg, errs = play(p, W, H)
    pg.evaluate(f"()=>{{battleCharInventory[{IDX}]=Object.assign({{}},Object.values(battleCharInventory)[0]||{{}},{{count:1}});assignBattleTeamCharacter({IDX});}}")
    time.sleep(3)
    print('live', pg.evaluate("()=>[...MRRig.live.values()].map(e=>[e.id,e.el?.id,Math.round(e.scale*1000)/1000])"))
    pg.locator('#battle-stage').screenshot(path=O + f'{tag}_battle.png')
    n = 0
    for rep in range(2):   # 공격(트레일 포함): MRRig.onState + MRBattleFX.attack 를 같이 — 실제 공격과 같은 순서
        slot = pg.evaluate("()=>{for(const [s,e] of MRRig.live)if(e.rig)return s;return null}")
        el = pg.evaluate("()=>{for(const [s,e] of MRRig.live)if(e.rig)return e.el?.id;return null}")
        pg.evaluate(f"()=>{{MRRig.onState('attack',{json.dumps(slot)});window.MRBattleFX?.attack({json.dumps(el)});}}"); t0 = time.time()
        while time.time() - t0 < 0.8:
            pg.locator('#battle-stage').screenshot(path=O + f'{tag}_atk{n}.png'); n += 1
        time.sleep(1.5)
    print('attack shots', n, 'trailUp', pg.evaluate(f"()=>MRRig.trailUp({json.dumps(el)})"))
    pg.evaluate("()=>startBattleTeamSkill({kind:'slash',duration:2500})")
    for i, t in enumerate([.25, .6, 1.0, 1.6]):
        time.sleep(t - [0, .25, .6, 1.0][i]); pg.locator('#battle-stage').screenshot(path=O + f'{tag}_cut{i}.png')
    time.sleep(2.0); pg.locator('#battle-stage').screenshot(path=O + f'{tag}_after.png')   # 컷인 끝난 뒤 리그가 돌아왔나
    time.sleep(4.0); pg.locator('#battle-stage').screenshot(path=O + f'{tag}_after2.png')
    print('live after', pg.evaluate("()=>[...MRRig.live.values()].map(e=>[e.id,e.el?.id,e.anim?.action?.name||null])"))
    pg.evaluate(f"()=>MRWorld.openDetail({{meta:BATTLE_CHARACTER_META[{IDX}],tier:'L',owned:true,count:1,slot:0,team:[...battleTeam],slotRaw:i=>['주 캐릭터','동료 1','동료 2'][i],roomOwned:()=>true}})")
    time.sleep(2.5); pg.locator('.mrw-box').screenshot(path=O + f'{tag}_dex1.png')
    pg.locator('.mrw-nav.next').click(); time.sleep(2.5); pg.locator('.mrw-box').screenshot(path=O + f'{tag}_dex2.png')
    print('errs', [e for e in errs if 'handleAsset' not in e][:5]); b.close()
srv.shutdown()
