# 게임 안에서 11 확인: 전투·스킬 컷인·도감 2장 찍기 — python3 game_check.py [가로 세로 이름] (base.py: 스토리 건너뛰기·시작 선택 자동)
exec(open(''+__import__('os').path.dirname(__file__)+'/game_base.py').read())
W=int(sys.argv[1]) if len(sys.argv)>1 else 1280;H=int(sys.argv[2]) if len(sys.argv)>2 else 800;tag=sys.argv[3] if len(sys.argv)>3 else 'd'
with sync_playwright() as p:
    b,pg,errs=play(p,W,H)
    print(pg.evaluate("()=>JSON.stringify(Object.entries(battleCharInventory).slice(0,2))"))
    pg.evaluate("()=>{battleCharInventory[10]=Object.assign({},Object.values(battleCharInventory)[0]||{},{count:1});assignBattleTeamCharacter(10);}")
    time.sleep(3)
    pg.locator('#battle-stage').screenshot(path=O+f'{tag}_battle.png')
    pg.evaluate("()=>startBattleTeamSkill({kind:'slash',duration:2500})")
    for i,t in enumerate([.25,.6,1.0,1.6]):
        time.sleep(t-( [0,.25,.6,1.0][i] ));pg.locator('#battle-stage').screenshot(path=O+f'{tag}_cut{i}.png')
    time.sleep(2)
    pg.evaluate("()=>MRWorld.openDetail({meta:BATTLE_CHARACTER_META[10],tier:'L',owned:true,count:1,slot:0,team:[...battleTeam],slotRaw:i=>['주 캐릭터','동료 1','동료 2'][i],roomOwned:()=>true})")
    time.sleep(2.5);pg.locator('.mrw-box').screenshot(path=O+f'{tag}_dex1.png')
    pg.locator('.mrw-nav.next').click();time.sleep(2.5);pg.locator('.mrw-box').screenshot(path=O+f'{tag}_dex2.png')
    print(pg.evaluate("""()=>{const h=document.querySelector('.mrw-hero').getBoundingClientRect();return {hero:[h.left,h.width]}}"""))
    print('errs',[e for e in errs if 'handleAsset' not in e][:5]);b.close()
srv.shutdown()
