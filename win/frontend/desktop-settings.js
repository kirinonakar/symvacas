export function createDesktopSettings({document=globalThis.document,tauri=globalThis.window.__TAURI__,clipboard=globalThis.navigator.clipboard}={}) {
  const {invoke,Channel}=tauri.core;
  const byId=id=>document.getElementById(id);
  let status=null,info=null,installing=false,log=[],content,summary,path,install,output;
  const ko=()=>document.documentElement.lang.startsWith('ko');
  const text=(en,kr)=>ko()?kr:en;
  const node=(tag,value,className='')=>{const el=document.createElement(tag);el.textContent=value;el.className=className;return el;};
  const button=(label,action)=>{const el=node('button',label);el.type='button';el.addEventListener('click',action);return el;};
  function render(){
    if(!content)return;
    summary.textContent=installing?text('Installing Python dependencies…','Python 의존성 설치 중…'):status?.ready?`CPython ${status.python} · SymPy ${status.sympy} · mpmath ${status.mpmath}`:text('Python dependencies are not installed.','Python 의존성이 설치되어 있지 않습니다.');
    path.textContent=status?.path||'';
    install.disabled=installing||status?.ready===true;
    install.textContent=installing?text('Installing…','설치 중…'):status?.ready?text('Installed','설치됨'):text('Install Python dependencies','Python 의존성 설치');
    output.textContent=log.join('\n');
  }
  async function refresh(){
    try{status=await invoke('python_status');}catch(error){status={ready:false,error:String(error)};}
    render();return status;
  }
  async function installPython(){
    if(installing)return;
    installing=true;log=[];render();
    const onProgress=new Channel();
    onProgress.onmessage=message=>{log.push(String(message));log=log.slice(-80);render();};
    try{
      status=await invoke('install_python',{onProgress});
      if(status.ready)byId('retry').click();
    }catch(error){log.push(String(error));}
    finally{installing=false;await refresh();render();}
  }
  function open(){
    content=node('div','','desktop-settings');
    summary=node('p','');summary.setAttribute('role','status');
    path=node('code','','desktop-path');
    install=button('',installPython);install.id='desktop-install-python';
    output=node('pre','','desktop-install-log');output.setAttribute('role','log');output.setAttribute('aria-live','polite');
    content.append(summary,path,node('p',text('Install CPython, SymPy, mpmath and pip into python_embeded beside the executable. The first installation needs internet access and a writable application folder. Calculations then run locally.','실행 파일 옆 python_embeded에 CPython, SymPy, mpmath, pip를 설치합니다. 최초 설치에는 인터넷 연결과 앱 폴더 쓰기 권한이 필요하며, 이후 계산은 로컬에서 실행됩니다.')),install,output);
    const cfg=JSON.stringify(info?.mcp||{},null,2),config=node('textarea');
    config.value=cfg;config.readOnly=true;config.rows=9;config.setAttribute('aria-label','MCP configuration');
    const copy=button(text('Copy MCP configuration','MCP 설정 복사'),async()=>{
      try{await clipboard.writeText(cfg);copy.textContent=text('Copied','복사됨');}catch{config.focus();config.select();}
    });
    content.append(node('h3','MCP / CLI / Skill'),node('p',text('Register this stdio server in your MCP client. The GUI does not need to be running.','MCP 클라이언트에 아래 stdio 서버를 등록하세요. GUI 앱을 실행하지 않아도 사용할 수 있습니다.')),config,copy,
      node('pre',`& '${info?.cli||'symvacas-cli.exe'}' eval 'integrate(sin(x),x)'\n& '${info?.cli||'symvacas-cli.exe'}' --help`),
      node('p',text('Bundled agent skill:','함께 제공되는 에이전트 skill:')),node('code',info?.skill||'skills/symvacas/SKILL.md','desktop-path'),
      node('p',text('Copy the symvacas skill folder into your agent’s skills directory. Python scripts run with your Windows account’s file and network access.','symvacas skill 폴더를 에이전트의 skills 폴더에 복사해서 사용하세요. Python 스크립트는 현재 Windows 계정의 파일 및 네트워크 권한으로 실행됩니다.')));
    byId('dialog-title').textContent=text('Python runtime & integrations','Python 런타임 및 연동');
    const dialog=byId('dialog');dialog.classList.remove('catalog-dialog','history-dialog');
    byId('dialog-body').replaceChildren(content);render();if(!dialog.open)dialog.showModal();
    void refresh();
  }
  byId('desktop-settings-button').addEventListener('click',open);
  return {open,refresh,async initialize(){
    info=await invoke('integration_info');
    const current=await refresh();
    if(!current.ready)open();
    byId('offline-status').textContent=text('Local CPython engine','로컬 CPython 엔진');
  }};
}
