import {createDesktopSettings} from './desktop-settings.js';
import {syncDesktopTheme} from './desktop-theme.js';

const desktop=createDesktopSettings();
const stopThemeSync=syncDesktopTheme();
window.addEventListener('pagehide',stopThemeSync,{once:true});
try {
  await import('./app.js');
  await desktop.initialize();
} catch(error) {
  console.error('SymvaCAS initialization failed:',error);
  document.documentElement.dataset.engine='error';
  document.getElementById('status').textContent=String(error);
  const retry=document.getElementById('retry');retry.hidden=false;retry.onclick=()=>location.reload();
}
