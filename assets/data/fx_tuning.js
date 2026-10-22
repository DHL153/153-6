// 이펙트 조절 값 — '이펙트 조절실' 아티팩트에서 맞춘 값을 이 파일로 PR 함 (게임 코드는 이 값만 읽음)
// alphaCurve = 진하기 커브 [[진행 0~1, 배율],…] · sizeCurve = 크기 커브 [[진행 0~1, 배율],…] · colorCurve = 색 커브 [[진행 0~1, "#색", 세기 0~1],…] (null = 안 씀)
// chars = 캐릭터별(전투 캐릭터 번호 1~30) trail·hit 값 — 적힌 값만 공통 값을 덮음 · custom[].chars = 그 캐릭터들만
// custom[] 플립북: cols×rows 시트, frameStart~frameEnd, fps(0 = len 에 맞춤)·loops·pingpong, blend "screen"(검은 배경 지움) | "normal"(투명 PNG 그대로)
// ms = 1/1000초, size = 기본 크기 배율, x·y = 캐릭터 그림 안 위치(0~1)
// off = true 면 그 이펙트를 안 그림(그림 파일·값은 그대로) — trail.off: 2026-10-22 DHL 흰 칼 트레일을 전투에서 뺌
window.MR_FX_TUNING={
 "version":1,
 "trail":{"off":true,"lead":-60,"len":300,"imgDelay":60,"size":2.25,"opacity":1,"x":0.73,"y":0.53,"cw":true,"frameStart":3,"frameEnd":22,"rotStart":-105,"spin":0,"alphaCurve":[[0,0],[0.211,1],[0.833,1],[1,0]],"colorCurve":null},
 "hit":{"offset":0,"len":300,"size":1.5,"opacity":1,"spin":true,"syncRig":true,"alphaCurve":null,"colorCurve":null},
 "lightning":{"start":0.18,"span":0.52,"opacity":0.94,"alphaCurve":null,"colorCurve":null},
 "mergeRing":{"playMs":125,"fadeMs":125,"cell":1.8,"rCell":2.0,"peak":9,"rPeak":7,"alphaCurve":null,"colorCurve":null},
 "swirl":{
  "weak":{"s0":0.62,"s1":0.22,"rot":300,"peak":0.38,"dur":750},
  "gustPeak":0.3,
  "combo":{"s0":0.11,"rot":40,"peak":0.07,"dur":60,"max":6,"window":1600},
  "boss":[
   {"layer":"thick","s0":1.25,"s1":0.12,"rot":720,"peak":1,"dur":1300,"delay":0},
   {"layer":"thin2","s0":1.6,"s1":0.4,"rot":420,"peak":0.75,"dur":1250,"delay":90},
   {"layer":"thin","s0":0.9,"s1":0.1,"rot":900,"peak":0.9,"dur":1100,"delay":180}
  ]
 },
 "chars":{},
 "custom":[
  {"name":"새 이펙트","src":"assets/art/effects/battle/fx_battle_attack_slash_blue_0001.png","trigger":"attack","anchor":"hero","chars":[],"cols":2,"rows":2,"frameStart":0,"frameEnd":3,"fps":15,"loops":1,"pingpong":false,"blend":"normal","at":-60,"len":90,"size":2.9,"opacity":1,"x":0.85,"y":0.15,"rotate":-140,"spin":195,"flipX":false,"fadeOut":0,"off":false,"alphaCurve":[[0,0],[0.172,1],[0.52,1],[0.642,0.146],[0.845,0],[1,0]],"sizeCurve":[[0,0],[0.13790714743750943,1],[1,1]]}
 ]
};
