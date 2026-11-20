(function(root){
  'use strict';
  const defaults={forward:'KeyW',back:'KeyS',left:'KeyA',right:'KeyD',jump:'Space',dash:'ShiftLeft',interact:'KeyE',pulse:'KeyQ',pause:'Escape'};
  function normalize(value){
    const out={...defaults},used=new Set();
    for(const action of Object.keys(defaults)){
      const key=value&&value[action];
      if(typeof key==='string'&&/^[A-Za-z][A-Za-z0-9]{0,39}$/.test(key)&&!used.has(key))out[action]=key;
      if(used.has(out[action]))return {...defaults};
      used.add(out[action]);
    }
    return out;
  }
  function assign(bindings,action,key){
    if(!(action in defaults)||!key||!/^[A-Za-z][A-Za-z0-9]{0,39}$/.test(key))return {error:'Phím không hợp lệ.'};
    const other=Object.keys(bindings).find(a=>a!==action&&bindings[a]===key);
    if(other)return {error:'Phím này đã dùng cho '+other+'. Chọn phím khác.'};
    return {bindings:{...bindings,[action]:key}};
  }
  const aliases={forward:['ArrowUp'],back:['ArrowDown'],left:['ArrowLeft'],right:['ArrowRight'],dash:['ShiftRight'],pause:['KeyP']};
  function active(keys,action,bindings){
    if(keys.has(bindings[action]))return true;
    return bindings[action]===defaults[action]&&(aliases[action]||[]).some(k=>keys.has(k)&&!Object.values(bindings).includes(k));
  }
  function label(code){return /^Key[A-Z]$/.test(code)?code.slice(3):/^Digit/.test(code)?code.slice(5):({Escape:'Esc',ShiftLeft:'Shift trái',ShiftRight:'Shift phải',ArrowUp:'Phím lên',ArrowDown:'Phím xuống',ArrowLeft:'Phím trái',ArrowRight:'Phím phải'}[code]||code);}
  root.LanternAccess={defaults,normalize,assign,active,label};
})(globalThis);
