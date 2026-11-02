import test from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {createDesktopSettings} from '../frontend/desktop-settings.js';
const tick=()=>new Promise(resolve=>setImmediate(resolve));

function setup({fail=false}={}){
  const dom=new JSDOM('<html lang="en"><body><button id="desktop-settings-button"></button><button id="retry"></button><span id="offline-status"></span><dialog id="dialog"><h2 id="dialog-title"></h2><div id="dialog-body"></div></dialog></body></html>');
  const document=dom.window.document,calls=[];let ready=false,restarts=0,copied;
  document.getElementById('dialog').showModal=function(){this.open=true;};
  document.getElementById('retry').onclick=()=>restarts++;
  const tauri={core:{Channel:class {},invoke:async(name,args)=>{
    calls.push(name);
    if(name==='python_status')return {ready,path:'C:\\App\\python_embeded',python:'3.14.10',sympy:'1.14.0',mpmath:'1.3.0'};
    if(name==='integration_info')return {cli:'C:\\App\\symvacas-cli.exe',skill:'C:\\App\\skills\\symvacas\\SKILL.md',mcp:{mcpServers:{symvacas:{command:'C:\\App\\symvacas-cli.exe',args:['mcp']}}}};
    if(name==='install_python'){
      args.onProgress.onmessage('Verified CPython');
      await tick();
      if(fail)throw new Error('Network unavailable');
      ready=true;return {ready:true};
    }
  }}};
  const controller=createDesktopSettings({document,tauri,clipboard:{writeText:async text=>{copied=text;}}});
  return {document,controller,calls,get restarts(){return restarts;},get copied(){return copied;}};
}

test('first launch offers install; success restarts the engine and shows usable integrations',async()=>{
  const app=setup();await app.controller.initialize();
  assert.equal(app.document.getElementById('dialog').open,true);
  const install=app.document.getElementById('desktop-install-python');
  assert.equal(install.disabled,false);install.click();assert.equal(install.disabled,true);
  await tick();await tick();
  assert.equal(app.restarts,1);assert.equal(install.textContent,'Installed');assert.equal(install.disabled,true);
  assert.match(app.document.querySelector('[role="log"]').textContent,/Verified/);
  const copy=[...app.document.querySelectorAll('button')].find(b=>b.textContent==='Copy MCP configuration');copy.click();await tick();
  assert.equal(JSON.parse(app.copied).mcpServers.symvacas.command,'C:\\App\\symvacas-cli.exe');
});

test('failed install is visible and can be retried',async()=>{
  const app=setup({fail:true});await app.controller.initialize();
  app.document.getElementById('desktop-install-python').click();await tick();await tick();
  assert.equal(app.restarts,0);assert.equal(app.document.getElementById('desktop-install-python').disabled,false);
  assert.match(app.document.querySelector('[role="log"]').textContent,/Network unavailable/);
});
