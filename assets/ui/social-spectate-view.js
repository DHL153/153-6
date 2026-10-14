/* =====================================================================
 * Merge & Run — 관전 화면 부품 (MRSpectateView)
 *
 * '받은 관전 데이터 → 작은 전투 화면 그리기'만 담당한다.
 * 게임 상태·세이브·네트워크에 접근하지 않으므로 어디서든 띄울 수 있다.
 *   - index.html 소셜 탭의 관전 패널
 *   - spectate.html 단독 관전 창 (웹: 팝업 / exe: 바탕화면에 뜨는 작은 창)
 *
 * 사용법
 *   const view = MRSpectateView.create(container, { t: key => 번역문 });
 *   view.apply(data);          // 관전 데이터 (아래 sanitize 형식)
 *   view.overlay('social.spectateNoData');  // 안내 문구 (null = 숨김)
 *   view.destroy();
 * ===================================================================== */
(function(){
  'use strict';
  if(window.MRSpectateView) return;

  const ASSET_RE=/^assets\/art\/[\w\-\/.]+\.(png|jpe?g|webp|gif)$/i;
  const POSES=['idle','attack','skill','victory'];

  // 진형(파티 위치 %): 메인 게임의 battleFormation이 있으면 그것을, 없으면(단독 창) 기본값을 사용
  const FALLBACK_HEROES=[[30],[22,40],[14,30,46]];
  function formation(count,W,H){
    try{ if(typeof window.battleFormation==='function') return window.battleFormation(count||1,W,H); }catch(e){}
    return { heroes:FALLBACK_HEROES[Math.max(0,Math.min(2,(count||1)-1))], enemy:78 };
  }

  // 전투 하늘 단계 5개(새벽·낮·노을·밤·포털) — 본 게임 #battle-sky와 같은 색
  const SKY_GRADIENTS=['linear-gradient(#4b5b8c,#a993b5 26%,#f1c39e 48%)','linear-gradient(#5fa9dc,#a9d6ec 26%,#efe6cc 48%)','linear-gradient(#56396b,#cf6f58 26%,#f5b462 48%)','linear-gradient(#141c3a,#26345e 26%,#3f5582 48%)','linear-gradient(#35296a,#6f53aa 26%,#bda2e4 48%)'];
  function cleanSrc(src){
    const s=String(src||'').split('?')[0].replace(/^\.\//,'');
    return ASSET_RE.test(s)?s:'';
  }
  // 받은 데이터는 항상 이 함수를 거친다 (형식·범위·이미지 경로 검사)
  function sanitize(p){
    if(!p || typeof p!=='object') return null;
    const team=(Array.isArray(p.team)?p.team:[]).slice(0,3).map(m=>({
      slot:Math.max(0,Math.min(2,Number(m&&m.slot)||0)), src:cleanSrc(m&&m.src), pose:POSES.includes(m&&m.pose)?m.pose:'idle'
    })).filter(m=>m.src);
    const num=(v,max)=>Math.max(0,Math.min(max,Math.floor(Number(v)||0)));
    const enemy=p.enemy||{};
    return {
      team, bg:cleanSrc(p.bg), skyStage:(Number.isInteger(p.skyStage)&&p.skyStage>=0&&p.skyStage<5)?p.skyStage:null,
      enemy:{ src:cleanSrc(enemy.src), boss:!!enemy.boss },
      boss:p.boss?{ name:String(p.boss.name||'').replace(/[^\w .\-]/g,'').slice(0,24), hp:num(p.boss.hp,9999), max:Math.max(1,num(p.boss.max,9999)) }:null,
      pips:p.pips?{ on:num(p.pips.on,10), max:Math.max(1,num(p.pips.max,10)) }:null,
      paused:!!p.paused
    };
  }

  const CSS=`
.mrsv-stage{position:relative;height:100%;min-height:120px;border-radius:10px;overflow:hidden;background:#1d2a3c;isolation:isolate;}
.mrsv-bg{position:absolute;inset:0;background-size:auto 100%;background-repeat:repeat-x;background-position:0 50%;animation:mrsv-scroll 40s linear infinite;z-index:0;}
.mrsv-stage.paused .mrsv-bg{animation-play-state:paused;}
@keyframes mrsv-scroll{to{background-position:-1200px 50%;}}
.mrsv-bg.has-sky{background-size:auto 100%,100% 100%;background-position:0 50%,0 0;animation-name:mrsv-scroll-sky;}
@keyframes mrsv-scroll-sky{to{background-position:-1200px 50%,0 0;}}
.mrsv-hero{position:absolute;bottom:8%;height:72%;width:auto;max-width:34%;object-fit:contain;transform:translateX(-50%);z-index:3;pointer-events:none;user-select:none;}
.mrsv-hero[hidden]{display:none;}
.mrsv-hero.attack{animation:mrsv-lunge .4s ease-out;}
.mrsv-hero.skill{filter:drop-shadow(0 0 10px rgba(124,227,209,.9));}
@keyframes mrsv-lunge{40%{translate:14% 0;}}
.mrsv-enemy{position:absolute;bottom:26%;height:52%;transform:translateX(-50%);z-index:2;display:flex;align-items:flex-end;justify-content:center;}
.mrsv-enemy.boss{bottom:8%;height:78%;}
.mrsv-enemy img{height:100%;width:auto;max-width:none;object-fit:contain;user-select:none;}
.mrsv-enemy img[hidden]{display:none;}
.mrsv-enemy.hit{animation:mrsv-hit .32s ease-out;}
@keyframes mrsv-hit{25%{translate:7px 0;filter:brightness(2.2);}70%{translate:-4px 0;}}
.mrsv-boss{position:absolute;top:7px;left:50%;transform:translateX(-50%);width:62%;z-index:4;text-align:center;}
.mrsv-boss[hidden]{display:none;}
.mrsv-boss-name{font-size:10px;font-weight:1000;color:#ffe08a;text-shadow:0 1px 2px #000;}
.mrsv-boss-track{height:7px;border-radius:99px;background:rgba(0,0,0,.55);overflow:hidden;margin-top:2px;}
.mrsv-boss-fill{height:100%;width:100%;background:linear-gradient(90deg,#ff5d6c,#ffb36b);transition:width .25s;}
.mrsv-pips{position:absolute;top:8px;right:10px;display:flex;gap:3px;z-index:4;}
.mrsv-pips i{width:8px;height:8px;border-radius:50%;background:rgba(0,0,0,.5);border:1px solid rgba(255,255,255,.5);}
.mrsv-pips i.on{background:#ff6b7d;}
.mrsv-overlay{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;padding:0 16px;background:rgba(15,24,36,.72);color:#9fb1c4;font-size:11.5px;font-weight:800;z-index:6;}
.mrsv-overlay[hidden]{display:none;}
@media (prefers-reduced-motion:reduce){.mrsv-bg,.mrsv-hero.attack,.mrsv-enemy.hit{animation:none;}}`;
  function ensureCss(doc){
    if(doc.getElementById('mrsv-style')) return;
    const st=doc.createElement('style'); st.id='mrsv-style'; st.textContent=CSS;
    (doc.head||doc.documentElement).appendChild(st);
  }
  function retrigger(el,cls){ el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); }

  function create(container,opts={}){
    const doc=container.ownerDocument||document;
    ensureCss(doc);
    const t=k=>{ try{ return typeof opts.t==='function'?opts.t(k):k; }catch(err){ return k; } };
    container.innerHTML=`<div class="mrsv-stage">
      <div class="mrsv-bg"></div>
      <img class="mrsv-hero" alt="" hidden><img class="mrsv-hero" alt="" hidden><img class="mrsv-hero" alt="" hidden>
      <div class="mrsv-enemy"><img alt="" hidden></div>
      <div class="mrsv-boss" hidden><div class="mrsv-boss-name"></div><div class="mrsv-boss-track"><div class="mrsv-boss-fill"></div></div></div>
      <div class="mrsv-pips"></div>
      <div class="mrsv-overlay"></div>
    </div>`;
    const q=s=>container.querySelector(s);
    const e={ stage:q('.mrsv-stage'), bg:q('.mrsv-bg'), heroes:[...container.querySelectorAll('.mrsv-hero')], enemy:q('.mrsv-enemy'), enemyImg:q('.mrsv-enemy img'),
      boss:q('.mrsv-boss'), bossName:q('.mrsv-boss-name'), bossFill:q('.mrsv-boss-fill'), pips:q('.mrsv-pips'), overlay:q('.mrsv-overlay') };
    let prev=null, overlayKey='social.spectateWaiting', lastAt=0;

    function overlay(key){
      overlayKey=key||null;
      if(!key){ e.overlay.hidden=true; return; }
      e.overlay.hidden=false;
      e.overlay.textContent=t(key);
      e.overlay.setAttribute('data-i18n',key);
    }
    function apply(raw){
      const d=sanitize(raw); if(!d) return false;
      lastAt=Date.now();
      overlay(d.paused?'social.spectatePaused':null);
      e.stage.classList.toggle('paused',d.paused);
      // 땅(투명 하늘) 뒤에 친구의 현재 하늘 단계 색을 깔아 줌. 정보가 없으면 예전처럼 땅만
      const sky=d.skyStage===null?'':SKY_GRADIENTS[d.skyStage];
      if(d.bg) e.bg.style.backgroundImage=sky?`url("${d.bg}"),${sky}`:`url("${d.bg}")`;
      e.bg.classList.toggle('has-sky',!!(d.bg&&sky));
      const W=e.stage.clientWidth||300, H=e.stage.clientHeight||150;
      const form=formation(d.team.length,W,H);
      e.heroes.forEach((img,i)=>{
        const m=d.team[i];
        if(!m){ img.hidden=true; img.classList.remove('attack','skill'); return; }
        img.hidden=false;
        if(img.getAttribute('src')!==m.src) img.setAttribute('src',m.src);
        img.style.left=form.heroes[i]+'%';
        img.style.zIndex=String(5-i);
        const prevPose=prev&&prev.team[i]&&prev.team[i].pose;
        if(m.pose==='attack' && prevPose!=='attack') retrigger(img,'attack');
        img.classList.toggle('skill',m.pose==='skill');
      });
      e.enemy.style.left=form.enemy+'%';
      e.enemy.classList.toggle('boss',d.enemy.boss);
      if(d.enemy.src){ e.enemyImg.hidden=false; if(e.enemyImg.getAttribute('src')!==d.enemy.src) e.enemyImg.setAttribute('src',d.enemy.src); }
      else e.enemyImg.hidden=true;
      e.boss.hidden=!d.boss;
      if(d.boss){ e.bossName.textContent=d.boss.name; e.bossFill.style.width=(d.boss.hp/d.boss.max*100)+'%'; }
      e.pips.innerHTML=d.pips?Array.from({length:d.pips.max},(_,i)=>`<i class="${i<d.pips.on?'on':''}"></i>`).join(''):'';
      if(prev && ((d.boss&&prev.boss&&d.boss.hp<prev.boss.hp) || (d.pips&&prev.pips&&d.pips.on<prev.pips.on))) retrigger(e.enemy,'hit');
      prev=d;
      return true;
    }
    overlay(overlayKey);
    return Object.freeze({
      apply, overlay,
      lastUpdate:()=>lastAt,
      stage:e.stage,
      relabel(fn){ if(typeof fn==='function'){ opts.t=fn; } overlay(overlayKey); },
      destroy(){ container.innerHTML=''; prev=null; }
    });
  }

  window.MRSpectateView=Object.freeze({ create, sanitize, cleanSrc, version:1 });
})();
