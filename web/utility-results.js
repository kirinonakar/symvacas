import {$,control,element,value} from './app-ui.js';
import {t} from './i18n.js';
import {displayText} from './display-format.js';
import {tipBreakdown} from './money.js';
import {latexResult,resultDisplayTree,resultMathDisplay,resultText} from './result-display.js';

export const utilityModes=['programmer','units','tip','currency','functions'];

export function createUtilityResults({state,clipboard}) {
  const results=new Map();
  let functionDecimal=false;
  function set(mode,snapshot){
    if(snapshot)results.set(mode,snapshot);
    else results.delete(mode);
    render(mode);
    if(value('mode')===mode&&(snapshot?.result||snapshot?.error))$(`${mode}-result`).scrollIntoView?.({block:'nearest'});
  }
  function render(mode){
    const target=$(`${mode}-result`),snapshot=results.get(mode);
    target.replaceChildren();target.hidden=!snapshot;
    if(!snapshot)return;

    const heading=element('div','','statistics-result-heading');
    heading.append(element('h3','Result'));
    target.append(heading);
    if(snapshot.error){
      heading.append(control('Clear',()=>set(mode,null)));
      target.append(element('p',snapshot.error,'error'));
      return;
    }
    if(!snapshot.result){target.append(element('p','Calculating…','hint'));return;}

    const {result,source,amount,from,to,rate,people}=snapshot;
    const format={digits:state.digits,decimal:mode!=='functions'||functionDecimal,notation:state.resultDisplayMode,grouping:mode==='currency',preserveSmallValues:true};
    let copyText;
    if(mode==='programmer'){
      const {width,signed}=snapshot;
      target.append(element('p',`${width} ${t('Bits').toLowerCase()} · ${t(signed?'Signed':'Unsigned')}`,'utility-detail'));
      const values=['DEC','HEX','OCT','BIN'].map(base=>[base,result.bases[base]]);
      const metrics=element('dl','','utility-metrics programmer-metrics');
      for(const [base,digits] of values){
        const binary=base==='BIN';
        const card=element('div','',binary?'utility-metric programmer-binary':'utility-metric');
        const shown=binary?digits.match(/.{1,4}/g).join(' '):digits;
        const data=element('dd');
        data.append(element('strong',shown));
        card.append(element('dt',base),data);metrics.append(card);
      }
      target.append(metrics);
      copyText=values.map(([base,digits])=>`${base} ${digits}`).join('\n');
    }else if(mode==='tip'){
      const {tip,tax,total,share,extraShare,extraPeople,percent}=tipBreakdown(result);
      const splits=extraPeople?`${people-extraPeople} × ${share} + ${extraPeople} × ${extraShare}`:'';
      const metrics=[['Total',total],['Per person',extraPeople?`${share} · ${extraShare}`:share],['Tip amount',`${tip} (${percent}%)`],['Tax',tax]];
      const cards=element('div','','utility-metrics');
      for(const [label,amount] of metrics){
        const card=element('div','','utility-metric');card.append(element('span',label),element('strong',amount));cards.append(card);
      }
      target.append(cards);
      if(splits)target.append(element('p',splits,'utility-detail'));
      copyText=metrics.map(([label,amount])=>`${t(label)} ${amount}`).concat(splits||[]).join('\n');
    }else{
      if(mode==='functions'){
        const modes=element('div','','utility-display-modes');
        for(const decimal of [false,true]){
          const button=control(decimal?'Decimal':'Fraction',()=>{
            functionDecimal=decimal;
            render(mode);
            target.querySelector('[aria-pressed="true"]').focus();
          });
          button.setAttribute('aria-pressed',String(decimal===functionDecimal));modes.append(button);
        }
        target.append(modes);
      }
      const context=mode==='functions'?source:`${amount} ${from} → ${to}`;
      const suffix=mode==='functions'?'':to;
      target.append(element('p',context,'utility-detail'));
      const output=element('div','','utility-value'),tree=resultDisplayTree(result,format);
      const shown=resultText(result,format);
      output.append(tree?resultMathDisplay(tree,state.digits,format.decimal||result.approximate,format):element('span',shown));
      if(suffix)output.append(element('span',suffix,'utility-unit'));
      target.append(output);
      const rateDetail=mode==='currency'&&/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(rate.trim())
        ? `1 ${from} = ${displayText(rate.trim(),state.digits,{preserveSmallValues:true})} ${to}` : '';
      const details=[rateDetail,mode==='functions'?result.note:'',...(result.conditions||[])].filter(Boolean);
      for(const detail of details)target.append(element('p',detail,'utility-detail'));
      const answer=mode==='functions'&&state.copyAsLatex?latexResult(result,format):shown;
      copyText=[[answer,suffix].filter(Boolean).join(' '),...details].join('\n');
    }
    heading.append(control('Copy',()=>clipboard(copyText)),control('Clear',()=>set(mode,null)));
  }
  return {set,render:()=>utilityModes.forEach(render)};
}
