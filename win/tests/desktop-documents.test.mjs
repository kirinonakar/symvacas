import test from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {readFileSync} from 'node:fs';
import {createDesktopDocuments} from '../dist/desktop-documents.js';

const tick=()=>new Promise(resolve=>setImmediate(resolve));
const source=name=>readFileSync(new URL('../'+name,import.meta.url));
function setup(context,fetch=async name=>new Response(source(name),{headers:{'Content-Type':'text/plain; charset=windows-1252'}})){
  const dom=new JSDOM('<html lang="ko"><body><input id="draft" value="1+2"><footer><a href="README.md">Windows 가이드</a><a href="THIRD_PARTY.md">오픈소스 라이선스</a></footer></body></html>',{url:'http://tauri.localhost/'});
  const {document}=dom.window;
  dom.window.HTMLDialogElement.prototype.showModal=function(){this.open=true;};
  dom.window.HTMLDialogElement.prototype.close=function(){this.open=false;this.dispatchEvent(new dom.window.Event('close'));};
  const controller=createDesktopDocuments({document,fetch});
  context.after(()=>{controller.dispose();dom.window.close();});
  return {dom,document,controller,dialog:document.getElementById('desktop-document-dialog'),body:document.querySelector('.desktop-document-body')};
}

test('footer links open UTF-8 guide and licenses in a modal without navigating away',async context=>{
  const app=setup(context);
  const click=href=>{
    const event=new app.dom.window.MouseEvent('click',{bubbles:true,cancelable:true});
    app.document.querySelector(`footer a[href="${href}"]`).dispatchEvent(event);
    assert.equal(event.defaultPrevented,true);
  };
  click('README.md');await tick();
  assert.equal(app.dialog.open,true);
  assert.equal(app.document.getElementById('desktop-document-title').textContent,'Windows 가이드');
  assert.ok(app.body.textContent.includes('웹 버전 UI와 공통 Python 계산 엔진'));
  assert.equal(app.body.textContent.includes('\uFFFD'),false);
  assert.ok(app.body.querySelector('h1'));assert.ok(app.body.querySelector('pre code'));
  assert.equal(app.document.getElementById('draft').value,'1+2');
  assert.equal(app.dom.window.location.href,'http://tauri.localhost/');
  app.dialog.querySelector('button').click();assert.equal(app.dialog.open,false);
  click('THIRD_PARTY.md');await tick();
  assert.equal(app.document.getElementById('desktop-document-title').textContent,'오픈소스 라이선스');
  assert.ok(app.body.textContent.includes('Windows third-party components'));assert.ok(app.body.textContent.includes('SymPy'));
  assert.ok(app.body.querySelector('ul li'));
});

test('guide links open bundled MCP documentation in the same popup',async context=>{
  const app=setup(context);
  await app.controller.open('README.md');
  const link=app.body.querySelector('a[href="MCP_GUIDE.md"]');assert.ok(link);
  link.click();await tick();
  assert.equal(app.document.getElementById('desktop-document-title').textContent,'MCP 가이드');
  assert.equal(app.body.textContent.includes('\uFFFD'),false);assert.ok(app.body.textContent.includes('MCP'));
});

test('loading errors can be retried and a late response cannot replace another document',async context=>{
  let fail=true,resolveGuide;
  const app=setup(context,async name=>{
    if(name==='README.md')return await new Promise(resolve=>{resolveGuide=resolve;});
    if(fail){fail=false;return new Response('',{status:404});}
    return new Response(source(name));
  });
  const pending=app.controller.open('README.md');
  await app.controller.open('THIRD_PARTY.md');
  assert.equal(app.body.querySelector('[role="alert"]').textContent,'문서를 불러올 수 없습니다.');
  app.body.querySelector('button').click();await tick();
  assert.ok(app.body.textContent.includes('SymPy'));
  resolveGuide(new Response(source('README.md')));await pending;
  assert.ok(app.body.textContent.includes('Windows third-party components'));
  assert.equal(app.body.textContent.includes('웹 버전 UI와 공통 Python 계산 엔진'),false);
});

test('document content is rendered as text and cannot inject HTML or script links',async context=>{
  const app=setup(context,async()=>new Response('# 문서\n\n<img src=x onerror=alert(1)>\n\n[실행](javascript:alert)\n\n```text\n<script>bad()</script>\n```'));
  await app.controller.open('README.md');
  assert.equal(app.body.querySelector('img,script,a'),null);
  assert.ok(app.body.textContent.includes('<script>bad()</script>'));
});
