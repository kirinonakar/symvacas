import {removeGraphInputLine} from './graph-input.js';
import {t} from './i18n.js';

// Match the graph editor's line controls without replacing the native textarea.
export function bindEquationInput(field,gutter,onDelete=()=>{}){
  const syncScroll=()=>{gutter.style.transform=`translateY(${-field.scrollTop}px)`;};
  function refresh(){
    gutter.replaceChildren();
    field.value.split(/\r?\n/).forEach((_,index)=>{
      const row=document.createElement('div'),number=document.createElement('span'),remove=document.createElement('button');
      row.className='graph-input-line';number.textContent=String(index+1);
      remove.type='button';remove.textContent='×';remove.title=`${t('Delete line')} ${index+1}`;remove.setAttribute('aria-label',remove.title);
      remove.onclick=()=>{
        const start=field.value.split(/\r?\n/).slice(0,index).reduce((offset,line)=>offset+line.length+1,0);
        field.value=removeGraphInputLine(field.value,index);
        field.setSelectionRange(Math.min(start,field.value.length),Math.min(start,field.value.length));
        field.dispatchEvent(new Event('input',{bubbles:true}));
        onDelete();
      };
      row.append(remove,number);gutter.append(row);
    });
    syncScroll();
  }
  field.addEventListener('input',refresh);
  field.addEventListener('scroll',syncScroll);
  refresh();
  return refresh;
}
