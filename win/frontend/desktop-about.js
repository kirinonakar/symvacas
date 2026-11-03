export function createDesktopAbout({document=globalThis.document,invoke=globalThis.window.__TAURI__.core.invoke}={}){
  const dialog=document.getElementById('dialog');
  async function click(event){
    const link=event.target.closest?.('.about-content a[href]');
    if(!link||!dialog.contains(link)||link.href!=='https://github.com/kirinonakar/symvacas')return;
    event.preventDefault();
    const content=link.closest('.about-content');
    content.querySelector('.desktop-about-error')?.remove();
    try{await invoke('open_project_website');}
    catch(error){
      if(!content.isConnected)return;
      const message=document.createElement('p');message.className='desktop-about-error';message.setAttribute('role','alert');
      message.textContent=(document.documentElement.lang.startsWith('ko')?'브라우저를 열 수 없습니다: ':'Could not open browser: ')+String(error);
      content.append(message);
    }
  }
  dialog.addEventListener('click',click);
  return {dispose(){dialog.removeEventListener('click',click);}};
}
