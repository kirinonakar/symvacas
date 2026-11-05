import test from 'node:test';
import assert from 'node:assert/strict';
import {followTape} from '../calculation-tape.js';

function fixture(){
  const scroll=new EventTarget(),frames=new Map(),timers=new Map();
  let clock=0,next=0,historyHeight=640;
  scroll.scrollTop=0;scroll.clientTop=2;
  scroll.getBoundingClientRect=()=>({top:24});
  const active={getBoundingClientRect:()=>({top:26+historyHeight-scroll.scrollTop})};
  const follow=followTape(scroll,active,{
    now:()=>clock,
    requestFrame:callback=>{const id=++next;frames.set(id,callback);return id;},
    cancelFrame:id=>frames.delete(id),
    schedule:(callback,delay)=>{const id=++next;timers.set(id,{callback,time:clock+delay});return id;},
    cancel:id=>timers.delete(id),
  });
  const paint=()=>{const callbacks=[...frames.values()];frames.clear();for(const callback of callbacks)callback();};
  const advance=time=>{clock+=time;for(const [id,timer] of [...timers])if(timer.time<=clock){timers.delete(id);timer.callback();}};
  return {scroll,follow,frames,timers,paint,advance,resize:height=>{historyHeight=height;}};
}

test('opening the calculator aligns the input above the current result',()=>{
  const f=fixture();f.follow.latest();
  assert.equal(f.scroll.scrollTop,640);
  f.paint();assert.equal(f.scroll.scrollTop,640);
  f.follow.dispose();
});

test('startup realigns after shell mounting resets the scroll and changes history layout',()=>{
  const f=fixture();f.follow.latest();f.follow.latest();
  assert.equal(f.frames.size,1);
  f.scroll.scrollTop=0;f.resize(900);f.paint();
  assert.equal(f.scroll.scrollTop,900);
  f.follow.dispose();
});

for(const gesture of ['wheel','pointerdown'])test(`deferred startup scrolling waits for a ${gesture} gesture`,()=>{
  const f=fixture();f.follow.latest();
  f.scroll.dispatchEvent(new Event(gesture));f.scroll.scrollTop=100;f.paint();
  assert.equal(f.scroll.scrollTop,100);
  if(gesture==='pointerdown'){
    f.advance(300);assert.equal(f.scroll.scrollTop,100);
    f.scroll.dispatchEvent(new Event('pointerup'));
  }
  f.advance(160);assert.equal(f.scroll.scrollTop,640);
  f.follow.dispose();
});

test('disposal cancels pending alignment before the next paint',()=>{
  const f=fixture();f.follow.latest();f.scroll.scrollTop=0;f.follow.dispose();f.paint();
  assert.equal(f.frames.size,0);assert.equal(f.timers.size,0);
  assert.equal(f.scroll.scrollTop,0);
});
