const state={mode:'phone'};
const message=document.getElementById('message');
const command=document.getElementById('command');
const send=document.getElementById('send');
const modeButton=document.getElementById('modeButton');
const modeNav=document.getElementById('modeNav');

function render(){
  const phone=state.mode==='phone';
  modeButton.textContent=phone?'📱 PHONE MODE':'🖥️ PC MODE';
  modeNav.textContent=phone?'📱 Телефон':'🖥️ ПК';
  message.textContent=phone?'Готов к управлению телефоном, сэр.':'Готов к управлению компьютером, сэр.';
}
function toggleMode(){state.mode=state.mode==='phone'?'pc':'phone';render()}
function sendCommand(){
  const text=command.value.trim();
  if(!text)return;
  message.textContent=`Команда принята: «${text}»`;
  // Transport to the future mobile/PC API will be connected here.
  command.value='';
}
modeButton.addEventListener('click',toggleMode);
modeNav.addEventListener('click',toggleMode);
send.addEventListener('click',sendCommand);
command.addEventListener('keydown',e=>{if(e.key==='Enter')sendCommand()});
render();
