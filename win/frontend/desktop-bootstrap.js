import {createDesktopSettings} from './desktop-settings.js';
import {syncDesktopTheme} from './desktop-theme.js';
import {createDesktopDocuments} from './desktop-documents.js';
import {createWorkspaceLayout} from './workspace-layout.js';
import {createDesktopPreferences} from './desktop-preferences.js';
import {createDesktopAbout} from './desktop-about.js';

const desktop=createDesktopSettings();
const documents=createDesktopDocuments();
const preferences=createDesktopPreferences();
const about=createDesktopAbout();
window.addEventListener('pagehide',()=>about.dispose(),{once:true});
window.addEventListener('pagehide',()=>preferences.dispose(),{once:true});
window.addEventListener('pagehide',()=>documents.dispose(),{once:true});
const stopThemeSync=syncDesktopTheme();
window.addEventListener('pagehide',stopThemeSync,{once:true});
try {
  const {mountCalculatorPanel}=await import('./app.js');
  const layout=createWorkspaceLayout(document,undefined,mountCalculatorPanel);
  window.addEventListener('pagehide',()=>layout.dispose(),{once:true});
  await desktop.initialize();
} catch(error) {
  console.error('SymvaCAS initialization failed:',error);
  document.documentElement.dataset.engine='error';
  document.getElementById('status').textContent=String(error);
  const retry=document.getElementById('retry');retry.hidden=false;retry.onclick=()=>location.reload();
}
