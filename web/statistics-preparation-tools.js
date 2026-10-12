import {statisticsPreparationSchema} from './statistics-preparation-schema.js';
import {preparationDataset,preparationTransform,preparationFilterConditions} from './statistics-preparation-data.js';
import {defaultStatisticsGroupValues} from './statistics-group-column.js';
import {statisticsColumnNames} from './workspace-commands.js';
import {$,element} from './app-ui.js';
import {t} from './i18n.js';

export function createPreparationTools({state,data,kind,persist,applyData,saveAsNew}){
  const root=$('statistics-preparation-tools'),panels=new Map();
  let cachedSource,cachedKind,cachedDataset;
  function dataset(){const source=data(),selectedKind=kind();if(source!==cachedSource||selectedKind!==cachedKind||!cachedDataset){cachedDataset=preparationDataset(source,selectedKind);cachedSource=source;cachedKind=selectedKind;}return cachedDataset;}
  for(const definition of statisticsPreparationSchema){
    const section=element('details','','statistics-section');section.id=`statistics-preparation-tool-${definition.id}`;
    section.open=state.statisticsSections[section.id]===true;section.addEventListener('toggle',persist);
    const summary=element('summary',definition.label),fields=element('div','','form-row'),preview=element('div','','statistics-analysis-result'),status=element('p','','hint'),actions=element('div','','form-row');
    const filtering=definition.id==='filter';
    const run=element('button',filtering?'Preview filter':'Preview transformation'),apply=element('button',filtering?'Save as new dataset':'Apply to current data');run.type=apply.type='button';apply.disabled=true;apply.dataset.invalidAnalysis='true';
    section.append(summary,fields,status,preview,actions);actions.append(run,apply);root.append(section);
    const panel={definition,fields,preview,status,run,apply,snapshot:null,signature:'',widgets:new Map()};panels.set(definition.id,panel);
    run.onclick=()=>{
      if(document.documentElement.dataset.busy==='true')return;
      try{
        const settings=read(panel),key=context(panel),result=preparationTransform(data(),kind(),definition.id,settings);
        panel.snapshot={key,result};renderPreview(panel,result);status.textContent=filtering?`${t('Input rows')}: ${result.rows.length+result.changed} · ${t('Kept rows')}: ${result.rows.length} · ${t('Removed rows')}: ${result.changed}${!result.rows.length?' · '+t('No rows match the filter; adjust the conditions'):''}`:`${t('Output rows')}: ${result.rows.length} · ${t('Output columns')}: ${result.headers.length} · ${t('Changed / computed rows')}: ${result.changed}${result.omitted?' · '+t('Blank derived values')+': '+result.omitted:''}`;
        apply.disabled=!result.rows.length;apply.dataset.invalidAnalysis=String(apply.disabled);
      }catch(error){panel.snapshot=null;preview.replaceChildren();status.textContent=t(error.message);apply.disabled=true;apply.dataset.invalidAnalysis='true';}
    };
    apply.onclick=()=>{
      if(apply.disabled||document.documentElement.dataset.busy==='true'||panel.snapshot?.key!==context(panel))return;
      try{
        const result=panel.snapshot.result;
        if(filtering){saveAsNew(result,read(panel).datasetName);status.textContent=t('Filtered rows saved as a new dataset');}
        else {applyData(result);status.textContent=t('Transformation applied to current data');}
        panel.snapshot=null;apply.disabled=true;apply.dataset.invalidAnalysis='true';
      }catch(error){status.textContent=t(error.message);}
    };
  }
  function id(panel,key){return `statistics-preparation-${panel.definition.id}-${key}`;}
  function read(panel){return Object.fromEntries(panel.definition.fields.map(field=>{
    let value=String(state.fields[id(panel,field.key)]??field.default);
    if(field.type==='column'){const count=dataset().headers.length;const at=Number(value);value=String(at===-1?count-1:Math.max(0,Math.min(count-1,Number.isInteger(at)?at:0)));}
    return [field.key,value];
  }));}
  function context(panel){const settings=read(panel);return JSON.stringify([data(),kind(),Object.fromEntries(panel.definition.fields.filter(field=>field.preview!==false).map(field=>[field.key,settings[field.key]]))]);}
  function edited(panel,field,value){
    const key=id(panel,field.key),old=String(state.fields[key]??field.default);
    if(panel.definition.id==='recode'&&field.key==='cuts'){
      const groups=id(panel,'groups');if(String(state.fields[groups]??'0,1')===defaultStatisticsGroupValues(old))state.fields[groups]=defaultStatisticsGroupValues(value);
      const widget=panel.widgets.get('groups');if(widget)widget.value=String(state.fields[groups]??'0,1');
    }
    state.fields[key]=value;
    if(panel.definition.id==='wideToLong'&&field.key==='ids'){
      const measures=id(panel,'measures');if(state.fields[measures]&&state.fields[measures]!=='auto')state.fields[measures]=state.fields[measures].split(',').filter(at=>!value.split(',').includes(at)).join(',');
    }
    updatePanel(panel);persist();
  }
  function updatePanel(panel){
    let headers=[];try{headers=dataset().headers;}catch{headers=[];}
    const aliases=statisticsColumnNames(headers.length),columnLabels=headers.map((name,i)=>name===aliases[i]?name:`${name} (${aliases[i]})`);
    const settings=readSafe(panel),visible=panel.definition.fields.filter(field=>!field.when||Object.entries(field.when).every(([key,value])=>settings[key]===value));
    const signature=JSON.stringify([headers,visible.map(field=>field.type==='conditions'?[field.key,preparationFilterConditions(settings[field.key]).map(item=>item.operator)]:field.key)]);
    if(signature!==panel.signature){
      panel.signature=signature;panel.fields.replaceChildren();panel.widgets.clear();
      for(const field of visible){
        const grouped=['columns','conditions'].includes(field.type);
        const label=element(grouped?'fieldset':'label',grouped?'':field.label),key=id(panel,field.key);
        if(field.type==='conditions'){
          label.className='statistics-form-columns';label.append(element('legend',field.label));
          const conditions=preparationFilterConditions(settings[field.key]);
          const change=(index,property,value)=>{const next=preparationFilterConditions(read(panel)[field.key]);next[index][property]=value;edited(panel,field,JSON.stringify(next));};
          conditions.forEach((condition,index)=>{
            const row=element('div','','form-row');
            for(const [property,title,options] of [['column','Source column',headers.map((_,i)=>[String(i),columnLabels[i]])],['operator','Filter operator',field.options],['value','Filter value',null]]){
              if(property==='value'&&['blank','notBlank'].includes(condition.operator))continue;
              const entry=element('label',title),widget=element(options?'select':'input');widget.id=`${key}-${index}-${property}`;
              if(options)options.forEach(([value,name])=>{const option=element('option',name);option.value=value;widget.append(option);});else widget.type='text';
              widget.value=String(condition[property]);widget.addEventListener('input',()=>change(index,property,widget.value));entry.append(widget);row.append(entry);
            }
            const remove=element('button','Remove condition');remove.type='button';remove.disabled=conditions.length===1;
            remove.onclick=()=>{const next=preparationFilterConditions(read(panel)[field.key]);next.splice(index,1);edited(panel,field,JSON.stringify(next));};row.append(remove);label.append(row);
          });
          const add=element('button','Add condition');add.type='button';add.id=`${key}-add`;
          add.onclick=()=>edited(panel,field,JSON.stringify([...preparationFilterConditions(read(panel)[field.key]),{column:'0',operator:'notBlank',value:''}]));label.append(add);
        }else if(field.type==='columns'){
          label.className='statistics-form-columns';label.append(element('legend',field.label));
          const selected=settings[field.key]==='auto'?headers.map((_,i)=>String(i)).filter(i=>!settings.ids.split(',').includes(i)):settings[field.key].split(',');
          headers.forEach((name,i)=>{const entry=element('label',columnLabels[i],'check'),check=element('input');check.type='checkbox';check.value=String(i);check.checked=selected.includes(String(i));check.dataset.preparationField=key;
            check.onchange=()=>edited(panel,field,[...label.querySelectorAll('input:checked')].map(input=>input.value).join(','));entry.append(check);label.append(entry);});
        }else{
          const widget=element(field.type==='choice'||field.type==='column'?'select':field.type==='multiline'?'textarea':'input');widget.id=key;
          if(field.type==='column')headers.forEach((name,i)=>{const option=element('option',columnLabels[i]);option.value=String(i);widget.append(option);});
          if(field.type==='choice')field.options.forEach(([value,name])=>{const option=element('option',name);option.value=value;widget.append(option);});
          if(widget.tagName==='INPUT')widget.type='text';if(field.type==='multiline')widget.rows=4;
          widget.value=settings[field.key];widget.addEventListener('input',()=>edited(panel,field,widget.value));label.append(widget);panel.widgets.set(field.key,widget);
        }
        panel.fields.append(label);
      }
    }else{
      // Update structural column selections without replacing focused text inputs.
      for(const field of visible.filter(field=>field.type==='columns')){
        const selected=settings[field.key]==='auto'?headers.map((_,i)=>String(i)).filter(i=>!settings.ids.split(',').includes(i)):settings[field.key].split(',');
        for(const check of panel.fields.querySelectorAll(`input[data-preparation-field="${id(panel,field.key)}"]`))check.checked=selected.includes(check.value);
      }
    }
    if(panel.snapshot?.key!==contextSafe(panel)){panel.apply.disabled=true;panel.apply.dataset.invalidAnalysis='true';if(panel.snapshot)panel.status.textContent=t('Preview is outdated; preview the transformation again');}
    panel.run.disabled=!headers.length;
    if(!panel.snapshot&&!panel.status.textContent)panel.status.textContent=t(help(panel.definition.id));
  }
  function readSafe(panel){try{return read(panel);}catch{return Object.fromEntries(panel.definition.fields.map(field=>[field.key,String(state.fields[id(panel,field.key)]??field.default)]));}}
  function contextSafe(panel){try{return context(panel);}catch{return '';}}
  function renderPreview(panel,result){
    const table=element('table'),heading=element('tr');result.headers.forEach(name=>heading.append(element('th',name)));table.append(heading);
    result.rows.slice(0,6).forEach(row=>{const tr=element('tr');row.forEach(cell=>tr.append(element('td',cell)));table.append(tr);});
    const scroll=element('div','','table-scroll');scroll.append(table);panel.preview.replaceChildren(scroll);
  }
  function help(id){return {
    filter:'Choose columns and add conditions. Numeric comparisons omit blank or nonnumeric cells; text comparisons are case-sensitive. AND requires every condition, OR requires at least one. Preview the kept rows, then save them as a new dataset. The source dataset is preserved.',
    wideToLong:'ID columns are repeated for each measurement. With no ID columns, row IDs are generated. Blank measurements are retained.',
    longToWide:'Choose ID, variable and value columns. Missing combinations become blank. Set a text prefix for numeric variable names. Duplicate pairs require an explicit policy.',
    recode:'Write one old value, new value rule per line; <missing> matches a blank cell. Numeric intervals use < and ≥. Unmatched values follow the selected option.',
    derive:'Use column names (x, y, z, …) or header names in arithmetic formulas. A label such as test (x) accepts test or x. Supports sqrt, abs, exp, log, trigonometric functions (radians), round, min, max, sum, mean and if(condition,a,b). Missing or invalid numerical results become blank.'
  }[id];}
  return {update:()=>{for(const panel of panels.values())updatePanel(panel);}};
}
