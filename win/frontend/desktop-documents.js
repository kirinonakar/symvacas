import {parseCatalogHelp} from './catalog-help.js';

const documents={
  'README.md':['Windows guide','Windows 가이드'],
  'THIRD_PARTY.md':['Open-source licenses','오픈소스 라이선스'],
  'MCP_GUIDE.md':['MCP guide','MCP 가이드'],
  'LICENSE':['MIT license','MIT 라이선스']
};

export function createDesktopDocuments({document=globalThis.document,fetch=globalThis.fetch}={}){
  const ko=()=>document.documentElement.lang.startsWith('ko');
  const text=(en,kr)=>ko()?kr:en;
  const node=(tag,value='',className='')=>{
    const element=document.createElement(tag);element.textContent=value;element.className=className;return element;
  };
  const dialog=node('dialog','','desktop-document-dialog');dialog.id='desktop-document-dialog';dialog.setAttribute('aria-labelledby','desktop-document-title');
  const header=node('div','','desktop-document-header'),title=node('h2');title.id='desktop-document-title';
  const close=node('button');close.type='button';close.autofocus=true;close.onclick=()=>dialog.close();
  const body=node('article','','desktop-document-body');body.translate=false;
  header.append(title,close);dialog.append(header,body);document.body.append(dialog);
  let request=0;
  dialog.addEventListener('close',()=>{request++;});
  dialog.addEventListener('click',event=>{
    if(event.target!==dialog)return;
    const r=dialog.getBoundingClientRect();
    if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();
  });
  const localDocument=value=>{
    try{
      const url=new URL(value,document.baseURI),base=new URL('.',document.baseURI);
      const name=url.pathname.slice(base.pathname.length);
      return url.origin===base.origin&&url.pathname.startsWith(base.pathname)&&Object.hasOwn(documents,name)?{name,hash:url.hash}:null;
    }catch{return null;}
  };
  function inline(parent,value){
    let from=0;
    for(const match of value.matchAll(/\[([^\]]+)\]\(([^\s)]+)\)/g)){
      parent.append(document.createTextNode(value.slice(from,match.index)));
      const local=localDocument(match[2]);let link;
      if(local){
        link=node('a',match[1]);link.href=match[2];link.setAttribute('aria-haspopup','dialog');
        link.onclick=event=>{event.preventDefault();void open(local.name,local.hash);};
      }else{
        try{
          const url=new URL(match[2]);
          if(['https:','http:'].includes(url.protocol)){link=node('a',match[1]);link.href=url.href;link.target='_blank';link.rel='noopener noreferrer';}
        }catch{}
      }
      parent.append(link||document.createTextNode(match[1]));from=match.index+match[0].length;
    }
    parent.append(document.createTextNode(value.slice(from)));
  }
  function render(markdown){
    const fragment=document.createDocumentFragment();let list=null,listType='';
    for(const block of parseCatalogHelp(markdown)){
      const bullet=block.kind==='body'&&block.text.match(/^([-*]|\d+\.)\s+(.*)$/);
      if(bullet){
        const type=/\d/.test(bullet[1])?'ol':'ul';
        if(!list||listType!==type){list=node(type);listType=type;fragment.append(list);}
        const item=node('li');inline(item,bullet[2]);list.append(item);continue;
      }
      list=null;
      if(block.kind==='diagram'){const pre=node('pre'),code=node('code',block.text);pre.append(code);fragment.append(pre);}
      else if(block.kind==='table'){
        const scroll=node('div','','desktop-document-table'),table=node('table'),head=node('thead'),heading=node('tr'),rows=node('tbody');
        for(const caption of block.columns){const cell=node('th');inline(cell,caption);heading.append(cell);}
        head.append(heading);
        for(const values of block.rows){const row=node('tr');for(const value of values){const cell=node('td');inline(cell,value);row.append(cell);}rows.append(row);}
        table.append(head,rows);scroll.append(table);fragment.append(scroll);
      }else{
        const element=node(({heading:'h1',category:'h2',subheading:'h3'})[block.kind]||'p');
        inline(element,(block.signature?block.signature+' — ':'')+block.text);fragment.append(element);
      }
    }
    body.replaceChildren(fragment);body.scrollTop=0;
  }
  async function open(name,hash=''){
    if(!Object.hasOwn(documents,name))return;
    const current=++request;
    title.textContent=documents[name][ko()?1:0];close.textContent=text('Close','닫기');
    const loading=node('p',text('Loading…','불러오는 중…'));loading.setAttribute('role','status');body.replaceChildren(loading);
    if(!dialog.open)dialog.showModal();
    try{
      const response=await fetch(name);
      if(!response.ok)throw new Error(`HTTP ${response.status}`);
      // Decode the bundled UTF-8 bytes independently of the native Markdown MIME header.
      const markdown=new TextDecoder('utf-8',{fatal:true}).decode(await response.arrayBuffer());
      if(current!==request||!dialog.open)return;
      render(markdown);
      if(hash){const heading=[...body.querySelectorAll('h1,h2,h3')].find(el=>'#'+el.textContent.toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu,'').replace(/\s+/g,'-')===hash);heading?.scrollIntoView();}
    }catch{
      if(current!==request||!dialog.open)return;
      const error=node('p',text('Could not load this document.','문서를 불러올 수 없습니다.'));error.setAttribute('role','alert');
      const retry=node('button',text('Retry','다시 시도'));retry.type='button';retry.onclick=()=>void open(name,hash);body.replaceChildren(error,retry);
    }
  }
  const links=[...document.querySelectorAll('footer a')].flatMap(link=>{
    const local=localDocument(link.getAttribute('href'));if(!local)return [];
    const click=event=>{event.preventDefault();void open(local.name,local.hash);};
    link.setAttribute('aria-haspopup','dialog');link.addEventListener('click',click);return [{link,click}];
  });
  return {open,dispose(){request++;for(const {link,click} of links)link.removeEventListener('click',click);dialog.remove();}};
}
