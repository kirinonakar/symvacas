// Preserve WASM streaming compilation while bounding stalled downloads. Wheels
// stay buffered so a body failure can be retried before installing any files.
function streamWasm(response,controller,input,timeout) {
  const reader=response.body.getReader();
  let timer;
  const body=new ReadableStream({
    start(stream) {
      timer=setTimeout(()=>{
        stream.error(new Error(`Engine download timed out: ${input}`));
        controller.abort();
        reader.cancel().catch(()=>{});
      },timeout);
    },
    async pull(stream) {
      try {
        const {done,value}=await reader.read();
        if(done){clearTimeout(timer);stream.close();}
        else stream.enqueue(value);
      } catch(error){clearTimeout(timer);stream.error(error);}
    },
    cancel(reason){clearTimeout(timer);controller.abort();return reader.cancel(reason);}
  });
  return new Response(body,{status:response.status,headers:response.headers});
}

export async function fetchEngineAsset(fetcher,input,options={},timeout=30000) {
  let lastError;
  for(let attempt=0;attempt<2;attempt++) {
    const controller=new AbortController();
    let timer;
    const started=Date.now();
    try {
      return await Promise.race([
        (async()=>{
          const response=await fetcher(input,{...options,signal:controller.signal,...(attempt?{cache:'reload'}:{})});
          if(!response.ok)throw new Error(`Engine download failed (${response.status}): ${input}`);
          if(/\.wasm(?:[?#]|$)/i.test(String(input?.url??input))&&response.body&&response.headers.get('content-type')?.split(';')[0].trim()==='application/wasm')
            // A stream failure is retried by Emscripten's ArrayBuffer fallback.
            return streamWasm(response,controller,input,Math.max(1,timeout-(Date.now()-started)));
          const body=await response.arrayBuffer();
          return new Response(body,{status:response.status,headers:response.headers});
        })(),
        new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(new Error(`Engine download timed out: ${input}`));},timeout);})
      ]);
    } catch(error) {lastError=error;}
    finally {clearTimeout(timer);}
  }
  throw lastError;
}
