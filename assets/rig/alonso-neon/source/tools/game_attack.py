# 게임 전투에서 11 리그 공격 장면 찍기(MRRig.onState('attack') 직접 호출 — 자동 공격을 기다리지 않음): python3 game_attack.py 가로 세로 이름
exec(open(__import__('os').path.dirname(__file__)+'/game_base.py').read())
W=int(sys.argv[1]);H=int(sys.argv[2]);tag=sys.argv[3]
with sync_playwright() as p:
    b,pg,errs=play(p,W,H)
    pg.evaluate("()=>{battleCharInventory[10]=Object.assign({},Object.values(battleCharInventory)[0]||{},{count:1});assignBattleTeamCharacter(10);}")
    time.sleep(2.5); n=0
    for rep in range(2):
        slot=pg.evaluate("()=>{for(const [s,e] of MRRig.live)if(e.id==='alonso-neon')return s;return null}")
        pg.evaluate(f"()=>MRRig.onState('attack',{json.dumps(slot)})"); t0=time.time()
        while time.time()-t0<0.9:
            pg.locator('#battle-stage').screenshot(path=O+f'{tag}_atk{n}.png'); n+=1
        time.sleep(1.5)
    print('shots',n,'errs',[e for e in errs if 'handleAsset' not in e][:5]); b.close()
srv.shutdown()
