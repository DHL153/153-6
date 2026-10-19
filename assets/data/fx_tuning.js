// 이펙트 조절 값 — '이펙트 조절실' 아티팩트에서 맞춘 값을 이 파일로 PR 함 (게임 코드는 이 값만 읽음)
// ms = 1/1000초, size = 기본 크기 배율, x·y = 캐릭터 그림 안 위치(0~1)
window.MR_FX_TUNING={
 "version":1,
 "trail":{"lead":-95,"len":190,"imgDelay":60,"size":1.5,"opacity":1,"x":0.58,"y":0.52,"cw":true,"frameStart":3,"frameEnd":22},
 "hit":{"offset":0,"len":300,"size":1.5,"opacity":1,"spin":true,"syncRig":true},
 "lightning":{"start":0.18,"span":0.52,"opacity":0.94},
 "mergeRing":{"playMs":125,"fadeMs":125,"cell":1.8,"rCell":2.0,"peak":9,"rPeak":7},
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
 "custom":[]
};
