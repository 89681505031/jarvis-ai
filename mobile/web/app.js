const state={mode:'phone'};
const message=document.getElementById('message');
const command=document.getElementById('command');
const send=document.getElementById('send');
const modeButton=document.getElementById('modeButton');
const modeNav=document.getElementById('modeNav');
const appsNav=document.getElementById('appsNav');
const appsPanel=document.getElementById('appsPanel');
const appsList=document.getElementById('appsList');
const refreshApps=document.getElementById('refreshApps');

function render(){
  const phone=state.mode==='phone';
  modeButton.textContent=phone?'📱 PHONE MODE':'🖥️ PC MODE';
  modeNav.textContent=phone?'📱 Телефон':'🖥️ ПК';
  if(!phone) appsPanel.hidden=true;
  message.textContent=phone?'Готов к управлению телефоном, сэр.':'Готов к управлению компьютером, сэр.';
}
function toggleMode(){state.mode=state.mode==='phone'?'pc':'phone';render()}
function sendCommand(){
  const text=command.value.trim();
  if(!text)return;
  message.textContent='Выполняю: «'+text+'»';
  if(state.mode==='phone' && window.AndroidJarvis){
    try{message.textContent=window.AndroidJarvis.command(text)||'Команда выполнена.'}
    catch(e){message.textContent='Ошибка выполнения команды на телефоне.'}
  }else if(state.mode==='phone') message.textContent='PHONE MODE работает в APK JARVIS.';
  else message.textContent='PC MODE: подключение к компьютеру будет следующим этапом.';
  command.value='';
}
function loadApps(){
  if(!(window.AndroidJarvis&&typeof window.AndroidJarvis.listApps==='function')){appsList.innerHTML='<div class="app-empty">Список приложений доступен внутри APK JARVIS.</div>';return}
  try{
    const apps=JSON.parse(window.AndroidJarvis.listApps()); appsList.innerHTML='';
    apps.forEach(app=>{
      const row=document.createElement('label'); row.className='app-row';
      row.innerHTML='<span>'+app.label+'</span><input type="checkbox" '+(app.allowed?'checked':'')+'>';
      row.querySelector('input').addEventListener('change',e=>{message.textContent=window.AndroidJarvis.setAppAllowed(app.packageName,e.target.checked)});
      appsList.appendChild(row);
    });
    if(!apps.length)appsList.innerHTML='<div class="app-empty">Приложения не найдены.</div>';
  }catch(e){appsList.innerHTML='<div class="app-empty">Не удалось загрузить приложения.</div>'}
}
function toggleApps(){if(state.mode!=='phone')state.mode='phone';appsPanel.hidden=!appsPanel.hidden;if(!appsPanel.hidden)loadApps()}
modeButton.addEventListener('click',toggleMode); modeNav.addEventListener('click',toggleMode);
appsNav.addEventListener('click',toggleApps); refreshApps.addEventListener('click',loadApps);
send.addEventListener('click',sendCommand); command.addEventListener('keydown',e=>{if(e.key==='Enter')sendCommand()});
render();
