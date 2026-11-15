import {roundNumber} from './display-format.js';

export function tipCommand({bill,percent='15',fixed='15',tax='0',people='2',method='percent',whole=true}){
  const clean=text=>{text=String(text).replace(/,/g,'');if(text.length>128||!/^\+?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(text))throw new Error('Enter non-negative amounts and percentages');return text;};
  bill=clean(bill);percent=method==='amount'?'0':clean(percent);fixed=method==='amount'?clean(fixed):'0';tax=clean(tax);
  if(!Number.isInteger(Number(people))||Number(people)<1||Number(people)>999)throw new Error('People must be between 1 and 999');
  const cents=value=>`floor((${value})*100+1/2)/100`,originalTip=cents(method==='amount'?fixed:`(${bill})*(${percent})/100`),taxAmount=cents(`(${bill})*(${tax})/100`),originalTotal=`(${cents(bill)}+${originalTip}+${taxAmount})`,total=whole?`(ceil(${originalTotal}/${people})*${people})`:originalTotal,tip=whole?`(${originalTip}+${total}-${originalTotal})`:originalTip,share=`floor(${total}*100/${people})/100`,extras=`mod(${total}*100,${people})`;
  const tipPercent=method==='amount'||whole?(Number(bill)===0?'0':`(${tip})/(${bill})*100`):percent;
  return `[${tip},${taxAmount},${total},${share},${share}+1/100,${extras},${tipPercent}]`;
}
function moneyNumber(node){
  if(node.kind==='fraction'){
    const [numerator,denominator]=node.args.map(part=>BigInt(part.value));
    const hundredths=(numerator*200n+denominator)/(denominator*2n);
    const raw=hundredths.toString().padStart(3,'0');
    return `${raw.slice(0,-2)}.${raw.slice(-2)}`;
  }
  const [whole,fraction='']=roundNumber(node.value,2).split('.');
  return `${whole}.${fraction.padEnd(2,'0')}`;
}

export function tipBreakdown(result){
  const [tip,tax,total,share,extraShare,extraPeople,percent]=result.tree.args;
  return {tip:moneyNumber(tip),tax:moneyNumber(tax),total:moneyNumber(total),share:moneyNumber(share),
    extraShare:moneyNumber(extraShare),extraPeople:Number(extraPeople.value),percent:moneyNumber(percent)};
}
