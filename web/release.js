const $=id=>document.getElementById(id);
let candidate=null;
export function offerScore(score,nightsWon,seed,eligible){
  candidate=eligible?{score,nights_won:nightsWon,seed}:null;
  $('save-score').hidden=!eligible;$('score-status').textContent='';$('score-submit').disabled=false;
}
export function bindReleaseUI({settings,show,apply,save}){
  let capture=null;
  const names={forward:'Đi tới',back:'Đi lùi',left:'Sang trái',right:'Sang phải',jump:'Nhảy',dash:'Lướt',interact:'Tương tác',pulse:'Tỏa sáng',pause:'Tạm dừng'};
  function draw(){
    $('keybindings').textContent='';
    for(const action of Object.keys(names)){
      const label=document.createElement('label');label.textContent=names[action];
      const button=document.createElement('button');button.type='button';button.textContent=LanternAccess.label(settings.bindings[action]);
      button.dataset.action=action;button.setAttribute('aria-label','Đổi phím '+names[action]);
      button.onclick=()=>{capture=action;button.textContent='Nhấn phím mới…';$('key-error').textContent='';};
      label.append(button);$('keybindings').append(label);
    }
    const b=settings.bindings,l=LanternAccess.label;
    document.querySelector('.control-hint').textContent=[l(b.forward),l(b.left),l(b.back),l(b.right)].join(' ')+' di chuyển · '+l(b.jump)+' nhảy · '+l(b.pause)+' tạm dừng';
  }
  draw();
  addEventListener('keydown',e=>{
    if(!capture)return;
    e.preventDefault();e.stopImmediatePropagation();
    const result=LanternAccess.assign(settings.bindings,capture,e.code);
    if(result.error)$('key-error').textContent=result.error;
    else{settings.bindings=result.bindings;save();$('key-error').textContent='Đã lưu phím.';}
    capture=null;draw();
  },true);
  $('reset-keys').onclick=()=>{capture=null;settings.bindings={...LanternAccess.defaults};save();draw();$('key-error').textContent='Đã khôi phục phím mặc định.';};
  for(const [id,key]of[['reduced-motion','reducedMotion'],['large-text','largeText']]){
    $(id).checked=!!settings[key];$(id).onchange=()=>{settings[key]=$(id).checked;save();apply();};
  }
  $('menu-leaderboard').onclick=async()=>{
    show('leaderboard');$('leaderboard-body').textContent='';$('leaderboard-status').textContent='Đang tải…';
    try{
      const response=await fetch('/api/leaderboard');if(!response.ok)throw Error('Không đọc được dữ liệu trên đĩa.');
      const {entries}=await response.json();
      for(const e of entries){const row=document.createElement('tr');for(const text of[e.name,e.score,e.nights_won+'/3',new Date(e.achieved_at).toLocaleString('vi-VN'),e.seed]){const cell=document.createElement('td');cell.textContent=text;row.append(cell);}$('leaderboard-body').append(row);}
      $('leaderboard-status').textContent=entries.length?'Top '+entries.length+' hành trình':'Chưa có điểm được lưu. Bắt đầu một hành trình nhé.';
    }catch(e){$('leaderboard-status').textContent=e.message;}
  };
  $('leaderboard-back').onclick=()=>show('menu');
  $('save-score').onsubmit=async e=>{
    e.preventDefault();if(!candidate||$('score-submit').disabled)return;
    const name=$('player-name').value;
    if(!/^[A-Za-z0-9_]{3,12}$/.test(name)){$('score-status').textContent='Tên cần 3–12 ký tự A–Z, a–z, 0–9 hoặc _.';return;}
    $('score-submit').disabled=true;
    try{
      const r=await fetch('/api/leaderboard',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...candidate,name})});
      const data=await r.json();if(!r.ok)throw Error(data.error||'Không lưu được điểm.');
      $('score-status').textContent='Đã lưu điểm trên máy này.';candidate=null;
    }catch(error){$('score-status').textContent=error.message;$('score-submit').disabled=false;}
  };
}
