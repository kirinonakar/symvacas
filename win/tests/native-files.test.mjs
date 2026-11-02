import test from 'node:test';
import assert from 'node:assert/strict';
import {saveExport} from '../frontend/native-files.js';

test('native save preserves Unicode scripts and binary exports',async()=>{
  let saved;
  const invoke=async(command,args)=>{assert.equal(command,'save_export');saved=args;return true;};
  assert.equal(await saveExport('수식.py','print("안녕")','text/x-python',invoke),true);
  assert.equal(new TextDecoder().decode(new Uint8Array(saved.bytes)),'print("안녕")');
  const source=new Uint8Array([0,255,127,1]);
  await saveExport('plot.png',new Blob([source]),'image/png',invoke);
  assert.deepEqual(saved.bytes,[0,255,127,1]);
  assert.equal(await saveExport('cancel.txt','text','text/plain',async()=>false),false);
});
