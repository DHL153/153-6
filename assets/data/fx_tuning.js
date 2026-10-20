// 이펙트 조절 값 — '이펙트 조절실' 아티팩트에서 맞춘 값을 이 파일로 PR 함 (게임 코드는 이 값만 읽음)
// alphaCurve = 진하기 커브 [[진행 0~1, 배율],…] · colorCurve = 색 커브 [[진행 0~1, "#색", 세기 0~1],…] (null = 안 씀)
// chars = 캐릭터별(전투 캐릭터 번호 1~30) trail·hit 값 — 적힌 값만 공통 값을 덮음 · custom[].chars = 그 캐릭터들만
// custom[] 플립북: cols×rows 시트, frameStart~frameEnd, fps(0 = len 에 맞춤)·loops·pingpong, blend "screen"(검은 배경 지움) | "normal"(투명 PNG 그대로)
// ms = 1/1000초, size = 기본 크기 배율, x·y = 캐릭터 그림 안 위치(0~1)
window.MR_FX_TUNING={
 "version":1,
 "trail":{"lead":-95,"len":190,"imgDelay":60,"size":1.5,"opacity":1,"x":0.58,"y":0.52,"cw":true,"frameStart":3,"frameEnd":22,"rotStart":0,"spin":0,"alphaCurve":null,"colorCurve":null},
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
 "custom":[]
};
