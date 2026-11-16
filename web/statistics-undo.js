function sameDraft(left,right){
  return Object.keys(left).every(key=>left[key]===right[key]);
}

export function createStatisticsUndoHistory(){
  const entries=[];
  let characters=0,editGroup=null,lastEdit=0;
  function endGroup(){editGroup=null;}
  function undo(){
    endGroup();
    const draft=entries.pop();
    if(draft)characters-=draft.csv.length;
    return draft;
  }
  return {
    get canUndo(){return entries.length>0;},
    endGroup,undo,
    record(before,after,group=null,now=performance.now()){
      if(sameDraft(before,after))return;
      const coalesce=group!==null&&group===editGroup&&now-lastEdit<=750&&entries.length>0;
      editGroup=group;
      lastEdit=now;
      if(coalesce){
        if(sameDraft(entries.at(-1),after))undo();
        return;
      }
      entries.push(before);
      characters+=before.csv.length;
      while(entries.length>1&&(entries.length>50||characters>8_000_000))characters-=entries.shift().csv.length;
    }
  };
}
