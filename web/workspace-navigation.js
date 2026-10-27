import {$,control,element} from './app-ui.js';

// Reuse the mode picker and section headings so navigation follows the same
// ordering and translations as the compact layout.
export function createWorkspaceNavigation({changeMode}) {
  const navigation=$('workspace-navigation');
  const heading=element('h2','Workspace','workspace-navigation-heading');
  const modes=element('ul','','workspace-navigation-modes');
  const modeButtons=new Map(),sectionButtons=new Map();
  let activeSection=null;
  for(const option of $('mode').options) {
    const item=element('li');
    const button=control(option.textContent,()=>{
      activeSection=null;
      changeMode(option.value);
      update(option.value);
      if(option.value==='statistics')document.querySelector('.instrument').scrollIntoView({block:'start'});
    },'workspace-navigation-mode');
    button.dataset.workspaceTarget=option.value;
    modeButtons.set(option.value,button);
    item.append(button);
    if(option.value==='statistics') {
      const sections=element('ul','','workspace-navigation-sections');
      for(const section of document.querySelectorAll('.workspace[data-mode="statistics"] > details.statistics-section, #statistics-models, #statistics-tests')) {
        const summary=section.querySelector(':scope > summary');
        const sectionItem=element('li');
        const shortcut=control(summary.textContent,()=>{
          changeMode('statistics');
          // Nested analyses need their containing section expanded as well.
          for(let parent=section;parent;parent=parent.parentElement) {
            if(parent.tagName==='DETAILS')parent.open=true;
          }
          activeSection=section.id;
          update('statistics');
          section.scrollIntoView({block:'start'});
          summary.focus({preventScroll:true});
        },'workspace-navigation-section');
        shortcut.setAttribute('aria-controls',section.id);
        sectionButtons.set(section.id,shortcut);
        sectionItem.append(shortcut);
        sections.append(sectionItem);
      }
      item.append(sections);
    }
    modes.append(item);
  }
  navigation.replaceChildren(heading,modes);

  function update(mode) {
    if(mode!=='statistics')activeSection=null;
    for(const [name,button] of modeButtons) {
      if(name===mode)button.setAttribute('aria-current','page');
      else button.removeAttribute('aria-current');
    }
    for(const [id,button] of sectionButtons) {
      if(id===activeSection)button.setAttribute('aria-current','location');
      else button.removeAttribute('aria-current');
    }
  }
  update($('mode').value);
  return {update};
}
