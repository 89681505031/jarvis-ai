const state={mode:'phone',persona:localStorage.getItem('jarvisPersona')||'J.A.R.V.I.S.',waitingForCommand:false};
const $=id=>document.getElementById(id);
const message=$('message'),command=$('command'),send=$('send'),modeButton=$('modeButton'),modeNav=$('modeNav'),appsNav=$('appsNav'),commandsNav=$('commandsNav'),appsPanel=$('appsPanel'),commandsPanel=$('commandsPanel'),appsList=$('appsList'),refreshApps=$('refreshApps'),settingsNav=$('settingsNav'),settingsPanel=$('settingsPanel'),personaList=$('personaList'),orbButton=$('orbButton'),fishApiKey=$('fishApiKey'),gigaApiKey=$('gigaApiKey'),saveApiKeys=$('saveApiKeys'),checkUpdates=$('checkUpdates'),apiStatus=$('apiStatus');
const personas=[['J.A.R.V.I.S.','Стандартный'],['Astra','Творческий'],['Luna','Аналитический'],['Terra','Практичный'],['Cyber','Безопасность']];

function showMessage(text){message.textContent=text||''}
function render(){
  const phone=state.mode==='phone';
  modeButton.textContent=phone?'📱 PHONE MODE':'🖥️ PC MODE';
  modeNav.textContent=phone?'📱 Телефон':'🖥️ ПК';
  if(!phone){appsPanel.hidden=true;commandsPanel.hidden=true}
  showMessage(phone?'Готов к работе, сэр. Персонаж: '+state.persona:'Готов к управлению компьютером, сэр.');
}
function sendCommand(textOverride){
  const text=(textOverride||command.value).trim();
  if(!text)return;
  state.waitingForCommand=false;
  showMessage('Выполняю: «'+text+'»');
  if(state.mode==='phone'&&window.AndroidJarvis){
    try{
      const result=window.AndroidJarvis.command(text);
      if(result)showMessage(result);
      else showMessage('Обрабатываю запрос…');
    }catch(e){showMessage('Ошибка выполнения команды: '+e.message)}
  }else if(state.mode==='phone')showMessage('PHONE MODE работает в APK JARVIS.');
  else showMessage('PC MODE: подключение к компьютеру будет следующим этапом.');
  command.value='';
}
function startListening(){
  if(!(window.AndroidJarvis&&typeof window.AndroidJarvis.startListening==='function')){showMessage('Голосовой ввод доступен в APK JARVIS.');return}
  state.waitingForCommand=true;showMessage('Слушаю…');window.AndroidJarvis.startListening();
}
function onSpeechResult(text){
  if(!text){showMessage('Не удалось распознать речь.');return}
  const clean=text.trim();
  const wake=/^(джарвис|jarvis|астра|astra|луна|luna|сайбер|cyber|терра|terra)[,\s.!?]*/i;
  if(state.waitingForCommand){sendCommand(clean);return}
  if(!wake.test(clean))return;
  const spokenWake=clean.match(wake)?.[1]?.toLowerCase()||'';
  const active=String(state.persona||'J.A.R.V.I.S.').toLowerCase().replace(/[^a-zа-яё]/g,'');
  const aliases={
    'джарвис':'jarvis','jarvis':'jarvis',
    'астра':'astra','astra':'astra',
    'луна':'luna','luna':'luna',
    'сайбер':'cyber','cyber':'cyber',
    'терра':'terra','terra':'terra'
  };
  const activeKey=aliases[active]||'jarvis';
  const spokenKey=aliases[spokenWake]||spokenWake;
  if(spokenKey!==activeKey){
    const activeName=state.persona==='J.A.R.V.I.S.'?'Джарвис':state.persona;
    showMessage('Я не '+spokenWake+', я '+activeName+'.');
    if(window.AndroidJarvis&&typeof window.AndroidJarvis.speak==='function')window.AndroidJarvis.speak('Я не '+spokenWake+', я '+activeName+'.');
    return;
  }
  const commandText=clean.replace(wake,'').trim();
  if(!commandText){state.waitingForCommand=true;showMessage('Слушаю…');return}
  sendCommand(commandText);
}
window.onJarvisSpeechResult=onSpeechResult;
window.onGigaChatResult=function(text){showMessage(text)};

