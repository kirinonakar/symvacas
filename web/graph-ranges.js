// Full-precision numeric fields, paired sliders, and range-track interaction.
import {displayNumber} from './display-format.js';
import {hasImplicitSurface} from './graph-input.js';

export function createGraphRangeControls({
  $,
  analysisControls,
  currentBounds,
  getAnalysisSliders,
  options,
  persist,
  queue,
  render,
  state,
  value
}){
  const rangeIds=['graph-min','graph-max','graph-ymin','graph-ymax','graph-xmin','graph-xmax','graph-analysis-a','graph-analysis-b','graph-t0','graph-zmin','graph-zmax'];
  const sliderIds=rangeIds.filter(id=>id!=='graph-t0');
  const rangePairs=[['graph-min','graph-max'],['graph-ymin','graph-ymax'],['graph-xmin','graph-xmax'],['graph-zmin','graph-zmax'],['graph-analysis-a','graph-analysis-b']];
  const pairedSliders=new Map();

  function fieldNumber(input){return input.value.trim()===''?NaN:Number(input.dataset.displayValue===input.value?input.dataset.fullValue:input.value);}

  function numeric(id){return fieldNumber($(id));}

  function displayField(input,number){input.dataset.fullValue=String(number);input.value=displayNumber(number,options().displayDigits);input.dataset.displayValue=input.value;}

  function editField(input){input.onfocus=()=>{if(input.dataset.displayValue===input.value){input.value=input.dataset.fullValue;input.dataset.displayValue=input.value;}};input.onblur=()=>{const number=fieldNumber(input);if(Number.isFinite(number)&&!input.hasAttribute('aria-invalid'))displayField(input,number);};}

  function analysisRange(){return [numeric('graph-min'),numeric('graph-max')];}

  function syncRangePair(pair){
    const numbers=pair.ids.map(numeric);if(!numbers.every(Number.isFinite))return;
    const sliders=pair.ids.map(id=>$(id+'-slider')),linked=pair.ids[0]==='graph-analysis-a';
    const [low,high]=linked?analysisRange():[Math.min(...sliders.map(slider=>Number(slider.min)),...numbers),Math.max(...sliders.map(slider=>Number(slider.max)),...numbers)];
    if(!Number.isFinite(high-low)||high<=low)return;
    const positions=numbers.map(number=>Math.max(low,Math.min(high,number)));
    sliders.forEach((slider,index)=>{slider.min=String(low);slider.max=String(high);slider.value=String(positions[index]);slider.setAttribute('aria-valuetext',displayNumber(positions[index],options().displayDigits));});
    pair.track.style.setProperty('--range-start',`${100*(positions[0]-low)/(high-low)}%`);pair.track.style.setProperty('--range-end',`${100*((sliders[1].hidden?positions[0]:positions[1])-low)/(high-low)}%`);
  }

  function resetRangeDomain(pair){
    if(pair.ids[0]==='graph-analysis-a'){syncRangePair(pair);return;}
    const [min,max]=pair.ids.map(numeric),span=max-min;if(!Number.isFinite(span)||span<=0)return;
    const low=min-span/2,high=max+span/2;if(!Number.isFinite(high-low))return;
    for(const id of pair.ids){$(id+'-slider').min=String(low);$(id+'-slider').max=String(high);}
    syncRangePair(pair);
  }

  function showNumber(id,number){const input=$(id);if(!Number.isFinite(number))return;displayField(input,number);const output=$(id+'-value');if(output)output.textContent=displayNumber(number,options().displayDigits);const slider=$(id+'-slider');if(slider){if(number<Number(slider.min))slider.min=String(number);if(number>Number(slider.max))slider.max=String(number);slider.value=String(number);slider.setAttribute('aria-valuetext',displayNumber(number,options().displayDigits));}const pair=pairedSliders.get(id);if(pair)syncRangePair(pair);}

  function renderRangeNumbers(){for(const id of rangeIds){if(value(id)!==''&&document.activeElement!==$(id))showNumber(id,numeric(id));}}

  function bindRangeTrackClick(track){
    track.addEventListener('click',event=>{
      if(event.target!==track||event.button!==0)return;
      const sliders=[...track.querySelectorAll('input[type="range"]')].filter(slider=>!slider.hidden&&!slider.disabled);
      const rect=track.getBoundingClientRect(),width=rect.width-20;
      if(!sliders.length||width<=0)return;
      const position=Math.max(0,Math.min(1,(event.clientX-rect.left-10)/width));
      const distance=slider=>Math.abs((Number(slider.value)-Number(slider.min))/(Number(slider.max)-Number(slider.min))-position);
      const slider=sliders.reduce((nearest,current)=>distance(current)<distance(nearest)||distance(current)===distance(nearest)&&current===document.activeElement?current:nearest);
      slider.value=String(Number(slider.min)+(Number(slider.max)-Number(slider.min))*position);
      slider.focus({preventScroll:true});
      for(const type of ['input','change'])slider.dispatchEvent(new track.ownerDocument.defaultView.Event(type,{bubbles:true}));
    });
  }

  function initializeRanges(){
    for(const id of rangeIds){const field=$(id);editField(field);for(const name of ['input','change'])field.addEventListener(name,()=>{if(field.dataset.displayValue!==field.value)delete field.dataset.displayValue;const pair=pairedSliders.get(id);if(pair)resetRangeDomain(pair);if(['graph-min','graph-max','graph-analysis-a'].includes(id))analysisControls();});}
    for(const id of sliderIds){const field=$(id),slider=document.createElement('input'),current=numeric(id);slider.type='range';slider.id=id+'-slider';slider.min=String(Math.min(-30,current-20));slider.max=String(Math.max(30,current+20));slider.step='any';slider.value=String(current);slider.setAttribute('aria-label',field.closest('label').firstChild.textContent.trim());field.insertAdjacentElement('afterend',slider);
      slider.oninput=()=>{
        const number=Number(slider.value),pair=pairedSliders.get(id),partner=pair&&!pair.ids.some(key=>$(key+'-slider').hidden)?pair.ids.find(key=>key!==id):null;
        let bounded=number;
        if(partner&&Number.isFinite(numeric(partner))){const limit=numeric(partner),gap=Math.max(2e-7,Math.abs(limit)*1e-10);bounded=id===pair.ids[0]?Math.min(number,limit-gap):Math.max(number,limit+gap);}
        if(id.startsWith('graph-analysis'))bounded=Math.max(Number(slider.min),Math.min(Number(slider.max),bounded));
        showNumber(id,bounded);if(!id.startsWith('graph-analysis')){state.bounds=currentBounds();render();}else renderRangeNumbers();
      };
      slider.onchange=()=>{persist();if(id.startsWith('graph-analysis'))analysisControls();else if(!id.startsWith('graph-z')||hasImplicitSurface(value('graph-source')))queue();};
    }
    for(const ids of rangePairs){
      const group=document.createElement('div'),fields=document.createElement('div'),track=document.createElement('div'),labels=ids.map(id=>$(id).closest('label'));
      group.className='graph-range-pair';fields.className='graph-range-fields';track.className='graph-range-slider';group.setAttribute('role','group');group.setAttribute('aria-labelledby',ids.map(id=>id+'-label').join(' '));
      const analysisPair=ids[0]==='graph-analysis-a';if(analysisPair)track.classList.add('graph-axis-slider');
      group.append(fields,track);labels[0].before(group);
      labels.forEach((label,index)=>{label.id=ids[index]+'-label';fields.append(label);track.append($(ids[index]+'-slider'));});
      if(analysisPair)getAnalysisSliders().prepend(group);
      const pair={ids,track};for(const id of ids)pairedSliders.set(id,pair);resetRangeDomain(pair);
      bindRangeTrackClick(track);
    }

  }
  return {fieldNumber,numeric,displayField,editField,analysisRange,syncRangePair,resetRangeDomain,showNumber,renderRangeNumbers,bindRangeTrackClick,rangeIds,sliderIds,rangePairs,pairedSliders,initializeRanges};
}
