/* Standard scene and measurement helpers; never called by normal gameplay/headless. */
(function(root){
  'use strict';
  function create(contract,seed){
    const g=new Lantern.Game(contract,seed,1,{random_motes:false,random_shades:false,random_drifters:false,
      lanterns:[{id:'L1',lit:true,fuel:100},{id:'L2',lit:true,fuel:100},{id:'L3',lit:true,fuel:100}]});
    const rand=Lantern.random(seed),point=()=>{const a=rand()*Math.PI*2,r=Math.sqrt(rand())*40;return [r*Math.cos(a),.8,r*Math.sin(a)];};
    for(let i=0;i<200;i++)g.shades.push({id:'S'+(i+1),pos:point(),state:'wander',timer:0,pushTicks:0,recoilTicks:0});
    for(let i=0;i<100;i++){const p=point();p[1]=0;g.addMote(p);}
    return g;
  }
  function step(g){
    g.tick++;g.simTick++;g.safeShades();
    for(const s of g.shades){
      if(s.safeTicks>0){const l=g.lanterns.find(l=>l.id===s.safeId),d=g.direction(l.pos,s.pos),n=Lantern.distance(l.pos,s.pos),push=Math.max(0,g.t.safe_radius-n)/s.safeTicks;s.pos[0]+=d[0]*push;s.pos[2]+=d[1]*push;s.safeTicks--;continue;}
      let target=null,best=Infinity;
      for(const l of g.lanterns)if(!l.lit){const d=Lantern.distance(s.pos,l.pos);if(d<best||(d===best&&l.id<target.id)){best=d;target=l;}}
      if(target)g.moveShade(s,g.direction(s.pos,target.pos),Math.min(g.t.shade_speed/60,best));
    }
  }
  function metrics(dts){
    if(!dts.length||dts.some(x=>!Number.isFinite(x)||x<=0))throw Error('No valid benchmark frames');
    const sorted=dts.slice().sort((a,b)=>a-b),n=dts.length,k=Math.max(1,Math.ceil(.01*n));
    const worst=sorted.slice(n-k),sum=dts.reduce((a,b)=>a+b,0);
    return {avg_fps:1000*n/sum,p1_low_fps:1000/(worst.reduce((a,b)=>a+b,0)/k),frame_ms_p95:sorted[Math.ceil(.95*n)-1],frames:n};
  }
  root.LanternBench={create,step,metrics};
})(globalThis);
