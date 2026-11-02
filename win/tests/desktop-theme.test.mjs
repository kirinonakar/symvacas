import test from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {syncDesktopTheme} from '../frontend/desktop-theme.js';

test('native title bar follows the resolved theme at startup and on every change',async context=>{
  const dom=new JSDOM('<html data-theme="dark"></html>');
  const original=globalThis.MutationObserver;globalThis.MutationObserver=dom.window.MutationObserver;
  context.after(()=>{globalThis.MutationObserver=original;dom.window.close();});
  const calls=[],root=dom.window.document.documentElement;
  const stop=syncDesktopTheme(root,async(name,args)=>{calls.push([name,args.theme]);});
  const flush=()=>new Promise(resolve=>setImmediate(resolve));
  await flush();
  root.dataset.theme='light';await flush();
  root.dataset.theme='light';await flush();
  root.dataset.theme='dark';await flush();
  assert.deepEqual(calls,[['set_window_theme','dark'],['set_window_theme','light'],['set_window_theme','dark']]);
  stop();root.dataset.theme='light';await flush();assert.equal(calls.length,3);
});
