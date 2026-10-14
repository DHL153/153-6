/* Merge & Run art edition: cosmetic presentation; physics remains in index.html. */
window.MR = (() => {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const $ = id => document.getElementById(id);
  const imageCache = new Map();
  const deadlineY = 16;
  let observer, fitFrame = 0, cinematicTimer, ready = false;
  let audioContext, musicGain, musicSource, musicPromise;
  let musicVolume=0;
  function syncMusic(settings,unlocked){
    musicVolume=settings.bgm?Math.max(0,Math.min(1,settings.masterVolume/100))*Math.max(0,Math.min(1,settings.bgmVolume/100)):0;
    if(!unlocked)return;
    const AudioContext=window.AudioContext||window.webkitAudioContext;if(!AudioContext)return;
    if(!audioContext){audioContext=new AudioContext();musicGain=audioContext.createGain();musicGain.gain.value=0;musicGain.connect(audioContext.destination);}
    if(audioContext.state==='suspended')audioContext.resume().catch(()=>{});
    if(!musicPromise){
      musicPromise=fetch('assets/audio/bgm/starlight_atelier.ogg').then(r=>{if(!r.ok)throw new Error('BGM unavailable');return r.arrayBuffer();}).then(bytes=>audioContext.decodeAudioData(bytes)).then(buffer=>{
        musicSource=audioContext.createBufferSource();musicSource.buffer=buffer;musicSource.loop=true;musicSource.connect(musicGain);musicSource.start();
        musicGain.gain.setTargetAtTime(musicVolume,audioContext.currentTime,.7);
      }).catch(error=>{musicPromise=null;console.warn('Music:',error.message);});
    }
    musicGain.gain.setTargetAtTime(musicVolume,audioContext.currentTime,.15);
  }
  // 소셜·마이룸용 아이콘 (icon-nodes.js에 없는 것만 보충)
  window.MR_ICON_NODES=window.MR_ICON_NODES||{};
  if(!window.MR_ICON_NODES.Users)window.MR_ICON_NODES.Users=[["path",{"d":"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["circle",{"cx":"9","cy":"7","r":"4"}],["path",{"d":"M22 21v-2a4 4 0 0 0-3-3.87"}],["path",{"d":"M16 3.13a4 4 0 0 1 0 7.75"}]];
  if(!window.MR_ICON_NODES.House)window.MR_ICON_NODES.House=[["path",{"d":"M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"}],["path",{"d":"M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"}]];
  const emojiIcons = {
    '🏠':'House','👥':'Users',
    '⚔':'Swords','🗡':'Sword','🛒':'ShoppingBag','🎒':'Layers','📚':'BookOpen','☰':'Menu',
    '🏆':'Trophy','⭐':'Star','🌟':'Star','🪙':'Coins','🧩':'Puzzle','🔄':'Repeat2','🤖':'Bot',
    '🧲':'Magnet','🌪':'Waves','🌀':'Tornado','⏸':'Pause','▶':'Play','↗':'Maximize2',
    '🔊':'Volume2','🔇':'VolumeX','✨':'Sparkles','🎁':'Gift','😊':'Smile','⏳':'Clock3',
    '✅':'Check','🔒':'LockKeyhole','🔓':'LockKeyholeOpen','⚙':'Settings2','📊':'ChartNoAxesCombined',
    '🖼':'Image','🐾':'UserRound','❤':'Heart','💖':'Heart','💗':'Heart','🗑':'Trash2','🛠':'WandSparkles',
    '⚡':'Zap','💥':'Zap','🔥':'Flame','👑':'Crown','🔮':'Circle','⚠':'CircleAlert','🎫':'Diamond',
    '🧹':'WandSparkles','🎉':'Sparkles','🎊':'Sparkles','💎':'Diamond','💫':'Sparkles','💨':'Waves',
    '🎮':'Gamepad2','🌸':'Flower2','🚗':'Plane','🧸':'Shapes','🍓':'Sun','🧑':'UserRound',
    '🐱':'Smile','🌿':'Flower2','🛍':'ShoppingBag','❓':'CircleHelp'
  };
  function icon(name, className='') {
    const nodes = window.MR_ICON_NODES[name] || window.MR_ICON_NODES.Sparkles;
    const children=nodes.map(([tag,attrs])=>`<${tag} ${Object.entries(attrs).map(([k,v])=>`${k}="${v}"`).join(' ')}></${tag}>`).join('');
    return `<svg class="ui-icon ${className}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${children}</svg>`;
  }
  const iconContext='button,.nav-item,.icon,.icon-main,.panel-title,.settings-title,.stat-badge,.mini-stat,.mini-label,.mini-mode-type,.control-name,.cost-label,.mmi-icon,.mmi-name,.mmi-cost,.floating-text,.score-hero-label,.score-hero-value,.score-hero-sub,.mini-stage,.subnav-btn,.cat-tab,.craft-filter-btn,.economy-tab,.codex-category-tab,.char-bg-tier-btn,.emoji-category-btn,.lock-mark,.title,.pause-title,.ss-rays,#go-icon,#top-gacha-timer,#go-record-title,#mini-gacha,#mini-mode-type,#boss-name,#warning-banner,#mini-footer-text,#mini-footer-battle-left';
  const pictogram=/[\p{Extended_Pictographic}⏸▶☰↗](?:\uFE0F|\u200D[\p{Extended_Pictographic}])*/gu;
  function polishIcons(root) {
    if(!root || root.nodeType!==1 || root.closest('svg,.ui-icon,script,style')) return;
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    const changes=[];
    while(walker.nextNode()){
      const node=walker.currentNode, parent=node.parentElement;
      if(!parent || !parent.closest(iconContext) || parent.closest('svg,script,style,.emoji,.char-placed-emoji,.placed-emoji')) continue;
      if(parent.closest('.char-item-btn,.inv-item,.economy-item,.gacha-card') && !parent.closest('.lock-mark')) continue;
      pictogram.lastIndex=0;
      if(pictogram.test(node.nodeValue)) changes.push(node);
    }
    for(const node of changes){
      if(!node.parentNode) continue;
      const frag=document.createDocumentFragment();
      const value=node.nodeValue; let last=0;
      pictogram.lastIndex=0;
      for(const match of value.matchAll(pictogram)){
        frag.append(document.createTextNode(value.slice(last,match.index)));
        const name=emojiIcons[match[0].replace(/\uFE0F/g,'')] || 'Sparkles';
        const holder=document.createElement('span'); holder.innerHTML=icon(name);
        frag.append(holder.firstElementChild);last=match.index+match[0].length;
      }
      frag.append(document.createTextNode(value.slice(last)));node.replaceWith(frag);
    }
  }
  function preload(url) {
    if(imageCache.has(url)) return imageCache.get(url);
    const promise=new Promise(resolve=>{
      const img=new Image(); img.decoding='async';
      img.onload=()=>resolve(img);img.onerror=()=>resolve(null);img.src=url;
    });
    imageCache.set(url,promise);return promise;
  }
  async function preloadBeads(beads) {
    await Promise.all(beads.flatMap(b=>[preload(b.path),preload(b.smile)]));
  }
  async function preloadBattleRuns(characters) {
    await Promise.all(characters.flatMap(c=>(c.runFrames||[]).map(preload)));
  }
  function beginSmile(body,meta,timestamp) {
    if(!meta?.smile || !body.render.sprite) return;
    body._expression={start:timestamp,neutral:meta.path,smile:meta.smile,x:body.render.sprite.xScale,y:body.render.sprite.yScale};
    body.render.sprite.texture=meta.smile;
  }
  function updateSmile(body,timestamp) {
    const ex=body._expression;if(!ex)return;
    const age=timestamp-ex.start, sprite=body.render.sprite;
    if(age>=1450){sprite.texture=ex.neutral;sprite.xScale=ex.x;sprite.yScale=ex.y;delete body._expression;return;}
    sprite.texture=ex.smile;
    const bounce=reducedMotion.matches?0:Math.sin(Math.min(age,420)/420*Math.PI*2)*.11*Math.max(0,1-age/420);
    sprite.xScale=ex.x*(1+bounce);sprite.yScale=ex.y*(1-bounce);
  }
  function mergeBurst(area,nx,ny,level,shake) {
    const fx=document.createElement('div');fx.className='merge-burst';
    fx.style.left=(nx*100)+'%';fx.style.top=(ny*100)+'%';
    fx.style.setProperty('--burst-color',level>=8?'#f5c972':level>=5?'#b69afa':'#6fdadc');
    const size=Math.min(110,28+level*9);fx.style.setProperty('--burst-size',size+'px');
    fx.innerHTML='<i class="burst-ring"></i><i class="burst-light"></i>';
    if(!reducedMotion.matches){
      const count=level>=7?12:7;
      for(let i=0;i<count;i++){
        const p=document.createElement('i');p.className='burst-spark';const angle=i/count*Math.PI*2;
        p.style.setProperty('--dx',Math.cos(angle)*(size*.6+15)+'px');p.style.setProperty('--dy',Math.sin(angle)*(size*.6+15)+'px');
        p.style.setProperty('--turn',angle+'rad');p.style.animationDelay=(i%3*15)+'ms';fx.append(p);
      }
    }
    area.append(fx);setTimeout(()=>fx.remove(),650);
    if(level>=5&&shake&&!reducedMotion.matches){$('merge-box').classList.remove('art-impact');void $('merge-box').offsetWidth;$('merge-box').classList.add('art-impact');setTimeout(()=>$('merge-box')?.classList.remove('art-impact'),220);}
  }
  function setEnemy(id) {
    const enemy=$('enemy');if(!enemy)return;
    const boss=id==='boss';
    const names=['사슬 망령','삼지창 망령','망치 망령','장창 망령','비취 도끼 망령','비취 쌍검 망령','비취 방패 망령','비취 작살 망령'];
    const n=Math.max(0,(Number(id)||1)-1)%names.length;
    const image=document.createElement('img');
    image.src=boss?'assets/art/villains/boss_0004.png':`assets/art/villains/villain_${String(8+n).padStart(4,'0')}.png`;
    image.alt=boss?'광견 하이에나':names[n];image.draggable=false;
    enemy.replaceChildren(image);
  }
  function hitMarkup(state) {
    return `<span class="art-hit ${state==='skill'?'art-hit-skill':''}"><i></i><i></i><i></i></span>`;
  }
  function clearCutscene(){
    clearTimeout(cinematicTimer);const el=$('skill-cinematic');if(el){el.classList.remove('on');el.replaceChildren();}
  }
  function skillCutscene(meta={}) {
    clearCutscene();const el=$('skill-cinematic');if(!el)return;
    const img=document.createElement('img');img.src=meta.portrait||'assets/art/characters/char_0001.png';img.alt='';
    const title=document.createElement('div');title.className='skill-cinematic-copy';
    const kicker=document.createElement('small');kicker.textContent=`${meta.name||'루미'} · SKILL`;
    const name=document.createElement('strong');name.textContent=meta.skillName||'스타라이트 브레이크';
    title.append(kicker,name);el.append(img,title);el.classList.add('on');
    if(typeof playSfx==='function')playSfx('skillCharge',{gain:.4,minGap:600});
    cinematicTimer=setTimeout(clearCutscene,1350);
  }
  function fit() {
    cancelAnimationFrame(fitFrame);
    fitFrame=requestAnimationFrame(()=>{
      const app=$('app'),box=$('merge-box');
      if(!app||!box||!box.clientHeight||app.classList.contains('mini-battle-mode'))return;
      const mini=app.classList.contains('mini-mode');
      // Match the mini board's deadline position relative to its background:
      // mini top = 10.5%, canvas width = 89% of a square board.
      const deadlineRatio=.105+.89*deadlineY/360;
      const targetY=box.clientHeight*deadlineRatio;
      const width=box.clientWidth*(mini ? .89 : .96);
      let worldWidth=window.gameRender?.options.width||360;
      if(!mini && typeof window.expandMergeWorld==='function'){
        const requiredWidth=width*(330-deadlineY)/(box.clientHeight*.98-targetY);
        worldWidth=window.expandMergeWorld(Math.max(360,requiredWidth));
      }
      // Both views render the same world. Mini changes only its display scale.
      app.style.setProperty('--mini-merge-aspect',worldWidth/360);
      const height=width*330/worldWidth;
      app.style.setProperty('--merge-width',width+'px');
      app.style.setProperty('--merge-height',height+'px');
      app.style.setProperty('--merge-left',(box.clientWidth-width)/2+'px');
      app.style.setProperty('--merge-top',(targetY-deadlineY*width/worldWidth)+'px');
      if(typeof window.syncDeadlineVisual==='function')window.syncDeadlineVisual();
      if(typeof updatePreview==='function')updatePreview();
    });
  }
  function updateQuickSound(){
    const el=$('quick-sound');if(!el)return;
    const on=typeof gameSettings!=='undefined'&&gameSettings.masterVolume>0;
    el.innerHTML=icon(on?'Volume2':'VolumeX');el.setAttribute('aria-label',on?'전체 소리 끄기':'전체 소리 켜기');el.setAttribute('aria-pressed',String(on));
  }
  function toggleSound(){
    if(typeof gameSettings==='undefined')return;
    gameSettings.masterVolume=gameSettings.masterVolume>0?0:70;
    unlockGameAudio();saveGameSettings();applyGameSettings();updateQuickSound();
  }
  function stageCaption(){
    const meta=typeof BACKGROUND_META!=='undefined'?BACKGROUND_META.battle?.[bgConfig.battle]:null;
    const cap=$('stage-caption');if(cap){cap.querySelector('b').textContent=meta?.name||'새벽의 하늘항';cap.querySelector('span').textContent=['SKY HARBOR','LUMINOUS FOREST','MOONLIT RUINS','GOLDEN PALACE'][(bgConfig?.battle||1)-1]||'ADVENTURE';}
  }
  function setPanorama(src){
    const layer=$('battle-panorama');if(!layer)return;
    layer.querySelectorAll('img').forEach(img=>{if(img.getAttribute('src')!==src)img.src=src;});
  }
  function annotateImages(root) {
    if(!ready||!root.querySelectorAll)return;
    root.querySelectorAll('img:not([data-art-named])').forEach(img=>{
      const src=img.getAttribute('src');if(!src?.startsWith('assets/art/'))return;
      const all=[...Object.values(CHARACTER_META),...Object.values(BATTLE_CHARACTER_META),...Object.values(BEAD_META_BY_PATH),...Object.values(BACKGROUND_META.lobby),...Object.values(BACKGROUND_META.battle),...Object.values(BACKGROUND_META.merge)];
      const meta=all.find(m=>m.path===src||m.idle===src);if(!meta)return;
      // 이름은 번역 사전을 거친다 (구슬 스킨·배경은 다른 언어에서 종류 이름으로). 카드가 이미 자기 title을 가지면 덮어쓰지 않는다
      const name=(window.MRLocale?.t?.(meta.name||'')||meta.name||'');
      img.dataset.artNamed='true';img.alt=name;img.draggable=false;
      const card=img.closest('.inv-item,.char-item-btn,.economy-item');if(card&&!card.getAttribute('title'))card.title=`${meta.name} · ${meta.tier}`;
    });
  }
  function initialize(){
    $('quick-sound').innerHTML=icon('Volume2');
    $('quick-mini-merge').innerHTML=icon('Circle')+'<span class="shortcut-label">머지</span>';
    $('quick-mini-battle').innerHTML=icon('Swords')+'<span class="shortcut-label">전투</span>';
    if($('quick-mini-room'))$('quick-mini-room').innerHTML=icon('House')+'<span class="shortcut-label">마이룸</span>';
    const navIcons={shop:'ShoppingBag',collection:'Layers',battle:'Swords',social:'Users',menu:'Menu'};
    Object.entries(navIcons).forEach(([id,name])=>{
      const el=$('nav-'+id);if(!el)return;el.querySelector('.icon').innerHTML=icon(name);el.setAttribute('role','button');el.tabIndex=0;
      el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();el.click();}});
    });
    polishIcons($('app'));
    observer=new MutationObserver(records=>{
      const roots=new Set();
      for(const rec of records){
        const el=rec.target.nodeType===1?rec.target:rec.target.parentElement;
        if(el&&!el.closest('svg,.ui-icon'))roots.add(el);
      }
      for(const root of roots){polishIcons(root);annotateImages(root);}
    });
    observer.observe($('app'),{childList:true,characterData:true,subtree:true});
    window.addEventListener('resize',fit);
    if(window.ResizeObserver)new ResizeObserver(fit).observe($('merge-box'));
    document.addEventListener('click',()=>{fit();if(ready){stageCaption();updateQuickSound();}});
    // Native-only switches are still wired when the original desktop bridge is supplied.
    if(!window.desktopBridge&&!window.electronAPI&&!window.mergeRollBridge){
      ['setting-always-top','setting-remember-pos','setting-snap'].forEach(id=>{
        const el=$(id);if(el){el.disabled=true;el.title='데스크톱 앱에서 사용할 수 있습니다.';el.closest('.setting-row')?.classList.add('native-only');}
      });
    }
    $('btn-test-unlock-all').setAttribute('aria-label','모든 아트 미리보기 모드');
    $('btn-test-unlock-all').title='아트 감상용 임시 해금 · 수집 기록에는 저장되지 않습니다.';
    fit();
  }
  function gameReady(){ready=true;annotateImages($('app'));stageCaption();updateQuickSound();fit();}
  return {icon,initialize,ready:gameReady,fit,deadlineY,preloadBeads,preloadBattleRuns,beginSmile,updateSmile,mergeBurst,setEnemy,hitMarkup,skillCutscene,clearCutscene,toggleSound,syncMusic,setPanorama};
})();
