// A small DOM/event harness for controller tests, without launching a browser.
export function layoutFixture({width=1200,saved={},mode='scientific'}={}) {
  const observers=[];
  class Events {
    listeners=new Map();
    addEventListener(type,handler){if(!this.listeners.has(type))this.listeners.set(type,new Set());this.listeners.get(type).add(handler);}
    removeEventListener(type,handler){this.listeners.get(type)?.delete(handler);}
    dispatchEvent(event){this[`on${event.type}`]?.(event);for(const handler of this.listeners.get(event.type)||[])handler(event);}
  }
  class Node extends Events {
    children=[];attributes=new Map();dataset={};hidden=false;id='';className='';
    style={setProperty:(key,value)=>this.attributes.set(key,value)};
    classList={
      add:(...names)=>{this.className=[...new Set([...this.className.split(' '),...names])].join(' ').trim();},
      remove:(...names)=>{this.className=this.className.split(' ').filter(name=>!names.includes(name)).join(' ');},
      contains:name=>this.className.split(' ').includes(name)
    };
    constructor(tag){super();this.tagName=tag.toUpperCase();}
    append(...nodes){for(const node of nodes){node.remove();node.parentElement=this;this.children.push(node);}}
    prepend(...nodes){const previous=[...this.children];this.append(...nodes,...previous);}
    before(...nodes){const parent=this.parentElement,previous=[...parent.children];parent.append(...previous.slice(0,previous.indexOf(this)),...nodes,...previous.slice(previous.indexOf(this)));}
    after(...nodes){const parent=this.parentElement,previous=[...parent.children],at=previous.indexOf(this)+1;parent.append(...previous.slice(0,at),...nodes,...previous.slice(at));}
    remove(){if(this.parentElement){const siblings=this.parentElement.children;siblings.splice(siblings.indexOf(this),1);this.parentElement=null;}}
    setAttribute(key,value){this.attributes.set(key,String(value));}
    getAttribute(key){return this.attributes.get(key)??null;}
    matches(selector){return selector.split(',').some(part=>{
      let simple=part.trim();
      const excluded=simple.match(/:not\(([^)]+)\)/);
      if(excluded){if(this.matches(excluded[1]))return false;simple=simple.replace(excluded[0],'');}
      const mode=simple.match(/\[data-mode="([^"]+)"\]/);
      if(mode){if(this.dataset.mode!==mode[1])return false;simple=simple.replace(mode[0],'');}
      if(simple.startsWith('#'))return this.id===simple.slice(1);
      if(simple.startsWith('.'))return this.classList.contains(simple.slice(1));
      return this.tagName===simple.toUpperCase();
    });}
    querySelector(selector){
      const parts=selector.split('>').map(part=>part.trim());
      for(const child of this.children){
        if(child.matches(parts.at(-1))&&(parts.length===1||child.parentElement.matches(parts[0])))return child;
        const found=child.querySelector(selector);if(found)return found;
      }
      return null;
    }
    closest(selector){return this.matches(selector)?this:this.parentElement?.closest(selector);}
    contains(node){return this===node||this.children.some(child=>child.contains(node));}
    focus(){doc.activeElement=this;}
    getBoundingClientRect(){return {width,left:0};}
  }
  const view=new Events();view.innerWidth=width;view.Event=class {constructor(type){this.type=type;}};
  view.MutationObserver=class {
    constructor(callback){this.callback=callback;observers.push(this);}
    observe(target){this.target=target;}
    disconnect(){this.target=null;}
  };
  view.getComputedStyle=()=>({display:view.innerWidth<900?'none':'block'});
  const storage=new Map([['symvacas.desktop-layout.v1',JSON.stringify(saved)]]);
  view.localStorage={getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value)};
  const doc=new Node('document');doc.defaultView=view;doc.createElement=tag=>new Node(tag);
  doc.getElementById=id=>doc.querySelector('#'+id);
  const add=(parent,tag,id='',className='')=>{const node=new Node(tag);node.id=id;node.className=className;parent.append(node);return node;};
  const root=add(doc,'html');root.lang='en';root.dataset.workspace=mode;doc.documentElement=root;
  const instrument=add(add(root,'body'),'div','','instrument');
  add(instrument,'nav','workspace-navigation');
  const actions=add(add(instrument,'header'),'div','','header-actions');
  for(const id of ['history-button','catalog-button'])add(actions,'button',id);
  add(instrument,'div','','mode-bar');add(instrument,'div','','runtime-bar');
  const main=add(instrument,'main');
  for(const mode of ['graph','statistics']){
    const workspace=add(main,'section','','workspace');workspace.dataset.mode=mode;
    if(mode==='graph'){
      add(workspace,'textarea','graph-source').value='sin(x)';
      add(workspace,'div','graph-parameter-actions','graph-toolbar');
      add(workspace,'div','','graph-toolbar');add(workspace,'div','','graph-plot-frame');
      for(const id of ['graph-formulas','graph-status','graph-trace'])add(workspace,'div',id);
      add(workspace,'details','graph-ranges','graph-section').open=true;
      add(workspace,'details','graph-surface-rendering','graph-section');
      const analysis=add(workspace,'details','graph-analysis','graph-section');analysis.open=true;add(analysis,'div','graph-analysis-sliders');
      add(workspace,'details','graph-coordinates','graph-section');
    }else{
      const toolbar=add(workspace,'div','','form-row');add(toolbar,'select','dataset-list');
      add(toolbar,'input','dataset-name');
      for(const id of ['dataset-save','dataset-delete','csv-open','csv-save'])add(toolbar,'button',id);
      const editor=add(workspace,'div','statistics-editor');add(editor,'textarea','statistics-data');add(editor,'div','statistics-grid');
      add(workspace,'button','statistics-collapse-all');
      add(workspace,'div','statistics-error');add(workspace,'div','statistics-summary');add(workspace,'details','statistics-models');
    }
  }
  return {doc,view,root,storage,observers,find:id=>doc.getElementById(id),
    mutate(target){for(const observer of observers)if(observer.target===target)observer.callback();}};
}
