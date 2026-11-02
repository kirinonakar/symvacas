// Convert grouped counts or individual observations to one 2×2 table per stratum.
export function stratifiedStatisticsData(rows,opts,columnLabels=[]){
  const layout=opts.layout||'tables',width=Math.max(0,...rows.map(row=>row.length));
  const col=key=>{const i=Number(opts[key]);if(!Number.isInteger(i)||i<0||i>=width)throw new Error('Choose valid data columns');return i;};
  const groupA=String(opts.groupA??'A').trim(),groupB=String(opts.groupB??'B').trim();
  if(!groupA||!groupB||groupA===groupB)throw new Error('Enter two different treatment/group values');
  const count=value=>{
    if(!/^\+?\d+(?:\.0+)?$/.test(value))throw new Error('Enter nonnegative integer counts');
    return BigInt(value.replace(/\.0+$/,''));
  };
  const labels={'group:1':groupA,'group:2':groupB};
  let tables,event='Event',nonEvent='No event';
  if(layout==='tables'){
    const indices=['a','b','c','d'].map(col);
    if(new Set(indices).size!==4)throw new Error('Roles must use different columns');
    tables=rows.map(row=>indices.map(i=>{
      const value=String(row[i]??'').trim();if(!value)throw new Error('Complete selected rows required');return String(count(value));
    }));
  }else{
    if(!['counts','observations'].includes(layout))throw new Error('Invalid analysis option');
    const raw=layout==='observations';
    const keys=raw?['patientStratum','patientGroup','outcome']:['stratum','group','events',opts.countType==='total'?'total':'nonEvents'];
    const indices=keys.map(col);
    if(new Set(indices).size!==indices.length)throw new Error('Roles must use different columns');
    const eventValue=String(opts.eventValue??'1').trim(),nonEventValue=String(opts.nonEventValue??'0').trim();
    if(raw&&(!eventValue||!nonEventValue||eventValue===nonEventValue))throw new Error('Enter two different outcome values');
    const name=(key,fallback)=>columnLabels[col(key)]||fallback;
    event=raw?`${name('outcome','Outcome')} = ${eventValue}`:name('events','Event');
    nonEvent=raw?`${name('outcome','Outcome')} = ${nonEventValue}`:opts.countType==='total'?'No event':name('nonEvents','No event');
    const strata=new Map();
    for(const row of rows){
      const selected=indices.map(i=>String(row[i]??'').trim());
      if(selected.some(value=>!value))throw new Error('Complete selected rows required');
      const [stratum,group]=selected;
      if(group!==groupA&&group!==groupB)throw new Error('Treatment/group column must contain only the two selected groups');
      if(!strata.has(stratum))strata.set(stratum,[0n,0n,0n,0n]);
      const totals=strata.get(stratum),offset=group===groupA?0:2;
      if(raw){
        if(![eventValue,nonEventValue].includes(selected[2]))throw new Error('Outcome column must contain only the two selected outcome values');
        totals[offset+(selected[2]===eventValue?0:1)]++;
      }else{
        const events=count(selected[2]),other=count(selected[3]);
        if(opts.countType==='total'&&other<events)throw new Error('Total count must be at least the event count');
        totals[offset]+=events;totals[offset+1]+=opts.countType==='total'?other-events:other;
      }
    }
    tables=[...strata.values()].map(row=>row.map(String));
    [...strata.keys()].forEach((name,i)=>{labels[`stratum:${i+1}`]=name;});
  }
  labels['count:1']=`${groupA} · ${event}`;labels['count:2']=`${groupA} · ${nonEvent}`;
  labels['count:3']=`${groupB} · ${event}`;labels['count:4']=`${groupB} · ${nonEvent}`;
  labels['outcome:event']=event;labels['outcome:nonevent']=nonEvent;
  return {tables,labels};
}
