const state={mode:'phone',persona:localStorage.getItem('jarvisPersona')||'J.A.R.V.I.S.',waitingForCommand:false};
const message=document.getElementById('message');
const command=document.getElementById('command');
const send=document.getElementById('send');
const modeButton=document.getElementById('modeButton');
const modeNav=document.getElementById('modeNav');
const appsNav=document.getElementById('appsNav');
const appsPanel=document.getElementById('appsPanel');
const appsList=document.getElementById('appsList');
const refreshApps=document.getElementById('refreshApps');
const settingsNav=document.getElementById('settingsNav');
const settingsPanel=document.getElementById('settingsPanel');
const personaList=document.getElementById('personaList');
const orbButton=document.getElementById('orbButton');
const fishApiKey=document.getElementById('fishApiKey');
const gigaApiKey=document.getElementById('gigaApiKey');
const saveApiKeys=document.getElementById('saveApiKeys');
const apiStatus=document.getElementById('apiStatus');

const personas=[
  ['J.A.R.V.I.S.','Стандартный'],
  ['Astra','Творческий'],
  ['Luna','Аналитический'],
  ['Terra','Практичный'],
  ['Cyber','Безопасность']
];

function render(){
  const phone=state.mode==='phone';
  modeButton.textContent=phone?'📱 PHONE MODE':'🖥️ PC MODE';
  modeNav.textContent=phone?'📱 Телефон':'🖥️ ПК';
  if(!phone) appsPanel.hidden=true;
  message.textContent=phone?`Готов к работе, сэр. Персонаж: ${state.persona}`:'Готов к управлению компьютером, сэр.';
}
function toggleMode(){state.mode=state.mode==='phone'?'pc':'phone';render()}
function showMessage(text){message.textContent=text;}
function sendCommand(textOverride){
  const text=(textOverride||command.value).trim();
  if(!text)return;
  state.waitingForCommand=false;
  showMessage('Выполняю: «'+text+'»');
  if(state.mode==='phone' && window.AndroidJarvis){
    try{
      const result=window.AndroidJarvis.command(text);
      showMessage(result||'Команда выполнена.');
      if(typeof window.AndroidJarvis.speak==='function') window.AndroidJarvis.speak(result||'Команда выполнена.');
    }catch(e){showMessage('Ошибка выполнения команды на телефоне.')}
  }else if(state.mode==='phone') showMessage('PHONE MODE работает в APK JARVIS.');
  else showMessage('PC MODE: подключение к компьютеру будет следующим этапом.');
  command.value='';
}
function startListening(){
  if(!(window.AndroidJarvis&&typeof window.AndroidJarvis.startListening==='function')){showMessage('Голосовой ввод доступен в APK JARVIS.');return;}
  state.waitingForCommand=false; showMessage('Слушаю…'); window.AndroidJarvis.startListening();
}
function listenForCommand(){
  state.waitingForCommand=true; showMessage('Слушаю…');
  if(window.AndroidJarvis&&typeof window.AndroidJarvis.speak==='function') window.AndroidJarvis.speak('Слушаю');
  setTimeout(()=>{if(window.AndroidJarvis&&typeof window.AndroidJarvis.startListening==='function')window.AndroidJarvis.startListening()},900);
}
function onSpeechResult(text){
  if(!text)return; const clean=text.trim(); const wake=/^(джарвис|jarvis)[,\s.!?]*/i;
  if(state.waitingForCommand){sendCommand(clean);return;}
  if(wake.test(clean)){const commandText=clean.replace(wake,'').trim();if(!commandText){listenForCommand();return}sendCommand(commandText);return}
  sendCommand(clean);
}
window.onJarvisSpeechResult=onSpeechResult;
function loadApps(){
  if(!(window.AndroidJarvis&&typeof window.AndroidJarvis.listApps==='function')){appsList.innerHTML='<div class="app-empty">Список приложений доступен внутри APK JARVIS.</div>';return}
  try{const apps=JSON.parse(window.AndroidJarvis.listApps());appsList.innerHTML='';apps.forEach(app=>{const row=document.createElement('label');row.className='app-row';row.innerHTML='<span>'+app.label+'</span><input type="checkbox" '+(app.allowed?'checked':'')+'>';row.querySelector('input').addEventListener('change',e=>{showMessage(window.AndroidJarvis.setAppAllowed(app.packageName,e.target.checked))});appsList.appendChild(row)});if(!apps.length)appsList.innerHTML='<div class="app-empty">Приложения не найдены.</div>'}catch(e){appsList.innerHTML='<div class="app-empty">Не удалось загрузить приложения.</div>'}
}
function toggleApps(){if(state.mode!=='phone')state.mode='phone';settingsPanel.hidden=true;appsPanel.hidden=!appsPanel.hidden;if(!appsPanel.hidden)loadApps()}
function loadPersonas(){
  personaList.innerHTML=''; personas.forEach(([name,description])=>{const row=document.createElement('label');row.className='app-row';row.innerHTML=`<span><strong>${name}</strong><small> — ${description}</small></span><input type="radio" name="persona" ${state.persona===name?'checked':''}>`;row.querySelector('input').addEventListener('change',()=>{state.persona=name;localStorage.setItem('jarvisPersona',name);if(window.AndroidJarvis&&typeof window.AndroidJarvis.setPersona==='function')window.AndroidJarvis.setPersona(name);showMessage(`Персонаж ${name} выбран.`);render()});personaList.appendChild(row)});
  if(window.AndroidJarvis&&typeof window.AndroidJarvis.getApiKeyStatus==='function'){
    try{const s=JSON.parse(window.AndroidJarvis.getApiKeyStatus());apiStatus.textContent=`Fish Audio: ${s.fish?'✓ настроен':'не настроен'} · GigaChat: ${s.giga?'✓ настроен':'не настроен'}`}catch(e){}
  }
}
function toggleSettings(){appsPanel.hidden=true;settingsPanel.hidden=!settingsPanel.hidden;if(!settingsPanel.hidden)loadPersonas()}
function saveKeys(){
  const fish=fishApiKey.value.trim(), giga=gigaApiKey.value.trim();
  if(window.AndroidJarvis&&typeof window.AndroidJarvis.setApiKeys==='function'){
    const result=window.AndroidJarvis.setApiKeys(fish,giga); apiStatus.textContent=result; fishApiKey.value=''; gigaApiKey.value='';
  }else apiStatus.textContent='Сохранение доступно в APK JARVIS.';
}
modeButton.addEventListener('click',toggleMode);modeNav.addEventListener('click',toggleMode);appsNav.addEventListener('click',toggleApps);refreshApps.addEventListener('click',loadApps);settingsNav.addEventListener('click',toggleSettings);saveApiKeys.addEventListener('click',saveKeys);send.addEventListener('click',()=>sendCommand());command.addEventListener('keydown',e=>{if(e.key==='Enter')sendCommand()});orbButton.addEventListener('click',startListening);orbButton.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' ')startListening()});render();
