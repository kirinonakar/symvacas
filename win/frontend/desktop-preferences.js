// Move the shared settings controls, preserving their handlers and saved values.
export function createDesktopPreferences(doc=document) {
  const dialog=doc.getElementById('settings-dialog'),body=doc.getElementById('settings-body');
  const preferences=dialog.querySelector('.preferences');
  const local=(en,ko)=>doc.documentElement.lang.startsWith('ko')?ko:en;
  const node=(tag,value='',className='')=>{const el=doc.createElement(tag);el.textContent=value;el.className=className;return el;};
  const definitions=[
    ['general','General','일반','Language, appearance and input','언어, 화면 및 입력'],
    ['calculation','Calculation','계산','Precision and calculation behavior','정밀도 및 계산 동작'],
    ['graph','Graph colors','그래프 색상','Choose the colors for each graph','그래프별 색상 지정'],
    ['data','Data & backup','데이터 및 백업','History, backups and reset','기록, 백업 및 초기화']
  ];
  let selected='general',tabs=[],panels=[],footer;
  dialog.classList.add('desktop-preferences-dialog');
  dialog.setAttribute('aria-labelledby','desktop-preferences-title');
  dialog.querySelector('h2').id='desktop-preferences-title';
  function select(id,focus=false){
    selected=id;
    for(const tab of tabs){const active=tab.dataset.page===id;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;if(active&&focus)tab.focus();}
    for(const panel of panels)panel.hidden=panel.dataset.page!==id;
  }
  function labels(){
    dialog.querySelector('h2').textContent=local('Settings','설정');
    doc.getElementById('settings-button').textContent=local('Settings','설정');
    if(!footer)return;
    footer.firstElementChild.textContent=local('Changes apply immediately.','변경 사항은 즉시 적용됩니다.');
    footer.lastElementChild.textContent=local('Close','닫기');
    body.querySelector('[role="tablist"]').setAttribute('aria-label',local('Settings categories','설정 분류'));
    for(const [id,en,ko,description,descriptionKo] of definitions){
      const tab=tabs.find(tab=>tab.dataset.page===id),panel=panels.find(panel=>panel.dataset.page===id);
      tab.textContent=local(en,ko);panel.querySelector('h3').textContent=local(en,ko);
      panel.querySelector('.desktop-preferences-description').textContent=local(description,descriptionKo);
    }
    const storage=body.querySelector('[data-settings-note="storage"]');
    if(storage){storage.setAttribute('translate','no');storage.textContent=local('History, variables, functions and drafts are saved on this PC. Full backups also include Python code.','계산 기록, 변수, 함수, 작업 내용은 이 PC에 저장됩니다. 전체 백업에는 Python 코드도 포함됩니다.');}
    const transfer=body.querySelector('[data-settings-note="transfer"]');
    if(transfer){transfer.setAttribute('translate','no');transfer.textContent=local('Transfer variables, saved statistics datasets and functions between Windows, Android and Web. Matching names are replaced; other data and settings are kept.','Windows, Android, 웹 간에 변수, 저장된 통계 데이터셋과 함수를 옮깁니다. 같은 이름은 덮어쓰며, 다른 데이터와 설정은 유지됩니다.');}
  }
  function arrange(){
    const source=body.firstElementChild;
    const shell=node('div','','desktop-preferences-shell'),nav=node('div','','desktop-preferences-nav'),pages=node('div','','desktop-preferences-pages');
    nav.setAttribute('role','tablist');nav.setAttribute('aria-orientation','vertical');
    nav.setAttribute('aria-label',local('Settings categories','설정 분류'));
    tabs=[];panels=[];
    for(const [id] of definitions){
      const tab=node('button');tab.type='button';tab.id=`desktop-preferences-tab-${id}`;tab.dataset.page=id;tab.setAttribute('role','tab');
      const panel=node('section','','desktop-preferences-page');panel.id=`desktop-preferences-page-${id}`;panel.dataset.page=id;panel.setAttribute('role','tabpanel');panel.tabIndex=0;
      tab.setAttribute('aria-controls',panel.id);panel.setAttribute('aria-labelledby',tab.id);
      tab.onclick=()=>select(id);
      tab.onkeydown=event=>{
        const current=tabs.indexOf(tab),last=tabs.length-1;
        const next={ArrowDown:(current+1)%tabs.length,ArrowUp:(current+last)%tabs.length,Home:0,End:last}[event.key];
        if(next===undefined)return;event.preventDefault();select(tabs[next].dataset.page,true);
      };
      panel.append(node('h3'),node('p','','desktop-preferences-description'));
      tabs.push(tab);panels.push(panel);nav.append(tab);pages.append(panel);
    }
    const page=id=>panels.find(panel=>panel.dataset.page===id);
    page('general').append(preferences);
    for(const child of [...source.children]){
      const input=child.querySelector('[data-setting]'),key=input?.dataset.setting;
      // Windows has no vibration feedback; retain the stored preference for Android.
      if(key==='haptics')continue;
      let group='data';
      if(child.classList.contains('graph-color-settings'))group='graph';
      else if(['inputFont','outputFont','wordWrap','sound'].includes(key))group='general';
      else if((key&&key!=='persistHistory')||child.dataset.settingsNote==='limits')group='calculation';
      if(input?.type==='range'){
        const output=node('output',`${input.value} px`,'desktop-preferences-value');
        output.setAttribute('for',input.id=`desktop-setting-${key}`);
        input.addEventListener('input',()=>{output.textContent=`${input.value} px`;});child.append(output);
      }
      if(input?.type==='checkbox')child.prepend(input);
      if(input?.type==='number'){
        const range=node('small',`${input.min}–${input.max}`,'desktop-preferences-range');child.append(range);
      }
      page(group).append(child);
    }
    doc.getElementById('variables-button')?.remove();
    const data=page('data');
    // Pair the existing backup buttons without creating new action handlers.
    const backupButtons=[...data.children].filter(child=>child.tagName==='BUTTON');
    if(backupButtons.length>=2){const actions=node('div','','desktop-preferences-actions');backupButtons[0].before(actions);actions.append(...backupButtons.slice(0,2));}
    for(const button of backupButtons.slice(2))button.classList.add('desktop-preferences-danger');
    shell.append(nav,pages);body.replaceChildren(shell);
    if(!footer){
      footer=node('div','','desktop-preferences-footer');const close=node('button');close.type='button';close.onclick=()=>dialog.close();footer.append(node('span'),close);dialog.append(footer);
    }
    labels();select(selected);
  }
  dialog.addEventListener('settingsrender',arrange);
  const observer=new doc.defaultView.MutationObserver(labels);
  observer.observe(doc.documentElement,{attributes:true,attributeFilter:['lang']});
  labels();
  return {dispose(){observer.disconnect();dialog.removeEventListener('settingsrender',arrange);}};
}
