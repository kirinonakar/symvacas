import {t} from './i18n.js';

export function statisticsDetailText(detail){
  const context=(detail.context||[]).map(item=>`${t(item.label)}: ${item.value}`).join(' / ');
  const section=detail.section&&detail.section!=='Summary'?t(detail.section):'';
  return [section,context,`${t(detail.label)}: ${t(detail.text)}`].filter(Boolean).join(' · ');
}
