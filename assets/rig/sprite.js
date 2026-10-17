/*  SpriteChar — 그림 넘기기(프레임 애니메이션) 캐릭터, 리그(CharacterRig/RunAnimator)와 같은 사용법 (2026-10-17, 알론소 '섞어 쓰기')
 *
 *  const sp = new SpriteChar(def, image);            // def = MR_SPRITE_DEFS['alonso'], image = def.image 그림
 *  sp.update(dt, { vx });                             // vx = 리그와 같은 단위(달리기 ≈ 620 리그 단위/초)
 *  sp.attack('smash');                                // 공격 (hit 이벤트는 sp.events 에)
 *  sp.draw(ctx, footX, footY, scale, facing);         // scale = 화면 px / 리그 단위 (리그와 같은 값을 그대로 넘김)
 *
 *  달리기: 땅이 움직인 거리만큼 그림을 넘김(한 바퀴 = def.anims.run.cycle 시트 px) → 발이 땅에서 미끄러지지 않음
 *  멈춤: 지금 달리던 그림을 끝까지 보여 주고 준비 자세로, 숨쉬기 그림이 없으면 몸 높이 1% 안쪽으로 살짝 늘었다 줄었다
 *  공격: 키마다 정해진 시간만큼, 타격 그림에서 멈칫(hitStop) + 흔들림(shake 이벤트), 땅은 리그처럼 공격 중 멈춤(busy)
 */
(function (global) {
  "use strict";
  const RIG_BODY = 753;   // 리그 bodyHeight 기준 — 같은 scale 로 그리면 리그 캐릭터와 같은 크기
  class SpriteChar {
    constructor(def, image) {
      this.def = def; this.image = image; this.k = RIG_BODY / def.bodyHeight;   // 시트 px → 리그 단위
      this.odo = 0; this.t = 0; this.act = null; this.events = []; this.facing = 1; this.breath = 0; this.moving = false; this.runF = 0; this.expr = null;
    }
    get busy() { return !!this.act }
    get facingScale() { return this.facing }
    setExpression(n) { this.expr = n }
    attack(name = "smash") {
      const A = this.def.anims[name]; if (!A || this.act) return false;
      this.act = { name, A, t: 0, i: 0, hit: false, stop: 0 }; return true;
    }
    update(dt, s = {}) {
      dt = Math.min(dt, .05); this.t += dt; this.events.length = 0;
      const vx = s.vx || 0; if (!this.act && Math.abs(vx) > 1) this.facing = Math.sign(vx);
      if (this.act) {
        const a = this.act;
        if (a.stop > 0) { a.stop -= dt; return }                         // 타격 멈칫: 시간이 멈춘 듯
        a.t += dt; let acc = 0, i = 0;
        for (; i < a.A.keys.length; i++) { acc += a.A.keys[i][1]; if (a.t < acc) break }
        if (i !== a.i) { a.i = i; if (i === a.A.hit && !a.hit) { a.hit = true; a.stop = a.A.hitStop || 0; this.events.push({ type: "hit" }); if (a.A.shake) this.events.push({ type: "shake", power: a.A.shake }) } }
        if (i >= a.A.keys.length) { this.act = null; this.runF = 0 }
        return;
      }
      const R = this.def.anims.run, sp = Math.abs(vx) / this.k;              // 시트 px/초
      this.moving = sp > 10;
      // 그림 넘김 속도: 기준 속도(refSpeed)에서 fps장/초, 속도에 비례 — 시트의 보폭이 SD 비율이라 땅 거리로만 넘기면 너무 느려(약 5장/초) 뚝뚝 끊김
      if (this.moving) { this.odo += (R.fps || 12) * (Math.abs(vx) / (R.refSpeed || 620)) * dt; this.runF = Math.floor(this.odo) % R.frames.length }
      else { this.odo = 0; this.breath += dt }
    }
    frame() {
      const D = this.def, a = this.act;
      if (a) { const k = a.A.keys[Math.min(a.i, a.A.keys.length - 1)]; return { f: D.frames[k[0]], dx: (a.A.lunge || [])[a.i] || 0 } }
      if (this.moving) return { f: D.frames[D.anims.run.frames[this.runF]], dx: 0 };
      return { f: D.frames[D.anims.ready.frames[0]], dx: 0, breath: true };
    }
    draw(ctx, x, y, scale, facing = this.facing) {
      const { f, dx, breath } = this.frame(), s = scale * this.k;
      const by = breath ? 1 + Math.sin(this.breath * Math.PI * 2 / 2.6) * .008 : 1;   // 숨쉬기 그림이 오기 전 임시: 몸 높이 0.8% 안쪽
      ctx.save(); ctx.setTransform(s * facing, 0, 0, s * by, x, y);
      ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = "high";
      ctx.drawImage(this.image, f.x, f.y, f.w, f.h, -f.ax + dx, -f.ay, f.w, f.h);
      ctx.restore();
    }
  }
  global.SpriteChar = SpriteChar;
})(typeof window !== "undefined" ? window : globalThis);
