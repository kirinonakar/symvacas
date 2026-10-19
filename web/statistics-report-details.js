import {t} from './i18n.js';

export function statisticsDetailText(detail){
  const context=(detail.context||[]).map(item=>`${t(item.label)}: ${item.value}`).join(' / ');
  const section=detail.section&&detail.section!=='Summary'?t(detail.section):'';
  return [section,context,`${t(detail.label)}: ${t(detail.text)}`].filter(Boolean).join(' · ');
}

// Keep contextual explanations intact; standalone assumptions and notes share
// one disclosure and identical source text appears only once.
export function statisticsModelDetails(report,note=''){
  const normalize=value=>String(value||'').trim().replace(/\s+/g,' ');
  const seen=new Set(),detailTexts=new Set(),paragraphs=[];
  const add=(text,key)=>{if(normalize(text)&&!seen.has(key)){seen.add(key);paragraphs.push(text);}};
  for(const detail of report.details||[]){
    const raw=normalize(detail.text);if(!raw)continue;
    detailTexts.add(raw);
    const text=statisticsDetailText(detail);
    add(text,detail.context?.length?normalize(text):raw);
  }
  for(const raw of [...(report.assumptions||[]),...(report.notes||[]),note]){
    const key=normalize(raw);if(key&&!detailTexts.has(key))add(t(String(raw).trim()),key);
  }
  return paragraphs;
}
