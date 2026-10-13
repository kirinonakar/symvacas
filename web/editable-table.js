import {element,control} from './app-ui.js';
import {t} from './i18n.js';

// One spreadsheet surface for statistics, matrices, and vectors.
export function editableTable({rows,columns,value,onInput,onDeleteRow,onMoveColumn,onDeleteColumn,onRenameColumn,label,normalizePaste,viewport}) {
  const table=element('table','','editable-table'),colgroup=element('colgroup'),head=element('thead'),heading=element('tr'),body=element('tbody');
  // Fixed table layout needs explicit column sizes; cell min-width is unreliable.
  table.style.minWidth=`${columns.length*80+36+(onDeleteRow?36:0)}px`;
  if(onDeleteRow){const actionColumn=element('col');actionColumn.style.width='36px';colgroup.append(actionColumn);}
  const numberColumn=element('col');numberColumn.style.width='36px';colgroup.append(numberColumn);
  colgroup.append(...columns.map(()=>element('col')));
  table.setAttribute('aria-label',label);
  if(onDeleteRow)heading.append(element('th',''));
  heading.append(element('th','#'));
  columns.forEach((name,col)=>{
    const th=element('th',onRenameColumn?'':name);th.scope='col';
    if(onRenameColumn){const button=control(name,()=>onRenameColumn(col),'table-column-header');button.dataset.column=String(col);button.dataset.columnAction='rename';button.setAttribute('aria-label',`${t('Edit column header')}: ${name}`);th.append(button);}
    heading.append(th);
  });
  head.append(heading);
  // Column actions mirror the Android statistics table editor: move left, move right, delete.
  if((onMoveColumn||onDeleteColumn)&&columns.length>1){
    const actions=element('tr','','table-column-actions');
    if(onDeleteRow)actions.append(element('th',''));
    actions.append(element('th',''));
    columns.forEach((_,col)=>{
      const cell=element('th');
      if(onMoveColumn){
        const left=control('◀',()=>onMoveColumn(col,-1));
        left.disabled=col===0;left.dataset.column=String(col);left.dataset.columnAction='left';left.setAttribute('aria-label',t('Move column left'));
        const right=control('▶',()=>onMoveColumn(col,1));
        right.disabled=col===columns.length-1;right.dataset.column=String(col);right.dataset.columnAction='right';right.setAttribute('aria-label',t('Move column right'));
        cell.append(left,right);
      }
      if(onDeleteColumn){
        const remove=control('×',()=>onDeleteColumn(col));
        remove.dataset.column=String(col);remove.dataset.columnAction='delete';remove.setAttribute('aria-label',t('Delete column'));
        cell.append(remove);
      }
      actions.append(cell);
    });
    head.append(actions);
  }
  const virtual=!!viewport&&rows>200,rowHeight=40,rendered=new Map();let scheduled=null,windowKey='';
  table.setAttribute('aria-rowcount',String(rows+head.children.length));
  if(virtual)table.classList.add('virtual-table');
  function makeRow(row){
    const tr=element('tr'),number=element('th',String(row+1));number.scope='row';
    tr.setAttribute('aria-rowindex',String(row+head.children.length+1));
    if(onDeleteRow){const td=element('td'),remove=control('×',()=>onDeleteRow(row));remove.setAttribute('aria-label',`${t('Delete')} ${row+1}`);td.className='table-row-action';td.append(remove);tr.append(td);}
    tr.append(number);
    for(let col=0;col<columns.length;col++){
      const td=element('td'),input=element('input');
      input.value=value(row,col);input.dataset.row=String(row);input.dataset.column=String(col);
      input.setAttribute('aria-label',`${columns[col]}, ${row+1}`);
      input.autocomplete='off';input.spellcheck=false;input.size=1;
      input.oninput=()=>onInput(row,col,input.value,input);
      if(normalizePaste)input.onpaste=event=>{
        const text=event.clipboardData?.getData('text/plain');if(!text)return;
        const normalized=normalizePaste(text);if(normalized===text)return;
        event.preventDefault();input.setRangeText(normalized,input.selectionStart,input.selectionEnd,'end');input.oninput();
      };
      input.onkeydown=event=>{
        const delta={ArrowLeft:[0,-1],ArrowRight:[0,1],ArrowUp:[-1,0],ArrowDown:[1,0]}[event.key];
        if(!delta||event.isComposing||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;
        event.preventDefault();event.stopPropagation();
        const target=row+delta[0],column=col+delta[1];
        if(virtual&&target>=0&&target<rows&&column>=0&&column<columns.length&&!rendered.has(target)){
          viewport.scrollTop=(head.offsetHeight||60)+target*rowHeight;renderWindow(target);
        }
        const next=table.querySelector(`input[data-row="${target}"][data-column="${column}"]`);
        if(next){next.focus({preventScroll:true});next.select();next.scrollIntoView?.({block:'nearest',inline:'nearest'});}
      };
      td.append(input);tr.append(td);
    }
    return tr;
  }
  function renderWindow(target){
    const first=Math.max(0,Math.floor((viewport.scrollTop-(head.offsetHeight||60))/rowHeight)-6),count=Math.ceil((viewport.clientHeight||300)/rowHeight)+14;
    const start=target===undefined?first:Math.max(0,target-6),end=Math.min(rows,start+count),wanted=new Set();
    const active=document.activeElement,activeRow=table.contains(active)&&active.dataset.row!==undefined?Number(active.dataset.row):-1,key=`${start}:${end}:${activeRow}`;
    if(key===windowKey)return;windowKey=key;
    for(let row=start;row<end;row++)wanted.add(row);
    if(activeRow>=0)wanted.add(activeRow);
    const nodes=[];let previous=0;
    for(const row of [...wanted].sort((a,b)=>a-b)){
      if(row>previous){const spacer=element('tr'),cell=element('td');spacer.setAttribute('aria-hidden','true');cell.colSpan=columns.length+1+(onDeleteRow?1:0);cell.style.height=`${(row-previous)*rowHeight}px`;cell.className='table-row-spacer';spacer.append(cell);nodes.push(spacer);}
      if(!rendered.has(row))rendered.set(row,makeRow(row));nodes.push(rendered.get(row));previous=row+1;
    }
    if(previous<rows){const spacer=element('tr'),cell=element('td');spacer.setAttribute('aria-hidden','true');cell.colSpan=columns.length+1+(onDeleteRow?1:0);cell.style.height=`${(rows-previous)*rowHeight}px`;cell.className='table-row-spacer';spacer.append(cell);nodes.push(spacer);}
    for(const child of [...body.children])if(!nodes.includes(child))child.remove();
    nodes.forEach((node,index)=>{if(body.children[index]!==node)body.insertBefore(node,body.children[index]||null);});
    for(const row of rendered.keys())if(!wanted.has(row))rendered.delete(row);
  }
  function schedule(){if(scheduled===null)scheduled=requestAnimationFrame(()=>{scheduled=null;renderWindow();});}
  table.append(colgroup,head,body);
  if(virtual){
    renderWindow();viewport.addEventListener('scroll',schedule,{passive:true});table.addEventListener('focusout',schedule);
    table.refreshEditableTable=()=>renderWindow();
    table.disposeEditableTable=()=>{viewport.removeEventListener('scroll',schedule);table.removeEventListener('focusout',schedule);if(scheduled!==null)cancelAnimationFrame(scheduled);};
  }else for(let row=0;row<rows;row++)body.append(makeRow(row));
  return table;
}
