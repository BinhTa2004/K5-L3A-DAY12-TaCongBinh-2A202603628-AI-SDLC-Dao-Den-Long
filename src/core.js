/* Pure simulation: no DOM, network, wall clock, rendering or platform dependencies. */
(function (root) {
  'use strict';
  const DT = 1 / 60, EPS = 1e-9;
  const clone = x => JSON.parse(JSON.stringify(x));
  const round = x => Math.round(x * 1000) / 1000;
  const rounded = p => p.map(round);
  const distance = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);
  const within = (a, b, r) => distance(a, b) <= r + EPS;
  // Avoid locale APIs: QuickJS and browsers must order ids identically.
  const byId = (a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
  function fail(message) { throw new Error('ContractError: ' + message); }
  function object(v, name) { if (!v || typeof v !== 'object' || Array.isArray(v)) fail(name + ' must be an object'); }
  function number(v, name, min = -Infinity, integer = false) {
    if (typeof v !== 'number' || !Number.isFinite(v) || v < min || (integer && !Number.isInteger(v))) fail(name + ' is invalid');
  }
  function position(v, name) { if (!Array.isArray(v) || v.length !== 3) fail(name + ' needs xyz'); v.forEach(x => number(x, name)); }
  function validateScenario(s, count) {
    object(s, 'scenario');
    for (const k of ['random_motes', 'random_shades', 'random_drifters', 'wind_enabled']) if (k in s && typeof s[k] !== 'boolean') fail(k + ' must be boolean');
    if ('time_left_s' in s) number(s.time_left_s, 'time_left_s', 0);
    if ('player' in s) {
      object(s.player, 'player');
      if ('pos' in s.player) position(s.player.pos, 'player.pos');
      for (const k of ['carried', 'flames', 'invuln_ticks', 'dash_cd_ticks', 'pulse_cd_ticks', 'charm_ticks']) if (k in s.player) number(s.player[k], k, 0, true);
    }
    for (const name of ['motes', 'shades', 'lanterns', 'drifters', 'charms']) {
      if (!(name in s)) continue;
      if (!Array.isArray(s[name])) fail(name + ' must be an array');
      const ids = new Set();
      s[name].forEach((v, i) => {
        if (name === 'motes' && Array.isArray(v)) { position(v, 'mote'); return; }
        object(v, name);
        if ('pos' in v) position(v.pos, name + '.pos');
        else if (name !== 'charms' && name !== 'lanterns') fail(name + ' needs pos');
        if ('id' in v) { if (typeof v.id !== 'string' || !v.id || ids.has(v.id)) fail('duplicate/invalid ' + name + ' id'); ids.add(v.id); }
        if (name === 'lanterns' && (!/^L[1-9]\d*$/.test(v.id || '') || Number(v.id.slice(1)) > count)) fail('unknown lantern id');
        for (const k of ['deposited', 'stolen', 'state_ticks_left', 'respawn_ticks', 'ttl_ticks']) if (k in v) number(v[k], k, 0, true);
        for (const k of ['lit', 'available']) if (k in v && typeof v[k] !== 'boolean') fail(k + ' must be boolean');
        if (name === 'shades' && 'state' in v && !['spawning', 'wander', 'chase', 'recoil', 'stunned'].includes(v.state)) fail('invalid shade state');
        if (name === 'drifters' && 'state' in v && !['idle', 'chase', 'flee', 'removed'].includes(v.state)) fail('invalid drifter state');
      });
    }
  }
  function validateInputs(inputs) {
    object(inputs, 'inputs');
    const frames = inputs.frames === undefined ? [] : inputs.frames;
    if (!Array.isArray(frames)) fail('frames must be an array');
    let previous = -1;
    for (const f of frames) {
      object(f, 'frame'); number(f.tick, 'frame.tick', 0, true);
      if (f.tick <= previous) fail('frame ticks must increase strictly'); previous = f.tick;
      if ('move' in f) {
        if (!Array.isArray(f.move) || f.move.length !== 2) fail('move needs x,z');
        f.move.forEach(n => { number(n, 'move', -1); if (n > 1) fail('move exceeds 1'); });
      }
      if ('cam_yaw_deg' in f) number(f.cam_yaw_deg, 'cam_yaw_deg');
      for (const k of ['jump', 'interact', 'pulse', 'dash', 'pause']) if (k in f && typeof f[k] !== 'boolean') fail(k + ' must be boolean');
    }
    return frames;
  }
  function random(seed) {
    let a = seed >>> 0;
    return () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t ^= t + Math.imul(t ^ t >>> 7, 61 | t); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  }
  function ring(n, radius, y = 0, cx = 0, start = 0) {
    return Array.from({length: n}, (_, i) => {
      const a = (start + i * 360 / n) * Math.PI / 180;
      return [Math.cos(a) * radius + cx, y, Math.sin(a) * radius];
    });
  }
  function mapFor(night) {
    return {name: 'Đảo Bến', centers: [[0, 0, 0]], radius: 40,
      lanterns: [[0,0,25], [23.8,0,7.7], [14.7,0,-20.2], [-14.7,0,-20.2], [-23.8,0,7.7]],
      motePoints: ring(8,12).concat(ring(16,33)), shadePoints: ring(12,37,0,0,15), pads: [], charms: [], shadeInterval: 480, shadeMax: 6};
  }
  class Game {
    constructor(contract, seed = 1, night = 1, scenario = {}) {
      if (night !== 1) fail('night must be 1');
      this.contract = contract; this.t = clone(contract.tuning); this.night = night; this.map = mapFor(night);
      validateScenario(scenario, this.map.lanterns.length);
      this.rng = random(seed); this.tick = 0; this.simTick = 0; this.state = 'playing'; this.score = 0; this.events = [];
      this.duration = this.t['night' + night + '_duration_s'];
      this.remainingTicks = (scenario.time_left_s === undefined ? this.duration : scenario.time_left_s) * 60;
      this.input = {move: [0,0], cam_yaw_deg: 0, jump: false, interact: false, pulse: false, dash: false, pause: false};
      this.player = {pos: [0,0,0], vel: [0,0,0], carried: 0, flames: this.t.flames, grounded: true,
        invuln: 0, pulseCd: 0, dashCd: 0, charm: 0, dashTicks: 0, facing: [0,1], launched: false};
      const sp = scenario.player || {};
      for (const k of ['pos', 'carried', 'flames']) if (k in sp) this.player[k] = clone(sp[k]);
      this.player.grounded = Math.abs(this.player.pos[1] - this.ground(this.player.pos)) < EPS;
      for (const pair of [['invuln_ticks','invuln'], ['pulse_cd_ticks','pulseCd'], ['dash_cd_ticks','dashCd'], ['charm_ticks','charm']]) this.player[pair[1]] = sp[pair[0]] || 0;
      this.lanterns = this.map.lanterns.map((pos, i) => ({id: 'L'+(i+1), pos: pos.slice(), lit: false, deposited: 0}));
      for (const l of scenario.lanterns || []) Object.assign(this.lanterns.find(x => x.id === l.id), clone(l));
      this.randomMotes = scenario.random_motes !== false; this.randomShades = scenario.random_shades !== false;
      this.moteId = 0; this.shadeId = 0;
      this.motes = []; this.shades = [];
      if (scenario.motes !== undefined) for (const m of scenario.motes) this.addMote(Array.isArray(m) ? m : m.pos, Array.isArray(m) ? {} : m);
      else if (this.randomMotes) for (const pos of this.map.motePoints) for (let j = 0; j < 3; j++) this.addMote(pos);
      for (const s of scenario.shades || []) { const v = clone(s); this.shades.push({id: v.id || 'S'+(++this.shadeId), pos: v.pos, state: v.state || 'chase', timer: v.state_ticks_left || 0}); }
      this.drifters = []; this.charms = []; this.wind = {active: false, dir_deg: 0};
    }
    ground(p) { return Math.hypot(p[0], p[2]) <= this.map.radius + EPS ? 0 : -Infinity; }
    addMote(pos, options = {}) {
      let id = options.id;
      if (!id) { do { id = 'M' + (++this.moteId); } while (this.motes.some(m => m.id === id)); }
      this.motes.push({id, pos: pos.slice(), kind: options.kind || 'random', ttl: options.kind === 'dropped' ? (options.ttl_ticks === undefined ? 900 : options.ttl_ticks) : null});
    }
    emit(name, data = {}) { this.events.push({type: 'event', tick: this.tick, name, data}); }
    direction(from, to) { const d = distance(from, to); return d < EPS ? [0,1] : [(to[0]-from[0])/d, (to[2]-from[2])/d]; }
    hit(by) {
      const p = this.player;
      if (p.invuln > 0) return;
      const dropped = Math.floor(p.carried * this.t.hit_drop_ratio);
      p.carried -= dropped; p.flames = Math.max(0, p.flames - 1); p.invuln = Math.round(this.t.invuln_s * 60);
      for (let i = 0; i < dropped; i++) this.addMote(p.pos, {kind: 'dropped'});
      this.emit('player_hit', {by, flames: p.flames, dropped});
    }
    step(patch = {}) {
      if (this.state === 'won' || this.state === 'lost') return [];
      this.events = []; this.tick++;
      const old = this.input; this.input = Object.assign({}, old, patch); const input = this.input;
      const pressed = k => input[k] && !old[k];
      this.simTick++; this.remainingTicks = Math.max(0, this.remainingTicks - 1);
      const p = this.player, t = this.t;
      for (const k of ['invuln', 'pulseCd', 'dashCd', 'charm']) p[k] = Math.max(0, p[k] - 1);
      for (const s of this.shades) if (s.timer > 0) { s.timer--; if (s.timer === 0) s.state = 'chase'; }
      for (const m of this.motes) if (m.ttl !== null) m.ttl--;
      this.motes = this.motes.filter(m => m.ttl === null || m.ttl > 0);
      let [mx, mz] = input.move, length = Math.hypot(mx, mz); if (length > 1) { mx /= length; mz /= length; }
      const a = input.cam_yaw_deg * Math.PI / 180, dx = mx*Math.cos(a) + mz*Math.sin(a), dz = -mx*Math.sin(a) + mz*Math.cos(a);
      if (Math.hypot(dx,dz) > EPS) p.facing = [dx / Math.hypot(dx,dz), dz / Math.hypot(dx,dz)];
      p.vel[0] = dx*t.player_speed; p.vel[2] = dz*t.player_speed;
      if (pressed('jump') && p.grounded) { p.vel[1] = 8; p.grounded = false; }
      const previous = p.pos.slice();
      p.pos[0] += p.vel[0]*DT; p.pos[2] += p.vel[2]*DT;
      if (!p.grounded) { p.pos[1] += p.vel[1]*DT; p.vel[1] -= 20*DT; }
      const floor = this.ground(p.pos);
      if (p.pos[1] <= floor && p.vel[1] <= 0) { p.pos[1] = floor; p.vel[1] = 0; p.grounded = true; }
      else if (floor < p.pos[1] - EPS && p.grounded) p.grounded = false;
      if (p.pos[1] < -8) { if (t.fall_enabled) this.hit('fall'); p.pos = [0,0,0]; p.vel = [0,0,0]; p.grounded = true; }
      const collected = new Set();
      for (const m of this.motes) if (p.carried < t.carry_capacity && within(p.pos,m.pos,t.pickup_radius)) { p.carried++; collected.add(m.id); this.emit('mote_picked',{carried:p.carried}); }
      this.motes = this.motes.filter(m => !collected.has(m.id));
      if (pressed('interact')) {
        const candidates = this.lanterns.filter(l => !l.lit && within(p.pos,l.pos,t.interact_radius)).sort((a,b) => distance(p.pos,a.pos)-distance(p.pos,b.pos) || byId(a,b));
        if (candidates.length && p.carried > 0) {
          const l = candidates[0], amount = Math.min(p.carried, Math.max(0,t.lantern_cost-l.deposited));
          p.carried -= amount; l.deposited += amount; this.score += amount*t.score.per_mote;
          this.emit('deposit',{lantern_id:l.id,amount,deposited:l.deposited});
          if (l.deposited >= t.lantern_cost) { l.lit = true; this.score += t.score.per_lantern; this.emit('lantern_lit',{lantern_id:l.id}); }
        }
      }
      this.safeShades();
      if (pressed('pulse') && p.pulseCd === 0 && p.carried >= t.pulse_cost) {
        p.carried -= t.pulse_cost; p.pulseCd = Math.round(t.pulse_cooldown_s*60); const stunned_ids = [];
        for (const s of this.shades.slice().sort(byId)) if (within(p.pos,s.pos,t.pulse_radius)) {
          s.state = 'stunned'; s.timer = Math.round(t.pulse_stun_s*60); const d = this.direction(p.pos,s.pos);
          s.pos[0] += d[0]*t.pulse_push_m; s.pos[2] += d[1]*t.pulse_push_m; stunned_ids.push(s.id); this.score += t.score.per_stun;
        }
        this.emit('pulse',{stunned_ids});
      }
      for (const s of this.shades.slice().sort(byId)) {
        if (['stunned','spawning','recoil'].includes(s.state)) continue;
        s.state = 'chase'; const d = this.direction(s.pos,p.pos), step = Math.min(t.shade_speed*DT,distance(s.pos,p.pos));
        s.pos[0] += d[0]*step; s.pos[2] += d[1]*step;
      }
      this.safeShades();
      for (const s of this.shades.slice().sort(byId)) if (!['stunned','spawning','recoil'].includes(s.state) && within(p.pos,s.pos,t.shade_hit_radius)) this.hit('shade');
      this.spawn();
      if (p.flames <= 0) this.finish('lost','no_flames');
      else if (this.lanterns.every(l => l.lit)) this.finish('won','all_lit');
      else if (this.remainingTicks <= 0) this.finish('lost','dawn');
      return this.events;
    }
    safeShades() {
      for (const s of this.shades) for (const l of this.lanterns) if (l.lit && within(s.pos,l.pos,this.t.safe_radius)) {
        const d = this.direction(l.pos,s.pos); s.pos[0] = l.pos[0]+d[0]*(this.t.safe_radius+1e-6); s.pos[2] = l.pos[2]+d[1]*(this.t.safe_radius+1e-6);
      }
    }
    spawn() {
      if (this.randomMotes && this.simTick % 180 === 0 && this.motes.length < 90) this.addMote(this.map.motePoints[Math.floor(this.rng()*this.map.motePoints.length)]);
      if (this.randomShades && this.simTick >= 300 && (this.simTick-300)%this.map.shadeInterval===0) {
        const points = this.map.shadePoints.filter(pos => distance(pos,this.player.pos)>=15);
        for (let i=0; i<2 && this.shades.length<this.map.shadeMax && points.length; i++) {
          let id; do { id='S'+(++this.shadeId); } while (this.shades.some(s=>s.id===id));
          const pos = points.splice(Math.floor(this.rng()*points.length),1)[0]; this.shades.push({id,pos:pos.slice(),state:'spawning',timer:60}); this.emit('shade_spawned',{id});
        }
      }
    }
    finish(state,reason) {
      this.state=state;
      if(state==='won') this.score += Math.floor(this.remainingTicks/60)*this.t.score.per_second_left + this.player.flames*this.t.score.per_flame_left;
      this.emit('game_over',{result:state,reason});
    }
    snapshot() {
      const p=this.player;
      return {type:'snapshot',tick:this.tick,sim_tick:this.simTick,state:this.state,time_left_s:round(this.remainingTicks/60),score:this.score,
        player:{pos:rounded(p.pos),flames:p.flames,carried:p.carried},
        lanterns:this.lanterns.map(l=>({id:l.id,pos:rounded(l.pos),lit:l.lit,deposited:l.deposited})),
        shades:this.shades.map(s=>({id:s.id,pos:rounded(s.pos),state:s.state})),motes_active:this.motes.length,
        motes:this.motes.map(m=>({id:m.id,pos:rounded(m.pos),kind:m.kind,ttl_s:m.ttl===null?null:round(m.ttl/60)}))};
    }
  }
  function run(o) {
    object(o,'options'); number(o.seed,'seed',-Infinity,true); number(o.ticks,'ticks',0,true); number(o.snapshotEvery,'snapshotEvery',1,true);
    const frames=validateInputs(o.inputs||{}), g=new Game(o.contract,o.seed,o.night,o.scenario||{}), lines=[JSON.stringify(g.snapshot())];
    let index=0;
    for(let k=0;k<o.ticks && !['won','lost'].includes(g.state);k++) {
      const frame=index<frames.length && frames[index].tick===k ? frames[index++] : {};
      for(const event of g.step(frame)) lines.push(JSON.stringify(event));
      if(g.tick%o.snapshotEvery===0) lines.push(JSON.stringify(g.snapshot()));
    }
    lines.push(JSON.stringify({type:'end',ticks:g.tick,state:g.state,score:g.score}));
    return lines.join('\n')+'\n';
  }
  root.Lantern={Game,run,validateInputs,validateScenario,mapFor,DT,distance};
})(globalThis);
