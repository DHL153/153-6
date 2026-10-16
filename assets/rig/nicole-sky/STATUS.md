# 니콜 스카이 (nicole-sky, 28번) — v3 완성 (2026-10-16)
검수: 팀원 audit 위반 0 · 동작 밖 튐 0 · 발 미끄러짐 0.83 / 추가 검사(tools/audit_extra.py) 허리 이음매 0~4px · 두 손 자루 위 매 프레임 · 팔꿈치 방향 유지 · 치마 메시 접힘 0 / 반응 5종(hop·nod·surprise·cute·cute2) 손 놓침 0.
구조: 창 먼저(spearGrip) → 두 손이 자루를 따라 미끄러지며 시트 그림 그대로 쥠. 앞손 F 3각도, 뒷손 N 3각도 + 윗팔 armU3, 찌른 순간 뒷팔 TH 한 장. 상체 T(벨트 아래 늘림)는 치마 밑, 주머니는 치마 위. 치마 윗단 상체 따라 기울기(skirtFollow), 밑단 들림 한계(hemLimit). 다리 L 시트 실측(허벅지 111·정강이 122). 치마 오른쪽 자락은 원본대로 두고, 허리 오른쪽 모서리만 벨트 끝에서 시작하도록 안으로 모음(source/cut_skirt.py, 2026-10-17).
다시 만들기: source/ 에서 python3 -I build_sky_v3.py && python3 -I apply_v3.py  (v2 원본: source/rig_v2.json, source/parts_v2/)
시트: source/sheets_v3/ (N·F·TH·T·L, 2026-10-16 DHL 제작)
