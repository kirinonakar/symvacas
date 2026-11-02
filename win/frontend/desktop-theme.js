// Preserve system mode: forcing the resolved color also pins WebView2's
// prefers-color-scheme and prevents subsequent Windows theme changes.
export function syncDesktopTheme(root=document.documentElement,invoke=window.__TAURI__.core.invoke){
  let last,queue=Promise.resolve();
  const sync=()=>{
    const theme=root.dataset.themeChoice;
    if(!['light','dark','system'].includes(theme)||theme===last)return;
    last=theme;
    queue=queue.then(()=>invoke('set_window_theme',{theme:theme==='system'?null:theme})).catch(error=>{
      last=undefined;console.error('Cannot update window theme:',error);
    });
  };
  const observer=new MutationObserver(sync);
  observer.observe(root,{attributes:true,attributeFilter:['data-theme-choice']});
  sync();
  return ()=>observer.disconnect();
}
