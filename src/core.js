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
        for (const k of ['respawn_s', 'ttl_s']) if (k in v&&v[k]!==null) number(v[k], k, 0);
        if(name==='motes'&&'kind' in v&&!['random','dropped'].includes(v.kind))fail('invalid mote kind');
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
    if (night === 2) return {name:'Đảo Cau',centers:[[0,0,0],[70,0,0]],radius:28,
      lanterns:[[0,0,20],[17,0,-10],[-17,0,-10],[70,0,20],[87,0,-10],[53,0,-10]],
      motePoints:ring(4,10).concat(ring(8,22),ring(4,10,0,70),ring(8,22,0,70)),
      shadePoints:ring(8,26,0,0,22.5).concat(ring(8,26,0,70,22.5)),
      pads:[{pos:[20,0,18],target:[70,0,0],vy:14,speed:24},{pos:[50,0,-18],target:[0,0,0],vy:14,speed:24}],
      charms:[[35,0,0]],shadeInterval:420,shadeMax:8};
    if (night === 3) return {name:'Đảo Chuông',centers:[[0,0,0]],radius:45,
      lanterns:[[0,6,6],[18,3,10],[-18,3,10],[35,0,-10],[-35,0,-10],[20,0,-35],[-20,0,-35]],
      motePoints:ring(18,34).concat(Array.from({length:8},(_,i)=>{const a=(20+i*20)*Math.PI/180;return [18*Math.cos(a),3,18*Math.sin(a)];}),ring(4,5,6,0,45)),
      shadePoints:ring(16,43),pads:[{pos:[0,3,13],target:[0,6,0],vy:12,speed:8}],
      charms:[[30,0,25],[-30,0,25]],shadeInterval:360,shadeMax:10};
    return {name: 'Đảo Bến', centers: [[0, 0, 0]], radius: 40,
      lanterns: [[0,0,25], [23.8,0,7.7], [14.7,0,-20.2], [-14.7,0,-20.2], [-23.8,0,7.7]],
      motePoints: ring(8,12).concat(ring(16,33)), shadePoints: ring(12,37,0,0,15), pads: [], charms: [], shadeInterval: 480, shadeMax: 6};
  }
  class Game {
    constructor(contract, seed = 1, night = 1, scenario = {}) {
      if (![1,2,3].includes(night)) fail('night must be 1, 2 or 3');
      this.contract = contract; this.t = clone(contract.tuning); this.night = night; this.map = mapFor(night);
      validateScenario(scenario, this.map.lanterns.length);
      this.rng = random(seed); this.tick = 0; this.simTick = 0; this.state = 'playing'; this.score = 0; this.events = [];
      this.duration = this.t['night' + night + '_duration_s'];
      this.remainingTicks = (scenario.time_left_s === undefined ? this.duration : scenario.time_left_s) * 60;
      this.input = {move: [0,0], cam_yaw_deg: 0, jump: false, interact: false, pulse: false, dash: false, pause: false};
      this.player = {pos: [0,0,0], vel: [0,0,0], carried: 0, flames: this.t.flames, grounded: true,
        invuln: 0, pulseCd: 0, dashCd: 0, charm: 0, dashTicks: 0, facing: [0,1], launched: false,
        launchVel:[0,0],dashDir:[0,1],respawn:0,verticalSaved:null};
      const sp = scenario.player || {};
      for (const k of ['pos', 'carried', 'flames']) if (k in sp) this.player[k] = clone(sp[k]);
      this.player.grounded = Math.abs(this.player.pos[1] - this.support(this.player.pos)) < EPS;
      for (const pair of [['invuln_ticks','invuln'], ['pulse_cd_ticks','pulseCd'], ['dash_cd_ticks','dashCd'], ['charm_ticks','charm']]) this.player[pair[1]] = sp[pair[0]] || 0;
      this.lanterns = this.map.lanterns.map((pos, i) => ({id: 'L'+(i+1), pos: pos.slice(), lit: false, deposited: 0}));
      for (const l of scenario.lanterns || []) Object.assign(this.lanterns.find(x => x.id === l.id), clone(l));
      this.randomMotes = scenario.random_motes !== false; this.randomShades = scenario.random_shades !== false;
      this.moteId = 0; this.shadeId = 0;
      this.motes = []; this.shades = [];
      if (scenario.motes !== undefined) for (const m of scenario.motes) this.addMote(Array.isArray(m) ? m : m.pos, Array.isArray(m) ? {} : m);
      else if (this.randomMotes) {
        const points=this.map.motePoints.slice();
        for(let i=0;i<20&&points.length;i++) this.addMote(points.splice(Math.floor(this.rng()*points.length),1)[0]);
      }
      for (const s of scenario.shades || []) { const v = clone(s); let id=v.id;if(!id){do{id='S'+(++this.shadeId);}while(this.shades.some(x=>x.id===id)||(scenario.shades||[]).some(x=>x.id===id));}const timer=v.state_ticks_left===undefined?({spawning:60,stunned:120,recoil:60}[v.state]||0):v.state_ticks_left;this.shades.push({id, pos:v.pos, state:v.state||'chase', timer,pushTicks:0,pushDir:[1,0],recoilTicks:v.state==='recoil'?timer:0,recoilDir:[1,0]}); }
      this.randomDrifters=scenario.random_drifters!==false;
      this.drifterId=0;
      this.drifters=(scenario.drifters||[]).map(d=>({id:d.id||'D'+(++this.drifterId),pos:d.pos.slice(),state:d.state||'idle',stolen:d.stolen||0,timer:d.state_ticks_left===undefined?((d.state==='flee')?240:0):d.state_ticks_left,dir:[1,0],hasStolen:(d.stolen||0)>0}));
      this.charms=(scenario.charms===undefined?this.map.charms.map((pos,i)=>({id:'C'+(i+1),pos})):scenario.charms).map((c,i)=>({id:c.id||'C'+(i+1),pos:(c.pos||this.map.charms[i]||[0,0,0]).slice(),available:c.available!==false,respawn:c.respawn_ticks||Math.round((c.respawn_s||0)*60)}));
      this.windEnabled=night===3&&scenario.wind_enabled!==false;this.wind={active:false,dir_deg:0};this.windWarning=false;
    }
    ramp(p) {
      if(this.night!==3)return null;
      for(const deg of[30,150]){const a=deg*Math.PI/180,r=p[0]*Math.cos(a)+p[2]*Math.sin(a),side=-p[0]*Math.sin(a)+p[2]*Math.cos(a);if(r>=24-EPS&&r<=30+EPS&&Math.abs(side)<=1.5+EPS)return (30-r)/2;}
      return null;
    }
    ground(p) {
      if(this.night===2)return (this.map.centers.some(c=>distance(p,c)<=28+EPS)||(p[0]>=26-EPS&&p[0]<=44+EPS&&Math.abs(p[2])<=2+EPS))?0:-Infinity;
      const r=Math.hypot(p[0],p[2]);if(r>this.map.radius+EPS)return -Infinity;
      if(this.night!==3)return 0;
      const ramp=this.ramp(p);if(ramp!==null)return ramp;
      if(r<=8+EPS)return 6;
      if(r>=12-EPS&&r<=24+EPS&&p[2]>0)return 3;
      return 0;
    }
    support(p) {
      const top=this.ground(p);
      // A scenario may place Mây under a terrace; do not teleport to its roof.
      return top<=p[1]+.08?top:(Number.isFinite(top)?0:top);
    }
    addMote(pos, options = {}) {
      let id = options.id;
      if (!id) { do { id = 'M' + (++this.moteId); } while (this.motes.some(m => m.id === id)); }
      this.motes.push({id, pos: pos.slice(), kind: options.kind || 'random', ttl: options.kind === 'dropped' ? (options.ttl_ticks === undefined ? (options.ttl_s===undefined?480:Math.round(options.ttl_s*60)) : options.ttl_ticks) : null,born:this.simTick});
    }
    emit(name, data = {}) { this.events.push({type: 'event', tick: this.tick, name, data}); }
    direction(from, to) { const d = distance(from, to); return d < EPS ? [1,0] : [(to[0]-from[0])/d, (to[2]-from[2])/d]; }
    dropMotes(pos,count) {
      for(let i=0;i<count;i++){const a=this.rng()*Math.PI*2,r=1.5+this.rng();const x=pos[0]+Math.cos(a)*r,z=pos[2]+Math.sin(a)*r;let y=this.ground([x,pos[1],z]);if(!Number.isFinite(y))y=pos[1];this.addMote([x,y,z],{kind:'dropped'});}
    }
    hit(by) {
      const p = this.player;
      if(by==='fall'){
        const lost=p.carried;p.carried=0;p.flames=Math.max(0,p.flames-1);p.respawn=p.flames>0?60:0;p.vel=[0,0,0];p.dashTicks=0;p.launched=false;p.verticalSaved=null;
        this.emit('player_hit',{by,flames:p.flames,dropped:0,lost});return;
      }
      if (p.invuln > 0) return;
      const dropped = Math.floor(p.carried * this.t.hit_drop_ratio);
      p.carried -= dropped; p.flames = Math.max(0, p.flames - 1); p.invuln = Math.round(this.t.invuln_s * 60);
      this.dropMotes(p.pos,dropped);
      this.emit('player_hit', {by, flames: p.flames, dropped});
    }
    step(patch = {}) {
      if (this.state === 'won' || this.state === 'lost') return [];
      this.events = []; this.tick++;
      const old = this.input; this.input = Object.assign({}, old, patch); const input = this.input;
      const pressed = k => input[k] && !old[k];
      if(pressed('pause')){this.state=this.state==='paused'?'playing':'paused';this.emit(this.state==='paused'?'paused':'resumed');if(this.state==='paused')return this.events;}
      if(this.state==='paused')return this.events;
      this.simTick++; this.remainingTicks = Math.max(0, this.remainingTicks - 1);
      const p = this.player, t = this.t;
      for (const k of ['invuln', 'pulseCd', 'dashCd', 'charm']) p[k] = Math.max(0, p[k] - 1);
      for (const s of this.shades) {
        if(s.timer>0){s.timer--;if(s.timer===0&&!(s.state==='recoil'&&s.recoilTicks>0))s.state='wander';}
        else if(s.state==='recoil'&&s.recoilTicks===0)s.state='wander';
      }
      for(const d of this.drifters)if(d.state==='flee'&&d.timer>0){d.timer--;if(d.timer===0)d.state='removed';}
      this.drifters=this.drifters.filter(d=>d.state!=='removed');
      for(const c of this.charms)if(!c.available&&c.respawn>0){c.respawn--;if(c.respawn===0)c.available=true;}
      for (const m of this.motes) if (m.ttl !== null) m.ttl--;
      this.motes = this.motes.filter(m => m.ttl === null || m.ttl > 0);
      let justRespawned=false;
      if(p.respawn>0){p.respawn--;if(p.respawn===0){p.pos=[0,0,0];p.vel=[0,0,0];p.invuln=90;p.grounded=this.support(p.pos)===p.pos[1];justRespawned=true;}}
      if(this.windEnabled){const k=this.simTick%1800;if(k===1680){this.wind.dir_deg=this.rng()*360;this.windWarning=true;}if(k===0){this.wind.active=true;this.windWarning=false;}if(k===300)this.wind.active=false;}
      if(p.respawn===0&&!justRespawned){
      let [mx, mz] = input.move, length = Math.hypot(mx, mz); if (length > 1) { mx /= length; mz /= length; }
      const a = input.cam_yaw_deg * Math.PI / 180, dx = mx*Math.cos(a) + mz*Math.sin(a), dz = -mx*Math.sin(a) + mz*Math.cos(a);
      if (Math.hypot(dx,dz) > EPS) p.facing = [dx / Math.hypot(dx,dz), dz / Math.hypot(dx,dz)];
      const running=p.charm>0?7.2:t.player_speed;
      if(p.dashTicks===0&&p.verticalSaved!==null){p.vel[1]=p.verticalSaved;p.verticalSaved=null;}
      if(!p.launched){p.vel[0]=dx*running;p.vel[2]=dz*running;}else{p.vel[0]=p.launchVel[0];p.vel[2]=p.launchVel[1];}
      for(const pad of this.map.pads)if(p.grounded&&within(p.pos,pad.pos,1)&&Math.abs(p.pos[1]-pad.pos[1])<=.1){const d=this.direction(pad.pos,pad.target);p.launched=true;p.launchVel=[d[0]*pad.speed,d[1]*pad.speed];p.vel=[p.launchVel[0],pad.vy,p.launchVel[1]];p.grounded=false;}
      if (pressed('jump') && p.grounded) { p.vel[1] = t.jump_speed; p.grounded = false; }
      if(pressed('dash')&&p.dashTicks===0&&(p.dashCd===0||p.charm>0)){p.dashTicks=12;p.dashCd=p.charm>0?0:90;p.dashDir=p.facing.slice();p.verticalSaved=p.vel[1];p.vel[1]=0;this.emit('dash');}
      if(p.dashTicks>0){p.vel[0]=p.dashDir[0]*t.dash_speed;p.vel[2]=p.dashDir[1]*t.dash_speed;}
      const previous = p.pos.slice();
      p.pos[0] += p.vel[0]*DT; p.pos[2] += p.vel[2]*DT;
      if(this.wind.active){const w=this.wind.dir_deg*Math.PI/180;p.pos[0]+=Math.cos(w)*2*DT;p.pos[2]+=Math.sin(w)*2*DT;}
      if (!p.grounded && p.dashTicks===0) { p.pos[1] += p.vel[1]*DT + .5*t.gravity*DT*DT; p.vel[1] += t.gravity*DT; }
      let floor = this.ground(p.pos);
      const ramp=this.ramp(p.pos), rampWalk=p.grounded&&ramp!==null&&Math.abs(ramp-previous[1])<.25;
      const wall=Number.isFinite(floor)&&floor>p.pos[1]+.1&&!rampWalk&&this.ground(previous)<=previous[1]+.1;
      const tower=this.night===3&&Math.hypot(p.pos[0],p.pos[2])<2&&p.pos[1]>=6-EPS&&p.pos[1]<14;
      if(wall||tower){p.pos[0]=previous[0];p.pos[2]=previous[2];floor=this.support(previous);}
      if(floor>p.pos[1]+.1&&previous[1]<floor-EPS)floor=this.support(p.pos);
      if(rampWalk){p.pos[1]=ramp;p.vel[1]=0;floor=ramp;}
      if (p.pos[1] <= floor+EPS && p.vel[1] <= 0 && (previous[1]>=floor-EPS||rampWalk)) { p.pos[1] = floor; p.vel[1] = 0; p.grounded = true;p.launched=false; }
      else if (floor < p.pos[1] - EPS && p.grounded) p.grounded = false;
      if(p.grounded&&!p.launched)for(const pad of this.map.pads)if(within(p.pos,pad.pos,1)&&Math.abs(p.pos[1]-pad.pos[1])<=.1){const d=this.direction(pad.pos,pad.target);p.launched=true;p.launchVel=[d[0]*pad.speed,d[1]*pad.speed];if(p.dashTicks===0)p.vel=[p.launchVel[0],pad.vy,p.launchVel[1]];else p.verticalSaved=pad.vy;p.grounded=false;}
      if(p.dashTicks>0)p.dashTicks--;
      if (p.pos[1] < -10) { if (t.fall_enabled) this.hit('fall'); }
      }
      if(p.respawn===0&&p.flames>0&&!justRespawned){
      const collected = new Set();
      for (const m of this.motes) if (m.born<this.simTick&&p.carried < t.carry_capacity && within(p.pos,m.pos,t.pickup_radius)&&Math.abs(p.pos[1]-m.pos[1])<=1.5+EPS) { p.carried++; collected.add(m.id); this.emit('mote_picked',{carried:p.carried}); }
      this.motes = this.motes.filter(m => !collected.has(m.id));
      for(const c of this.charms)if(c.available&&within(p.pos,c.pos,t.pickup_radius)&&Math.abs(p.pos[1]-c.pos[1])<=1.5+EPS){c.available=false;c.respawn=2700;p.charm=600;this.emit('charm_picked',{charm_id:c.id,charm_ticks:600});}
      if (pressed('interact')) {
        const candidates = this.lanterns.filter(l => !l.lit && within(p.pos,l.pos,t.interact_radius)).sort((a,b) => distance(p.pos,a.pos)-distance(p.pos,b.pos) || byId(a,b));
        if (candidates.length && p.carried > 0) {
          const l = candidates[0], amount = Math.min(p.carried, Math.max(0,t.lantern_cost-l.deposited));
          p.carried -= amount; l.deposited += amount; this.score += amount*t.score.per_mote;
          this.emit('deposit',{lantern_id:l.id,amount,deposited:l.deposited});
          if (l.deposited >= t.lantern_cost) { l.lit = true; this.score += t.score.per_lantern; this.emit('lantern_lit',{lantern_id:l.id}); }
        }
      }
      }
      this.safeShades();
      if (p.respawn===0 && p.flames>0 && !justRespawned && pressed('pulse') && p.pulseCd === 0 && p.carried >= t.pulse_cost) {
        p.carried -= t.pulse_cost; p.pulseCd = Math.round(t.pulse_cooldown_s*60); const stunned_ids = [];
        const pulseHits=pos=>Math.hypot(pos[0]-p.pos[0],pos[1]-p.pos[1]-.8,pos[2]-p.pos[2])<=t.pulse_radius+EPS;
        for (const s of this.shades.slice().sort(byId)) if (pulseHits(s.pos)) {
          s.state = 'stunned'; s.timer = Math.round(t.pulse_stun_s*60);s.pushDir=this.direction(p.pos,s.pos);s.pushTicks=15;
          stunned_ids.push(s.id); this.score += t.score.per_stun;
        }
        for(const d of this.drifters)if(pulseHits(d.pos)){
          if(d.state==='chase'){d.state='flee';d.timer=240;d.dir=this.direction(p.pos,d.pos);d.hasStolen=true;}
          else if(d.state==='flee'&&d.stolen>0){const amount=d.stolen;const pos=d.pos.slice(),floor=this.ground(pos);if(Number.isFinite(floor))pos[1]=floor;for(let i=0;i<amount;i++)this.addMote(pos,{kind:'dropped'});d.stolen=0;d.timer=120;this.emit('drifter_drop',{drifter_id:d.id,amount});}
        }
        this.emit('pulse',{stunned_ids});
      }
      for (const s of this.shades.slice().sort(byId)) {
        if(s.safeTicks>0){const l=this.lanterns.find(l=>l.id===s.safeId);const d=this.direction(l.pos,s.pos),len=distance(l.pos,s.pos),push=Math.max(0,t.safe_radius-len)/s.safeTicks;s.pos[0]+=d[0]*push;s.pos[2]+=d[1]*push;s.safeTicks--;if(s.safeTicks===0){s.pos[0]=l.pos[0]+d[0]*t.safe_radius;s.pos[2]=l.pos[2]+d[1]*t.safe_radius;}continue;}
        if(s.state==='stunned'){if(s.pushTicks>0){this.moveShade(s,s.pushDir,t.pulse_push_m/15);s.pushTicks--;}continue;}
        if(s.state==='spawning')continue;
        if(s.state==='recoil'){if(s.recoilTicks>0){this.moveShade(s,s.recoilDir,2/60);s.recoilTicks--;}continue;}
        const dist=distance(s.pos,p.pos);
        if(s.state==='chase'&&dist>18)s.state='wander';else if(s.state==='wander'&&dist<=12+EPS)s.state='chase';
        const d=s.state==='chase'?this.direction(s.pos,p.pos):[Math.cos(this.simTick*.008+s.pos[0]),Math.sin(this.simTick*.008+s.pos[2])];
        this.moveShade(s,d,Math.min((this.night===3?4.5:t.shade_speed)*DT,dist));
      }
      this.moveDrifters();
      if(p.respawn===0&&p.flames>0&&!justRespawned){
        for(const d of this.drifters.slice().sort(byId))if(!d.hasStolen&&d.state==='chase'&&within(d.pos,p.pos,1.2)){
          const amount=Math.min(3,p.carried);p.carried-=amount;d.stolen=amount;d.hasStolen=true;d.state='flee';d.timer=240;d.dir=this.direction(p.pos,d.pos);this.emit('drifter_steal',{drifter_id:d.id,amount,carried:p.carried});
        }
        for (const s of this.shades.slice().sort(byId)) if (!['stunned','spawning','recoil'].includes(s.state)&&!s.safeTicks&&p.invuln===0&&within(p.pos,s.pos,t.shade_hit_radius)&&Math.abs(p.pos[1]-s.pos[1])<=1.5+EPS){this.hit('shade');s.state='recoil';s.timer=60;s.recoilTicks=60;s.recoilDir=this.direction(p.pos,s.pos);break;}
      }
      this.spawn();
      if (p.flames <= 0) this.finish('lost','no_flames');
      else if (this.lanterns.every(l => l.lit)) this.finish('won','all_lit');
      else if (this.remainingTicks <= 0) this.finish('lost','dawn');
      return this.events;
    }
    safeShades() {
      for (const s of this.shades) for (const l of this.lanterns) if (l.lit && distance(s.pos,l.pos)<this.t.safe_radius-EPS&&!s.safeTicks) {
        s.safeTicks=30;s.safeId=l.id;
      }
    }
    moveShade(s,d,step){
      const next=[s.pos[0]+d[0]*step,s.pos[1],s.pos[2]+d[1]*step];
      for(const l of this.lanterns)if(l.lit&&distance(s.pos,l.pos)>=this.t.safe_radius-EPS&&distance(next,l.pos)<this.t.safe_radius){const dir=this.direction(l.pos,next);next[0]=l.pos[0]+dir[0]*this.t.safe_radius;next[2]=l.pos[2]+dir[1]*this.t.safe_radius;}
      if(this.night===3&&Math.hypot(next[0],next[2])<2&&s.pos[1]>=6&&s.pos[1]<14)return;
      const before=this.ground(s.pos),after=this.ground(next);if(Number.isFinite(before)&&Number.isFinite(after)&&after>before+.3&&this.ramp(next)===null)return;
      if(Number.isFinite(after)&&Number.isFinite(before)&&Math.abs(after-before)<.3)next[1]+=after-before;
      s.pos=next;
    }
    moveDrifters(){
      const p=this.player;
      for(const d of this.drifters){
        if(d.state!=='flee')d.state=p.carried>=5&&within(d.pos,p.pos,15)?'chase':'idle';
        let dir,speed;
        if(d.state==='chase'){dir=this.direction(d.pos,p.pos);speed=7;}
        else if(d.state==='flee'){dir=this.direction(p.pos,d.pos);d.dir=dir;speed=7;}
        else{const angle=this.simTick*.008+Number(d.id.replace(/\D/g,''));dir=[Math.cos(angle),Math.sin(angle)];speed=2;}
        d.pos[0]+=dir[0]*speed*DT;d.pos[2]+=dir[1]*speed*DT;
      }
    }
    spawn() {
      if (this.randomMotes && this.simTick % 240 === 0 && this.motes.length < 30){const empty=this.map.motePoints.filter(pos=>!this.motes.some(m=>within(m.pos,pos,.01)&&Math.abs(m.pos[1]-pos[1])<.1));if(empty.length)this.addMote(empty[Math.floor(this.rng()*empty.length)]);}
      if (this.randomShades && this.simTick >= 300 && (this.simTick-300)%this.map.shadeInterval===0) {
        const points = this.map.shadePoints.filter(pos => distance(pos,this.player.pos)>=15);
        for (let i=0; i<(this.simTick===300?2:1) && this.shades.length<this.map.shadeMax && points.length; i++) {
          let id; do { id='S'+(++this.shadeId); } while (this.shades.some(s=>s.id===id));
          const pos = points.splice(Math.floor(this.rng()*points.length),1)[0].slice();pos[1]=this.ground(pos)+.8;this.shades.push({id,pos,state:'spawning',timer:60,pushTicks:0,pushDir:[1,0],recoilTicks:0,recoilDir:[1,0]}); this.emit('shade_spawned',{id});
        }
      }
      if(this.randomDrifters&&this.night>=2&&this.simTick%1200===0&&this.drifters.length<2){let id;do{id='D'+(++this.drifterId);}while(this.drifters.some(d=>d.id===id));const pos=this.map.shadePoints[Math.floor(this.rng()*this.map.shadePoints.length)].slice();this.drifters.push({id,pos,state:'idle',stolen:0,timer:0,dir:[1,0],hasStolen:false});}
    }
    finish(state,reason) {
      this.state=state;
      if(state==='won') this.score += Math.floor(this.remainingTicks/60)*this.t.score.per_second_left + this.player.flames*this.t.score.per_flame_left;
      this.emit('game_over',{result:state,reason});
    }
    snapshot() {
      const p=this.player;
      return {type:'snapshot',tick:this.tick,sim_tick:this.simTick,state:this.state,night:this.night,wind:{active:this.wind.active,dir_deg:round(this.wind.dir_deg)},time_left_s:round(this.remainingTicks/60),score:this.score,
        player:{pos:rounded(p.pos),vel:rounded(p.vel),grounded:p.grounded,invuln:p.invuln>0,dash_cd_s:round(p.dashCd/60),pulse_cd_s:round(p.pulseCd/60),charm_s:round(p.charm/60),flames:p.flames,carried:p.carried},
        lanterns:this.lanterns.map(l=>({id:l.id,pos:rounded(l.pos),lit:l.lit,deposited:l.deposited})),
        shades:this.shades.map(s=>({id:s.id,pos:rounded(s.pos),state:s.state})),motes_active:this.motes.length,
        motes:this.motes.map(m=>({id:m.id,pos:rounded(m.pos),kind:m.kind,ttl_s:m.ttl===null?null:round(m.ttl/60)})),
        drifters:this.drifters.map(d=>({id:d.id,pos:rounded(d.pos),state:d.state,stolen:d.stolen})),charms:this.charms.map(c=>({id:c.id,available:c.available,respawn_s:round(c.respawn/60)}))};
    }
  }
  function run(o) {
    object(o,'options'); number(o.seed,'seed',-Infinity,true); number(o.ticks,'ticks',0,true); number(o.snapshotEvery,'snapshotEvery',1,true);
    const frames=validateInputs(o.inputs||{}), g=new Game(o.contract,o.seed,o.night,o.scenario||{}), lines=[JSON.stringify(g.snapshot())];
    lines.push(JSON.stringify({type:'event',tick:0,name:'night_start',data:{night:o.night}}));
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