function filterApps(){const q=(document.getElementById('appsSearch')?.value||'').trim().toLowerCase();document.querySelectorAll('#appsList .app-row').forEach(row=>{const n=(row.querySelector('span')?.textContent||'').toLowerCase();row.hidden=!!q&&!n.includes(q)})}
function loadApps(){
  if(!(window.AndroidJarvis&&typeof window.AndroidJarvis.listApps==='function')){appsList.innerHTML='<div class="app-empty">Список приложений доступен внутри APK JARVIS.</div>';return}
  try{
    const apps=JSON.parse(window.AndroidJarvis.listApps());appsList.innerHTML='';
    apps.forEach(app=>{
      const row=document.createElement('label');row.className='app-row';
      row.innerHTML='<span>'+app.label+'</span><input type="checkbox" '+(app.allowed?'checked':'')+'>';
      row.querySelector('input').addEventListener('change',e=>showMessage(window.AndroidJarvis.setAppAllowed(app.packageName,e.target.checked)));
      appsList.appendChild(row);
    });
    if(!apps.length)appsList.innerHTML='<div class="app-empty">Приложения не найдены.</div>';
  }catch(e){appsList.innerHTML='<div class="app-empty">Не удалось загрузить приложения.</div>'}
}
function toggleApps(){commandsPanel.hidden=true;settingsPanel.hidden=true;if(state.mode!=='phone')state.mode='phone';appsPanel.hidden=!appsPanel.hidden;if(!appsPanel.hidden)loadApps()}
function toggleCommands(){appsPanel.hidden=true;settingsPanel.hidden=true;commandsPanel.hidden=!commandsPanel.hidden}
function loadPersonas(){
  personaList.innerHTML='';
  personas.forEach(([name,description])=>{
    const row=document.createElement('label');row.className='app-row';
    row.innerHTML='<span><strong>'+name+'</strong><small> — '+description+'</small></span><input type="radio" name="persona" '+(state.persona===name?'checked':'')+'>';
    row.querySelector('input').addEventListener('change',()=>{
      state.persona=name;localStorage.setItem('jarvisPersona',name);
      if(window.AndroidJarvis&&typeof window.AndroidJarvis.setPersona==='function')window.AndroidJarvis.setPersona(name);
      showMessage('Персонаж '+name+' выбран.');render();
    });
    personaList.appendChild(row);
  });
  if(window.AndroidJarvis&&typeof window.AndroidJarvis.getApiKeyStatus==='function'){
    try{const s=JSON.parse(window.AndroidJarvis.getApiKeyStatus());apiStatus.textContent='Fish Audio: '+(s.fish?'✓ настроен':'не настроен')+' · GigaChat: '+(s.giga?'✓ настроен':'не настроен')}catch(e){}
  }
}
function toggleSettings(){appsPanel.hidden=true;commandsPanel.hidden=true;settingsPanel.hidden=!settingsPanel.hidden;if(!settingsPanel.hidden)loadPersonas()}
function saveKeys(){
  const fish=fishApiKey.value.trim(),giga=gigaApiKey.value.trim();
  if(!fish&&!giga){apiStatus.textContent='Введите хотя бы один ключ.';return}
  if(window.AndroidJarvis&&typeof window.AndroidJarvis.setApiKeys==='function'){
    try{apiStatus.textContent=window.AndroidJarvis.setApiKeys(fish,giga);fishApiKey.value='';gigaApiKey.value=''}catch(e){apiStatus.textContent='Ошибка сохранения: '+e.message}
  }else apiStatus.textContent='Сохранение доступно в APK JARVIS.';
}
function askUpdates(){if(window.AndroidJarvis&&typeof window.AndroidJarvis.checkUpdates==='function')window.AndroidJarvis.checkUpdates();else showMessage('Проверка обновлений доступна в APK JARVIS.')}

modeButton.addEventListener('click',()=>{state.mode=state.mode==='phone'?'pc':'phone';render()});
modeNav.addEventListener('click',()=>{state.mode=state.mode==='phone'?'pc':'phone';render()});
appsNav.addEventListener('click',toggleApps);
commandsNav.addEventListener('click',toggleCommands);
settingsNav.addEventListener('click',toggleSettings);
refreshApps.addEventListener('click',loadApps);document.getElementById('appsSearch')?.addEventListener('input',filterApps);
saveApiKeys.addEventListener('click',saveKeys);
checkUpdates.addEventListener('click',askUpdates);
send.addEventListener('click',()=>sendCommand());
command.addEventListener('keydown',e=>{if(e.key==='Enter')sendCommand()});
orbButton.addEventListener('click',startListening);
orbButton.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' ')startListening()});

render();
