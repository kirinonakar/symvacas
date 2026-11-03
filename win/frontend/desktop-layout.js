const storageKey='symvacas.desktop-layout.v1';
const defaults={graph:.36,statistics:.5};
const minimums={graph:[280,320],statistics:[300,320]};

// Run after the shared app has bound its controls and built section navigation.
// Moving the existing nodes preserves editor state, analysis handlers and results.
export function createDesktopLayout(doc=document,storage,mountCalculatorPanel) {
  const view=doc.defaultView,root=doc.documentElement;
  let saved={};
  try{storage??=view.localStorage;saved=JSON.parse(storage.getItem(storageKey))||{};}catch{}
  const state={collapsed:saved.collapsed===true,calculatorCollapsed:saved.calculatorCollapsed===true,
    calculatorTab:saved.calculatorTab==='functions'?'functions':'history'};
  for(const mode of Object.keys(defaults))state[mode]=typeof saved[mode]==='number'&&Number.isFinite(saved[mode])?Math.max(.1,Math.min(.9,saved[mode])):defaults[mode];
  const persist=()=>{try{storage.setItem(storageKey,JSON.stringify(state));}catch{}};
  const local=(en,ko)=>root.lang.startsWith('ko')?ko:en;
  const cleanups=[],panels=[];
  const navigation=doc.getElementById('workspace-navigation');
  const toggle=doc.createElement('button');
  toggle.id='desktop-sidebar-toggle';toggle.type='button';toggle.textContent='☰';
  toggle.setAttribute('aria-controls',navigation.id);
  doc.querySelector('.instrument > header').prepend(toggle);
  function sidebar(){
    root.dataset.desktopSidebar=state.collapsed?'collapsed':'expanded';
    navigation.hidden=state.collapsed;
    toggle.setAttribute('aria-expanded',String(!state.collapsed));
    const label=state.collapsed?local('Show sidebar','사이드바 펼치기'):local('Hide sidebar','사이드바 접기');
    toggle.setAttribute('aria-label',label);toggle.title=label;
  }
  toggle.onclick=()=>{state.collapsed=!state.collapsed;sidebar();persist();};
  sidebar();
  const calculatorPanel=createDesktopCalculatorPanel({document:doc,state,persist,mount:mountCalculatorPanel});
  cleanups.push(()=>calculatorPanel.dispose());

  for(const mode of Object.keys(defaults)) {
    const workspace=doc.querySelector(`.workspace[data-mode="${mode}"]`);
    const left=doc.createElement('div'),right=doc.createElement('div'),separator=doc.createElement('div');
    left.id=`desktop-${mode}-input`;right.id=`desktop-${mode}-output`;
    left.className='desktop-pane desktop-input-pane';right.className='desktop-pane desktop-output-pane';
    left.setAttribute('role','region');right.setAttribute('role','region');
    separator.className='desktop-splitter';separator.tabIndex=0;
    separator.setAttribute('role','separator');separator.setAttribute('aria-orientation','vertical');
    separator.setAttribute('aria-controls',`${left.id} ${right.id}`);
    const children=[...workspace.children];
    if(mode==='graph') {
      for(const child of children) {
        const output=child.matches('.graph-toolbar:not(#graph-parameter-actions),.graph-plot-frame,#graph-formulas,#graph-status,#graph-trace');
        (output?right:left).append(child);
      }
      const analysis=left.querySelector('#graph-analysis'),sliders=analysis.querySelector('#graph-analysis-sliders');
      if(sliders){
        // Keep the shared axis insets and range handlers; the track now has
        // the same width and horizontal origin as the graph above it.
        right.querySelector('.graph-plot-frame').after(sliders);
        const visibility=()=>{sliders.hidden=analysis.hidden||!analysis.open;};
        const observer=new view.MutationObserver(visibility);
        observer.observe(analysis,{attributes:true,attributeFilter:['open','hidden']});
        visibility();cleanups.push(()=>observer.disconnect());
      }
    } else {
      let analysis=false;
      for(const child of children) {
        if(child.id==='statistics-summary')analysis=true;
        (analysis||child.id==='statistics-error'?right:left).append(child);
      }
      const actions=doc.createElement('div');actions.id='desktop-statistics-actions';actions.className='form-row';
      actions.append(left.querySelector('#statistics-collapse-all'));
      const results=doc.createElement('div');results.id='desktop-statistics-results';results.tabIndex=0;
      results.append(...right.children);right.append(actions,results);
      const toolbar=left.querySelector('#dataset-list').closest('.form-row');
      toolbar.classList.add('desktop-dataset-toolbar');
      const transfers=doc.createElement('div');transfers.className='desktop-dataset-transfers';
      transfers.append(left.querySelector('#dataset-name'),left.querySelector('#dataset-save'),left.querySelector('#dataset-delete'),left.querySelector('#csv-open'),left.querySelector('#csv-save'));toolbar.append(transfers);
    }
    workspace.classList.add('desktop-split');workspace.append(left,separator,right);
    let dragging=null;
    function limits(){
      const available=workspace.getBoundingClientRect().width-12;
      const [minLeft,minRight]=minimums[mode];
      return available>=minLeft+minRight?{available,min:minLeft/available,max:1-minRight/available}:null;
    }
    function update(){
      const bounds=limits();
      const ratio=bounds?Math.max(bounds.min,Math.min(bounds.max,state[mode])):state[mode];
      workspace.style.setProperty('--desktop-split-ratio',String(ratio));
      separator.setAttribute('aria-valuemin',String(Math.round((bounds?.min??.1)*100)));
      separator.setAttribute('aria-valuemax',String(Math.round((bounds?.max??.9)*100)));
      separator.setAttribute('aria-valuenow',String(Math.round(ratio*100)));
    }
    function setRatio(ratio){state[mode]=ratio;update();}
    function stop(event){
      if(dragging===null||event&&event.pointerId!==dragging)return;
      const pointer=dragging;dragging=null;
      if(separator.hasPointerCapture?.(pointer))separator.releasePointerCapture(pointer);
      separator.classList.remove('dragging');root.classList.remove('desktop-resizing');persist();
    }
    const down=event=>{
      if(event.button!==0||!limits()||view.getComputedStyle(separator).display==='none')return;
      event.preventDefault();dragging=event.pointerId;
      separator.setPointerCapture?.(event.pointerId);separator.focus({preventScroll:true});
      separator.classList.add('dragging');root.classList.add('desktop-resizing');
    };
    const move=event=>{
      if(dragging===null||event.pointerId!==dragging)return;
      const bounds=limits();if(!bounds){stop();return;}
      setRatio(Math.max(bounds.min,Math.min(bounds.max,(event.clientX-workspace.getBoundingClientRect().left-6)/bounds.available)));
    };
    const reset=()=>{setRatio(defaults[mode]);persist();};
    separator.addEventListener('pointerdown',down);
    view.addEventListener('pointermove',move);
    view.addEventListener('pointerup',stop);
    view.addEventListener('pointercancel',stop);
    separator.addEventListener('lostpointercapture',stop);
    separator.addEventListener('dblclick',reset);
    separator.addEventListener('keydown',event=>{
      const bounds=limits();if(!bounds)return;
      const ratio=Number(separator.getAttribute('aria-valuenow'))/100,step=event.shiftKey?.1:.02;
      const next={ArrowLeft:ratio-step,ArrowRight:ratio+step,Home:bounds.min,End:bounds.max,Enter:defaults[mode]}[event.key];
      if(next===undefined)return;
      event.preventDefault();setRatio(Math.max(bounds.min,Math.min(bounds.max,next)));persist();
    });
    const refreshEditor=()=>{
      if(mode==='statistics'){
        // The shared editors virtualize rows using their current viewport height.
        doc.getElementById('statistics-data').dispatchEvent(new view.Event('scroll'));
        doc.getElementById('statistics-grid').firstElementChild?.refreshEditableTable?.();
      }
    };
    const resize=()=>{stop();update();refreshEditor();};
    const observer=view.ResizeObserver?new view.ResizeObserver(resize):null;
    observer?.observe(workspace);
    // Editor width changes during a drag must refresh rows without ending it.
    const editorObserver=mode==='statistics'&&view.ResizeObserver?new view.ResizeObserver(refreshEditor):null;
    editorObserver?.observe(doc.getElementById('statistics-editor'));
    view.addEventListener('resize',resize);
    cleanups.push(()=>{
      stop();observer?.disconnect();editorObserver?.disconnect();view.removeEventListener('resize',resize);
      view.removeEventListener('pointermove',move);view.removeEventListener('pointerup',stop);view.removeEventListener('pointercancel',stop);
    });
    panels.push({mode,left,right,separator,update});update();
  }
  function labels(){
    sidebar();calculatorPanel.update();
    for(const id of ['csv-open','csv-save']){const button=doc.getElementById(id);button.title=button.textContent;}
    for(const {mode,left,right,separator} of panels){
      left.setAttribute('aria-label',mode==='graph'?local('Graph inputs','그래프 입력'):local('Dataset','데이터셋'));
      right.setAttribute('aria-label',mode==='graph'?local('Graph results','그래프 결과'):local('Analysis and results','분석 및 결과'));
      const label=local('Resize panels (arrow keys; Enter or double-click to reset)','패널 너비 조절 (방향키, Enter 또는 두 번 클릭으로 초기화)');
      separator.setAttribute('aria-label',label);separator.title=label;
    }
  }
  labels();
  const observer=new view.MutationObserver(()=>{labels();for(const panel of panels)panel.update();});
  observer.observe(root,{attributes:true,attributeFilter:['lang','data-workspace']});
  return {dispose(){observer.disconnect();for(const cleanup of cleanups)cleanup();toggle.onclick=null;}};
}
import {createDesktopCalculatorPanel} from './desktop-calculator-panel.js';

