(function(){
  const profiles={
    'J.A.R.V.I.S.':'Ты J.A.R.V.I.S. — спокойный универсальный помощник. Отвечай точно, кратко и уверенно.',
    'Astra':'Ты Astra — дружелюбный творческий помощник. Предлагай необычные идеи, вдохновляй и объясняй простым языком.',
    'Luna':'Ты Luna — аналитик и эксперт по знаниям. Давай подробные, логичные ответы, отмечай допущения и шаги.',
    'Terra':'Ты Terra — практический помощник. Сосредоточься на конкретных действиях, пошаговых инструкциях и управлении телефоном.',
    'Cyber':'Ты Cyber — специалист по технологиям, программированию и безопасности. Давай технические, безопасные и проверяемые решения.'
  };
  const native=window.AndroidJarvis;
  if(!native||typeof native.command!=='function')return;
  const original=native.command.bind(native);
  const deviceCommands=/^(открой|запусти|включи|выключи|найди в интернете|позвони|отправь|сделай скриншот|громкость|фонарик|камера|настройки|браузер)\b/i;
  native.command=function(text){
    const persona=localStorage.getItem('jarvisPersona')||'J.A.R.V.I.S.';
    const instruction=profiles[persona]||profiles['J.A.R.V.I.S.'];
    const value=String(text||'');
    return original(deviceCommands.test(value)?value:('[Персонаж: '+persona+'] '+instruction+'\nЗапрос пользователя: '+value));
  };
})();
