import {$,value,element,control} from './app-ui.js';
import {t} from './i18n.js';
import {downloadFile} from './storage.js';
import {bindPythonEditor} from './python-tools.js';
import {pythonActionIcon} from './python-action-icons.js';

export function createPythonWorkspace({engine,ui,persist,requestOptions,error,run}) {
  const {pickFile,clipboard}=ui;
  let fileName='symvacas.py';
  for(const [id,label,icon] of [['new','New','new'],['open','Open .py','open'],['save','Save .py','save'],['save-as','Save as','save_as']])pythonActionIcon($('python-'+id),label,icon);
  $('python-new').onclick=()=>{fileName='symvacas.py';$('python-source').value='';$('python-output').textContent='';persist();};
  $('python-open').onclick=()=>pickFile('.py,text/x-python',async file=>{$('python-source').value=await file.text();fileName=file.name;persist();});
  $('python-save').onclick=()=>downloadFile(fileName,value('python-source'),'text/x-python');
  $('python-save-as').onclick=()=>{
    const name=window.prompt(t('Save as'),fileName)?.trim();
    if(!name)return;
    fileName=/\.py$/i.test(name)?name:name+'.py';
    downloadFile(fileName,value('python-source'),'text/x-python');
  };
  $('python-source').onkeydown=event=>{if(event.key==='Enter'&&(event.ctrlKey||event.metaKey)){event.preventDefault();run('python');}};
  const pythonToolbar=$('python-save-as').parentElement,pythonToolsToolbar=element('div','','form-row python-tools-toolbar'),pythonSuggestions=element('div','','form-row');
  const sourceLabel=$('python-source').closest('label');
  sourceLabel.insertAdjacentElement('afterend',pythonSuggestions);
  sourceLabel.insertAdjacentElement('beforebegin',pythonToolsToolbar);
  bindPythonEditor($('python-source'),{toolbar:pythonToolbar,toolsToolbar:pythonToolsToolbar,suggestions:pythonSuggestions,onEdit:persist,copy:clipboard,paste:()=>navigator.clipboard.readText()});
  pythonToolbar.append(pythonToolbar.querySelector('[data-run="python"]'));
  function requestInput({prompt,output,signal}) {
    $('python-output').textContent=output+prompt;
    return new Promise(resolve=>{
      const dialog=element('dialog'),form=element('form'),label=element('label',prompt||'input()'),field=element('input'),actions=element('div','','form-row');
      dialog.setAttribute('aria-label',t('Python input'));
      field.type='text';field.autocomplete='off';label.append(field);
      const submit=element('button','Continue');submit.type='submit';
      actions.append(submit,control('Cancel',()=>finish(null)));form.append(label,actions);dialog.append(form);
      function finish(value){signal.removeEventListener('abort',abort);dialog.remove();resolve(value);}
      function abort(){finish(null);}
      form.onsubmit=event=>{event.preventDefault();finish(field.value);};
      dialog.addEventListener('cancel',event=>{event.preventDefault();finish(null);});
      dialog.addEventListener('close',()=>finish(null));
      signal.addEventListener('abort',abort,{once:true});
      if(signal.aborted){finish(null);return;}
      document.body.append(dialog);dialog.showModal();field.focus();
    });
  }
  async function execute() {
    $('python-output').textContent=t('실행 중…');
    const result=await engine.execute({...requestOptions(),action:'python',source:value('python-source'),inputs:value('python-input')===''?[]:value('python-input').split(/\r?\n/),filename:fileName},{onInput:requestInput,context:'python'});
    $('python-output').textContent=[result.output,result.error&&t(result.error)].filter(Boolean).join('\n')||t('실행 완료');
    if(!result.ok)error(result.error);
  }
  return {run:execute};
}
