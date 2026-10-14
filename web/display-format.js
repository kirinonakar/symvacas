// Display-only decimal rounding. Engine values and editable sources stay lossless.
export function roundNumber(value,digits=10,preserveSmallValues=false){
  const text=String(value),match=/^([+-]?)(\d*)(?:\.(\d*))?([eE][+-]?\d+)?$/.exec(text);
  if(!match||!match[2]&&!match[3])return text;
  let [,sign,whole,fraction='',exponent='']=match;
  if(!text.includes('.'))return text;
  digits=Math.max(0,Math.min(200,Math.trunc(digits)));
  const first=fraction.search(/[1-9]/);
  // Expand only when ordinary decimal-place rounding would erase a nonzero value.
  const expanded=preserveSmallValues&&!/[1-9]/.test(whole)&&first>=digits&&first>=0&&Number(fraction[digits]||'0')<5;
  if(expanded)digits=first+2;
  let raw=fraction.slice(0,digits).padEnd(digits,'0');whole=whole||'0';
  if(Number(fraction[digits]||'0')>=5){
    const rounded=(BigInt(whole+raw)+1n).toString().padStart(digits+1,'0');
    whole=digits?rounded.slice(0,-digits):rounded;raw=digits?rounded.slice(-digits):'';
  }
  if(expanded){
    // A carry (0.0000999 -> 0.00010) still has exactly two significant digits.
    raw=raw.slice(0,raw.search(/[1-9]/)+2);
  }else raw=raw.replace(/0+$/,'');
  if(!/[1-9]/.test(whole+raw))sign='';
  return sign+whole+(raw?'.'+raw:'')+exponent;
}
export function displayNumber(value,digits=10,preserveSmallValues=false){
  if(typeof value==='number'&&!Number.isFinite(value))return '—';
  return roundNumber(value,digits,preserveSmallValues);
}

// Text for the Copy button: the same digits, grouping, and notation the result view shows.
export function displayText(value,digits=10,{notation='off',grouping=false,engineeringShift=0,showZeroExponent=false,preserveSmallValues=false}={},allowNotation=true){
  const text=String(value);
  if(allowNotation&&notation!=='off'&&/^-?\d+(?:\.\d+)?(?:e[+-]?\d+)?$/i.test(text)&&/[1-9]/.test(text.split(/e/i)[0])){
    const [mantissa,exponent='0']=text.replace(/^-/,'').split(/e/i),[whole,fraction='']=mantissa.split('.'),combined=whole+fraction,first=combined.search(/[1-9]/),power=whole.length-first-1+Number(exponent),engPower=(notation==='eng'?Math.floor(power/3)*3:power)+engineeringShift,places=power-engPower+1;
    if(Math.abs(engPower)>40000||Math.abs(places)>40000)return roundNumber(text,digits,preserveSmallValues);
    const normalized=combined.slice(first).padEnd(Math.max(0,places),'0');
    const mantissaText=(text.startsWith('-')?'-':'')+(places<=0?'0.'+'0'.repeat(-places)+normalized:normalized.slice(0,places)+(normalized.length>places?'.'+normalized.slice(places):''));
    const shown=groupText(roundNumber(mantissaText,digits,preserveSmallValues),grouping);
    return engPower||showZeroExponent?`${shown}×10^${engPower}`:shown;
  }
  const shown=roundNumber(text,digits,preserveSmallValues);
  const number=/^-?[\d.]+(?:e[+-]?\d+)?$/i.test(shown);
  if(number&&/e/i.test(shown)){
    const [mantissa,exponent]=shown.split(/e/i);
    return `${mantissa}×10^${Number(exponent)}`;
  }
  return number?groupText(shown,grouping):shown;
}
function groupText(shown,grouping){
  if(!grouping)return shown;
  const [mantissa,exp]=shown.split(/e/i),[whole,fraction]=mantissa.split('.');
  return whole.replace(/\B(?=(\d{3})+(?!\d))/g,',')+(fraction?'.'+fraction:'')+(exp?'e'+exp:'');
}
