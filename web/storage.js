const LEGACY_KEY='symvacas-web-v1',SETTINGS_KEY='symvacas-web-settings-v2';
const DATABASE='symvacas-web',STORE='state',META=JSON.stringify(['meta','settings']);
const settingKeys=new Set(('language languageChosen theme secondKeys tapeClearedAt resultDisplayMode autoCloseBrackets wordWrap calcModeStepByStep copyAsLatex persistHistory haptics sound inputFont outputFont precision digits removeComputationLimit statisticsSections graphColors graphColorsVersion assumptions displayShortcuts rates').split(' '));
const collections=new Set(['datasets','datasetKinds','fields','variables']);
const object=value=>value&&typeof value==='object'&&!Array.isArray(value);

// Stop inspecting a value as soon as it exceeds the small-settings budget.
// Never stringify a large matrix/AST just to measure its size.
function small(value,budget=8192){
  const pending=[value];let size=0;
  while(pending.length){
    const item=pending.pop();size+=16;
    if(typeof item==='string')size+=item.length*6;
    else if(item&&typeof item==='object'){
      for(const key in item)if(Object.hasOwn(item,key)){
        size+=key.length*6+8;pending.push(item[key]);
        if(size+pending.length*16>budget)return false;
      }
    }
    if(size>budget)return false;
  }
  return true;
}
function equal(a,b){
  if(a===b)return true;
  if(!a||!b||typeof a!=='object'||typeof b!=='object'||Array.isArray(a)!==Array.isArray(b))return false;
  const keys=Object.keys(a);
  return keys.length===Object.keys(b).length&&keys.every(key=>Object.hasOwn(b,key)&&equal(a[key],b[key]));
}
function split(state){
  const settings={},variables={},records=new Map();
  for(const [key,value] of Object.entries(state)){
    if(key==='variables'&&object(value)){
      for(const [name,entry] of Object.entries(value)){
        if(small(entry)&&small({...variables,[name]:entry},32768))Object.defineProperty(variables,name,{value:entry,enumerable:true,configurable:true});
        else records.set(JSON.stringify(['variables',name]),entry);
      }
    }else if(settingKeys.has(key)&&small(value)&&small({...settings,[key]:value},32768))settings[key]=value;
    else if(collections.has(key)&&object(value)){
      if(!Object.keys(value).length)records.set(JSON.stringify(['values',key]),{});
      for(const [name,entry] of Object.entries(value))records.set(JSON.stringify([key,name]),entry);
    }else records.set(JSON.stringify(['values',key]),value);
  }
  settings.variables=variables;
  records.set(META,settings);
  return records;
}
function combine(records){
  const settings=records.get(META)||{},state={...settings,variables:{...settings.variables}};
  for(const [key,value] of records){
    const [section,name]=JSON.parse(key);
    if(section==='meta')continue;
    if(section==='values')Object.defineProperty(state,name,{value,enumerable:true,writable:true,configurable:true});
    else{
      if(!object(state[section]))state[section]={};
      Object.defineProperty(state[section],name,{value,enumerable:true,writable:true,configurable:true});
    }
  }
  return state;
}

export function createStorage({indexedDB=()=>globalThis.indexedDB,localStorage=()=>globalThis.localStorage}={}){
  let database,loading,loaded=false,loadFailed=false,committed=new Map(),requested,queue=Promise.resolve();
  function readLocal(key){try{const value=JSON.parse(localStorage().getItem(key));return object(value)?value:null;}catch{return null;}}
  function open(){
    if(!database)database=new Promise((resolve,reject)=>{
      const request=indexedDB().open(DATABASE,1);let rejected=false;
      request.onupgradeneeded=()=>request.result.createObjectStore(STORE);
      request.onerror=()=>reject(request.error);
      request.onblocked=()=>{rejected=true;reject(new Error('Database upgrade blocked'));};
      request.onsuccess=()=>{
        const db=request.result;
        if(rejected){db.close();return;}
        db.onversionchange=()=>{db.close();loadFailed=true;};resolve(db);
      };
    });
    return database;
  }
  async function readRecords(){
    const db=await open();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(STORE,'readonly'),store=tx.objectStore(STORE),keys=store.getAllKeys(),values=store.getAll();
      tx.oncomplete=()=>resolve(new Map(keys.result.map((key,i)=>[key,values.result[i]])));
      tx.onabort=tx.onerror=()=>reject(tx.error||new Error('Could not read storage'));
    });
  }
  async function commit(next){
    const db=await open();
    const changed=[...next].filter(([key,value])=>!committed.has(key)||!equal(value,committed.get(key)));
    const removed=[...committed.keys()].filter(key=>!next.has(key));
    if(changed.length||removed.length)await new Promise((resolve,reject)=>{
      const tx=db.transaction(STORE,'readwrite'),store=tx.objectStore(STORE);
      tx.oncomplete=resolve;tx.onabort=tx.onerror=()=>reject(tx.error||new Error('Could not save storage'));
      try{for(const key of removed)store.delete(key);for(const [key,value] of changed)store.put(value,key);}
      catch(error){tx.abort();reject(error);}
    });
    committed=next;
    // This small mirror is expendable: IndexedDB also keeps it atomically
    // with the workspace, so imports and resets cannot leave a partial state.
    try{localStorage().setItem(SETTINGS_KEY,JSON.stringify(next.get(META)));}catch{}
    try{localStorage().removeItem(LEGACY_KEY);}catch{}
  }
  async function readState({onError=()=>{}}={}){
    if(!loading)loading=(async()=>{
      const legacy=readLocal(LEGACY_KEY);
      try{
        committed=await readRecords();
        if(!committed.has(META)){
          const initial=legacy||readLocal(SETTINGS_KEY)||{};
          if(legacy)await commit(split(initial));
          else return initial;
        }
        return combine(committed);
      }catch(error){loadFailed=true;onError(error);return legacy||readLocal(SETTINGS_KEY)||{};}
      finally{loaded=true;}
    })();
    const initial=await loading;
    return structuredClone(committed.has(META)&&!loadFailed?combine(committed):initial);
  }
  function writeState(state){
    if(loadFailed)return Promise.resolve(false); // Never overwrite an unread workspace.
    let next;
    try{
      const previous=requested||committed;
      next=new Map([...split(state)].map(([key,value])=>[key,previous.has(key)&&equal(value,previous.get(key))?previous.get(key):structuredClone(value)]));
      requested=next;
    }catch{return Promise.resolve(false);}
    queue=queue.then(async()=>{
      if(!loaded)await readState();
      if(loadFailed)return false;
      try{await commit(next);return true;}catch{return false;}
    });
    return queue;
  }
  return {readState,writeState};
}
const storage=createStorage();
export const readState=storage.readState,writeState=storage.writeState;
export function downloadFile(name,content,type='text/plain') {
  const url=URL.createObjectURL(new Blob([content],{type}));
  const a=document.createElement('a'); a.href=url; a.download=name; a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
