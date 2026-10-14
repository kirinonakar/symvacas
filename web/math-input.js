import {latexInput} from './parser.js';

/** Normalize a pasted block without joining independent graph/equation lines. */
export function latexPaste(text,{prefix='',suffix='',multiline=false}={}) {
  prefix=prefix.slice(prefix.lastIndexOf('\n')+1);
  suffix=suffix.split('\n')[0];
  if(!multiline||!text.includes('\n'))return latexInput(text,{prefix,suffix});
  try {
    const lines=text.split(/(\r?\n)/);
    return lines.map((line,index)=>index%2?line:latexInput(line,{prefix:index===0?prefix:'',suffix:index===lines.length-1?suffix:''})).join('');
  }catch {
    // Matrices and a single wrapped formula may themselves span several lines.
    return latexInput(text,{prefix,suffix});
  }
}

export function bindMathPaste(field,{multiline=false,onError=()=>{}}={}) {
  field.addEventListener('paste',event=>{
    const text=event.clipboardData?.getData('text/plain')||event.clipboardData?.getData('text');
    if(!text||field.readOnly||field.disabled)return;
    const start=field.selectionStart,end=field.selectionEnd;
    try {
      const converted=latexPaste(text,{prefix:field.value.slice(0,start),suffix:field.value.slice(end),multiline});
      if(converted===text)return;
      event.preventDefault();
      field.setRangeText(converted,start,end,'end');
      field.dispatchEvent(new field.ownerDocument.defaultView.Event('input',{bubbles:true}));
    }catch(error){event.preventDefault();onError(error.message);}
  });
}
