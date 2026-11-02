// The shared UI resolves light/dark/system. Mirror its resolved theme to the
// native window, including startup, settings reset and OS theme changes.
export function syncDesktopTheme(root=document.documentElement,invoke=window.__TAURI__.core.invoke){
  let last,queue=Promise.resolve();
  const sync=()=>{
    const theme=root.dataset.theme;
    if(!['light','dark'].includes(theme)||theme===last)return;
    last=theme;
    queue=queue.then(()=>invoke('set_window_theme',{theme})).catch(error=>{
      last=undefined;console.error('Cannot update window theme:',error);
    });
  };
  const observer=new MutationObserver(sync);
  observer.observe(root,{attributes:true,attributeFilter:['data-theme']});
  sync();
  return ()=>observer.disconnect();
}
