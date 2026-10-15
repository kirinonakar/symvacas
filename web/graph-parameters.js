// Parameter values, ranges, animation toggles, and their accessible controls.
import {displayNumber} from './display-format.js';
import {t} from './i18n.js';

export function createGraphParameterControls({
  $,
  bindRangeTrackClick,
  displayField,
  editField,
  fieldNumber,
  onError,
  options,
  parameterChanged,
  persist,
  state
}){
  function parameterVisibility(){
    const hasParameters=$('graph-parameters').children.length>0;
    $('graph-parameter-actions').hidden=!hasParameters;
    $('graph-parameters').hidden=!hasParameters||!state.parametersOpen;
    $('graph-parameters-toggle').setAttribute('aria-expanded',String(state.parametersOpen));
  }

  function syncParameterControls(resetRange=false){
    for(const caption of $('graph-parameters').querySelectorAll('[data-parameter]')){
      const name=caption.dataset.parameter,group=caption.closest('.graph-parameter'),number=state.parameters[name],limits=state.parameterRanges[name]||[-5,5];
      caption.textContent=name;
      const slider=group.querySelector('input[type="range"]'),field=group.querySelector('[data-parameter-value]');
      slider.min=String(limits[0]);slider.max=String(limits[1]);slider.value=String(number);slider.setAttribute('aria-valuetext',displayNumber(number,options().displayDigits));
      if(document.activeElement!==field){displayField(field,number);field.removeAttribute('aria-invalid');}
      for(const bound of group.querySelectorAll('[data-parameter-bound]'))if(document.activeElement!==bound)displayField(bound,limits[Number(bound.dataset.parameterBound)]);
      const rangeTrack=group.querySelector('[data-parameter-range]'),rangeSliders=[...rangeTrack.querySelectorAll('input[type="range"]')],span=limits[1]-limits[0];
      const low=resetRange?limits[0]-span/2:Math.min(Number(rangeSliders[0].min),limits[0]),high=resetRange?limits[1]+span/2:Math.max(Number(rangeSliders[0].max),limits[1]);
      rangeSliders.forEach((slider,index)=>{slider.min=String(low);slider.max=String(high);slider.value=String(limits[index]);slider.setAttribute('aria-valuetext',displayNumber(limits[index],options().displayDigits));});
      rangeTrack.style.setProperty('--range-start',`${100*(limits[0]-low)/(high-low)}%`);rangeTrack.style.setProperty('--range-end',`${100*(limits[1]-low)/(high-low)}%`);
    }
  }

  function parameterControls(names=[],force=false){
    if(!force&&$('graph-parameters').dataset.names===JSON.stringify(names)){syncParameterControls();return;}
    $('graph-parameters').dataset.names=JSON.stringify(names);
    $('graph-parameters').replaceChildren();
    for(const name of names){if(!(name in state.parameters))state.parameters[name]=1;const limits=state.parameterRanges[name]||[-5,5],label=document.createElement('div'),caption=document.createElement('span'),input=document.createElement('input'),valueInput=document.createElement('input'),ranges=document.createElement('div'),low=document.createElement('input'),high=document.createElement('input');
      const toggleLabel=document.createElement('label'),toggle=document.createElement('input');toggleLabel.className='check graph-parameter-name';toggle.type='checkbox';toggle.checked=state.animationEnabled[name]!==false;toggle.dataset.animateParameter=name;toggle.setAttribute('aria-label',`${t('Animate')}: ${name}`);toggle.onchange=()=>{state.animationEnabled[name]=toggle.checked;if(state.animation&&toggle.checked)state.animation.phases[name]=parameterPhase(name)-state.animation.phase;persist();};toggleLabel.append(toggle,caption);
      input.type='range';input.min=String(limits[0]);input.max=String(limits[1]);input.step='any';input.value=String(state.parameters[name]);caption.dataset.parameter=name;caption.textContent=name;
      input.setAttribute('aria-label',`${t('Parameter value')}: ${name}`);
      input.oninput=()=>{state.parameters[name]=Number(input.value);if(state.animation)state.animation.phases[name]=parameterPhase(name)-state.animation.phase;syncParameterControls();parameterChanged(true);};
      const finishDrag=()=>{parameterChanged(false);persist();};
      input.onchange=finishDrag;input.addEventListener('pointercancel',finishDrag);
      valueInput.type='number';valueInput.step='any';displayField(valueInput,state.parameters[name]);editField(valueInput);valueInput.dataset.parameterValue=name;valueInput.setAttribute('aria-label',`${t('Parameter value')}: ${name}`);
      const applyValue=()=>{
        const number=fieldNumber(valueInput);
        if(!Number.isFinite(number)||Math.abs(number)>1e9){valueInput.setAttribute('aria-invalid','true');onError(t('Enter a finite value between -1e9 and 1e9'));return;}
        const [a,b]=state.parameterRanges[name]||[-5,5];
        const half=(b-a)/2;
        state.parameterRanges[name]=[number-half,number+half];state.parameters[name]=number;
        if(state.animation)state.animation.phases[name]=parameterPhase(name)-state.animation.phase;
        valueInput.removeAttribute('aria-invalid');$('graph-status').textContent='';syncParameterControls(true);persist();parameterChanged();
      };
      valueInput.oninput=()=>valueInput.removeAttribute('aria-invalid');valueInput.onchange=applyValue;
      valueInput.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();applyValue();}else if(event.key==='Escape'){event.preventDefault();displayField(valueInput,state.parameters[name]);if(document.activeElement===valueInput){valueInput.value=valueInput.dataset.fullValue;valueInput.dataset.displayValue=valueInput.value;}valueInput.removeAttribute('aria-invalid');}};
      for(const [index,[field,number,labelText]] of [[low,limits[0],'Slider minimum'],[high,limits[1],'Slider maximum']].entries()){field.type='number';field.step='any';displayField(field,number);editField(field);field.dataset.parameterBound=String(index);field.setAttribute('aria-label',`${t(labelText)}: ${name}`);field.onchange=()=>{const a=fieldNumber(low),b=fieldNumber(high);if(!Number.isFinite(a)||!Number.isFinite(b)||a>=b){onError(t('Enter finite values with minimum < maximum'));return;}state.parameterRanges[name]=[a,b];state.parameters[name]=a+(b-a)/2;if(state.animation)state.animation.phases[name]=parameterPhase(name)-state.animation.phase;parameterControls(names,true);persist();parameterChanged();};}
      const rangeTrack=document.createElement('div');rangeTrack.className='graph-range-slider';rangeTrack.dataset.parameterRange=name;
      for(const index of [0,1]){
        const boundSlider=document.createElement('input'),span=limits[1]-limits[0];boundSlider.type='range';boundSlider.step='any';boundSlider.min=String(limits[0]-span/2);boundSlider.max=String(limits[1]+span/2);boundSlider.value=String(limits[index]);
        boundSlider.setAttribute('aria-label',`${t(index===0?'Slider minimum':'Slider maximum')}: ${name}`);
        boundSlider.oninput=()=>{
          const next=[...(state.parameterRanges[name]||[-5,5])],number=Number(boundSlider.value),other=next[1-index],gap=Math.max(2e-7,Math.abs(other)*1e-10);
          next[index]=index===0?Math.min(number,other-gap):Math.max(number,other+gap);
          state.parameterRanges[name]=next;state.parameters[name]=next[0]+(next[1]-next[0])/2;
          if(state.animation)state.animation.phases[name]=parameterPhase(name)-state.animation.phase;
          syncParameterControls();parameterChanged(true);
        };
        boundSlider.onchange=finishDrag;boundSlider.addEventListener('pointercancel',finishDrag);rangeTrack.append(boundSlider);
      }
      bindRangeTrackClick(rangeTrack);
      label.className='graph-parameter-value';label.append(toggleLabel,input,valueInput);ranges.className='form-row';ranges.append(low,high);const group=document.createElement('div');group.className='graph-parameter';group.append(label,ranges,rangeTrack);$('graph-parameters').append(group);
    }
    syncParameterControls();parameterVisibility();
  }

  function parameterPhase(name){const [a,b]=state.parameterRanges[name]||[-5,5];return Math.asin(Math.max(-1,Math.min(1,2*(state.parameters[name]-a)/(b-a)-1)));}

  $('graph-parameters-toggle').onclick=()=>{state.parametersOpen=!state.parametersOpen;parameterVisibility();persist();};
  $('graph-reset-parameters').onclick=()=>{for(const name of Object.keys(state.parameters)){state.parameterRanges[name]=[-5,5];state.parameters[name]=1;if(state.animation)state.animation.phases[name]=parameterPhase(name)-state.animation.phase;}parameterControls(Object.keys(state.parameters),true);persist();parameterChanged();};
  return {parameterVisibility,syncParameterControls,parameterControls,parameterPhase};
}
