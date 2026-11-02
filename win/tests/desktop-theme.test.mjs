import test from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {syncDesktopTheme} from '../frontend/desktop-theme.js';

test('native window preserves explicit and system theme choices',async context=>{
  const dom=new JSDOM('<html data-theme="dark" data-theme-choice="dark"></html>');
  const original=globalThis.MutationObserver;globalThis.MutationObserver=dom.window.MutationObserver;
  context.after(()=>{globalThis.MutationObserver=original;dom.window.close();});
  const calls=[],root=dom.window.document.documentElement;
  const stop=syncDesktopTheme(root,async(name,args)=>{calls.push([name,args.theme]);});
  const flush=()=>new Promise(resolve=>setImmediate(resolve));
  await flush();
  root.dataset.themeChoice='light';root.dataset.theme='light';await flush();
  root.dataset.themeChoice='light';await flush();
  root.dataset.themeChoice='dark';root.dataset.theme='dark';await flush();
  // Switching to system must release the override even when the color stays dark.
  root.dataset.themeChoice='system';await flush();
  // Resolved OS color changes must never force a manual native theme again.
  root.dataset.theme='light';await flush();root.dataset.theme='dark';await flush();
  assert.deepEqual(calls,[['set_window_theme','dark'],['set_window_theme','light'],['set_window_theme','dark'],['set_window_theme',null]]);
  stop();root.dataset.themeChoice='light';await flush();assert.equal(calls.length,4);
});
