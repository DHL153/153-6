/*  CharacterRig + RunAnimator v4 — cut-out 2D rig for a side-scroller (no dependencies, Canvas2D).
 *
 *  const rig  = await CharacterRig.load("rig.json");   // loads parts/*.png next to rig.json
 *  const anim = new RunAnimator(rig);
 *  // every frame (dt in seconds):
 *  anim.update(dt, { vx });                             // vx = horizontal speed in rig units/s (full run ≈ 620)
 *  rig.draw(ctx, footX, footY, scale, anim.facingScale);
 *
 *  Gait model (per stride = two steps):
 *   - each foot: stance 36% (planted and locked to the ground → no foot-skate, also while speeding up / slowing down),
 *     swing 64% (toe-off → heel kicks up behind → knee drives forward with foot tucked → shin reaches → heel strike)
 *   - both feet are off the ground twice per stride (flight phase) → that is what makes it a run, not a walk
 *   - when the input stops, the airborne foot finishes its step and the trailing foot takes one small recovery step
 *   - pelvis lowest just after each contact, highest in flight; legs solved with 2-bone IK (hip-knee-ankle)
 *   - near arm swings opposite to the near leg with the elbow bent ~85°, hand closes into a fist while running;
 *     shoulder guard rides on the upper arm; the spear is locked inside the far fist (fist + shaft share one bone)
 *   - skirt hem is pushed by the knees / lifted by the kicking heel; cape, skirt, braid lag on springs
 */
