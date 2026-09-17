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
  message.textContent='Выполняю: «'+text+'»';

  if(state.mode==='phone' && window.AndroidJarvis){
    try {
      const result=window.AndroidJarvis.command(text);
      message.textContent=result || 'Команда выполнена.';
    } catch(e) {
      message.textContent='Ошибка выполнения команды на телефоне.';
    }
  } else if(state.mode==='phone') {
    message.textContent='PHONE MODE работает в приложении JARVIS. Для управления телефоном откройте APK.';
  } else {
    message.textContent='PC MODE: подключение к компьютеру будет следующим этапом.';
  }
  command.value='';
}
modeButton.addEventListener('click',toggleMode);
modeNav.addEventListener('click',toggleMode);
send.addEventListener('click',sendCommand);
command.addEventListener('keydown',e=>{if(e.key==='Enter')sendCommand()});
render();
