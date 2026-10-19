import {latexInput,latexMathBlocks,parse} from './parser.js';

/** Normalize a pasted block without joining independent graph/equation lines. */
export function latexPaste(text,{prefix='',suffix='',multiline=false,surface=false}={}) {
  prefix=prefix.slice(prefix.lastIndexOf('\n')+1);
  suffix=suffix.split('\n')[0];
  function block(text,prefix,suffix){
    const converted=latexInput(text,{prefix,suffix}),body=latexMathBlocks(text)?.[0]??text;
    if(multiline&&!surface&&/^\s*\\begin\s*\{(?:aligned|align\*?|gathered|split)\}/.test(body)){
      return parse(converted).args.map(node=>converted.slice(node.start,node.end)).join('\n');
    }
    return converted;
  }
  const blocks=multiline?latexMathBlocks(text):null;
  if(blocks)return blocks.map((body,index)=>block(`\\[${body}\\]`,index===0?prefix:'',index===blocks.length-1?suffix:'')).join('\n');
  if(!multiline||!text.includes('\n'))return block(text,prefix,suffix);
  try {
    const lines=text.split(/(\r?\n)/);
    return lines.map((line,index)=>index%2?line:block(line,index===0?prefix:'',index===lines.length-1?suffix:'')).join('');
  }catch {
    // Matrices and a single wrapped formula may themselves span several lines.
    return block(text,prefix,suffix);
  }
}

export function bindMathPaste(field,{multiline=false,surface=false,onError=()=>{}}={}) {
  let previous=field.value,selection=null;
  field.addEventListener('beforeinput',()=>{previous=field.value;selection={start:field.selectionStart,end:field.selectionEnd};});
  field.addEventListener('focus',()=>{previous=field.value;});
  // Some keyboards insert clipboard text through input without a paste event.
  // Normalize before the workspace's input handler reads source/rows/history.
  field.addEventListener('input',event=>{
    const source=field.value,before=previous,range=selection;previous=source;selection=null;
    const type=event.inputType||'';
    if(field.readOnly||field.disabled||event.isComposing||
      !['','insertFromPaste','insertReplacementText'].includes(type)&&!(type==='insertText'&&event.data?.length>1))return;
    let start,end;
    if(event.data&&source.slice(field.selectionEnd-event.data.length,field.selectionEnd)===event.data){
      start=field.selectionEnd-event.data.length;end=field.selectionEnd;
    }else if(range&&source.length>=range.start+before.length-range.end&&source.startsWith(before.slice(0,range.start))&&source.endsWith(before.slice(range.end))){
      start=range.start;end=source.length-(before.length-range.end);
    }else{
      start=0;while(start<before.length&&start<source.length&&before[start]===source[start])start++;
      let suffix=0;while(suffix<before.length-start&&suffix<source.length-start&&before[before.length-1-suffix]===source[source.length-1-suffix])suffix++;
      end=source.length-suffix;
    }
    if(start===end)return;
    try{
      const text=source.slice(start,end),converted=latexPaste(text,{prefix:source.slice(0,start),suffix:source.slice(end),multiline,surface:typeof surface==='function'?surface():surface});
      if(converted!==text)field.setRangeText(converted,start,end,'end');
      previous=field.value;
    }catch(error){onError(error.message);}
  },true);
  field.addEventListener('paste',event=>{
    const text=event.clipboardData?.getData('text/plain')||event.clipboardData?.getData('text');
    if(!text||field.readOnly||field.disabled)return;
    const start=field.selectionStart,end=field.selectionEnd;
    try {
      const converted=latexPaste(text,{prefix:field.value.slice(0,start),suffix:field.value.slice(end),multiline,surface:typeof surface==='function'?surface():surface});
      if(converted===text)return;
      event.preventDefault();
      field.setRangeText(converted,start,end,'end');
      previous=field.value;
      field.dispatchEvent(new field.ownerDocument.defaultView.Event('input',{bubbles:true}));
    }catch(error){event.preventDefault();onError(error.message);}
  });
}
