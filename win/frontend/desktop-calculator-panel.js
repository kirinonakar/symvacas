export function createDesktopCalculatorPanel({document:doc,state,persist,mount}){
  const root=doc.documentElement,view=doc.defaultView;
  const local=(en,ko)=>root.lang.startsWith('ko')?ko:en;
  const node=(tag,id)=>{const item=doc.createElement(tag);item.id=id;return item;};
  const main=doc.querySelector('main'),shell=node('div','desktop-workspace-shell');
  const panel=node('aside','desktop-calculator-panel'),bar=node('div','desktop-calculator-panel-bar');
  panel.setAttribute('role','complementary');
  main.before(shell);shell.append(main,panel);
  const toggle=node('button','desktop-calculator-toggle'),close=node('button','desktop-calculator-close');
  for(const button of [toggle,close]){button.type='button';button.setAttribute('aria-controls',panel.id);}
  close.textContent='✕';doc.querySelector('.header-actions').prepend(toggle);
  const tabs=node('div','desktop-calculator-tabs');tabs.setAttribute('role','tablist');
  const entries=new Map(),disposers=[];
  function select(kind,focus=false){
    state.calculatorTab=kind;state.calculatorCollapsed=false;update();persist();
    if(focus)entries.get(kind).button.focus();
  }
  for(const kind of ['history','functions']){
    const button=node('button',`desktop-tab-${kind}`),content=node('section',`desktop-panel-${kind}`);
    button.type='button';button.setAttribute('role','tab');button.setAttribute('aria-controls',content.id);
    content.setAttribute('role','tabpanel');content.setAttribute('aria-labelledby',button.id);
    button.onclick=()=>select(kind);
    button.onkeydown=event=>{
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();event.stopPropagation();
      select(event.key==='Home'?'history':event.key==='End'?'functions':kind==='history'?'functions':'history',true);
    };
    entries.set(kind,{button,content});tabs.append(button);panel.append(content);
    const dispose=mount?.(content,kind);if(dispose)disposers.push(dispose);
  }
  bar.append(tabs,close);panel.prepend(bar);
  function collapse(){
    // Return focus to a visible control when closing from inside the panel.
    const returnFocus=panel.contains(doc.activeElement);
    state.calculatorCollapsed=true;update();persist();if(returnFocus)toggle.focus();
  }
  toggle.onclick=()=>state.calculatorCollapsed?select(state.calculatorTab):collapse();
  close.onclick=collapse;
  for(const [id,kind] of [['history-button','history'],['catalog-button','functions']]){
    const button=doc.getElementById(id),original=button.onclick;
    button.onclick=event=>{
      if(root.dataset.workspace==='scientific'&&view.innerWidth>=900)select(kind);
      else original?.call(button,event);
    };
    disposers.push(()=>{button.onclick=original;});
  }
  function update(){
    root.dataset.desktopCalculator=state.calculatorCollapsed?'collapsed':'expanded';
    panel.hidden=state.calculatorCollapsed;
    toggle.setAttribute('aria-expanded',String(!state.calculatorCollapsed));
    toggle.textContent=local('History / Functions','기록 / 함수');
    const label=state.calculatorCollapsed?local('Show calculator panel','계산기 패널 펼치기'):local('Hide calculator panel','계산기 패널 접기');
    toggle.title=label;toggle.setAttribute('aria-label',label);
    close.title=local('Collapse panel','패널 접기');close.setAttribute('aria-label',close.title);
    panel.setAttribute('aria-label',local('Calculator tools','계산기 도구'));
    tabs.setAttribute('aria-label',local('Calculator tools','계산기 도구'));
    for(const [kind,{button,content}] of entries){
      const active=state.calculatorTab===kind;
      button.textContent=kind==='history'?local('History','기록'):local('Functions','함수');
      button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1;content.hidden=!active;
    }
  }
  update();
  return {update,dispose(){for(const dispose of disposers)dispose();toggle.onclick=close.onclick=null;}};
}