(function (global) {
  "use strict";
  const TAU = Math.PI * 2, clamp = (v, a, b) => (v < a ? a : v > b ? b : v), lerp = (a, b, t) => a + (b - a) * t;
  const damp = (a, b, k, dt) => a + (b - a) * (1 - Math.exp(-k * dt));
  const wrapA = a => Math.atan2(Math.sin(a), Math.cos(a));
  const smooth = (e0, e1, x) => { const t = clamp((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t) };
  const mul = (m, n) => [m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1], m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3], m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5]];
  const apply = (m, x, y) => [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]];
  const rotT = (x, y, a) => { const c = Math.cos(a), s = Math.sin(a); return [c, s, -s, c, x, y] };
  const set = (ctx, M) => ctx.setTransform(M[0], M[1], M[2], M[3], M[4], M[5]);

  class CharacterRig {
    constructor(def, images) {
      this.def = def; this.images = images;
      this.bones = def.bones.map(b => ({ ...b, rot: b.rot || 0, ax: 0, ay: 0, ar: 0, asx: 1, asy: 1, m: [1, 0, 0, 1, 0, 0] }));
      this.by = {}; for (const b of this.bones) this.by[b.name] = b;
      this.meshFx = {}; this.legPose = null; this.blink = 0; this.debug = false; this.swap = {};
      this.alpha = {}; for (const n of def.hidden || []) this.alpha[n] = 0;   // per-bone opacity (0 = not drawn)
      this.face = {};                                                       // expression name → weight 0..1 (drawn over the head)
      this.hemProfile = this._profile(images.skirt);
    }
    // lowest opaque pixel of the skirt image in each of 32 columns → the real hem curve (legs only show below it)
    _profile(img) {
      if (!img) return null; const N = 32, c = document.createElement("canvas"); c.width = img.width; c.height = img.height;
      const g = c.getContext("2d"); g.drawImage(img, 0, 0); const d = g.getImageData(0, 0, c.width, c.height).data, out = [];
      for (let i = 0; i <= N; i++) { const x = Math.min(c.width - 1, Math.round(i / N * (c.width - 1))); let y = -1;
        for (let yy = c.height - 1; yy >= 0; yy--) if (d[(yy * c.width + x) * 4 + 3] > 128) { y = yy; break }
        if (y >= 0) out.push([i / N, x, y]) }
      return out;
    }
    _hemPath(ctx, base) { // device-space clip: everything below the (deformed) hem line
      const b = this.by.skirt, part = this.def.parts.skirt, img = this.images.skirt; if (!b || !img || !this.hemProfile) return false;
      const k = part.scale || 1, [px, py] = part.pivot, fx = this.meshFx.skirt, M = mul(base, b.m), pts = [];
      for (const [u, x, y] of this.hemProfile) { const o = fx ? fx(u, y / img.height, (x - px) * k, (y - py) * k) : [0, 0]; pts.push(apply(M, (x - px) * k + o[0], (y - py) * k + o[1] - 6)) }
      if (pts.length < 2) return false; const big = 1e5, L = pts[0], R = pts[pts.length - 1], dir = Math.sign(M[0]) || 1;
      if (this.def.hemOpenSides) {   // 짧은 치마(알론소 v4): 치마 폭 바깥에서는 다리를 높이와 상관없이 그림 (뒤로 찬 다리가 밑단 높이에서 평평하게 잘리지 않게)
        ctx.beginPath(); ctx.moveTo(L[0], L[1] - big); ctx.lineTo(L[0], L[1]); for (const p of pts) ctx.lineTo(p[0], p[1]);
        ctx.lineTo(R[0], R[1] - big); ctx.lineTo(R[0] + big * dir, R[1] - big); ctx.lineTo(R[0] + big * dir, R[1] + big); ctx.lineTo(L[0] - big * dir, L[1] + big); ctx.lineTo(L[0] - big * dir, L[1] - big); ctx.closePath(); return true }
      ctx.beginPath(); ctx.moveTo(L[0] - big * dir, L[1]); for (const p of pts) ctx.lineTo(p[0], p[1]);
      ctx.lineTo(R[0] + big * dir, R[1]); ctx.lineTo(R[0] + big * dir, R[1] + big); ctx.lineTo(L[0] - big * dir, L[1] + big); ctx.closePath(); return true;
    }
    static async load(url) {
      const def = await (await fetch(url)).json(), base = url.replace(/[^/]*$/, ""), images = {};
      await Promise.all(Object.entries(def.parts).map(([k, p]) => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(images[k] = im); im.onerror = rej; im.src = base + p.src + (def.version ? "?v=" + def.version : "") })));
      return new CharacterRig(def, images);
    }
    resetPose() { for (const b of this.bones) { b.ax = b.ay = b.ar = b.oy = 0; b.asx = b.asy = 1; b.wm = null } }
    compute() {
      for (const b of this.bones) {
        const c = Math.cos(b.rot + b.ar), s = Math.sin(b.rot + b.ar);
        const ox = b.oy ? -s * b.oy : 0, oy = b.oy ? c * b.oy : 0;   // b.oy = slide along the bone's own axis
        const local = [c * b.asx, s * b.asx, -s * b.asy, c * b.asy, b.pos[0] + b.ax + ox, b.pos[1] + b.ay + oy];
        b.m = b.wm ? b.wm : b.parent ? mul(this.by[b.parent].m, local) : local;   // wm = explicit root-space matrix (foreshortened limbs)
      }
    }
    /** world (root-space) position of a point given in a bone's local rig units */
    point(bone, x = 0, y = 0) { return apply(this.by[bone].m, x, y) }
    /** root-space position of a pixel of a part image (uses the part's pivot/scale on its bone) */
    partPoint(bone, px, py) { const b = this.by[bone], p = this.def.parts[this.swap[bone] || b.part], k = p.scale || 1; return apply(b.m, (px - p.pivot[0]) * k, (py - p.pivot[1]) * k) }
    draw(ctx, x, y, scale, facing = 1) {
      this.compute();
      const base = [scale * facing, 0, 0, scale, x, y];
      ctx.save(); ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = "high";
      for (const name of this.drawOrder || this.def.draw) {
        if (name === "legFar" || name === "legNear") { ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); if (this._hemPath(ctx, base)) ctx.clip();
          this._drawLeg(ctx, mul(base, this.by.root.m), name === "legNear" ? "near" : "far"); ctx.restore(); continue }
        // overlay = part of a bone's image drawn again on top (e.g. a sleeve cuff over the forearm that comes out of it)
        const ov = this.def.overlays && this.def.overlays[name];
        if (ov) { const ob = this.by[ov.bone], opn = this.swap[ov.bone] || ob.part, op_ = this.def.parts[opn], oimg = this.images[opn], oa = (this.alpha[ov.bone] ?? 1) * (this.alpha[name] ?? 1);
          if (oimg && oa > .003) { const k = op_.scale || 1, M = mul(mul(base, ob.m), [k, 0, 0, k, 0, 0]); ctx.save(); set(ctx, M); const [rx, ry, rw, rh] = ov.rect;
            ctx.beginPath(); ctx.rect(rx - op_.pivot[0], ry - op_.pivot[1], rw, rh); ctx.clip(); ctx.globalAlpha = oa; ctx.drawImage(oimg, -op_.pivot[0], -op_.pivot[1]); ctx.restore() }
          continue }
        // headFront (opt-in, 알론소 v4): 머리 그림의 얼굴·귀·앞머리 부분만 한 번 더 그림(def.headFront.clip = 머리 그림 px 다각형)
        //   → 칼은 뒷머리 위로 지나가고, 손잡이는 얼굴·귀 뒤로 숨음(키 포즈와 같은 겹침). 표정 패치·깜빡임도 같이 그림
        if (name === "headFront" || name.startsWith("headFront_")) { const hf = this.def[name], hb = this.by.head;   // headFront_* (opt-in): 다른 클립 다각형(예: 얼굴만) if (!hf || !hb) continue;
          const hpn = this.swap.head || hb.part, hp = this.def.parts[hpn], him = this.images[hpn], hop = this.alpha.head ?? 1; if (!him || hop <= .003) continue;
          const hk = hp.scale || 1, HM = mul(base, hb.m); ctx.save(); set(ctx, mul(HM, [hk, 0, 0, hk, 0, 0])); ctx.beginPath();
          hf.clip.forEach(([cx, cy], i) => i ? ctx.lineTo(cx - hp.pivot[0], cy - hp.pivot[1]) : ctx.moveTo(cx - hp.pivot[0], cy - hp.pivot[1])); ctx.closePath(); ctx.clip();
          ctx.globalAlpha = hop; ctx.drawImage(him, -hp.pivot[0], -hp.pivot[1]); ctx.globalAlpha = 1;
          if (this.def.faces && !hf.facesFree) this._drawFaces(ctx, HM);
          if (this.def.blinkFaces && this.blink > .15) { const bf = this.def.blinkFaces, n2 = this.blink > .7 ? bf.closed : bf.half, q2 = this.def.parts[n2], m2 = this.images[n2];
            if (m2) { const k2 = q2.scale || 1; set(ctx, mul(HM, [k2, 0, 0, k2, 0, 0])); ctx.drawImage(m2, -q2.pivot[0], -q2.pivot[1]) } }
          ctx.restore();
          if (this.def.faces && hf.facesFree) { ctx.save(); this._drawFaces(ctx, HM); ctx.restore() }   // facesFree (opt-in, 6 카르덴): 표정 패치는 클립 밖까지(입이 수염 속) — 클립은 코만
          continue }
        const b = this.by[name], pn = this.swap[name] || b.part, part = this.def.parts[pn], img = this.images[pn]; if (!img) continue;
        const op = this.alpha[name] ?? 1; if (op <= .003) continue; ctx.globalAlpha = op;
        const k = part.scale || 1, M = mul(mul(base, b.m), [k, 0, 0, k, 0, 0]);
        if (part.mesh) this._drawMesh(ctx, M, img, part, this.meshFx[pn]);
        else { set(ctx, M); ctx.drawImage(img, -part.pivot[0], -part.pivot[1]) }
        ctx.globalAlpha = 1;
        if (name === "head" && this.def.faces && !(this.def.headFront && this.def.headFront.facesFree)) this._drawFaces(ctx, mul(base, b.m));
        if (this.def.blinkFaces && name === "head" && this.blink > .15) {   // 그린 깜빡임 얼굴 (반쯤 → 감음 → 반쯤)
          const bf = this.def.blinkFaces, pn2 = this.blink > .7 ? bf.closed : bf.half, p2 = this.def.parts[pn2], im2 = this.images[pn2];
          if (im2) { const k2 = p2.scale || 1; set(ctx, mul(mul(base, b.m), [k2, 0, 0, k2, 0, 0])); ctx.drawImage(im2, -p2.pivot[0], -p2.pivot[1]) } }
        else if (this.def.blink && name === this.def.blink.bone && this.blink > 0) { set(ctx, M); this._drawBlink(ctx, part.pivot[0], part.pivot[1]) }
        if (name === "weapon" && this.trail && this.drawTrail) this._drawTrail(ctx, base);   // off by default: effects are made by the game
      }
      if (this.debug) this._drawDebug(ctx, base);
      ctx.restore();
    }
    // expression = face-only patch (eyes, brows, mouth) laid over the base head; several can cross-fade
    _drawFaces(ctx, HM) {
      for (const n in this.face) { const w = this.face[n]; if (w <= .003) continue;
        const pn = this.def.faces[n], p = this.def.parts[pn], img = this.images[pn]; if (!img) continue;
        const k = p.scale || 1, M = mul(HM, [k, 0, 0, k, 0, 0]); set(ctx, M); ctx.globalAlpha = Math.min(1, w); ctx.drawImage(img, -p.pivot[0], -p.pivot[1]) }
      ctx.globalAlpha = 1;
    }
    // speed streak behind each prong tip (root-space history points, newest last)
    _drawTrail(ctx, base) {
      const T = this.trail; if (!T || T.a <= .01) return; set(ctx, base);
      for (const pts of T.pts) { const n = pts.length; if (n < 2) continue;
        for (let i = 1; i < n; i++) { const p = pts[i - 1], q = pts[i], k0 = (i - 1) / (n - 1), k1 = i / (n - 1), dx = q[0] - p[0], dy = q[1] - p[1], l = Math.hypot(dx, dy) || 1, nx = -dy / l, ny = dx / l, w0 = 2 + 9 * k0, w1 = 2 + 9 * k1;
          ctx.globalAlpha = T.a * .5 * k1; ctx.fillStyle = "#FFF1DC"; ctx.beginPath();
          ctx.moveTo(p[0] + nx * w0, p[1] + ny * w0); ctx.lineTo(q[0] + nx * w1, q[1] + ny * w1); ctx.lineTo(q[0] - nx * w1, q[1] - ny * w1); ctx.lineTo(p[0] - nx * w0, p[1] - ny * w0); ctx.closePath(); ctx.fill() } }
      ctx.globalAlpha = 1;
    }
    // map an image segment (joint a → joint b, in image px) onto a world segment (P → Q); w = thickness factor
    _seg(R, a, b, P, Q, w) {
      const ia = Math.atan2(b[1] - a[1], b[0] - a[0]), il = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const wa = Math.atan2(Q[1] - P[1], Q[0] - P[0]), wl = Math.hypot(Q[0] - P[0], Q[1] - P[1]), s = wl / il;
      let M = mul(R, rotT(P[0], P[1], wa)); M = mul(M, [s, 0, 0, s * w, 0, 0]); M = mul(M, rotT(0, 0, -ia)); return mul(M, [1, 0, 0, 1, -a[0], -a[1]]);
    }
    // ---- legs: boot, shin (enters the boot behind its front rim), thigh — all hidden under the skirt except below the hem
    _drawLeg(ctx, R, side) {
      const L = this.def.legs, P = this.legPose && this.legPose[side]; if (!L || !P) return;
      const S = L[side], dark = S.shade || 0, useF = dark && "filter" in ctx;
      if (useF) ctx.filter = `brightness(${1 - dark})`;
      const bd = L.boot, bp = this.def.parts[bd.part], kb = bp.scale || 1;
      const Bk = mul(mul(R, rotT(P.ankle[0], P.ankle[1], P.foot)), [kb, 0, 0, kb, 0, 0]);
      const boot = (n) => { const p = this.def.parts[n], im = this.images[n]; if (im) { set(ctx, Bk); ctx.drawImage(im, -p.pivot[0], -p.pivot[1]) } };
      // boot inside/back rim → shin (enters the opening) → boot front (its rim line overlaps the shin) → thigh
      // legs.thighFirst (opt-in, 알론소 v4): 허벅지를 먼저 → 무릎 보호대가 붙은 정강이 그림이 무릎 위를 덮음
      // S.thighImg / S.shinImg (opt-in): 가까운·먼 다리에 다른 그림. L.kneeImg / S.kneeImg (opt-in): 무릎 덮개(보호대)를 무릎 위에 따로 — 허벅지·정강이 가운데 각도
      if (L.tube) {   // legs.tube (opt-in, 6 카르덴 10-18): 다리 = 엉덩이→발목 곧은 바지 통 하나(무릎에서 꺾이지 않음, 굵기 고정) + 부츠 — 바지가 몸처럼 고정인 캐릭터에서 무릎이 바지 밖으로 튀어나와 '떨어진 다리'로 보이던 것
        const T_ = L.tube, im_ = this.images[T_.part], il_ = Math.hypot(T_.b[0] - T_.a[0], T_.b[1] - T_.a[1]), wl_ = Math.hypot(P.ankle[0] - P.hip[0], P.ankle[1] - P.hip[1]) || 1;
        set(ctx, this._seg(R, T_.a, T_.b, P.hip, P.ankle, (T_.k || 1) * il_ / wl_)); ctx.drawImage(im_, 0, 0); boot(bd.part);
        if (useF) ctx.filter = "none"; return }
      const th = S.thighImg || L.thighImg, thigh = () => { set(ctx, this._seg(R, th.a, th.b, P.hip, P.knee, th.w)); ctx.drawImage(this.images[th.part], 0, 0) };
      if (L.thighFirst) thigh();
      if (bd.back) boot(bd.back);
      const sh = S.shinImg || L.shinImg; set(ctx, this._seg(R, sh.a, sh.b, P.knee, P.ankle, sh.w)); ctx.drawImage(this.images[sh.part], 0, 0);
      boot(bd.part);
      if (!L.thighFirst) thigh();
      const kc = S.kneeImg || L.kneeImg;
      if (kc && this.images[kc.part]) {
        const at = Math.atan2(P.knee[1] - P.hip[1], P.knee[0] - P.hip[0]), as = Math.atan2(P.ankle[1] - P.knee[1], P.ankle[0] - P.knee[0]);
        const am = at + wrapA(as - at) * (kc.mix ?? .5) - Math.PI / 2 + (kc.rot || 0), kp = this.def.parts[kc.part], k = kp.scale || 1;
        set(ctx, mul(mul(R, rotT(P.knee[0] + (kc.dx || 0), P.knee[1] + (kc.dy || 0), am)), [k, 0, 0, k, 0, 0])); ctx.drawImage(this.images[kc.part], -kp.pivot[0], -kp.pivot[1]);
      }
      if (useF) ctx.filter = "none";
    }
    // ---- textured triangle mesh: every grid cell = 2 triangles, each drawn with its own affine map (no strip seams)
    _drawMesh(ctx, M, img, part, fx) {
      const { cols, rows } = part.mesh, W = img.width, H = img.height, [px, py] = part.pivot, k = part.scale || 1, n = cols + 1;
      const sx = new Float32Array(n * (rows + 1)), sy = new Float32Array(sx.length), dx = new Float32Array(sx.length), dy = new Float32Array(sx.length);
      for (let j = 0; j <= rows; j++) for (let i = 0; i <= cols; i++) {
        const id = j * n + i, X = i / cols * W, Y = j / rows * H; sx[id] = X; sy[id] = Y;
        const o = fx ? fx(i / cols, j / rows, (X - px) * k, (Y - py) * k) : null;
        dx[id] = X - px + (o ? o[0] / k : 0); dy[id] = Y - py + (o ? o[1] / k : 0);
      }
      for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
        const a = j * n + i, b = a + 1, c = a + n + 1, d = a + n;
        this._tri(ctx, M, img, sx, sy, dx, dy, a, b, c); this._tri(ctx, M, img, sx, sy, dx, dy, a, c, d);
      }
    }
    _tri(ctx, M, img, sx, sy, dx, dy, i0, i1, i2) {
      const s0x = sx[i0], s0y = sy[i0], s1x = sx[i1], s1y = sy[i1], s2x = sx[i2], s2y = sy[i2];
      let d0x = dx[i0], d0y = dy[i0], d1x = dx[i1], d1y = dy[i1], d2x = dx[i2], d2y = dy[i2];
      const den = (s1x - s0x) * (s2y - s0y) - (s2x - s0x) * (s1y - s0y); if (Math.abs(den) < 1e-6) return;
      const a = ((d1x - d0x) * (s2y - s0y) - (d2x - d0x) * (s1y - s0y)) / den, b = ((d1y - d0y) * (s2y - s0y) - (d2y - d0y) * (s1y - s0y)) / den;
      const c = ((d2x - d0x) * (s1x - s0x) - (d1x - d0x) * (s2x - s0x)) / den, d = ((d2y - d0y) * (s1x - s0x) - (d1y - d0y) * (s2x - s0x)) / den;
      const e = d0x - a * s0x - c * s0y, f = d0y - b * s0x - d * s0y;
      // grow the clip triangle ~1px so neighbouring triangles overlap (hides hairline seams)
      const cx = (d0x + d1x + d2x) / 3, cy = (d0y + d1y + d2y) / 3, g = (x, y) => { const l = Math.hypot(x - cx, y - cy) || 1; return [x + (x - cx) / l * 1.1, y + (y - cy) / l * 1.1] };
      [d0x, d0y] = g(d0x, d0y); [d1x, d1y] = g(d1x, d1y); [d2x, d2y] = g(d2x, d2y);
      ctx.save(); set(ctx, M);
      ctx.beginPath(); ctx.moveTo(d0x, d0y); ctx.lineTo(d1x, d1y); ctx.lineTo(d2x, d2y); ctx.closePath(); ctx.clip();
      ctx.transform(a, b, c, d, e, f);
      const x0 = Math.max(0, Math.floor(Math.min(s0x, s1x, s2x)) - 2), y0 = Math.max(0, Math.floor(Math.min(s0y, s1y, s2y)) - 2);
      const x1 = Math.min(img.width, Math.ceil(Math.max(s0x, s1x, s2x)) + 2), y1 = Math.min(img.height, Math.ceil(Math.max(s0y, s1y, s2y)) + 2);
      if (x1 > x0 && y1 > y0) ctx.drawImage(img, x0, y0, x1 - x0, y1 - y0, x0, y0, x1 - x0, y1 - y0);
      ctx.restore();
    }
    // eyelid: skin slides down over the eye (clipped to the eye shape), lash line rides on its lower edge
    _drawBlink(ctx, px, py) {
      const { skin, line, eyes } = this.def.blink, k = clamp(this.blink, 0, 1);
      for (const [ex, ey, rx, ry, lw] of eyes) {
        const cx = ex - px, cy = ey - py, top = cy - ry, lid = top + ry * 2 * k * .9;
        ctx.save(); ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, TAU); ctx.clip();
        ctx.fillStyle = skin; ctx.fillRect(cx - rx - 2, top - 2, rx * 2 + 4, lid - top + 2); ctx.restore();
        if (k > .25) { ctx.save(); ctx.strokeStyle = line; ctx.lineWidth = lw || 4; ctx.lineCap = "round"; ctx.globalAlpha = smooth(.25, .6, k);
          const w = rx * Math.sqrt(Math.max(0, 1 - Math.pow((lid - cy) / ry, 2))) + 1;
          ctx.beginPath(); ctx.moveTo(cx - w, lid - 1); ctx.quadraticCurveTo(cx, lid + 4 * k, cx + w, lid - 1); ctx.stroke(); ctx.restore() }
      }
    }
    _drawDebug(ctx, base) {
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.lineWidth = 2;
      const dot = (p, c) => { ctx.fillStyle = c; ctx.beginPath(); ctx.arc(p[0], p[1], 4, 0, TAU); ctx.fill() };
      for (const b of this.bones) { const p = apply(mul(base, b.m), 0, 0);
        if (b.parent) { const q = apply(mul(base, this.by[b.parent].m), 0, 0); ctx.strokeStyle = "rgba(62,224,176,.75)"; ctx.beginPath(); ctx.moveTo(q[0], q[1]); ctx.lineTo(p[0], p[1]); ctx.stroke() } dot(p, "#3EE0B0") }
      if (this.legPose) for (const s of ["far", "near"]) { const P = this.legPose[s], R = mul(base, this.by.root.m), h = apply(R, ...P.hip), kn = apply(R, ...P.knee), an = apply(R, ...P.ankle);
        ctx.strokeStyle = s === "near" ? "#FFB020" : "#C98A2A"; ctx.beginPath(); ctx.moveTo(h[0], h[1]); ctx.lineTo(kn[0], kn[1]); ctx.lineTo(an[0], an[1]); ctx.stroke(); dot(h, "#FFB020"); dot(kn, "#FFB020"); dot(an, "#FFB020") }
      const g = apply(base, 0, 0); ctx.strokeStyle = "rgba(255,255,255,.35)"; ctx.beginPath(); ctx.moveTo(g[0] - 400, g[1]); ctx.lineTo(g[0] + 400, g[1]); ctx.stroke();
    }
  }

  class Spring { constructor(k, c) { this.k = k; this.c = c; this.x = 0; this.v = 0 }
    step(target, dt) { const n = Math.max(1, Math.ceil(dt * 240)), h = dt / n; for (let i = 0; i < n; i++) { this.v += (this.k * (target - this.x) - this.c * this.v) * h; this.x += this.v * h } return this.x } }

  // Catmull-Rom through key points with explicit knot times (non-uniform keys), returns [x, y, angle]
  function pathAt(keys, u) {
    let i = 0; while (i < keys.length - 2 && u > keys[i + 1].t) i++;
    const k0 = keys[Math.max(0, i - 1)], k1 = keys[i], k2 = keys[i + 1], k3 = keys[Math.min(keys.length - 1, i + 2)];
    const t = clamp((u - k1.t) / (k2.t - k1.t), 0, 1), t2 = t * t, t3 = t2 * t;
    const cr = (p0, p1, p2, p3) => .5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3);
    return [cr(k0.x, k1.x, k2.x, k3.x), cr(k0.y, k1.y, k2.y, k3.y), cr(k0.a, k1.a, k2.a, k3.a)];
  }

  // ---------- actions: keyframe tracks [time s, value, ease-to-next]; all additive offsets except grip/angle (root space) ----------
  const EASE = { lin: t => t, io: t => t * t * (3 - 2 * t), o: t => 1 - (1 - t) * (1 - t), i: t => t * t, o3: t => 1 - Math.pow(1 - t, 3), o5: t => 1 - Math.pow(1 - t, 5),
    // "strike": 20 ms-ish ease-in ramp, then a hard ease-out → explosive, but joint speed never jumps from 0 to max in one frame
    s: t => { const r = .2, g = (t < r ? t * t / (2 * r) : t - r / 2) / (1 - r / 2); return 1 - Math.pow(1 - g, 3) } };
  function track(keys, t) {
    if (!keys) return 0; if (t <= keys[0][0]) return keys[0][1];
    for (let i = 0; i < keys.length - 1; i++) { const [t0, v0, e] = keys[i], [t1, v1] = keys[i + 1];
      if (t <= t1) return v0 + (v1 - v0) * (EASE[e || "io"])((t - t0) / Math.max(1e-6, t1 - t0)) }
    return keys[keys.length - 1][1];
  }
  /* thrust (찌르기) v2, 0.80 s — side view, character faces +x. Times are seconds from the button press.
     0.00–0.18 wind-up ("흡"): breathe in (shoulders rise), spear swings down to level and both hands draw it back to the hip,
               rear foot steps back to load the back leg, hips sink, chest turns away (far shoulder back, near shoulder forward)
     0.18–0.30 strike ("하앗!"): lead (far) foot lunges ~175 forward, hips drive forward/down, far shoulder drives through,
               arms extend → tip travels ~330 units; rear heel peels up
     0.30–0.42 impact: hit event at 0.30, the shaft kicks back a little and shudders, then settles
     0.42–0.80 recovery ("후"): exhale, spear pulls back and stands up, lead foot then rear foot step home, weight settles with a small dip */
  /* thrust (찌르기) v3, 0.80 s — side view, character faces +x. Key pose taken from a reference drawing:
     deep lunge with both knees bent, pelvis low, torso fairly upright and leaning into the target, both elbows down under the
     shaft, fists at chest height, shaft roughly level in front of the body.
     0.00–0.18 wind-up ("흡"): inhale, hands draw the spear back to the rear hip (tip a little up), rear foot steps back, hips sink
     0.18–0.30 strike ("하앗!"): lead foot lunges, pelvis drives forward and down, chest turns in, hands punch forward at chest height
     0.30–0.42 impact: hit event at 0.30, small kick-back and shudder
     0.42–0.80 recovery ("후"): exhale, spear stands back up, feet step home, weight settles */
  // gait feel. Defaults = the reference girl (light chibi run). Presets were audited (0 joint violations, no foot slide).
  const GAIT_DEFAULTS = { stance: .36, strideBase: 70, strideK: .2, hipBase: 8, bob: 13, lean: .2, leanBob: .025, waddle: 0, headBob: 0,
    armSwing: .62, armBias: .14, elbowRun: 1.42, kneeLift: 1, heelKick: 1, dropCap: 30 };
  const GAIT_PRESETS = {   // nimble 날렵 · heavy 무거움/뒤뚱 · bouncy 통통/경쾌 · sneak 살금살금 (sneak is for slow speeds ≤ 300)
    nimble: {"stance": 0.31, "strideBase": 78, "strideK": 0.21, "hipBase": 5, "bob": 10, "lean": 0.28, "armSwing": 0.68, "elbowRun": 1.5, "kneeLift": 1.12, "heelKick": 1.08, "dropCap": 46},
    heavy: {"stance": 0.44, "strideBase": 88, "strideK": 0.2, "hipBase": 14, "bob": 20, "lean": 0.08, "waddle": 0.07, "headBob": 4, "armSwing": 0.45, "elbowRun": 1.1, "kneeLift": 0.7, "heelKick": 0.55, "dropCap": 46},
    bouncy: {"stance": 0.34, "hipBase": 10, "bob": 22, "headBob": 6, "kneeLift": 1.15, "armSwing": 0.7, "dropCap": 46},
    sneak: {"stance": 0.52, "strideBase": 60, "strideK": 0.15, "hipBase": 22, "bob": 5, "lean": 0.32, "armSwing": 0.25, "kneeLift": 0.9, "heelKick": 0.6}
  };
  // steps per second = 2 · vx · stance / (strideBase + strideK · vx)
  const ACTIONS = {
    thrust: { dur: .80, hitAt: .30, cancelAt: .54,
      w:       [[0, 0, "o"], [.10, 1], [.58, 1, "io"], [.80, 0]],
      hipX:    [[0, 0, "io"], [.18, -26, "s"], [.30, 92], [.42, 88, "io"], [.70, 0]],
      hipY:    [[0, 0, "io"], [.18, 30, "s"], [.30, 64], [.42, 62, "io"], [.70, -2, "io"], [.75, 6, "io"], [.80, 0]],
      lean:    [[0, 0, "io"], [.18, -.10, "s"], [.30, .22], [.42, .20, "io"], [.70, 0]],
      head:    [[0, 0, "io"], [.18, .06, "s"], [.30, -.12], [.42, -.10, "io"], [.70, 0]],
      breath:  [[0, 0, "io"], [.16, 1, "o"], [.30, -.4, "io"], [.48, -.6, "io"], [.80, 0]],
      twist:   [[0, 0, "io"], [.18, -.7, "s"], [.30, .7], [.42, .6, "io"], [.70, 0]],
      // spear bone angle (0 = upright carry, π/2 = level, tip forward) and the lead upper-arm angle from straight down (+ = forward)
      ang:     [[0, .05, "io"], [.18, 1.00, "s"], [.30, 1.40, "o"], [.33, 1.36, "io"], [.42, 1.39, "io"], [.62, 1.2, "io"], [.79, .35]],
      thF:     [[0, .35, "io"], [.18, .22, "s"], [.30, .30, "o"], [.33, .26, "io"], [.42, .29, "io"], [.62, .30, "io"], [.79, .35]],
      nearW:   [[0, 0, "io"], [.17, 1], [.54, 1, "io"], [.70, 0]],
      gap:     [[0, 170, "io"], [.18, 165, "io"], [.30, 170, "io"], [.60, 170]],          // preferred distance rear fist → lead fist
      farDx:   [[0, 0, "io"], [.18, 0, "s"], [.30, 190], [.46, 190, "io"], [.64, 0]],
      farLift: [[0, 0], [.18, 0, "io"], [.24, 32, "io"], [.30, 0], [.46, 0, "io"], [.55, 24, "io"], [.64, 0]],
      farAng:  [[0, 0], [.21, 0, "io"], [.27, -.24, "io"], [.33, 0]],
      nearDx:  [[0, 0, "io"], [.03, 0, "io"], [.15, -45], [.62, -45, "io"], [.76, 0]],
      nearLift:[[0, 0], [.03, 0, "io"], [.09, 16, "io"], [.15, 0], [.62, 0, "io"], [.69, 14, "io"], [.76, 0]],
      nearAng: [[0, 0], [.21, 0, "io"], [.31, .2], [.44, .18, "io"], [.60, 0]],
      trail:   [[0, 0], [.19, 0, "lin"], [.22, 1], [.34, 1, "lin"], [.41, 0]],
      shake:   [[0, 0], [.30, 0, "lin"], [.31, 1], [.42, 0]],
      face:    [[0, "effort"], [.19, "shout"], [.40, "focus"], [.62, "relaxed"], [.76, null]] },   // stays focused while still lunged; relaxes when the body starts to come back (L42)
    /* wave (안녕~ 손 흔들기), 1.90 s — triggered by a touch.
       0.00–0.12 the spear fades out (event "weaponHide"); the far arm lowers to hang relaxed at the side
       0.05–0.34 the far (spear) arm rises: elbow bent and low, forearm up-forward, open hand beside the chin, palm to the viewer
       0.34–1.40 three waves: the forearm swings ±15° about the elbow, the shoulder follows a little, the body bobs with each wave
       1.40–1.62 the arm comes down; 1.62–1.76 the spear fades back in (event "weaponShow") into the carry pose
       Feet stay planted. Face: happy (eyes closed in arcs, big smile). Works for any weapon because nothing is held while waving. */
    wave: { kind: "wave", dur: 1.90, cancelAt: 1.76, plant: true,
      w:       [[0, 0, "io"], [.34, 1, "o3"], [1.40, 1, "io"], [1.70, 0]],                // near arm raise
      wAmp:    [[0, 0], [.30, 0, "io"], [.46, 1], [1.28, 1, "io"], [1.46, 0]],           // waving amplitude
      weapon:  [[0, 1, "io"], [.12, 0], [1.62, 0, "io"], [1.76, 1]],                     // spear opacity
      hipY:    [[0, 0, "io"], [.10, 9, "io"], [.28, -3, "io"], [.45, 0], [1.62, 0, "io"], [1.72, 5, "io"], [1.9, 0]],
      lean:    [[0, 0, "io"], [.30, -.05], [1.45, -.05, "io"], [1.8, 0]],
      head:    [[0, 0, "io"], [.30, -.07], [1.45, -.07, "io"], [1.8, 0]],
      face:    [[0, null], [.05, "happy"], [1.80, null]] }
  };
  /* smash (위에서 내려찍기, 대검·두 손) 1.0 s — 알론소 키 포즈 3장 기준 (2026-10-16)
     0–.30 준비: 칼을 머리 위 뒤로, 뒷발에 체중 · .30–.42 내려침: 칼이 머리 위로 원을 그리며 앞 수평 · .42 hit
     .42–.75 끌림: 칼끝이 앞 아래로, 몸이 따라 숙여짐 · .75–1.0 회수.
     트랙: sa = 칼날 방향(화면 각도, 0 = 오른쪽·앞, π/2 = 아래; 시계 방향으로 증가), gx/gy = 손잡이 위치(골반 기준 리그 단위),
          sh = 뒷어깨를 앞쪽으로 당기는 양(몸이 옆으로 돌아 두 손이 손잡이에서 만남) */
  ACTIONS.smash = { kind: "smash", dur: 1.0, hitAt: .42, cancelAt: .8,
    w:     [[0, 0, "o"], [.14, 1], [.84, 1, "io"], [1.0, 0]],
    sa:    [[0, 2.64, "io"], [.30, 2.5, "i"], [.42, 6.28, "o"], [.55, 6.86, "io"], [.75, 6.9, "io"], [1.0, 8.92]],
    gx:    [[0, -188, "io"], [.30, -120, "s"], [.36, -20, "i"], [.42, 95, "o"], [.55, 75, "io"], [.75, 70, "io"], [1.0, -188]],
    gy:    [[0, -4, "io"], [.30, -470, "s"], [.36, -470, "i"], [.42, -175, "o"], [.55, -95, "io"], [.75, -90, "io"], [1.0, -4]],
    sh:    [[0, 0, "io"], [.22, 1], [.80, 1, "io"], [1.0, 0]],
    hipX:  [[0, 0, "io"], [.30, -22, "s"], [.42, 58], [.75, 52, "io"], [1.0, 0]],
    hipY:  [[0, 0, "io"], [.30, -8, "s"], [.42, 34], [.60, 46, "io"], [.80, 40, "io"], [1.0, 0]],
    lean:  [[0, 0, "io"], [.30, -.14, "s"], [.42, .22], [.62, .30, "io"], [.80, .26, "io"], [1.0, 0]],
    head:  [[0, 0, "io"], [.30, .08, "s"], [.42, -.10], [.70, -.12, "io"], [1.0, 0]],
    breath:[[0, 0, "io"], [.28, 1, "o"], [.42, -.5, "io"], [.70, -.3, "io"], [1.0, 0]],
    farDx: [[0, 0, "io"], [.30, 0, "s"], [.42, 120], [.80, 120, "io"], [.96, 0]],
    farLift:[[0, 0], [.30, 0, "io"], [.36, 28, "io"], [.42, 0], [.80, 0, "io"], [.88, 18, "io"], [.96, 0]],
    nearDx:[[0, 0, "io"], [.08, 0, "io"], [.22, -30], [.80, -30, "io"], [.96, 0]],
    nearLift:[[0, 0], [.08, 0, "io"], [.15, 14, "io"], [.22, 0], [.80, 0, "io"], [.88, 12, "io"], [.96, 0]],
    shake: [[0, 0], [.42, 0, "lin"], [.43, 1], [.56, 0]],
    face:  [[0, "effort"], [.36, "shout"], [.58, "focus"], [.86, null]] };
  const wAng = m => Math.atan2(m[1], m[0]);
  // two-bone IK in world space; returns both elbow solutions [lower, upper]
  function solve2(S, T, L1, L2) {
    let dx = T[0] - S[0], dy = T[1] - S[1], d0 = Math.hypot(dx, dy);
    // soft reach: the arm eases into full extension instead of hitting the acos singularity (no one-frame elbow snap)
    const Lm = (L1 + L2) * .985, ds = Lm * .9; if (d0 > ds) d0 = ds + (Lm - ds) * (1 - Math.exp(-(d0 - ds) / (Lm - ds)));
    const d = clamp(d0, Math.abs(L1 - L2) + 1e-3, (L1 + L2) * .999), base = Math.atan2(dy, dx);
    const al = Math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1));
    const e1 = [S[0] + Math.cos(base - al) * L1, S[1] + Math.sin(base - al) * L1], e2 = [S[0] + Math.cos(base + al) * L1, S[1] + Math.sin(base + al) * L1];
    return e1[1] > e2[1] ? [e1, e2] : [e2, e1];
  }

  class RunAnimator {
    constructor(rig, opts = {}) {
      this.rig = rig; this.runSpeed = opts.runSpeed || 620;
      // gait feel (all optional in rig.json "gait"; defaults = the reference girl). See references/05_tuning.md
      this.setGait(opts.gait);
      this.t = 0; this.cyc = 0; this.A = 0; this.prevLVx = 0; this.facing = 1; this.turnT = 0; this.blinkT = 1.4; this.blinkAt = -9; this.odo = 0;
      this.lean = new Spring(55, 11); this.cape = new Spring(34, 6.5); this.braid = new Spring(60, 7); this.pony = new Spring(38, 5); this.weapon = new Spring(90, 9); this.headLag = new Spring(140, 16);
      this.hem = Array.from({ length: (rig.def.parts.skirt?.mesh?.cols || 8) + 1 }, () => [new Spring(170, 13), new Spring(170, 13)]);
      this.prevHipY = 0; this.hipVy = 0; this.fist = false;
      this.act = null; this.events = []; this.trailPts = [[], []]; this.prevActX = 0; this.actV = 0;
      this.expr = null; this.faceW = {}; this.gripW = 0;
      const L = rig.def.legs; this.L = L; const bp = rig.def.parts[L.boot.part]; this.kb = bp.scale || 1;
      this.hipX = {}; this.ft = {};   // feet: actual pose (root space) + ground lock / settle-step state
      for (const s of ["near", "far"]) { this.hipX[s] = rig.by.hip.pos[0] + L.hip[0] + L[s].x; this.ft[s] = { x: this.hipX[s] + ((rig.def.idleStance || {})[s] || 0), lift: 0, ang: 0, planted: true, lockW: 0, off: 0, step: null } }
      for (const s of ["near", "far"]) this.ft[s].lockW = this.odo + this.ft[s].x;
    }
    /** start an action ("thrust"); returns false while another one is still committed */
    /** touch greeting: hide weapon, smile and wave, weapon back. Returns false if another action is committed. */
    wave() { return this.attack("wave") }
    /** opts.speed: play the action faster (>1) or slower (<1) without re-keying it */
    attack(name = "thrust", opts = {}) {
      const def = (this.rig.def.actions && this.rig.def.actions[name]) || ACTIONS[name]; if (!def) return false;   // per-character actions in rig.json override the built-ins
      if (this.act && this.act.t < this.act.def.cancelAt) return false;
      const e = {}; for (const s of ["near", "far"]) { const f = this.ft[s]; e[s] = { x: f.x, lift: f.lift, ang: f.ang, lockW: this.odo + f.x } }
      this.act = { name, def, t: 0, speed: opts.speed || 1, entry: e, hit: false, prev: this.act ? { def: this.act.def, t: this.act.t } : null }; return true;
    }
    get busy() { return !!this.act }
    /** change the movement feel at runtime: gait = preset object (see GAIT_PRESETS / references/05_tuning.md); null = rig.json default */
    setGait(gait) { this.G = Object.assign({}, GAIT_DEFAULTS, this.rig.def.gait || {}, typeof gait === "string" ? GAIT_PRESETS[gait] : gait || {}); this.stance = this.G.stance }
    /** base expression when no action overrides it: null | "happy" | "sad" | "angry" | "focus" | "relaxed" | "effort" | "shout" | "grimace" */
    setExpression(name) { this.expr = name && this.rig.def.faces && this.rig.def.faces[name] ? name : null }
    // track value of the running action; when one action interrupts another, the old one keeps playing underneath and
    // fades out over 0.1 s so no joint jumps on the chain frame (the feet capture their own entry pose instead)
    _tr(name) { const a = this.act; if (!a) return 0; const v = track(a.def[name], a.t); if (!a.prev) return v;
      return lerp(track(a.prev.def[name], a.prev.t), v, smooth(0, .1, a.t)) }
    _faceAt(D, t) { if (!D || !D.face) return this.expr; let f = this.expr; for (const [k, n] of D.face) if (t >= k) f = n === null ? this.expr : n; return f }
    /** root-space point between the two prong tips */
    tip() { const p = this.rig.def.parts.weapon.tips; const a = this.rig.partPoint("weapon", ...p[0]), c = this.rig.partPoint("weapon", ...p[1]); return [(a[0] + c[0]) / 2, (a[1] + c[1]) / 2] }
    get facingScale() { const k = this.turnT > 0 ? .72 + .28 * Math.abs(Math.cos((1 - this.turnT / .16) * Math.PI)) : 1; return this.facing * k }
    _ik(H, A, soft = 0, kw = 0) { // two-bone IK, knee bends forward (+x); kw>0 = knee turned outward (kneeOut)
      const L1 = this.L.thigh, L2 = this.L.shin; let dx = A[0] - H[0], dy = A[1] - H[1], d = Math.hypot(dx, dy);
      // soft IK for a foot in the air: near full extension the knee angle changes infinitely fast (acos singularity),
      // which shows as a one-frame knee snap at toe-off. Ease the reach so the leg straightens smoothly (the foot lags a hair).
      if (soft > 0) { const Lm = (L1 + L2) * .995, ds = (L1 + L2) * .975; if (d > ds) { const ds2 = ds + (Lm - ds) * (1 - Math.exp(-(d - ds) / (Lm - ds))), dd = lerp(d, ds2, soft);
        A = [H[0] + dx / d * dd, H[1] + dy / d * dd]; dx = A[0] - H[0]; dy = A[1] - H[1]; d = dd } }
      const dm = Math.min(d, (L1 + L2) * .999), base = Math.atan2(dy, dx), cosA = clamp((L1 * L1 + dm * dm - L2 * L2) / (2 * L1 * dm), -1, 1), al = Math.acos(cosA);
      const k1 = [H[0] + Math.cos(base - al) * L1, H[1] + Math.sin(base - al) * L1], k2 = [H[0] + Math.cos(base + al) * L1, H[1] + Math.sin(base + al) * L1];
      let knee = k1[0] > k2[0] ? k1 : k2; const ankle = d > dm ? [H[0] + dx / d * (L1 + L2) * .999, H[1] + dy / d * (L1 + L2) * .999] : A;
      if (kw > 0) { const ux = Math.cos(base), uy = Math.sin(base), t = (knee[0] - H[0]) * ux + (knee[1] - H[1]) * uy, F = [H[0] + ux * t, H[1] + uy * t], c = Math.cos(Math.PI * Math.min(1, kw));
        knee = [F[0] + (knee[0] - F[0]) * c, F[1] + (knee[1] - F[1]) * c] }   // kneeOut (opt-in, 6 카르덴): 무릎이 바깥(뒤)으로 — 다리가 엉덩이-발목 축으로 돈 것처럼 수직 거리만 cos 로 줄임(3D 회전의 그림자)
      return { hip: H, knee, ankle };
    }
    _ankleFor(gx, lift, ang) { // ankle height so the lowest sole point (heel / ball / toe tip) touches the ground
      const c = Math.cos(ang), s = Math.sin(ang); let low = -1e9;
      for (const [x, y] of this.L.boot.sole) low = Math.max(low, (x * s + y * c) * this.kb);
      return [gx, -low - lift];
    }
    _foot(phase, S) { // phase 0..1 of this foot's stride; returns [x (rel. hip), lift, angle, inStance]
      const st = this.stance, xc = .5 * S, xt = xc - S;   // foot lands half a stride ahead of the hip (no over-striding: knee stays ~15–20° bent at contact)
      if (phase < st) { const u = phase / st; const ang = u < .16 ? lerp(this.G.landAng ?? -.22, 0, smooth(0, .16, u)) : u > .66 ? lerp(0, .7, smooth(.66, 1, u)) : 0; return [xc - S * u, 0, ang, true] }
      const u = (phase - st) / (1 - st), g = this.G, H1 = (.3 * S + 24) * g.heelKick, H2 = (.42 * S + 30) * g.kneeLift, H3 = (.16 * S + 14) * g.kneeLift;
      const keys = [{ t: -.2, x: xt + .2 * S, y: 0, a: .45 }, { t: 0, x: xt, y: 0, a: .7 }, { t: .26, x: xt - .28 * S, y: H1, a: 1.15 }, { t: .52, x: -.08 * S, y: H2, a: .5 },
        { t: .8, x: xc + (g.swingReach ?? .2) * S, y: H3, a: g.swingAng ?? -.12 }, { t: 1, x: xc, y: 0, a: g.landAng ?? -.22 }, { t: 1.2, x: xc - .2 * S, y: 0, a: -.1 }];
      // gait.swingReach/swingAng/landAng (opt-in, 알론소 v4): 동작 시트처럼 '무릎이 먼저 나가고 발은 무릎 밑에 접혀 따라와 평평하게 착지'
      //   — 기본값(니콜)은 발이 착지점보다 앞으로 뻗었다가(0.2) 뒤꿈치로 닿음(-0.22)
      const [x, y, a] = pathAt(keys, u); return [x, Math.max(0, y), a, false];
    }
    // feet: running gait while moving; ground-locked during stance; settle steps when stopping
    _feet(dt, sp, lvx, S, A) {
      const moving = sp > 14 && A > .04 && !(this.act && this.act.def.plant), ph = this.cyc, act = this.act;
      for (const side of ["near", "far"]) {
        const f = this.ft[side], rest = this.hipX[side] + (1 - A) * ((this.rig.def.idleStance || {})[side] || 0);   // idleStance: 서 있을 때만 발을 더 벌림 (opt-in, 18 네온)
        if (act && !act.def.plant) {   // action owns the feet: lead foot steps out and back, rear foot stays where it was planted
          const D = act.def, t = act.t, E = act.entry[side], land = 1 - smooth(0, .1, t);
          if (side === "far") { f.x = lerp(E.x, rest, smooth(.17, .29, t)) + track(D.farDx, t); f.lift = Math.max(track(D.farLift, t), E.lift * land); f.ang = track(D.farAng, t) + E.ang * land }
          else { f.x = lerp(E.lockW - this.odo, rest, smooth(.03, .15, t)) + track(D.nearDx, t); f.lift = Math.max(track(D.nearLift, t), E.lift * land); f.ang = track(D.nearAng, t) + E.ang * land }
          f.step = null; f.planted = f.lift < .01; if (f.planted) f.lockW = this.odo + f.x; f.off = 0; continue;
        }
        if (moving) {
          f.step = null;
          const fp = (ph + (side === "far" ? .5 : 0)) % 1, [fx, lift, ang, stance] = this._foot(fp, S);
          // legs.near/far.runX (opt-in, 알론소 v4): 달릴 때 발이 지나가는 가운데 줄 — 서 있을 때의 넓은 발 자리(A자)를 달리기에 그대로 쓰면
          // 먼 다리는 몸 훨씬 앞에, 가까운 다리는 몸 바로 밑에 착지해서 어긋나 보임 → 속도(A)에 따라 몸 가운데 줄로 모음
          const Ls = this.rig.def.legs[side], runRest = Ls.runX != null ? this.rig.by.hip.pos[0] + this.rig.def.legs.hip[0] + Ls.runX : rest;
          const gx = lerp(rest, runRest, A) + fx * A, gl = lift * A, ga = ang * A * (this.G.angK ?? 1);   // gait.angK (opt-in, 6 카르덴): 발목 꺾임 줄임 — 짧은 다리가 바짓단 밑에서 종종걸음
          if (f.settled) { f.settled = false; f.off = f.x - gx; f.planted = f.lift < .01 && gl < .5; if (f.planted) f.lockW = this.odo + f.x }   // 멈춤 발걸음 → 다시 달리기: 발 위치가 끊기지 않게 이어받음 (방향 바꿀 때 한 프레임 튐 수정)
          if ((stance && gl === 0) || (f.planted && gl < .5)) {   // a foot still touching the ground stays locked until it really lifts (no toe drag)
            if (!f.planted) { f.planted = true; f.lockW = this.odo + gx + f.off }
            const lx = f.lockW - this.odo; f.off = lx - gx;
            if (Math.abs(f.off) > 85) { f.planted = false; f.off = clamp(f.off, -85, 85) } // never stretch a leg to keep a lock
            f.x = gx + f.off;
          } else { f.planted = false; f.off = damp(f.off, 0, 9, dt); f.x = gx + f.off }
          f.lift = gl; f.ang = ga;
        } else {
          // settle: finish the airborne step, then a small recovery step for a foot left far from under the hip
          const other = this.ft[side === "near" ? "far" : "near"];
          if (!f.step && (f.lift > .5 || (Math.abs(f.x - rest) > 6 && !other.step && other.lift < .5)))
            f.step = { t: 0, dur: f.lift > .5 ? .13 : .2, x0: f.x, l0: f.lift, a0: f.ang, h: f.lift > .5 ? 0 : clamp(Math.abs(f.x - rest) * .25, 8, 22) };
          if (f.step) { const st = f.step; st.t = Math.min(1, st.t + dt / st.dur); const e = smooth(0, 1, st.t);
            f.x = lerp(st.x0, rest, e); f.lift = lerp(st.l0, 0, e) + Math.sin(Math.PI * st.t) * st.h; f.ang = lerp(st.a0, 0, e) - Math.sin(Math.PI * st.t) * .12;
            if (st.t >= 1) { f.step = null; f.lift = 0; f.ang = 0 } }
          else { f.lift = 0; f.ang = damp(f.ang, 0, 14, dt) }
          f.planted = f.lift === 0; if (f.planted) f.lockW = this.odo + f.x; f.off = f.x - rest; f.settled = true;
        }
      }
    }
    // lead (far) hand carries the spear along the keyed path; rear (near) hand grips the shaft behind it — both solved with 2-bone IK
    /* Two-hand spear work (side view, character faces +x) — v10, built on the user's key-pose drawing.
       Mechanics: reach comes from the legs (lunge, pelvis low); both elbows stay under the shaft; fists at chest height.
       Hands: each forearm + fist is ONE drawing (sheet F #3), so the wrist is exactly as drawn; the lead arm is forward
       kinematics from two keyed values (upper-arm angle thF, spear angle ang); the rear fist searches along the shaft for the
       spot where its arm closes with the elbow under the shaft and the drawing within ±25° of its drawn grip angle.
       Depth: torso < shaft < lead forearm+fist < near shoulder guard < rear forearm+fist. Effects are left to the game. */
    _actArms(D, t, T) {
      const rig = this.rig, b = rig.by, P = rig.def.parts, w = this._tr('w');
      rig.compute();
      const SN = apply(b.armU.m, 0, 0), SF = apply(b.armF.m, 0, 0);
      const a0 = wAng(b.weapon.m), G0 = apply(b.weapon.m, 0, 0);               // spear as carried (no action)
      const aK = this._tr('ang') + this._tr('shake') * Math.sin(T * 95) * .025;  // keyed spear bone angle (0 upright, π/2 level)
      const a = a0 + wrapA(aK - a0) * w, u = [Math.sin(a), -Math.cos(a)];
      // ---- lead (left) arm: forearm + fist is ONE drawing (sheet F #3, wrist exactly as drawn), forward kinematics from the
      //      keyed upper-arm angle: shoulder → elbow (upper arm) → fist on the shaft (along the drawing's own elbow→fist line)
      const pA = wAng(b.torso.m), hl = P.handL, sL = hl.scale;
      // Lead arm = the character's own forearm drawing (foreF, true size) + the key-pose fist (handL) at its end.
      // FK with two keyed DOF (upper-arm angle thF, spear angle ang). The fist turns with the shaft; the forearm direction
      // follows the fist's drawn wrist (toElbow) — bridged from the carry grip with a wrist bend of at most 29°.
      const E0 = apply(b.foreF.m, 0, 0), C0 = apply(b.fistF.m, 0, 0);
      const thRest = Math.atan2(E0[0] - SF[0], E0[1] - SF[1]), phiRest = Math.atan2(C0[1] - E0[1], C0[0] - E0[0]);
      const sd = Math.atan2(hl.shaftDir[1], hl.shaftDir[0]), dirA = x => x - Math.PI / 2;
      const r_c = wrapA(dirA(a0) - phiRest), r_g = wrapA(sd - Math.atan2(hl.toElbow[1], hl.toElbow[0]) - Math.PI);
      const kk = clamp(Math.abs(wrapA(a - a0)) / (Math.PI / 2 * .75), 0, 1), dr = wrapA(r_g - r_c), sg = Math.sign(dr) || 1;
      if (this.gripOn ? kk < .45 : kk > .55) this.gripOn = !this.gripOn;
      const L1 = Math.hypot(...b.foreF.pos), th = thRest + wrapA(this._tr('thF') + pA - thRest) * w;
      const E = [SF[0] + Math.sin(th) * L1, SF[1] + Math.cos(th) * L1];
      b.armF.ar = Math.atan2(E[1] - SF[1], E[0] - SF[0]) - Math.atan2(b.foreF.pos[1], b.foreF.pos[0]) - pA - b.armF.rot;
      for (let pass = 0; pass < 2; pass++) {
        const r = this.gripOn ? r_g - sg * .44 * (1 - smooth(.5, 1, kk)) : r_c + sg * .5 * smooth(0, .5, kk), phi = dirA(a) - r;
        this.handErr = this.gripOn ? wrapA(r - r_g) : 0;
        rig.compute();
        const cF = b.fistF.pos;
        b.foreF.ar = phi - Math.atan2(cF[1], cF[0]) - wAng(b.armF.m) - b.foreF.rot;
        rig.compute();
        const need = wrapA(a - b.weapon.rot - wAng(b.foreF.m) - b.fistF.rot);
        b.fistF.ar = need; this.wrist = b.fistF.rot + need;
        if (!this.gripOn && Math.abs(this.wrist) > .58) { this.gripOn = true; continue }
        break }
      rig.compute();
      let G;
      if (this.gripOn) {   // grip centre = forearm end (wrist, 14 units inside the bandage) minus the fist's own wrist offset
        const Wr = apply(b.fistF.m, 0, 0), rho = a - Math.PI / 2 - sd, c = Math.cos(rho), s2 = Math.sin(rho);
        const fd = [Math.cos(wAng(b.foreF.m) + Math.atan2(b.fistF.pos[1], b.fistF.pos[0])), Math.sin(wAng(b.foreF.m) + Math.atan2(b.fistF.pos[1], b.fistF.pos[0]))];
        const W = [Wr[0] - fd[0] * 14, Wr[1] - fd[1] * 14], wo = [(hl.wrist[0] - hl.pivot[0]) * sL, (hl.wrist[1] - hl.pivot[1]) * sL];
        G = [W[0] - (c * wo[0] - s2 * wo[1]), W[1] - (s2 * wo[0] + c * wo[1])];
      } else G = apply(b.weapon.m, 0, 0);
      const sl = this._tr('slide') || 0;   // 자루가 앞손 안에서 미끄러짐(+ = 창끝 쪽으로): 긴 창 준비 자세에서 뒤끝이 땅에 안 닿게 (rig.def.actions 의 slide 트랙, opt-in)
      if (sl) { G = [G[0] + u[0] * sl, G[1] + u[1] * sl]; b.handL.pos = [0, sl] } else b.handL.pos = [0, 0];
      { const F = b.fistF.m, det = F[0] * F[3] - F[1] * F[2], ix = G[0] - F[4], iy = G[1] - F[5];
        b.weapon.ax = (F[3] * ix - F[2] * iy) / det - b.weapon.pos[0]; b.weapon.ay = (-F[1] * ix + F[0] * iy) / det - b.weapon.pos[1];
        b.weapon.ar = wrapA(a - wAng(F) - b.weapon.rot) }
      // ---- rear (right) arm: forearm + fist is one key-pose drawing (handR) riding on the shaft; slide it along the shaft to the
      //      spot where the upper arm (shoulder → cuff end) closes, elbow under the shaft, near the preferred hand spacing
      const wn = this._tr('nearW');
      this.rearErr = 0;
      if (wn > 0) {
        const hr = P.handR, sR = hr.scale, sdR = Math.atan2(hr.shaftDir[1], hr.shaftDir[0]), rhoR = a - Math.PI / 2 - sdR, cR = Math.cos(rhoR), sR2 = Math.sin(rhoR);
        const eo = [(hr.elbow[0] - hr.pivot[0]) * sR, (hr.elbow[1] - hr.pivot[1]) * sR], off = [cR * eo[0] - sR2 * eo[1], sR2 * eo[0] + cR * eo[1]];
        const lu = Math.hypot(...b.armL.pos), kPref = -(this._tr('gap') || 170) - sl;
        const V = [G[0] + off[0] - SN[0], G[1] + off[1] - SN[1]], vu = V[0] * u[0] + V[1] * u[1], disc = vu * vu - (V[0] * V[0] + V[1] * V[1]) + lu * lu;
        let k = disc >= 0 ? null : -vu;
        if (disc >= 0) { let bc = 1e9; for (const rr of [-vu - Math.sqrt(disc), -vu + Math.sqrt(disc)]) { const c2 = Math.abs(rr - kPref) + (rr > -60 ? 1e4 : 0); if (c2 < bc) { bc = c2; k = rr } } }
        if (rig.def.rearBlend && disc >= 0 && wn > .9) {   // 뒷손 해(팔꿈치 뒤 ↔ 팔 뻗음)가 바뀔 때 한 프레임에 튀지 않게, 자루 위를 rearBlend 초 동안 미끄러져 옮김 (opt-in, 18 네온)
          const side = Math.sign(k + vu) || 1, B = this._rB;
          if (this._rSide && side !== this._rSide && this._rK != null) this._rB = { from: this._rK, t: 0 };
          this._rSide = side;
          if (this._rB) { const bb = this._rB; bb.t += this.dt || 1 / 60; const uu = Math.min(1, bb.t / rig.def.rearBlend), e_ = uu * uu * (3 - 2 * uu); k = bb.from + (k - bb.from) * e_; if (uu >= 1) this._rB = null } }
        else if (wn <= .9) { this._rSide = 0; this._rB = null }
        this._rK = k;
        this.rearK = k; this.rearReach = disc;
        const GN = [G[0] + u[0] * k, G[1] + u[1] * k], EN = [GN[0] + off[0], GN[1] + off[1]];
        b.handR.pos = [0, -k];
        const on = wn > .9;
        const base = b.armU.ar;
        b.armU.ar = Math.atan2(EN[1] - SN[1], EN[0] - SN[0]) - Math.atan2(b.armL.pos[1], b.armL.pos[0]) - pA - b.armU.rot;
        if (!on) {   // reaching: upper arm swings toward the grip pose, the running fist's forearm aims along the drawn forearm
          b.armU.ar = lerp(base, b.armU.ar, wn); rig.compute();
          const pl2 = P.armLF, gv = [(pl2.grip[0] - pl2.pivot[0]), (pl2.grip[1] - pl2.pivot[1])], fa = Math.atan2(-off[1], -off[0]);
          const tL = fa - Math.atan2(gv[1], gv[0]) - wAng(b.armU.m) - b.armL.rot; b.armL.ar = b.armL.ar + wrapA(tL - b.armL.ar) * wn; rig.swap.armL = (rig.def.releaseOpen && t > (D.hitAt || .3)) ? null : P.armL.alt }   // releaseOpen: 찌른 뒤 자루를 놓을 땐 손을 펴서 내림 (주먹→편 손 한 번에 바뀌는 것 방지, 18 네온 opt-in)
        rig.alpha.handR = on ? 1 : 0; rig.alpha.armL = on ? 0 : 1;
        b.pauldron.ar = b.armU.ar * .42; b.pauldron.ax = -b.armU.ar * 3 + b.armU.ax;
      } else { rig.alpha.handR = 0; rig.alpha.armL = 1 }
      rig.alpha.handL = this.gripOn ? 1 : 0; rig.alpha.fistF = this.gripOn ? 0 : 1;
      rig.compute();
      // hit event + speed trail
      const act = this.act;
      if (act && !act.hit && t >= D.hitAt) { act.hit = true; const p = this.tip(); this.events.push({ type: "hit", x: p[0], y: p[1] }) }
      const tr = this._tr('trail'), tips = P.weapon.tips;
      tips.forEach((tp, i) => { const Q = this.trailPts[i]; Q.push(rig.partPoint("weapon", tp[0], tp[1])); if (Q.length > 7) Q.shift(); if (tr <= 0) Q.length = 0 });
      rig.trail = tr > 0 ? { a: tr, pts: this.trailPts } : null;
    }
    /* wave: joint-space blends from the current pose (no IK → no elbow flips), world-angle targets:
       near upper arm points up-back beside the head, forearm vertical, the drawn open hand is mirrored so the thumb points
       forward (palm toward the viewer); forearm + hand are drawn in front of the head (rig.def.drawWave). */
    /** 위에서 내려찍기: 칼날 각도(sa)와 손잡이 위치(gx,gy)를 키로, 칼 팔(armF→foreF→fistF)과 뒷팔(armU→armL→fistN)을 두 관절 IK로 */
    _smashArms(D, t, T, act) {
      const rig = this.rig, b = rig.by, P = rig.def.parts, w = this._tr('w');
      rig.alpha.foreF = rig.alpha.fistF = rig.alpha.weapon = rig.alpha.armF = 1;
      rig.drawOrder = rig.def.drawSmash || null;
      // 뒷어깨를 앞으로 당김 (몸이 옆으로 돌아 두 손이 만남) — 어깨 갑옷도 따라감
      const sh = this._tr('sh'), SS = rig.def.smashShoulder || [-120, -8];
      b.armU.ax += SS[0] * sh; b.armU.ay += SS[1] * sh;
      rig.compute();
      const sa = this._tr('sa') + this._tr('shake') * Math.sin(T * 95) * .04, ux = Math.cos(sa), uy = Math.sin(sa);
      const G = apply(b.hip.m, this._tr('gx'), this._tr('gy'));
      // 칼날 방향(무기 그림의 손잡이→칼끝)이 sa가 되도록 손목(fistF) 세계 각도를 정함
      const wp = P.weapon, tm = wp.tips ? [(wp.tips[0][0] + wp.tips[1][0]) / 2, (wp.tips[0][1] + wp.tips[1][1]) / 2] : [wp.pivot[0], 0];
      const bl = Math.atan2(tm[1] - wp.pivot[1], tm[0] - wp.pivot[0]);               // 무기 뼈 기준 칼날 방향
      const phiW = sa - bl, phiF = phiW - (b.weapon.rot || 0);
      const c = Math.cos(phiF), s = Math.sin(phiF), wpos = b.weapon.pos;
      const Wt = [G[0] - (c * wpos[0] - s * wpos[1]), G[1] - (s * wpos[0] + c * wpos[1])];    // 손목이 가야 할 곳
      const SF = apply(b.armF.m, 0, 0), L1 = Math.hypot(...b.foreF.pos), L2 = Math.hypot(...b.fistF.pos);
      const [eLow] = solve2(SF, Wt, L1, L2);
      const tA = Math.atan2(eLow[1] - SF[1], eLow[0] - SF[0]) - Math.atan2(b.foreF.pos[1], b.foreF.pos[0]);
      b.armF.ar += wrapA(tA - wAng(b.armF.m)) * w; rig.compute();
      const E = apply(b.foreF.m, 0, 0), tF = Math.atan2(Wt[1] - E[1], Wt[0] - E[0]) - Math.atan2(b.fistF.pos[1], b.fistF.pos[0]);
      b.foreF.ar += wrapA(tF - wAng(b.foreF.m)) * w; rig.compute();
      b.fistF.ar += wrapA(phiF - wAng(b.fistF.m)) * w; b.weapon.ar = 0; rig.compute();
      this._nearToShaft(w, rig.def.smashHand2 || 46, ux, uy);
      b.pauldron.ar = b.armU.ar * .3; b.pauldron.ax = b.armU.ax; b.pauldron.ay = b.armU.ay;
      if (!act.hit && t >= D.hitAt) { act.hit = true; const p = this.tip(); this.events.push({ type: "hit", x: p[0], y: p[1] }) }
    }
    /** 봉 키 찌르기 (opt-in, D.kind "staff" — 6 카르덴 2026-10-17): 동작 시트가 두 주먹을 배 앞에 붙이고 팔뚝을 거의 안 보이게 그림(팔 길이 1.5배로 그림)
        → 어깨→팔로 봉 위치를 계산하면 가슴 높이에서 못 내려옴. 그래서 봉(앞 주먹 쥔 점 gx·gy 골반 기준, 각도 ang)을 키로 두고
        먼 팔은 앞 주먹 소매(handL.wrist)까지 두 관절 IK(수염 뒤라 거의 안 보임), 뒷주먹(handR)은 앞 주먹 뒤 gap 에 자루 위,
        가까운 팔은 어깨(sh 만큼 앞으로 — 몸이 돌아 두 손이 만남) → 팔꿈치 → 소매 조각(staffKey.sleeve)으로 뒷주먹 소매까지 두 관절 IK */
    _staffArms(D, t, T, act) {
      const rig = this.rig, b = rig.by, P = rig.def.parts, w = this._tr('w'), SK = rig.def.staffKey || {};
      rig.alpha.foreF = rig.alpha.weapon = rig.alpha.armF = 1; rig.drawOrder = (this._tr('w') > .3 && rig.def.drawStaff) || null;   // drawStaff(opt-in): 찌를 때 봉은 가까운 팔 앞(집게가 배 앞에 보임)
      const sh = this._tr('sh'), SS = SK.shoulder || [60, 0]; b.armU.ax += SS[0] * sh; b.armU.ay += SS[1] * sh; const PF = SK.pauldronFollow ?? 1; b.pauldron.ax += SS[0] * sh * PF; b.pauldron.ay += SS[1] * sh * PF;   // pauldronFollow<1: 어깨갑은 몸통 소매 구멍을 덮은 채 남음
      rig.compute();
      const G0 = apply(b.weapon.m, 0, 0), a0 = wAng(b.weapon.m);
      const aK = this._tr('ang') + this._tr('shake') * Math.sin(T * 95) * .025, a = a0 + wrapA(aK - a0) * Math.min(1, w * 2), u = [Math.sin(a), -Math.cos(a)];   // 봉은 손보다 먼저 눕힘 → 세운 봉 집게가 땅을 긁지 않음
      const LO = SK.leadOn ?? .5, on = w > LO;   // 앞 주먹(handL)으로 바꾸는 때 — 그 전엔 세운 봉 주먹 그대로 봉만 돎
      const GK = apply(b.hip.m, this._tr('gx'), this._tr('gy')), wg = smooth(LO, 1, w), G = [lerp(G0[0], GK[0], wg), lerp(G0[1], GK[1], wg)];   // 바꾸는 순간 G = 세운 봉 주먹이 쥔 점(이어짐)
      // 먼 팔: 어깨 → 앞 주먹 소매 (주먹을 쥐기 전엔 세운 봉 주먹의 손목)
      const hl = P.handL, sL = hl.scale, sd = Math.atan2(hl.shaftDir[1], hl.shaftDir[0]), rho = a - Math.PI / 2 - sd, c = Math.cos(rho), s = Math.sin(rho);
      const wo = [(hl.wrist[0] - hl.pivot[0]) * sL, (hl.wrist[1] - hl.pivot[1]) * sL], Wl = [G[0] + c * wo[0] - s * wo[1], G[1] + s * wo[0] + c * wo[1]];
      const W0 = apply(b.fistF.m, 0, 0), Wt = on ? Wl : W0;   // 바꾸기 전: 먼 팔은 그대로(달리기·대기 자세)
      const SF = apply(b.armF.m, 0, 0), L1 = Math.hypot(...b.foreF.pos), L2 = Math.hypot(...b.fistF.pos);
      const bend = (S, E, W) => wrapA(Math.atan2(W[1] - E[1], W[0] - E[0]) - Math.atan2(E[1] - S[1], E[0] - S[0]));   // 팔꿈치 굽힘(−: 대기 자세와 같은 쪽)
      const pick = (S, W, sol) => bend(S, sol[0], W) <= 0 ? sol[0] : bend(S, sol[1], W) <= 0 ? sol[1] : sol[0];   // 굽는 쪽이 대기와 같은 해(팔꿈치 뒤집힘 없음)
      const eF = pick(SF, Wt, solve2(SF, Wt, L1, L2));
      b.armF.ar += wrapA(Math.atan2(eF[1] - SF[1], eF[0] - SF[0]) - Math.atan2(b.foreF.pos[1], b.foreF.pos[0]) - wAng(b.armF.m)); rig.compute();
      const EF = apply(b.foreF.m, 0, 0); b.foreF.ar += wrapA(Math.atan2(Wt[1] - EF[1], Wt[0] - EF[0]) - Math.atan2(b.fistF.pos[1], b.fistF.pos[0]) - wAng(b.foreF.m)); rig.compute();
      // 봉: 앞 주먹 쥔 점 G, 각도 a (봉 뼈는 fistF 자식 → fistF 기준으로 환산). 앞 주먹으로 바꾸기 전(세운 봉 주먹이 보일 때)은 그 주먹이 쥔 점에서 돌리기만
      if (!on) { const g_ = apply(b.fistF.m, b.weapon.pos[0] + b.weapon.ax, b.weapon.pos[1] + b.weapon.ay); G[0] = g_[0]; G[1] = g_[1] }   // 손 안에서 밀린 만큼(runSlide·carryDrop) 그대로 이어받음 — 공격 시작 때 봉이 한 프레임에 튀지 않게
      { const F = b.fistF.m, det = F[0] * F[3] - F[1] * F[2], ix = G[0] - F[4], iy = G[1] - F[5];
        b.weapon.ax = (F[3] * ix - F[2] * iy) / det - b.weapon.pos[0]; b.weapon.ay = (-F[1] * ix + F[0] * iy) / det - b.weapon.pos[1]; b.weapon.ar = wrapA(a - wAng(F) - b.weapon.rot) }
      b.handL.pos = [0, 0];
      // 뒷주먹: 자루 위 앞 주먹 뒤 gap
      const gap = this._tr('gap') || 170; b.handR.pos = [0, gap];
      const hr = P.handR, sR = hr.scale, sdR = Math.atan2(hr.shaftDir[1], hr.shaftDir[0]), rR = a - Math.PI / 2 - sdR, cR = Math.cos(rR), sR2 = Math.sin(rR);
      const GN = [G[0] - u[0] * gap, G[1] - u[1] * gap], ro = [((hr.wrist || hr.elbow)[0] - hr.pivot[0]) * sR, ((hr.wrist || hr.elbow)[1] - hr.pivot[1]) * sR];
      const WN = [GN[0] + cR * ro[0] - sR2 * ro[1], GN[1] + sR2 * ro[0] + cR * ro[1]];
      // 가까운 팔: 어깨 → 팔꿈치 → 소매 끝 = 뒷주먹 손목. 쥐기 전(w<.5)에는 달리기 주먹 그림(armLF)으로 다가감
      const SN = apply(b.armU.m, 0, 0), sl = P[SK.sleeve || 'armL'], ks = sl.scale || 1, sg = sl.grip || sl.pivot;
      const N1 = Math.hypot(...b.armL.pos), N2 = Math.hypot(sg[0] - sl.pivot[0], sg[1] - sl.pivot[1]) * ks;
      const ww = smooth(0, 1, w);
      const onN = w > (SK.nearOn ?? .9);   // 가까운 손은 봉이 자리 잡은 뒤에만 쥠(옮겨 가는 동안 팔이 안 닿음)
      let n1 = N1;   // staffKey.upperLen: 다가갈 때·쥘 때 모두 같은 윗팔 길이(바꾸는 순간 팔꿈치 안 튐)
      if (SK.upperLen) { const p_ = b.armL.pos, l_ = Math.hypot(p_[0], p_[1]) || 1, l0_ = Math.hypot(p_[0] + b.armL.ax, p_[1] + b.armL.ay); n1 = lerp(l0_, SK.upperLen, smooth(0, .6, w)); b.armL.ax = p_[0] * (n1 / l_ - 1); b.armL.ay = p_[1] * (n1 / l_ - 1) }   // 공격 시작·끝에 0.05초 동안 이어서 바꿈
      if (onN) {
        rig.swap.armL = SK.sleeve || null;
        // staffKey.upperLen / fit (opt-in, 6 카르덴 10-18): 윗팔을 어깨갑 밖으로 빼고(upperLen), 소매를 어깨→손목 거리에 맞춰 늘임(fit = 펴짐 정도)
        //   → 팔꿈치가 윗팔 끝에 딱 붙고 손목이 뒷주먹 소매 테에 딱 닿음 (짧은 소매로는 팔이 봉 뒤에 숨거나 모자랐음)
        let n2 = N2;
        if (SK.foreFromHand && hr.toElbow) {   // staffKey.foreFromHand (opt-in, 6 카르덴 10-18 00:59 '손-팔꿈치-어깨가 다 나오게'): 팔뚝은 뒷주먹 소매 테가 향한 쪽으로 그대로 이어지고(팔꿈치 = 손목 + 소매 방향 × 팔뚝 길이),
          //   윗팔은 어깨→그 팔꿈치를 잇도록 길이만 맞춤 → 니콜처럼 어깨 밑으로 내려온 윗팔 + 앞으로 뻗은 팔뚝 + 손이 한 줄로 보임
          const tx_ = hr.toElbow[0], ty_ = hr.toElbow[1], dW = [cR * tx_ - sR2 * ty_, sR2 * tx_ + cR * ty_], ULn = SK.upperLen || 78;
          // 팔뚝 길이 배율 fk 를 0.85~1.4 에서 골라: 윗팔(어깨→팔꿈치)이 upperLen 에 가깝고 팔꿈치가 -20°~-150° 로 굽는 것 (돌아올 때 팔꿈치가 어깨에 붙어 접히던 것 방지)
          let best_ = SK.foreK ?? 1, bs_ = 1e9; for (let k_ = .85; k_ <= 1.401; k_ += .05) { const E_ = [WN[0] + dW[0] * N2 * k_, WN[1] + dW[1] * N2 * k_], u_ = Math.hypot(E_[0] - SN[0], E_[1] - SN[1]);
            const bd_ = wrapA(Math.atan2(WN[1] - E_[1], WN[0] - E_[0]) - Math.atan2(E_[1] - SN[1], E_[0] - SN[0])) * 180 / Math.PI, sc_ = Math.abs(u_ - ULn) + Math.abs(k_ - (SK.foreK ?? 1)) * 40 + (bd_ > -20 || bd_ < -150 ? 1e3 : 0); if (sc_ < bs_) { bs_ = sc_; best_ = k_ } }
          const first_ = this.fkS == null || w < (SK.nearOn ?? .9) + .02;
          this.fkS = first_ ? best_ : damp(this.fkS, best_, 20, 1 / 120);
          const fk_ = this.fkS, EH_ = [WN[0] + dW[0] * N2 * fk_, WN[1] + dW[1] * N2 * fk_];
          const bh_ = wrapA(Math.atan2(WN[1] - EH_[1], WN[0] - EH_[0]) - Math.atan2(EH_[1] - SN[1], EH_[0] - SN[0])) * 180 / Math.PI, ok_ = bh_ < -25 && bh_ > -140 && Math.hypot(EH_[0] - SN[0], EH_[1] - SN[1]) > ULn * .6;
          // 봉을 다시 세우는 동안(소매 방향대로는 팔꿈치가 어깨 위로 가거나 팔이 다 접힘)은 보통 IK 팔꿈치로 부드럽게 넘어감 — 팔꿈치 뒤집힘·접힘 없음
          this.hW = first_ ? (ok_ ? 1 : 0) : damp(this.hW ?? 1, ok_ ? 1 : 0, 30, 1 / 120);
          const D2_ = Math.hypot(WN[0] - SN[0], WN[1] - SN[1]), c50_ = Math.cos(.87), s50_ = Math.sin(.87);   // IK 쪽 팔뚝 길이: 팔꿈치가 약 −130° 로 굽게(다 접히지 않게)
          const n2i_ = clamp(D2_ > ULn * s50_ ? ULn * c50_ + Math.sqrt(D2_ * D2_ - ULn * ULn * s50_ * s50_) : ULn * c50_, N2 * .7, N2 * 1.4);
          const EI_ = pick(SN, WN, solve2(SN, WN, ULn, n2i_)), EN_ = [lerp(EI_[0], EH_[0], this.hW), lerp(EI_[1], EH_[1], this.hW)];
          const p_ = b.armL.pos, l_ = Math.hypot(p_[0], p_[1]) || 1, u1 = Math.hypot(EN_[0] - SN[0], EN_[1] - SN[1]), n1b = u1;   // 윗팔 길이 = 어깨→팔꿈치 (길이만 섞으면 팔꿈치가 목표를 지나쳐 팔뚝이 뒤로 접힘)
          b.armL.ax = p_[0] * (n1b / l_ - 1); b.armL.ay = p_[1] * (n1b / l_ - 1);
          b.armU.ar += wrapA(Math.atan2(EN_[1] - SN[1], EN_[0] - SN[0]) - Math.atan2(p_[1], p_[0]) - wAng(b.armU.m)); rig.compute();
          const EN = apply(b.armL.m, 0, 0); b.armL.ar += wrapA(Math.atan2(WN[1] - EN[1], WN[0] - EN[0]) - Math.atan2(sg[1] - sl.pivot[1], sg[0] - sl.pivot[0]) - wAng(b.armL.m));
          const dl_ = Math.hypot(WN[0] - EN[0], WN[1] - EN[1]); b.armL.asy = clamp(dl_ / N2, .7, 1.45); rig.compute();
          { const tip = rig.partPoint('armL', sg[0], sg[1]); this.rearErr = Math.hypot(tip[0] - WN[0], tip[1] - WN[1]) }
        } else {
        if (SK.fit) { const D_ = Math.hypot(WN[0] - SN[0], WN[1] - SN[1]), st_ = clamp((D_ / SK.fit - n1) / N2, SK.fitMin ?? .85, SK.fitMax ?? 1.6); b.armL.asy = st_; n2 = N2 * st_ }
        const eN = pick(SN, WN, solve2(SN, WN, n1, n2));
        b.armU.ar += wrapA(Math.atan2(eN[1] - SN[1], eN[0] - SN[0]) - Math.atan2(b.armL.pos[1], b.armL.pos[0]) - wAng(b.armU.m)); rig.compute();
        const EN = apply(b.armL.m, 0, 0); b.armL.ar += wrapA(Math.atan2(WN[1] - EN[1], WN[0] - EN[0]) - Math.atan2(sg[1] - sl.pivot[1], sg[0] - sl.pivot[0]) - wAng(b.armL.m)); rig.compute();
        { const tip = rig.partPoint('armL', sg[0], sg[1]); this.rearErr = Math.hypot(tip[0] - WN[0], tip[1] - WN[1]) }   // 팔이 안 닿은 거리(검사용)
        }
      } else {   // 다가가기: 주먹 그림으로 바꾸고 팔을 그 손목 쪽으로 반쯤
        rig.swap.armL = P.armL.alt || null; const pl = P[P.armL.alt || 'armL'], gp = pl.grip || pl.pivot, M2 = Math.hypot(gp[0] - pl.pivot[0], gp[1] - pl.pivot[1]) * (pl.scale || 1);
        const eN = pick(SN, GN, solve2(SN, GN, n1, M2)), base = b.armU.ar;   // 주먹 그림(armLF)의 쥔 점 = 뒷주먹 쥔 점
        b.armU.ar += wrapA(Math.atan2(eN[1] - SN[1], eN[0] - SN[0]) - Math.atan2(b.armL.pos[1], b.armL.pos[0]) - wAng(b.armU.m)) * Math.min(1, ww * 1.6); rig.compute();
        const EN = apply(b.armL.m, 0, 0); b.armL.ar += wrapA(Math.atan2(GN[1] - EN[1], GN[0] - EN[0]) - Math.atan2(gp[1] - pl.pivot[1], gp[0] - pl.pivot[0]) - wAng(b.armL.m)) * Math.min(1, ww * 1.6); rig.compute() }
      rig.alpha.handR = onN ? 1 : 0; rig.alpha.armL = 1; rig.alpha.handL = on ? 1 : 0; rig.alpha.fistF = on ? 0 : 1;
      if (!onN) this.rearErr = 0;
      b.pauldron.ar = b.armU.ar * (SK.pauldronRot ?? .35);
      rig.compute();
      if (act && !act.hit && t >= D.hitAt) { act.hit = true; const p = this.tip(); this.events.push({ type: "hit", x: p[0], y: p[1] }) }
      const tr = this._tr('trail'), tips = P.weapon.tips;
      tips.forEach((tp, i) => { const Q = this.trailPts[i]; Q.push(rig.partPoint("weapon", tp[0], tp[1])); if (Q.length > 7) Q.shift(); if (tr <= 0) Q.length = 0 });
      rig.trail = tr > 0 ? { a: tr, pts: this.trailPts } : null;
      this.gripOn = on;
    }
    /** 가까운(자유) 팔을 무기 자루 위 한 점에 붙임: 손잡이(weapon 뼈 원점)에서 칼끝 반대쪽으로 gap만큼. 두 관절 IK */
    _nearToShaft(w, gap, ux, uy) {
      const rig = this.rig, b = rig.by; rig.compute();
      if (ux === undefined) { const wp = rig.def.parts.weapon, tm = wp.tips ? [(wp.tips[0][0] + wp.tips[1][0]) / 2, (wp.tips[0][1] + wp.tips[1][1]) / 2] : [wp.pivot[0], 0];
        const T0 = rig.partPoint("weapon", tm[0], tm[1]), G0 = apply(b.weapon.m, 0, 0), l = Math.hypot(T0[0] - G0[0], T0[1] - G0[1]) || 1; ux = (T0[0] - G0[0]) / l; uy = (T0[1] - G0[1]) / l }
      const G2 = apply(b.weapon.m, 0, 0), H2 = [G2[0] - ux * gap, G2[1] - uy * gap];
      const SN = apply(b.armU.m, 0, 0), N1 = Math.hypot(...b.armL.pos), N2 = b.fistN ? Math.hypot(...b.fistN.pos) : 80;
      const sol = solve2(SN, H2, N1, N2), e = rig.def.nearElbowUp ? sol[1] : sol[0];
      const tU = Math.atan2(e[1] - SN[1], e[0] - SN[0]) - Math.atan2(b.armL.pos[1], b.armL.pos[0]);
      b.armU.ar += wrapA(tU - wAng(b.armU.m)) * w; rig.compute();
      if (b.fistN) { const EN = apply(b.armL.m, 0, 0), tL = Math.atan2(H2[1] - EN[1], H2[0] - EN[0]) - Math.atan2(b.fistN.pos[1], b.fistN.pos[0]);
        b.armL.ar += wrapA(tL - wAng(b.armL.m)) * w; rig.compute() }
    }
    /* ---- 창 먼저, 두 손은 자루를 따라 (rig.def.spearGrip, 니콜 스카이 v3 — 2026-10-16) ----
       팔 = 윗팔(어깨→팔꿈치) + 팔뚝·주먹 한 장(시트 그림, 그림 속 자루 방향이 정해져 있음).
       그림을 자루 각도에 맞춰 돌리고(손목 꺾임 = 추가 회전 δ, |δ| ≤ maxWrist), 자루 위 위치 s는 |어깨→팔꿈치| = 윗팔 길이를
       만족하는 2차식의 근으로 정한다 → 주먹은 항상 자루 중심선 위, 팔꿈치는 굽힘 범위 안쪽 해만 고른다.
       후보 = 그림 3장 × δ × 근 2개, 비용 = 선호 위치·손목 꺾임·이전 프레임과의 차이(튐 방지)·그림 바꿈. */
    _gripArm(cfg, S, Lu, A, U, st, tDown) {
      const P = this.rig.def.parts, maxW = (this.rig.def.spearGrip || this.rig.def.swordGrip).maxWrist || .35, aU = Math.atan2(U[1], U[0]);
      let best = null; const rej = this.gripRej = { disc: 0, s: 0, bend: 0, sh: 0, bendV: [] };
      for (let i = 0; i < cfg.pieces.length; i++) {
        const p = P[cfg.pieces[i]], k = p.scale, sd = Math.atan2(p.shaftDir[1], p.shaftDir[0]), eg = [(p.pivot[0] - p.grip[0]) * k, (p.pivot[1] - p.grip[1]) * k];
        for (let dd = -maxW; dd <= maxW + 1e-6; dd += maxW / 10) {
          const rho = aU - sd + dd, c = Math.cos(rho), s_ = Math.sin(rho), o = [c * eg[0] - s_ * eg[1], s_ * eg[0] + c * eg[1]];
          const V = [A[0] + o[0] - S[0], A[1] + o[1] - S[1]], vu = V[0] * U[0] + V[1] * U[1], disc = vu * vu - (V[0] * V[0] + V[1] * V[1] - Lu * Lu);
          if (disc < 0) { rej.disc++; continue }
          for (let ri = 0; ri < 2; ri++) { const s = ri ? -vu + Math.sqrt(disc) : -vu - Math.sqrt(disc);
            if (s < cfg.sMin || s > cfg.sMax) { rej.s++; continue }
            const G = [A[0] + U[0] * s, A[1] + U[1] * s], E = [G[0] + o[0], G[1] + o[1]];
            const up = Math.atan2(E[1] - S[1], E[0] - S[0]), fo = Math.atan2(G[1] - E[1], G[0] - E[0]), bend = wrapA(fo - up);
            if (bend < (cfg.bendMin ?? -2.53) || bend > (cfg.bendMax ?? 0)) { rej.bend++; if (rej.bendV.length < 6) rej.bendV.push(+(bend * 57.3).toFixed(0)); continue }                 // 팔꿈치: 굽는 쪽(−)으로만, 145° 이내
            const sh = wrapA(up - tDown); if (sh < (cfg.shMin ?? -2.97) || sh > (cfg.shMax ?? .96)) { rej.sh++; continue }   // 어깨 범위 (몸통 아래 방향 기준, 캐릭터별 shMin/shMax)
            let cost = ((s - cfg.sPref) / (cfg.sSig || 60)) ** 2 + (dd / .17) ** 2 + (cfg.pieceCosts ? cfg.pieceCosts[i] : (cfg.prefPiece === i ? 0 : (cfg.pieceCost || .15)));
            if (st.ok) cost += ((s - st.s) / 14) ** 2 + (i === st.i && ri !== st.r ? 25 : 0) + (i === st.i ? ((dd - st.d) / .05) ** 2 : (this.act ? 1.2 : 40) + (this.t - (st.swapT ?? -9) < .12 ? 30 : 0));   // 그림 바꿈: 액션 밖에서는 꼭 필요할 때만, 바꾼 뒤 0.12초는 다시 안 바꿈
            if (!best || cost < best.cost) best = { cost, i, ri, s, d: dd, G, E, rho, up, bend };
          }
        }
      }
      if (best) { if (st.ok && st.i !== best.i) st.swapT = this.t; st.ok = true; st.i = best.i; st.r = best.ri; st.s = best.s; st.d = best.d } else { st.ok = false; this.gripMiss = (this.gripMiss || 0) + 1 }
      return best;
    }
    _spearArms(D, at, T) {
      const rig = this.rig, b = rig.by, P = rig.def.parts, SG = rig.def.spearGrip;
      const isSpear = !!(D && D.kind === "spear"), w = isSpear ? this._tr("w") : 0, th = isSpear ? this._tr("th") : 0;
      rig.drawOrder = null; rig.compute();
      const tA = wAng(b.torso.m), C0 = SG.carry, C1 = SG.carryRun || SG.carry, cl = k => lerp(C0[k], C1[k], this.A);
      const Ac = apply(b.torso.m, cl("x"), cl("y")), aC = cl("a") + tA * (SG.tiltFollow ?? .4) + (this.wl || 0);
      let A = Ac, a = aC;
      if (w > 0) { const Ak = apply(b.hip.m, this._tr("gx"), this._tr("gy")), aK = this._tr("sa") + this._tr("shake") * Math.sin(T * 95) * .03;
        A = [lerp(Ac[0], Ak[0], w), lerp(Ac[1], Ak[1], w)]; a = aC + wrapA(aK - aC) * w }
      let U = [Math.cos(a), Math.sin(a)];
      const SN = [b.armU.m[4], b.armU.m[5]], SF = [b.armF.m[4], b.armF.m[5]], tDown = tA + Math.PI / 2;
      // 찌른 순간: 가까운 팔은 한 장 그림(armTH, 어깨 갑옷 포함) — 자루 선을 그 주먹으로 끌어와 겹침
      const TP = P[SG.th?.piece || "armTH"]; let thG = null, thRho = 0;
      if (th > 0 && TP) { thRho = a - Math.atan2(TP.shaftDir[1], TP.shaftDir[0]); const c = Math.cos(thRho), s_ = Math.sin(thRho), k = TP.scale;
        const v = [(TP.grip[0] - TP.pivot[0]) * k, (TP.grip[1] - TP.pivot[1]) * k]; thG = [SN[0] + c * v[0] - s_ * v[1], SN[1] + s_ * v[0] + c * v[1]];
        const N = [-U[1], U[0]], off0 = (thG[0] - A[0]) * N[0] + (thG[1] - A[1]) * N[1], off = off0 * smooth(0, .3, th); this.thOff = off0; A = [A[0] + N[0] * off, A[1] + N[1] * off] }
      // 팔이 창을 들고 있으니 창이 갈 수 있는 곳도 팔이 정한다: 자루 선이 뒷어깨에 dMin 보다 가까워지면 (뒷손 그림이 쥘 수 없음) 부드럽게 아래로 밀어냄
      if (SG.near.dMin) { const N = [-U[1], U[0]], x = (SN[0] - A[0]) * N[0] + (SN[1] - A[1]) * N[1] + SG.near.dMin, k = .5 * (x + Math.sqrt(x * x + 64)) * (1 - smooth(0, .3, th));
        A = [A[0] + N[0] * k, A[1] + N[1] * k]; this.spearPush = k }
      // 앞손이 닿는 거리: 자루 선이 앞어깨에서 dMax 보다 멀어지면 (팔을 다 뻗어도 손목이 꺾임) 부드럽게 어깨 쪽으로 당김
      if (SG.far.dMax) { const N = [-U[1], U[0]], d = (SF[0] - A[0]) * N[0] + (SF[1] - A[1]) * N[1], x = Math.abs(d) - SG.far.dMax, k = .5 * (x + Math.sqrt(x * x + 64)) * Math.sign(d) * (1 - w);   // 공격 키 동작은 키 포즈 그대로
        A = [A[0] + N[0] * k, A[1] + N[1] * k] }
      // 창
      const rw = a + Math.PI / 2; b.weapon.wm = [Math.cos(rw), Math.sin(rw), -Math.sin(rw), Math.cos(rw), A[0], A[1]];
      this.spearA = A; this.spearAng = a;
      const place = (bone, part, rot, X) => { rig.swap[bone] = part === b[bone].part ? null : part; const c = Math.cos(rot), s_ = Math.sin(rot); b[bone].wm = [c, s_, -s_, c, X[0], X[1]] };
      const upperRot = (p, S, E) => Math.atan2(E[1] - S[1], E[0] - S[0]) - Math.atan2(p.elbow[1] - p.pivot[1], p.elbow[0] - p.pivot[0]);
      // 앞손 (먼 팔)
      this.gripF = this.gripF || {}; this.gripN = this.gripN || {};
      const pF = P.armF, LuF = Math.hypot(pF.elbow[0] - pF.pivot[0], pF.elbow[1] - pF.pivot[1]) * pF.scale;
      const fF = this._gripArm(SG.far, SF, LuF, A, U, this.gripF, tDown);
      if (fF) { place("armF", "armF", upperRot(pF, SF, fF.E), SF); place("foreF", SG.far.pieces[fF.i], fF.rho, fF.E); b.fistF.wm = [1, 0, 0, 1, fF.G[0], fF.G[1]]; this.handErr = fF.d }
      // 뒷손 (가까운 팔)
      const pU = P[SG.near.upper], LuN = Math.hypot(pU.elbow[0] - pU.pivot[0], pU.elbow[1] - pU.pivot[1]) * pU.scale;
      const nearCfg = Object.assign({}, SG.near, { sPref: isSpear && D.gap ? -this._tr("gap") : SG.near.sPref });
      let useTH = th >= .3 && thG, fN = null;
      if (!useTH) { fN = this._gripArm(nearCfg, SN, LuN, A, U, this.gripN, tDown);
        if (!fN && th > 0 && thG && this.wasTH) { useTH = true; this.gripMiss = Math.max(0, (this.gripMiss || 1) - 1) } }   // 찌른 팔에서 돌아오는 첫 순간 뒷손이 아직 못 닿으면 찌른 팔 그림을 한 프레임 더 (어긋남 < 1)
      this.wasTH = !!useTH;
      if (useTH) {
        const k = TP.scale, c = Math.cos(thRho), s_ = Math.sin(thRho), ev = [(TP.elbow[0] - TP.pivot[0]) * k, (TP.elbow[1] - TP.pivot[1]) * k], E = [SN[0] + c * ev[0] - s_ * ev[1], SN[1] + s_ * ev[0] + c * ev[1]];
        place("armU", SG.near.upper, upperRot(pU, SN, E), SN);
        const pn = P[SG.near.pieces[1]]; place("armL", SG.near.pieces[1], Math.atan2(thG[1] - E[1], thG[0] - E[0]) - Math.atan2(pn.grip[1] - pn.pivot[1], pn.grip[0] - pn.pivot[0]), E);
        b.armTH.wm = [c, s_, -s_, c, SN[0], SN[1]]; rig.alpha.armTH = 1; rig.alpha.armU = rig.alpha.armL = rig.alpha.pauldron = 0; this.gripN.ok = false; this.gripN.swapT = this.t;
      } else {
        rig.alpha.armTH = 0; rig.alpha.armU = rig.alpha.armL = rig.alpha.pauldron = 1;
        if (fN) { place("armU", SG.near.upper, upperRot(pU, SN, fN.E), SN); place("armL", SG.near.pieces[fN.i], fN.rho, fN.E);
          b.pauldron.ar = wrapA(fN.up - (SG.near.restUp ?? 2.24)) * (SG.near.pauldronFollow ?? .35); this.rearErr = fN.d; this.nearS = fN.s }
      }
      rig.alpha.fistF = 0; rig.alpha.weapon = rig.alpha.armF = rig.alpha.foreF = 1;
      rig.compute();
      const act = this.act;
      if (isSpear && act && !act.hit && at >= D.hitAt) { act.hit = true; const p = this.tip(); this.events.push({ type: "hit", x: p[0], y: p[1] }) }
    }
    /* ---- 대검 두 손 겹쳐 쥐기 (rig.def.swordGrip, 알론소 v4 — 2026-10-17) ----
       평소: 가까운 팔이 메는 손(한 장 그림)으로 칼을 어깨에 멤 — FK 그대로.
       동작(kind "sword"): ① reach: 먼 손이 흔들던 주먹에서 손잡이로 감 (2관절 IK) ② two ≥ .5: 두 손 모두 쥔 손 그림으로 바꿈
       (가까운 손은 손잡이 위쪽 nearS, 먼 손은 아래쪽 farS) ③ w: 칼 위치·각도가 메기 자세에서 키(gx,gy,sa)로.
       칼을 먼저 놓고 두 손은 _gripArm(그림 × 손목 꺾임 × 손잡이 위 미끄러짐)으로 풂 — 못 닿으면 칼을 어깨 쪽으로 당겨 닿는 자리를 찾음.
       칼끝은 땅 아래로 내려가지 않음(groundTip). */
    _swordArms(D, at, T) {
      if (D.rigid) return this._swordRigid(D, at, T);   // 알론소 v4 (opt-in): 그림·팔꿈치를 프레임마다 고르지 않음 → 팔이 튀지 않음
      const rig = this.rig, b = rig.by, P = rig.def.parts, SG = rig.def.swordGrip, act = this.act;
      const w = this._tr("w"), reach = this._tr("reach");
      rig.compute();
      const Wm = b.weapon.m, G0 = [Wm[4], Wm[5]], a0 = Math.atan2(-Wm[3], -Wm[2]);   // 메기 자세의 손잡이 점·칼끝 방향 (무기 그림: 칼끝이 위)
      const SN = apply(b.armF.m, 0, 0), SF = apply(b.armU.m, 0, 0), tA = wAng(b.torso.m), tDown = tA + Math.PI / 2;
      const Gk = apply(b.hip.m, this._tr("gx"), this._tr("gy")), ak = this._tr("sa") + this._tr("shake") * Math.sin(T * 95) * .03;
      const wp = P.weapon, kW = wp.scale || 1, tipL = Math.hypot(wp.tip[0] - wp.pivot[0], wp.tip[1] - wp.pivot[1]) * kW;
      let G = [lerp(G0[0], Gk[0], w), lerp(G0[1], Gk[1], w)], a = a0 + wrapA(ak - a0) * w;
      const ground = () => { const ty = G[1] + Math.sin(a) * tipL, td = SG.tipDepth ?? 6; if (ty > td && Math.cos(a) > 0) a = Math.asin(clamp((td - G[1]) / tipL, -1, 1)) };
      ground();
      const place = (bone, part, rot, X) => { rig.swap[bone] = part === b[bone].part ? null : part; const c = Math.cos(rot), s_ = Math.sin(rot); b[bone].wm = [c, s_, -s_, c, X[0], X[1]] };
      const upperRot = (p, S, E) => Math.atan2(E[1] - S[1], E[0] - S[0]) - Math.atan2(p.elbow[1] - p.pivot[1], p.elbow[0] - p.pivot[0]);
      const ulen = p => Math.hypot(p.elbow[0] - p.pivot[0], p.elbow[1] - p.pivot[1]) * p.scale;
      this.gripN = this.gripN || {}; this.gripF = this.gripF || {};
      if (!this.inSword) { this.gripN.ok = this.gripF.ok = false; this.inSword = true }
      const pN = P[SG.near.upper], pF = P[SG.far.upper], LN = ulen(pN), LF = ulen(pF);
      // 가까운 손: 메는 손 그림(carry)은 칼이 메기 자세에 가까울 때만, 쥔 손 그림은 들어 올린 뒤
      const nc = SG.near.carry, nearCfg = Object.assign({}, SG.near, { pieces: SG.near.pieces.concat(nc ? [nc] : []),
        pieceCosts: SG.near.pieces.map(() => (1 - smooth(.15, .4, w)) * 2).concat(nc ? [smooth(.05, .3, w) * 2] : []) });
      const farOn = reach > .985;
      let fN = null, fF = null, U = null, pull = 0;
      const Gwant = G.slice(), Sm = [(SN[0] + SF[0]) / 2, (SN[1] + SF[1]) / 2];
      for (let k = 0; k <= 12; k++) {   // 못 닿으면 칼(손잡이)을 두 어깨 가운데 쪽으로 조금씩 당김
        const q = k / 12 * .7; G = [lerp(Gwant[0], Sm[0], q), lerp(Gwant[1], Sm[1], q)]; ground(); U = [Math.cos(a), Math.sin(a)];
        fN = this._gripArm(nearCfg, SN, LN, G, U, this.gripN, tDown); fF = farOn ? this._gripArm(SG.far, SF, LF, G, U, this.gripF, tDown) : null; pull = q;
        if (fN) break }   // 칼 위치는 가까운 손만 기준 (먼 손이 못 닿으면 주먹 IK로 손잡이 근처)
      this.swordPull = pull; this.swordA = a; this.swordG = G; this.swordMiss = (fN ? 0 : 1) + (farOn && !fF ? 2 : 0);
      const rw = a + Math.PI / 2; b.weapon.wm = [Math.cos(rw), Math.sin(rw), -Math.sin(rw), Math.cos(rw), G[0], G[1]];
      if (fN) { place("armF", SG.near.upper, upperRot(pN, SN, fN.E), SN); place("foreF", nearCfg.pieces[fN.i], fN.rho, fN.E); this.handErr = fN.d }
      if (fF) { place("armU", SG.far.upper, upperRot(pF, SF, fF.E), SF); place("armL", SG.far.pieces[fF.i], fF.rho, fF.E); this.rearErr = fF.d; b.pauldron.ar = 0 }
      else if (reach > 0) {   // 먼 손이 흔들던 주먹 → 손잡이 아래쪽(farS)으로 감 (2관절 IK, 주먹 그림 그대로)
        this.gripF.ok = false;
        const pl = P[b.armL.part], fc = pl.fist || pl.pivot, kL = pl.scale, fv = [(fc[0] - pl.pivot[0]) * kL, (fc[1] - pl.pivot[1]) * kL];
        const F0 = apply(b.armL.m, fv[0], fv[1]), Gf = [G[0] + U[0] * SG.far.sPref, G[1] + U[1] * SG.far.sPref];
        const Tg = [lerp(F0[0], Gf[0], reach), lerp(F0[1], Gf[1], reach)], L1 = Math.hypot(...b.armL.pos), L2 = Math.hypot(...fv);
        const [eLow, eHigh] = solve2(SF, Tg, L1, L2), e = SG.far.reachElbowUp ? eHigh : eLow;
        const tU = Math.atan2(e[1] - SF[1], e[0] - SF[0]) - Math.atan2(b.armL.pos[1], b.armL.pos[0]);
        b.armU.ar += wrapA(tU - wAng(b.armU.m)); rig.compute();
        const E = apply(b.armL.m, 0, 0), tL = Math.atan2(Tg[1] - E[1], Tg[0] - E[0]) - Math.atan2(fv[1], fv[0]);
        b.armL.ar += wrapA(tL - wAng(b.armL.m)); b.pauldron.ar = b.armU.ar * .3 }
      rig.drawOrder = (reach > .3 || w > .2) ? (rig.def.drawSword || null) : null;
      rig.compute();
      if (act && !act.hit && at >= D.hitAt) { act.hit = true; const p = this.tip(); this.events.push({ type: "hit", x: p[0], y: p[1] }) }
    }
    /* 키 기반 두 손 대검 (D.rigid, 알론소 v4):
       칼(손잡이 점 gx·gy, 각도 sa)을 키로 정하고, 각 손의 '쥔 팔뚝+주먹' 그림은 칼에 그대로 붙임(그림 속 손잡이 = 칼 손잡이, 손목 꺾기 없음).
       팔꿈치 = 그 그림의 팔꿈치 점, 윗팔 그림은 어깨→팔꿈치를 잇도록 돌리고 길이만 늘이거나 줄임(stretch 0.7~1.4).
       어떤 그림을 쓸지는 키(nPiece·fPiece·nUpper·fUpper, 구간별 고정)로 정해서 프레임마다 바뀌지 않음. 그리는 순서도 키(order). */
    _swordRigid(D, at, T) {
      const rig = this.rig, b = rig.by, P = rig.def.parts, SG = rig.def.swordGrip, act = this.act;
      const w = this._tr("w"), reach = this._tr("reach"), step = (k, d) => { const K = D[k]; if (!K) return d; let v = d; for (const [t, n] of K) if (at >= t) v = n; return v };
      { const SN_ = SG.shoulderN, SF_ = SG.shoulderF, kN = SN_ ? this._tr("shN") : 0, kF = SF_ ? this._tr("shF") : 0;   // (opt-in, 21 알론소) 어깨 옮기기: 몸을 튼 것처럼 가까운 어깨(+어깨갑)·먼 어깨를 키만큼 이동 — 3/4 보기에서 두 손이 한 손잡이에 닿게
        if (kN) { b.armU.ax += SN_[0] * kN; b.armU.ay += SN_[1] * kN; const pf = SG.pauldronFollow ?? 1; b.pauldron.ax += SN_[0] * kN * pf; b.pauldron.ay += SN_[1] * kN * pf }
        if (kF) { b.armF.ax += SF_[0] * kF; b.armF.ay += SF_[1] * kF } }
      rig.compute();
      const Wm = b.weapon.m, G0 = [Wm[4], Wm[5]], a0 = Math.atan2(-Wm[3], -Wm[2]);
      const SN = apply(b.armF.m, 0, 0), SF = apply(b.armU.m, 0, 0);
      const Gk = apply(b.hip.m, this._tr("gx"), this._tr("gy")), ak = this._tr("sa") + this._tr("shake") * Math.sin(T * 95) * .03;
      const wp = P.weapon, kW = wp.scale || 1, tipL = Math.hypot(wp.tip[0] - wp.pivot[0], wp.tip[1] - wp.pivot[1]) * kW;
      let G = [lerp(G0[0], Gk[0], w), lerp(G0[1], Gk[1], w)], a = a0 + wrapA(ak - a0) * w;
      const hs = D.hiltSlide ? this._tr("hilt") : 0, tL = tipL - hs;   // (opt-in) 긴 손잡이 줄이기: 칼날(+날밑)이 손 쪽으로 hs만큼 미끄러짐, 손잡이 감은 부분·폼멜은 손에 그대로
      const ty = G[1] + Math.sin(a) * tL, td = SG.tipDepth ?? 6; if (ty > td && Math.cos(a) > 0) a = Math.asin(clamp((td - G[1]) / tL, -1, 1));
      const U = [Math.cos(a), Math.sin(a)];
      this.swordA = a; this.swordG = G; this.swordPull = 0; this.swordMiss = 0;
      const rw = a + Math.PI / 2; b.weapon.wm = [Math.cos(rw), Math.sin(rw), -Math.sin(rw), Math.cos(rw), G[0] - U[0] * hs, G[1] - U[1] * hs];
      if (D.hiltSlide) for (const n of D.hiltSlide) if (b[n]) b[n].wm = [Math.cos(rw), Math.sin(rw), -Math.sin(rw), Math.cos(rw), G[0], G[1]];
      const ang = v => Math.atan2(v[1], v[0]);
      // 쥔 팔뚝 그림을 칼에 붙임 → 팔꿈치 점 반환
      const fore = (bone, pn, s) => { const p = P[pn], k = p.scale || 1, gp = p.grip, el = p.elbow || p.pivot, rho = ang(U) - ang(p.shaftDir);
        const GN = [G[0] + U[0] * s, G[1] + U[1] * s], c = Math.cos(rho), s_ = Math.sin(rho), dx = (gp[0] - p.pivot[0]) * k, dy = (gp[1] - p.pivot[1]) * k;
        const X = [GN[0] - (c * dx - s_ * dy), GN[1] - (s_ * dx + c * dy)];   // 그림 pivot(=팔꿈치)이 놓일 자리
        rig.swap[bone] = pn === b[bone].part ? null : pn; b[bone].wm = [c, s_, -s_, c, X[0], X[1]];
        const ex = (el[0] - p.pivot[0]) * k, ey = (el[1] - p.pivot[1]) * k; return [X[0] + c * ex - s_ * ey, X[1] + s_ * ex + c * ey] };
      // 윗팔 그림: 어깨(S)→팔꿈치(E), 축 방향으로만 늘임
      const upper = (bone, pn, S, E) => { const p = P[pn], k = p.scale || 1, ax = [p.elbow[0] - p.pivot[0], p.elbow[1] - p.pivot[1]], L = Math.hypot(...ax) * k;
        // 팔꿈치가 너무 멀면 어깨를 그쪽으로 내밂(최대 60, 어깨를 앞으로 뻗는 것처럼) → 윗팔 늘이기는 1.25배까지만
        let d = [E[0] - S[0], E[1] - S[1]], dl = Math.hypot(...d); const over = Math.min(60, Math.max(0, dl - L * 1.25));
        if (over > 0) { S = [S[0] + d[0] / dl * over, S[1] + d[1] / dl * over]; d = [E[0] - S[0], E[1] - S[1]]; dl -= over }
        const st = clamp(dl / L, .7, 1.4), phi = ang(ax), rot = ang(d) - phi;
        const R = (t) => [Math.cos(t), Math.sin(t), -Math.sin(t), Math.cos(t), 0, 0];
        let M = mul(R(rot + phi), [st, 0, 0, 1, 0, 0]); M = mul(M, R(-phi)); M[4] = S[0]; M[5] = S[1];
        rig.swap[bone] = pn === b[bone].part ? null : pn; b[bone].wm = M; return st };
      { const tp = step("tPiece", null); rig.swap.torso = tp && tp !== b.torso.part ? tp : null;
        const hd = rig.swap.torso && P[rig.swap.torso].hides; if (hd) for (const h of hd) rig.alpha[h] = 0 }   // 바꾼 상체 그림에 이미 그려진 조각(주머니 등)은 숨김   // 튼 상체(준비 자세) 등 상체 그림 바꾸기 — 구간 고정
      const nP = step("nPiece", SG.near.carry), nU = step("nUpper", SG.near.upper);
      const EN = fore("foreF", nP, this._tr("sN") || 0); this.stN = upper("armF", nU, SN, EN);
      if (b.fistF) b.fistF.wm = null;
      if (reach > .985) {   // 먼 손도 칼에 붙음
        const fP = step("fPiece", SG.far.pieces[0]), fU = step("fUpper", SG.far.upper);
        const EF = fore("armL", fP, this._tr("sF") || SG.far.sPref || 0); this.stF = upper("armU", fU, SF, EF); b.pauldron.ar = 0;
      } else if (reach > 0 && D.reachIK) {   // (opt-in, 21 알론소) 먼 손 잡기·놓기 = 두 관절 IK: 윗팔(어깨→팔꿈치) + 쥔 팔 조각(팔꿈치→주먹)을 진짜 관절처럼 — 손이 막대처럼 미끄러지지 않음.
        //  시작(reach≈0)은 흔들던 팔뚝 방향 그대로, 끝(reach=1)은 칼에 붙은 rigid 자리와 같음(팔 길이 1.0이면 IK 팔꿈치 = rigid 팔꿈치)
        const pl = P[b.armL.part], fc = pl.fist || pl.pivot, kL = pl.scale, fv = [(fc[0] - pl.pivot[0]) * kL, (fc[1] - pl.pivot[1]) * kL];
        const F0 = apply(b.armL.m, fv[0], fv[1]), E0 = apply(b.armL.m, 0, 0), sF = this._tr("sF") || SG.far.sPref || 0, Gf = [G[0] + U[0] * sF, G[1] + U[1] * sF];
        const fP = step("fPiece", SG.far.pieces[0]), fU = step("fUpper", SG.far.upper), p = P[fP], k = p.scale || 1, el = p.elbow || p.pivot, pu = P[fU];
        const gv = [(p.grip[0] - el[0]) * k, (p.grip[1] - el[1]) * k], L2 = Math.hypot(...gv), L1 = Math.hypot(pu.elbow[0] - pu.pivot[0], pu.elbow[1] - pu.pivot[1]) * (pu.scale || 1);
        const e = smooth(0, 1, reach), Tg = [lerp(F0[0], Gf[0], e), lerp(F0[1], Gf[1], e)], bv = SG.far.reachBulge;
        if (bv) { const v = bv[this._tr("reachUp") > .5 ? 0 : 1], C = [Gf[0] + v[0], Gf[1] + v[1]], a_ = (1 - e) * (1 - e), b_ = 2 * e * (1 - e), c_ = e * e;   // (opt-in) 손 경로 = 2차 곡선(흔들던 주먹 → 조절점 → 손잡이). 조절점 = 손잡이 + [잡을 때, 놓을 때] 오프셋 — 얼굴 앞을 지나지 않고 옆·위에서 손잡이로
          Tg[0] = a_ * F0[0] + b_ * C[0] + c_ * Gf[0]; Tg[1] = a_ * F0[1] + b_ * C[1] + c_ * Gf[1] }
        const [eLo, eHi] = solve2(SF, Tg, L1, L2), Ei = this._tr("reachUp") > .5 ? eHi : eLo;
        const rho0 = ang([F0[0] - E0[0], F0[1] - E0[1]]) - ang(gv), rhoI = ang([Tg[0] - Ei[0], Tg[1] - Ei[1]]) - ang(gv), rho1 = ang(U) - ang(p.shaftDir);
        let rho = rho0 + wrapA(rhoI - rho0) * smooth(0, .35, e); rho += wrapA(rho1 - rho) * Math.pow(e, 3);   // 시작: 흔들던 팔뚝 방향 → 중간: IK → 끝: 칼 축(손목이 손잡이에 맞춤)
        const c = Math.cos(rho), s_ = Math.sin(rho), dx = (p.grip[0] - p.pivot[0]) * k, dy = (p.grip[1] - p.pivot[1]) * k, X = [Tg[0] - (c * dx - s_ * dy), Tg[1] - (s_ * dx + c * dy)];
        rig.swap.armL = fP === b.armL.part ? null : fP; b.armL.wm = [c, s_, -s_, c, X[0], X[1]];
        const ex = (el[0] - p.pivot[0]) * k, ey = (el[1] - p.pivot[1]) * k; this.stF = upper("armU", fU, SF, [X[0] + c * ex - s_ * ey, X[1] + s_ * ex + c * ey]); b.pauldron.ar = 0;
      } else if (reach > 0 && D.reachPiece) {   // (opt-in) 먼 손: 처음부터 쥔 팔뚝 그림으로 바꾸고, 흔들던 주먹 자리·팔뚝 방향 → 손잡이로 옮겨 감(IK→그림 바뀜 튐 없음)
        const pl = P[b.armL.part], fc = pl.fist || pl.pivot, kL = pl.scale, fv = [(fc[0] - pl.pivot[0]) * kL, (fc[1] - pl.pivot[1]) * kL];
        const F0 = apply(b.armL.m, fv[0], fv[1]), E0 = apply(b.armL.m, 0, 0), sF = this._tr("sF") || SG.far.sPref || 0, Gf = [G[0] + U[0] * sF, G[1] + U[1] * sF];
        const fP = step("fPiece", SG.far.pieces[0]), fU = step("fUpper", SG.far.upper), p = P[fP], k = p.scale || 1, el = p.elbow || p.pivot;
        const e = smooth(0, 1, reach), rho0 = ang([F0[0] - E0[0], F0[1] - E0[1]]) - ang([p.grip[0] - el[0], p.grip[1] - el[1]]), rho1 = ang(U) - ang(p.shaftDir);
        const rho = rho0 + wrapA(rho1 - rho0) * e, Gp = [lerp(F0[0], Gf[0], e), lerp(F0[1], Gf[1], e)], c = Math.cos(rho), s_ = Math.sin(rho);
        const dx = (p.grip[0] - p.pivot[0]) * k, dy = (p.grip[1] - p.pivot[1]) * k, X = [Gp[0] - (c * dx - s_ * dy), Gp[1] - (s_ * dx + c * dy)];
        rig.swap.armL = fP === b.armL.part ? null : fP; b.armL.wm = [c, s_, -s_, c, X[0], X[1]];
        const ex = (el[0] - p.pivot[0]) * k, ey = (el[1] - p.pivot[1]) * k; this.stF = upper("armU", fU, SF, [X[0] + c * ex - s_ * ey, X[1] + s_ * ex + c * ey]); b.pauldron.ar = 0;
      } else if (reach > 0) {   // 먼 손이 흔들던 주먹 → 손잡이 아래쪽으로 다가감 (2관절 IK, 주먹 그림 그대로, 팔꿈치 방향 고정)
        const pl = P[b.armL.part], fc = pl.fist || pl.pivot, kL = pl.scale, fv = [(fc[0] - pl.pivot[0]) * kL, (fc[1] - pl.pivot[1]) * kL];
        const F0 = apply(b.armL.m, fv[0], fv[1]), sF = this._tr("sF") || SG.far.sPref || 0, Gf = [G[0] + U[0] * sF, G[1] + U[1] * sF];
        const Tg = [lerp(F0[0], Gf[0], reach), lerp(F0[1], Gf[1], reach)], L1 = Math.hypot(...b.armL.pos), L2 = Math.hypot(...fv);
        const [eLow, eHigh] = solve2(SF, Tg, L1, L2), e = (D.reachUp ? this._tr("reachUp") > .5 : SG.far.reachElbowUp) ? eHigh : eLow;   // reachUp(opt-in 키): 구간마다 팔꿈치 위/아래
        const tU = Math.atan2(e[1] - SF[1], e[0] - SF[0]) - Math.atan2(b.armL.pos[1], b.armL.pos[0]);
        b.armU.ar += wrapA(tU - wAng(b.armU.m)); rig.compute();
        const E = apply(b.armL.m, 0, 0), tL = Math.atan2(Tg[1] - E[1], Tg[0] - E[0]) - Math.atan2(fv[1], fv[0]);
        b.armL.ar += wrapA(tL - wAng(b.armL.m)); b.pauldron.ar = b.armU.ar * .3 }
      if (D.reachIK && b.fistN) rig.alpha.fistN = reach > 0 ? 0 : 1;   // 쥔 팔 조각이 팔뚝을 대신하는 동안 흔들던 주먹은 숨김
      const ord = step("order", null);
      rig.drawOrder = (reach > .3 || w > .2 || D.orderAlways) ? (rig.def[ord || "drawSword"] || null) : null;   // orderAlways(opt-in): 쥔 팔 조각이 처음부터 바뀌는 리그(21) — 기본 순서의 메는 주먹이 떠 보이지 않게
      rig.compute();
      if (act && !act.hit && at >= D.hitAt) { act.hit = true; if (D.hitStop) act.freeze = D.hitStop; const p = this.tip(); this.events.push({ type: "hit", x: p[0], y: p[1] }) }   // hitStop(초, opt-in): 칼이 땅에 닿는 순간 잠깐 멈춤(묵직함)
    }
    _waveArms(D, t, T) {
      const rig = this.rig, b = rig.by, P = rig.def.parts, pA = wAng(b.torso.m);
      const w = this._tr('w'), amp = this._tr('wAmp'), wa = this._tr('weapon');
      const ph = Math.sin((t - .34) * TAU * 2.6), ph2 = Math.sin((t - .34) * TAU * 2.6 - .9);   // hand lags the forearm a little
      rig.swap.armL = null;
      // Key pose (user drawing): the FAR (left) arm waves in front — upper arm hanging slightly forward, elbow deeply bent,
      // forearm rising forward-up so the open hand is beside the chin, palm to the viewer; the near arm hangs relaxed.
      // The spear hand rises as a fist, and once the spear is gone the forearm+open-hand drawing takes over.
      const WI0 = rig.def.waveImg, ss = WI0.shoulderShift || [0, 0];
      b.armF.ax += ss[0] * w; b.armF.ay += ss[1] * w; b.wSleeve.ax += ss[0] * w; b.wSleeve.ay += ss[1] * w;   // shoulder joint behind the chest front
      const upW = 1.12 + ((WI0.up ?? .90) - 1.12) * w + amp * ph2 * .03, foreW = (WI0.fore0 ?? -1.08) + amp * ph * .21;    // world directions (rad, y down)
      const tUF = upW - Math.atan2(b.foreF.pos[1], b.foreF.pos[0]) - pA - b.armF.rot;
      b.armF.ar = b.armF.ar + wrapA(tUF - b.armF.ar) * w;
      rig.compute();
      const cF = b.fistF.pos, tFF = foreW - Math.atan2(cF[1], cF[0]) - wAng(b.armF.m) - b.foreF.rot;
      b.foreF.ar = b.foreF.ar + wrapA(tFF - b.foreF.ar) * w;
      b.fistF.ar = b.fistF.ar * (1 - w);
      this.wrist = b.fistF.rot + b.fistF.ar;
      const open = w > .45 && wa < .05;                                      // open arm only while the spear is away
      // ---- open arm = sheet W: sleeve (upper arm) < bandaged forearm < sleeve cuff lip, open LEFT hand (palm to viewer) on top.
      // Angles are world directions of each drawn segment; the hand flicks at the wrist a little behind the forearm.
      const WI = rig.def.waveImg, ph3 = Math.sin((t - .34) * TAU * 2.6 - 1.3);
      rig.compute();
      // follow the (blended) arm exactly, so swapping drawings never changes a segment's direction
      const sh = apply(b.armF.m, 0, 0), el = apply(b.foreF.m, 0, 0), fi = apply(b.fistF.m, 0, 0);
      const upO = Math.atan2(el[1] - sh[1], el[0] - sh[0]), foreO = Math.atan2(fi[1] - el[1], fi[0] - el[0]);
      const handO = foreO + WI.handRest * w + amp * ph3 * .16;
      b.wSleeve.ar = upO - WI.upper - pA - (b.wSleeve.rot || 0); rig.compute();
      b.wFore.ar = foreO - WI.fore - wAng(b.wSleeve.m) - (b.wFore.rot || 0); rig.compute();
      // the open sleeve is longer than the fist-arm sleeve: slide the (hidden) shoulder so both elbows meet at the swap,
      // then let it ease back to its own joint while the arm is up (no pop when the drawings change)
      { const eF = apply(b.foreF.m, 0, 0), eW = apply(b.wFore.m, 0, 0), k = 1 - smooth(.45, .95, w), T_ = b.torso.m, det = T_[0] * T_[3] - T_[1] * T_[2];
        const dx = (eF[0] - eW[0]) * k, dy = (eF[1] - eW[1]) * k;
        b.wSleeve.ax += (T_[3] * dx - T_[2] * dy) / det; b.wSleeve.ay += (-T_[1] * dx + T_[0] * dy) / det; rig.compute();
        b.wFore.ar = foreO - WI.fore - wAng(b.wSleeve.m) - (b.wFore.rot || 0); rig.compute() }
      b.wHand.ar = handO - WI.hand - wAng(b.wFore.m) - (b.wHand.rot || 0);
      this.waveWrist = wrapA(handO - foreO);                                 // wrist bend (audit)
      const on = open ? 1 : 0;
      rig.alpha.wSleeve = rig.alpha.wCuff = on;                              // (a faded sleeve leaves a floating forearm: worse than a clean swap)
      rig.alpha.wFore = rig.alpha.wHand = on;
      rig.alpha.armF = 1 - on; rig.alpha.foreF = rig.alpha.fistF = 1 - on;
      // the body bobs a touch with each wave
      b.hip.ay += amp * Math.max(0, ph) * 3;
      rig.alpha.weapon = wa;
      // far sleeve comes in front of the torso as the arm rises (cross-fade, no pop); the forearm leaves through the cuff
      rig.drawOrder = rig.def.drawWave;                     // open hand in front of the hood edge, sleeve cuff over the forearm
      const act = this.act;
      if (act && !act.hidden && t >= .0) { act.hidden = true; this.events.push({ type: "weaponHide" }) }
      if (act && !act.shown && t >= 1.62) { act.shown = true; this.events.push({ type: "weaponShow" }) }
      rig.trail = null;
      rig.compute();
    }
    update(dt, s = {}) {
      dt = Math.min(dt, .05); this.t += dt; this.dt = dt;
      const rig = this.rig, b = rig.by, L = this.L; rig.resetPose();
      if (rig.def.swordGrip) { rig.swap.foreF = rig.swap.armF = rig.swap.armU = null; if (rig.def.parts.torsoTurn) { rig.swap.torso = null; for (const h of rig.def.parts.torsoTurn.hides || []) rig.alpha[h] = 1 } if (!this.act) this.inSword = false }   // 대검(알론소 v4): 쥔 손 그림은 동작 중에만
      const vx = s.vx || 0, want = this.act ? this.facing : (s.facing || (Math.abs(vx) > 1 ? Math.sign(vx) : this.facing));
      if (want !== this.facing) { this.facing = want; this.turnT = .16; this.prevLVx = -this.prevLVx; for (const k in this.ft) { const f = this.ft[k]; f.planted = false } }
      this.turnT = Math.max(0, this.turnT - dt);
      const lvx = vx * this.facing, sp = Math.abs(vx);
      this.odo += lvx * dt; this.events.length = 0;
      const act = this.act; if (act) { if (act.freeze > 0) act.freeze -= dt; else act.t += dt * (act.speed || 1); /* freeze: 타격 정지(hitStop, opt-in) 동안 동작 시간 멈춤 — 몸·칼 흔들림은 계속 */ if (act.prev) { act.prev.t = Math.min(act.prev.def.dur, act.prev.t + dt); if (act.t > .1) act.prev = null } if (act.t >= act.def.dur) this.act = null }
      const D = act && act.def, at = act ? act.t : 0;
      this.A = damp(this.A, act ? 0 : smooth(15, 200, sp), act ? 14 : 8, dt);
      const G = this.G, A = this.A, I = 1 - A, S = G.strideBase + G.strideK * sp;                 // stride length grows with speed
      if (!act) this.cyc = (this.cyc + dt * (sp * this.stance / S)) % 1;          // cadence chosen so the planted foot moves exactly with the ground
      // body velocity from the action's hip drive (feeds cape / skirt / hem drag like real forward motion)
      const ax_ = act ? this._tr('hipX') : 0; this.actV = damp(this.actV, (ax_ - this.prevActX) / Math.max(dt, 1e-4), 25, dt); this.prevActX = ax_;
      const accel = (lvx - this.prevLVx) / Math.max(dt, 1e-4) + (act ? this.actV * 6 : 0); this.prevLVx = lvx;
      const T = this.t, br = Math.sin(T * TAU / 2.9), ph = this.cyc, psi = (ph * 2) % 1;

      // ---------- pelvis & spine ----------
      const leanA = this.lean.step(act ? 0 : clamp(accel * .0003, -.2, .2), dt);
      const bob = Math.cos(TAU * (psi - .12));                          // +1 lowest (just after contact), -1 highest (flight)
      b.hip.ay = I * br * 4 + A * (G.hipBase + bob * G.bob);
      b.torso.ar = I * br * .012 + A * (G.lean + G.leanBob * bob + G.waddle * Math.sin(TAU * psi)) + leanA;   // waddle: body rocks with each step
      b.torso.asy = 1 + I * br * .013 - A * bob * .01; b.torso.asx = 1 - I * br * .006;
      const hipY = b.hip.ay; this.hipVy = damp(this.hipVy, (hipY - this.prevHipY) / Math.max(dt, 1e-4), 20, dt); this.prevHipY = hipY;
      const hl = this.headLag.step(this.hipVy * .006, dt);
      b.head.ar = I * Math.sin(T * .8) * .025 - A * .15 - leanA * .6 + hl * .02;
      b.head.ay = -I * br * 1.4 + hl * 2.5 + A * G.headBob * bob;
      b.skirt.ar = -leanA * .25 - A * .03;
      let twist = 0;
      if (act) { const lean = this._tr('lean'), brt = this._tr('breath'); twist = this._tr('twist');
        b.hip.ax += ax_; b.hip.ay += this._tr('hipY'); b.torso.ar += lean; b.head.ar += this._tr('head') - lean * .35; b.skirt.ar -= lean * .3;
        b.torso.asy += brt * .022; b.torso.asx -= Math.abs(twist) * .03; b.head.ay -= brt * 5 }
      if (rig.def.skirtFollow) b.skirt.ar += (b.torso.ar - I * br * .012) * rig.def.skirtFollow;   // 허리(골반)가 상체를 따라 기울어 치마 위 끝이 상체 밑단에서 떨어지지 않게 (opt-in)

      // ---------- near arm (opposite to the near leg) ----------
      const swing = Math.cos(TAU * (ph + (rig.def.armPhase || 0)));   // armPhase .5: 자유 팔이 화면 뒤쪽 팔인 캐릭터(알론소) — 같은 쪽 팔다리가 함께 나가지 않게                                 // +1 when the near foot strikes in front
      const fwd = -swing;                                               // near arm forward when the near leg is back
      b.armU.ar = I * br * .03 + A * (-G.armSwing * fwd + G.armBias);
      b.armL.ar = I * (br * .04 - .3) - A * (G.elbowRun + .3 * Math.max(0, fwd) - .14 * Math.max(0, -fwd));   // −.3: a hanging arm keeps ~10° elbow flexion
      b.armU.ax = -twist * 12; b.armF.ax = twist * 15; b.armU.ay = b.armF.ay = act ? -this._tr('breath') * 4 : 0;   // shoulders follow the chest turn / breath
      b.pauldron.ar = b.armU.ar * .42; b.pauldron.ax = -b.armU.ar * 3 + b.armU.ax; b.pauldron.ay = b.armU.ay;   // guard rides on the shoulder, turning with the upper arm
      if (A > .45) this.fist = true; else if (A < .3) this.fist = false; // hand closes while running
      if (rig.def.upperRun) { const p_ = b.armL.pos, l_ = Math.hypot(p_[0], p_[1]) || 1, k_ = (rig.def.upperRun / l_ - 1) * smooth(.3, .8, A); b.armL.ax += p_[0] * k_; b.armL.ay += p_[1] * k_ }   // upperRun(opt-in, 6 카르덴): 달릴 때 윗팔 뼈를 이 길이로 — 서 있을 땐 원화처럼 짧게(화면 쪽으로 줄어든 팔), 옆으로 흔들 땐 먼 팔만큼 길게
      rig.swap.armL = this.fist ? rig.def.parts.armL.alt : null;
      // ---------- far arm + spear: the shaft is locked in the fist; the arm lifts it so the butt clears the ground ----------
      const CS = rig.def.carrySwing ?? 1;   // 무기 팔을 달릴 때 뒤로 젖히는 양 (0 = 서 있을 때 각도 유지)
      b.armF.ar = I * br * .02 + A * (-.30 + .035 * swing) * CS - leanA * .3;
      const wl = this.weapon.step(this.hipVy * .00016 - accel * .00006, dt);
      const torsoTilt = b.torso.ar, want_ = I * br * .01 + A * (-.06 + (rig.def.runTilt || 0)) + wl;    // spear world tilt (rad, 0 = as in the reference)
      const FB = A * (rig.def.runForeBend || 0); b.foreF.ar += FB;   // 달릴 때 창 팔 팔꿈치를 더 굽혀 창을 듦 (긴 창 캐릭터, opt-in — 없으면 0)
      const WR = rig.def.wristRange || .28; b.fistF.ar = clamp(want_ - torsoTilt - b.armF.ar - FB, -WR, WR);   // wrist
      b.weapon.ar = 0;
      if (rig.def.runSlide || rig.def.carryDrop) { const rs = A * (rig.def.runSlide || 0) - (1 - A) * (rig.def.carryDrop || 0); b.weapon.ax = Math.sin(b.weapon.rot) * rs; b.weapon.ay = -Math.cos(b.weapon.rot) * rs }   // 달릴 때만 봉을 손 안에서 위로 밀어 올림 — 서 있을 땐 원화 그대로 (짧은 다리 + 긴 봉, 6 카르덴 opt-in) · carryDrop: 서 있을 때 봉을 그만큼 내림(집게가 땅 가까이, 6 카르덴 10-18)

      // ---------- feet + legs ----------
      this._feet(dt, sp, lvx, S, A);
      rig.compute();
      // a standing leg never locks fully straight (that is where IK snaps): if a planted foot would need more than ~16° short of
      // full extension, the pelvis sinks instead (rises back slowly) — the body lowers, the knee stays soft
      { const Lm = L.thigh + L.shin, dmax = Lm * .99; let need = 0;
        for (const side of ["near", "far"]) { const f = this.ft[side], hard = 1 - smooth(0, rig.def.dropLift || 3, f.lift); if (hard <= 0) continue;   // dropLift: 발이 닿기 전부터 골반을 미리 내림 (넓게 서는 캐릭터, opt-in)   // same weight the soft IK hands over with
          const H = apply(b.hip.m, L.hip[0] + (L[side].hipX ?? L[side].x), L.hip[1])   /* hipX: 알론소 v4 다리 뿌리 안쪽(opt-in) */, Ak = this._ankleFor(f.x, f.lift, f.ang), dx = Ak[0] - H[0], dy = Ak[1] - H[1];
          const nd_ = Math.hypot(dx, dy) > dmax ? hard * (dy - Math.sqrt(Math.max(0, dmax * dmax - dx * dx))) : 0;
          need = Math.max(need, nd_) }
        need = Math.min(need, this.G.dropCap); this.hipDrop = Math.max(need, damp(this.hipDrop || 0, need, 10, dt));   // sinks at once, rises back gently
        if (this.hipDrop > .01) { b.hip.ay += this.hipDrop; rig.compute() } }
      // footReach (opt-in, 6 카르덴 10-18): 동작 중 발이 다리 길이 밖이면(런지 뒤 몸이 돌아올 때) 발을 엉덩이 쪽으로 당김 — 다리와 부츠가 떨어져 보이지 않게
      if (act && rig.def.footReach) { const Lm_ = (L.thigh + L.shin) * rig.def.footReach;
        for (const side of ["near", "far"]) { const f = this.ft[side], H = apply(b.hip.m, L.hip[0] + (L[side].hipX ?? L[side].x), L.hip[1]), Ak = this._ankleFor(f.x, f.lift, f.ang), dx = Ak[0] - H[0], dy = Ak[1] - H[1];
          if (Math.hypot(dx, dy) > Lm_ && Math.abs(dy) < Lm_) { const nx = Math.sign(dx) * Math.sqrt(Lm_ * Lm_ - dy * dy); f.x += nx - dx } } }
      if (rig.def.spearGrip && !(act && D.kind === "wave" && rig.def.waveImg)) { this.wl = wl; this._spearArms(D, at, T) }   // 창 먼저 + 두 손 자루 위 (반응 동작 중에도)
      else if (act && D.kind === "wave" && !rig.def.waveImg) { }   // 손 흔들기 그림이 없는 캐릭터: 몸·표정 트랙만 (반응 동작)
      else if (act && D.kind === "wave") this._waveArms(D, at, T);
      else if (act && D.kind === "sword" && rig.def.swordGrip) this._swordArms(D, at, T);
      else if (act && D.kind === "smash") this._smashArms(D, at, T, act);
      else if (act && D.kind === "staff") this._staffArms(D, at, T, act);   // 봉 키 찌르기 (6 카르덴 opt-in)
      else if (act) { rig.alpha.wSleeve = rig.alpha.wFore = rig.alpha.wHand = rig.alpha.wCuff = 0; rig.alpha.foreF = rig.alpha.weapon = rig.alpha.armF = 1; rig.drawOrder = null; this._actArms(D, at, T) }   // an attack that cuts a wave short clears the wave-only layers
      else { if (rig.drawOrder === rig.def.drawSmash) rig.drawOrder = null; this.trailPts[0].length = this.trailPts[1].length = 0; rig.trail = null; rig.alpha.handL = rig.alpha.handR = rig.alpha.wSleeve = rig.alpha.wFore = rig.alpha.wHand = rig.alpha.wCuff = 0; rig.alpha.foreF = rig.alpha.fistF = rig.alpha.armL = rig.alpha.weapon = rig.alpha.armF = 1; this.gripOn = false; this.handErr = this.rearErr = 0; rig.drawOrder = null }
      if (rig.def.follow) for (const f of rig.def.follow) { const fb = b[f.bone], sb = b[f.src]; if (fb && sb) fb.ar = sb.ar * f.k }   // 따라 도는 조각 (18 네온: 먼 어깨갑이 먼 팔을 35%) — opt-in
      // weaponFloor (opt-in, 6 카르덴 10-18): 봉 끝(그림 아래 가운데)이 땅 위 weaponFloor 보다 내려가면 봉을 손 안에서 그만큼 위로 밀어 올림
      //   — 서 있기·달리기 모두 집게를 땅 바로 위까지 내리되(DHL '표시한 곳까지') 팔 흔들림·가속에서 땅을 뚫지 않게. 봉 키 찌르기(staff) 중엔 키가 봉을 정함
      if (rig.def.weaponFloor != null && !(act && act.def.kind === "staff")) { rig.compute(); const wi_ = rig.images.weapon, yb_ = rig.partPoint("weapon", wi_.width / 2, wi_.height)[1], pen_ = yb_ + rig.def.weaponFloor;
        if (pen_ > 0) { const wm_ = b.weapon.m, cy_ = Math.abs(wm_[3]) / (Math.hypot(wm_[2], wm_[3]) || 1), d_ = pen_ / Math.max(.3, cy_); b.weapon.ax += Math.sin(b.weapon.rot) * d_; b.weapon.ay -= Math.cos(b.weapon.rot) * d_; rig.compute() } }
      if (!act && rig.def.twoHand && !rig.def.spearGrip) { rig.swap.armL = null; this._nearToShaft(1, rig.def.twoHand.gap || 300); b.pauldron.ar = b.armU.ar * .3; rig.compute() }   // 니콜 스카이: 달릴 때도 창을 두 손으로
      const lp = {};
      if (L.near.kneeOut || L.far.kneeOut) this.koW = damp(this.koW ?? 1, (act ? (act.def.kneeOut ?? 0) : 1) * (1 - this.A), act && !act.def.kneeOut ? 16 : 9, dt);   // 동작별 kneeOut(opt-in): 봉 찌르기 런지에서도 가까운 무릎 바깥(시트 10~13)
      for (const side of ["near", "far"]) {
        const f = this.ft[side], H = apply(b.hip.m, L.hip[0] + (L[side].hipX ?? L[side].x), L.hip[1]);
        // ankle range: the boot shaft follows the shin within real dorsi/plantar-flexion limits (re-solve if clamped)
        // ankle range of motion: rotate the boot into range, then re-solve (the ground contact point moves with the angle)
        const [r0, r1] = (this.act && this.act.def.ankleRange) || L.boot.ankleRange || [-9, 9];   // 동작별 발목 범위(opt-in: 런지 뒷발을 평평하게)
        const soft = smooth(0, 3, f.lift);   // lifted foot: soft reach; planted foot: exact (the pelvis drop above keeps the knee soft)
        const kw = L[side].kneeOut ? L[side].kneeOut * this.koW : 0;   // kneeOut: 서 있을 때만 무릎 바깥(달리기·공격이면 0으로 부드럽게)
        let ang = f.ang, sol = this._ik(H, this._ankleFor(f.x, f.lift, ang), soft, kw);
        for (let it = 0; it < 6; it++) { const al = Math.atan2(sol.ankle[1] - sol.knee[1], sol.ankle[0] - sol.knee[0]), r = wrapA(al - Math.PI / 2 - ang);   // wrap: the shin crosses ±180° during the heel kick
          if (r >= r0 - 1e-3 && r <= r1 + 1e-3) break; ang = ang + r - clamp(r, r0, r1); sol = this._ik(H, this._ankleFor(f.x, f.lift, ang), soft, kw) }
        sol.foot = ang; sol.lift = f.lift; lp[side] = sol;
      }
      rig.legPose = lp;

      // ---------- skirt: knees push the front of the hem, the kicking heel lifts the back ----------
      const sk = b.skirt, skP = rig.def.parts.skirt;
      const skPivot = apply(sk.m, 0, 0), restKneeY = apply(b.hip.m, 0, L.hip[1])[1] + L.thigh * .98;
      const cols = this.hem.length - 1, drag = A * 26 + clamp(-accel * .008, -30, 30);
      const actW = act ? this._tr('w') : 0;
      let openT = 0;
      for (let i = 0; i <= cols; i++) {
        const u = i / cols, front = smooth(.45, 1, u), back = smooth(.6, 0, u);
        // running: the whole hem rides up a little (air under the cloth) so the boots show at every step (L41)
        const H_ = rig.def.hemRun || { lift: 0, knee: .9, heel: .55, reach: 0 };
        let tx = -drag * (.6 + .4 * back), ty = A * bob * 5 - A * H_.lift * (.7 + .3 * Math.abs(bob));
        for (const side of ["near", "far"]) {
          const P = lp[side]; let kneeFwd = Math.max(0, P.knee[0] - skPivot[0] - 20), kneeUp = Math.max(0, restKneeY - P.knee[1]);
          let reach = Math.max(0, P.ankle[0] - skPivot[0] - 60), heelBack = Math.max(0, skPivot[0] - 40 - P.ankle[0]); const heelUp = P.lift;
          if (rig.def.hemRest) {   // 서 있는 자세(첫 프레임) 기준으로만 밂: 코트 밑으로 다리가 보이게 넓게 서는 캐릭터 (opt-in, 18 네온)
            const R0 = this.hemRef || (this.hemRef = {}), r0 = R0[side] || (R0[side] = { kx: P.knee[0] - skPivot[0], ky: P.knee[1] - apply(b.hip.m, 0, 0)[1], ax: P.ankle[0] - skPivot[0] });
            const hy = apply(b.hip.m, 0, 0)[1];
            kneeFwd = Math.max(0, P.knee[0] - skPivot[0] - r0.kx); kneeUp = Math.max(0, r0.ky + hy - P.knee[1]);
            reach = Math.max(0, P.ankle[0] - skPivot[0] - r0.ax - 20); heelBack = Math.max(0, r0.ax - 20 - (P.ankle[0] - skPivot[0])) }
          const ak = 1 - actW * (1 - (H_.actKnee ?? 1));   // 공격·준비 자세 중 무릎이 치마 앞자락을 미는 양 (캐릭터별)
          tx += front * (kneeFwd * .8 * (H_.kneeX ?? 1) * ak + reach * .3) - back * heelBack * .35;
          ty -= front * kneeUp * H_.knee * ak + back * heelUp * H_.heel + front * reach * H_.reach * A;
          // lunge: a foot planted far in front drags the front hem up the shin (cloth drapes from the waist over the knee)
          const lunge = actW * clamp((rig.def.hemLungeRel ? P.ankle[0] - this.hipX[side] - 10 : P.ankle[0] - skPivot[0] + 30) * 1.1, 0, 115), fr2 = smooth(.4, .95, u);   // hemLungeRel: 발이 제자리보다 앞으로 나갈 때만 (스카이: 앞발이 원래 앞쪽에 서 있음)
          const LK = H_.lungeK ?? 1; ty -= fr2 * lunge * LK; tx += fr2 * lunge * .35 * (H_.lungeX ?? 1) * LK;
          if (rig.def.flap && i === cols) openT = Math.max(openT, kneeFwd * (rig.def.flap.knee ?? .012) + kneeUp * (rig.def.flap.kneeUp ?? .008) + lunge * (rig.def.flap.lunge ?? .009));   // 앞트임 벌어짐 (18 네온)
        }
        this.hem[i][0].step(tx, dt); this.hem[i][1].step(ty, dt);
      }
      const hem = this.hem, flare = A * (.02 + Math.max(0, -bob) * .03);
      // 천은 뒤집히지 않는다: 밑단이 치마 길이의 45% 넘게 올라가거나 앞뒤로 60% 넘게 밀리면 부드럽게 멈춤 (메시 칸 접힘 방지, 2026-10-16)
      const skH = (rig.images.skirt?.height || 300) * (skP?.scale || 1), HL = rig.def.hemLimit || {}, lyU = skH * (HL.up ?? .45), lx = skH * (HL.x ?? .6);
      const soft = (x, L) => { const a = Math.abs(x), k = .7 * L; return a <= k ? x : Math.sign(x) * (k + (L - k) * Math.tanh((a - k) / (L - k))) };
      this.hemC = this.hemC || []; for (let i = 0; i <= cols; i++) { const x = hem[i][0].x, y = hem[i][1].x; this.hemC[i] = rig.def.hemLimit ? [soft(x, lx), y < 0 ? soft(y, lyU) : y] : [x, y] }   // hemLimit 이 있는 캐릭터만 (8 니콜 원본 동작은 그대로)
      const hc = this.hemC;
      rig.meshFx.skirt = (u, v, x, y) => { const w = v * v * (1.4 - .4 * v), f = u * cols, i = Math.min(cols - 1, Math.floor(f)), t = f - i;
        const hx = lerp(hc[i][0], hc[i + 1][0], t), hy = lerp(hc[i][1], hc[i + 1][1], t); const HG = rig.def.hemGain ?? 1; return [(hx * w + x * flare * w) * HG, hy * w * HG + y * (rig.def.skirtStretch || 0) * v] };   // hemGain(opt-in, 6 카르덴): 원화 바지를 치마 뼈에 얹은 캐릭터 — 바지는 몸처럼 거의 안 늘어남   // skirtStretch: 치마 길이만 늘림 (허리띠를 벨트 뒤로 올린 만큼)
      // 코트 앞자락(앞트임 오른쪽, opt-in rig.def.flap): 같은 코트 변형을 따르고, 앞 무릎·런지만큼 트임 쪽 가장자리가 앞으로 벌어짐 → 안감(뒤판)이 보임
      if (rig.def.flap) { const FL = rig.def.flap, fim = rig.images[FL.part], sim = rig.images.skirt, skFx = rig.meshFx.skirt;
        this.flapOpen = this.flapOpen || new Spring(90, 12);
        if (FL.bounce) { this.flapLag = this.flapLag || Object.assign(new Spring(200, 8), { x: b.hip.ay }); openT += clamp(Math.abs(this.flapLag.step(b.hip.ay, dt) - b.hip.ay) * FL.bounce, 0, .35) }   // 걸음마다 앞자락이 살짝 들썩 (opt-in flap.bounce)
        const op = clamp(this.flapOpen.step(clamp(openT, 0, 1), dt), 0, 1.1); this.flapAmt = op;
        if (fim && sim) rig.meshFx[FL.part] = (u, v, x, y) => { const U = (u * fim.width + FL.off[0]) / sim.width, V = (v * fim.height + FL.off[1]) / sim.height, o = skFx(U, V, x, y), e = Math.pow(V, 1.25) * op;
          return [o[0] + e * FL.openX * (1 - .45 * u), o[1] - e * FL.openY * (1 - .3 * u)] } }

      // ---------- cape: trails behind, flutters, lags the bounce ----------
      const capeA = this.cape.step(clamp(lvx * .0011 + accel * .00012, -.25, .9), dt);
      b.cape.ar = capeA * .22;
      const wph = T * (2.4 + sp * .009), wamp = 5 + sp * .02;
      rig.meshFx.cape = (u, v) => { const w = Math.pow(v, 1.25) * (.35 + .65 * (1 - u)); const wave = Math.sin(wph - v * 4.2 - (1 - u) * 2.4);
        return [(-capeA * 85 + wave * wamp) * w, (-this.hipVy * .035 + wave * wamp * .45 - capeA * 30 * (1 - u)) * w] };

      // ---------- streamers (opt-in, 알론소 v4 목도리 긴 꼬리): 그림 오른쪽 끝(pivot)이 뿌리, 왼쪽(뒤)으로 날리는 천.
      //   동작 시트처럼 서 있어도 바람에 날리고(wind), 달릴수록 펴지고(처짐 sag·droop 줄어듦), 몸이 오르내리거나 갑자기 움직이면 늦게 따라옴(lag) ----------
      if (rig.def.streamers) for (const S of rig.def.streamers) { const bn = b[S.bone]; if (!bn) continue;
        const run = Math.max(S.wind ?? .5, A), L = S.len || 200, ph = T * (S.freq || 7) + (S.phase || 0), amp = (S.amp || 10) * (.55 + .45 * run), sag = (S.sag ?? 25) * (1 - run);
        bn.ar += -(S.droop ?? .4) * (1 - run) + capeA * (S.lag ?? .35) + clamp(this.hipVy * .0007, -.12, .12);
        rig.meshFx[S.part] = (u, v, x, y) => { const q = clamp(-x / L, 0, 1), e = Math.pow(q, 1.35), wv = Math.sin(ph - q * 5.5);
          return [-Math.abs(wv) * amp * .2 * e, (wv * amp + sag * q) * e] } }

      // ---------- braid (optional part): trails back a little, bounces with the steps ----------
      if (b.braid) { const bra = this.braid.step(clamp(lvx * .00022 + accel * .00006 - this.hipVy * .0012, -.12, .2), dt);
        b.braid.ar += clamp(bra, -.12, .2) * .5 + I * Math.sin(T * 1.6) * .02;
        rig.meshFx.braid = (u, v) => [-bra * 30 * v * v, -Math.abs(bra) * 5 * v] }

      // ---------- ponytail (optional bone 'pony'): swings back with speed, bounces with each step ----------
      if (b.pony && rig.def.ponySway) { const k = rig.def.ponySway, po = this.pony.step(clamp(lvx * .0005 + accel * .00012 - this.hipVy * .002, -.3, .45), dt);
        b.pony.ar += po * .9 * k + I * Math.sin(T * 1.9) * .05 * k + A * Math.sin(TAU * psi) * .06 * k }

      // ---------- 출렁이는 작은 조각 (opt-in rig.def.bounce: [{bone, stiff, damp, y, rot, max}], 18 네온 파우치) ----------
      //  골반 높이를 스프링이 늦게 따라감 → (늦은 높이 − 지금 높이)만큼 조각이 덜 따라오고(y) 살짝 돎(rot). 걸음마다 한 번 출렁이고 멈추면 가라앉음
      if (rig.def.bounce) { this.bnc = this.bnc || {}; const hy = b.hip.ay;
        for (const q of rig.def.bounce) { const bb = b[q.bone]; if (!bb) continue;
          const sp_ = this.bnc[q.bone] || (this.bnc[q.bone] = Object.assign(new Spring(q.stiff || 220, q.damp || 9), { x: hy }));
          const M_ = q.max || 12, lag = M_ * Math.tanh((sp_.step(hy, dt) - hy) / M_);   // 부드러운 한계 (딱 멈춤 없음)
          bb.ay += lag * (q.y ?? .6); bb.ar += lag * (q.rot ?? .004) } }
      // ---------- blink ----------
      // expression cross-fade (~70 ms) — only the face patch changes, hood and hair never do
      const fTarget = this._faceAt(D, at), faces = rig.def.faces || {};
      for (const n in faces) this.faceW[n] = n === fTarget ? 1 : 0;   // one-frame switch: a cross-fade between two faces shows double eyes (ghosting)
      rig.face = this.faceW;
      const faceSum = Object.values(this.faceW).reduce((a, v) => a + v, 0);
      if (act || faceSum > .2) { this.blinkT = Math.max(this.blinkT, .35); if (T - this.blinkAt > .02) this.blinkAt = -9 }   // eyes stay on the target / blink only on the base face
      this.blinkT -= dt; if (this.blinkT <= 0) { this.blinkT = 2.2 + Math.random() * 3; this.blinkAt = T }
      const bd = rig.def.blinkFaces ? .17 : .14, bt = T - this.blinkAt; rig.blink = bt < bd ? Math.sin(bt / bd * Math.PI) : 0;
    }
  }
  RunAnimator.ACTIONS = ACTIONS; RunAnimator.EASE = EASE; RunAnimator.GAIT_DEFAULTS = GAIT_DEFAULTS; RunAnimator.GAIT_PRESETS = GAIT_PRESETS;
  global.CharacterRig = CharacterRig; global.RunAnimator = RunAnimator;
})(typeof window !== "undefined" ? window : globalThis);
