import * as THREE from '/vendor/three.module.js';
// Same spheres, eyes and glow textures as gameplay, rendered in batches in every mode.
export class EntityBatches{
  constructor(scene,materials,glow){
    const count=1024;
    this.dummy=new THREE.Object3D();this.color=new THREE.Color();
    this.body=new THREE.InstancedMesh(new THREE.SphereGeometry(.65,12,8),new THREE.MeshStandardMaterial({color:0xffffff,roughness:.85}),count);
    this.eyes=new THREE.InstancedMesh(new THREE.SphereGeometry(.065,6,4),materials.rim,count*2);
    this.motes=new THREE.InstancedMesh(new THREE.SphereGeometry(.12,6,4),materials.mote,count);
    const points=(color,size)=>{const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(new Float32Array(count*3),3));return new THREE.Points(geo,new THREE.PointsMaterial({color,size,map:glow,transparent:true,opacity:.5,depthWrite:false,blending:THREE.AdditiveBlending}));};
    this.shadeGlow=points(0x7a3cff,2.5);this.moteGlow=points(0xffe58a,1.4);
    for(const object of[this.body,this.eyes,this.motes,this.shadeGlow,this.moteGlow]){object.frustumCulled=false;scene.add(object);}
  }
  update(game,now,colorblind){
    const d=this.dummy,shadePositions=this.shadeGlow.geometry.attributes.position;
    this.body.count=game.shades.length;this.eyes.count=game.shades.length*2;
    const rim=colorblind?0x00b3ff:0x7a3cff;this.eyes.material.color.setHex(rim);this.shadeGlow.material.color.setHex(rim);
    for(let i=0;i<game.shades.length;i++){
      const s=game.shades[i],[x,baseY,z]=s.pos,y=baseY+Math.sin(now*.003+x)*.15;
      const theta=Math.atan2(game.player.pos[0]-x,game.player.pos[2]-z);
      d.position.set(x,y,z);d.rotation.set(0,theta,0);d.scale.set(1,1.3,1);d.updateMatrix();this.body.setMatrixAt(i,d.matrix);
      this.body.setColorAt(i,this.color.setHex(s.state==='stunned'?0x3a3450:0x120a1a));
      for(let j=0;j<2;j++){const ox=j===0?-.2:.2;d.position.set(x+Math.cos(theta)*ox+Math.sin(theta)*.56,y+.2,z-Math.sin(theta)*ox+Math.cos(theta)*.56);d.scale.setScalar(1);d.updateMatrix();this.eyes.setMatrixAt(i*2+j,d.matrix);}
      shadePositions.setXYZ(i,x,y,z);
    }
    this.body.instanceMatrix.needsUpdate=true;if(this.body.instanceColor)this.body.instanceColor.needsUpdate=true;this.eyes.instanceMatrix.needsUpdate=true;
    shadePositions.needsUpdate=true;this.shadeGlow.geometry.setDrawRange(0,game.shades.length);
    const motePositions=this.moteGlow.geometry.attributes.position;this.motes.count=game.motes.length;
    for(let i=0;i<game.motes.length;i++){const m=game.motes[i],[x,y,z]=m.pos,sy=y+.65+Math.sin(now*.002+x)*.18;d.position.set(x,sy,z);d.rotation.set(0,0,0);d.scale.setScalar(1);d.updateMatrix();this.motes.setMatrixAt(i,d.matrix);motePositions.setXYZ(i,x,sy,z);}
    this.motes.instanceMatrix.needsUpdate=true;motePositions.needsUpdate=true;this.moteGlow.geometry.setDrawRange(0,game.motes.length);
  }
}
