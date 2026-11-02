// The native registry is authoritative for saved datasets; other state stays in IndexedDB.
export function createDesktopStorage(storage,invoke=window.__TAURI__.core.invoke){
  let baseline={},available=false,queue=Promise.resolve();
  const records=state=>Object.fromEntries(Object.entries(state?.datasets||{}).map(([name,source])=>[name,{source,kind:state.datasetKinds?.[name]||'list'}]));
  return {
    async readState(options={}){
      const state=await storage.readState(options);
      try{
        const result=await invoke('sync_statistics_datasets',{base:{},changes:records(state),bootstrap:true});
        baseline=result.datasets;
        state.datasets=Object.fromEntries(Object.entries(baseline).map(([name,record])=>[name,record.source]));
        state.datasetKinds=Object.fromEntries(Object.entries(baseline).map(([name,record])=>[name,record.kind]));
        available=true;
      }catch(error){options.onError?.(error);available=false;}
      return state;
    },
    writeState(state){
      const snapshot=structuredClone(state),next=records(snapshot);
      queue=queue.then(async()=>{
        if(!available)return false;
        const changes={};
        for(const name of new Set([...Object.keys(baseline),...Object.keys(next)])){
          if(JSON.stringify(baseline[name])!==JSON.stringify(next[name]))Object.defineProperty(changes,name,{value:next[name]??null,enumerable:true});
        }
        try{
          if(Object.keys(changes).length)await invoke('sync_statistics_datasets',{base:baseline,changes,bootstrap:false});
          baseline=structuredClone(next);
          return await storage.writeState(snapshot);
        }catch(error){console.error('Could not save shared statistics datasets:',error);return false;}
      });
      return queue;
    }
  };
}
