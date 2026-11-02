export async function saveExport(name,content,type='text/plain',invoke=window.__TAURI__.core.invoke) {
  try {
    const bytes=Array.from(new Uint8Array(await new Blob([content],{type}).arrayBuffer()));
    return await invoke('save_export',{name,bytes});
  } catch(error) {
    const toast=document.getElementById('toast');
    if(toast){toast.textContent=String(error);toast.hidden=false;setTimeout(()=>{toast.hidden=true;},6000);}
    return false;
  }
}
