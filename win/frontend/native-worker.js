// Worker-compatible transport so every existing workspace keeps its engine contract.
let nextSession=0;
export class NativeWorker {
  constructor({invoke=window.__TAURI__.core.invoke,Channel=window.__TAURI__.core.Channel}={}) {
    this.invoke=invoke;this.Channel=Channel;this.session=++nextSession;this.active=true;
    this.starting=Promise.resolve().then(()=>invoke('native_start',{session:this.session}));
    this.starting.then(info=>{
      if(!this.active){void this.stop();return;}
      this.deliver({type:'ready',version:info.python});
    },error=>this.deliver({type:'fatal',error:String(error)}));
  }
  deliver(data){if(this.active)this.onmessage?.({data});}
  postMessage(data) {
    if(!this.active)return;
    if(data.type==='input') {
      this.invoke('native_input',{session:this.session,id:data.id,inputId:data.inputId,value:data.value})
        .catch(error=>{if(this.active)this.onerror?.({message:String(error)});});
      return;
    }
    const onEvent=new this.Channel();onEvent.onmessage=message=>this.deliver(message);
    this.starting.then(()=>{
      if(!this.active)return;
      return this.invoke('native_execute',{session:this.session,id:data.id,request:data.request,onEvent})
        .then(result=>this.deliver({type:'result',id:data.id,result}),
          error=>this.deliver({type:'result',id:data.id,result:{ok:false,error:String(error)}}));
    }).catch(()=>{});
  }
  async stop(){try{await this.invoke('native_cancel',{session:this.session});}catch{}}
  terminate(){this.active=false;void this.stop();}
}
