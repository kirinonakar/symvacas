// ExchangeRate-API's available codes, bundled so selection also works offline.
// https://open.er-api.com/v6/latest/USD (2026-11-03)
const currencies=`USD AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB BRL BSD BTN BWP BYN BZD CAD CDF CHF CLF CLP CNH CNY COP CRC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP FOK GBP GEL GGP GHS GIP GMD GNF GTQ GYD HKD HNL HRK HTG HUF IDR ILS IMP INR IQD IRR ISK JEP JMD JOD JPY KES KGS KHR KID KMF KRW KWD KYD KZT LAK LBP LKR LRD LSL LYD MAD MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MYR MZN NAD NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON RSD RUB RWF SAR SBD SCR SDG SEK SGD SHP SLE SLL SOS SRD SSP STN SYP SZL THB TJS TMT TND TOP TRY TTD TVD TWD TZS UAH UGX UYU UZS VES VND VUV WST XAF XCD XCG XDR XOF XPF YER ZAR ZMW ZWG ZWL`.split(' ').sort();
const extraNames={
  CNH:['Chinese Yuan (offshore)','중국 위안화 (역외)'],
  FOK:['Faroese Króna','페로 제도 크로나'],GGP:['Guernsey Pound','건지 파운드'],
  IMP:['Manx Pound','맨섬 파운드'],JEP:['Jersey Pound','저지 파운드'],
  KID:['Kiribati Dollar','키리바시 달러'],TVD:['Tuvaluan Dollar','투발루 달러'],
  XCG:['Caribbean Guilder','카리브 길더'],ZWG:['Zimbabwean Gold','짐바브웨 골드']
};

export function createConversionControls(doc=document){
  const byId=id=>doc.getElementById(id),root=doc.documentElement;
  const fields=['currency-from','currency-to'].map(id=>{
    const input=byId(id),select=doc.createElement('select');select.id=id;select.setAttribute('translate','no');
    for(const code of currencies){const option=doc.createElement('option');option.value=code;select.append(option);}
    select.value=input.value.trim().toUpperCase();input.replaceWith(select);return select;
  });
  const swaps=[];
  for(const kind of ['currency','unit']){
    const from=byId(`${kind}-from`).closest('label'),to=byId(`${kind}-to`).closest('label');
    const swap=byId(kind==='unit'?'units-swap':'currency-swap'),pair=doc.createElement('div');pair.className='conversion-pair';
    const svg=doc.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');svg.setAttribute('focusable','false');
    const path=doc.createElementNS(svg.namespaceURI,'path');path.setAttribute('d','M7 7h14v2H7v3L2 8l5-4v3zm10 8H3v2h14v3l5-4-5-4v3z');svg.append(path);
    swap.type='button';swap.classList.add('conversion-swap');swap.replaceChildren(svg);
    from.before(pair);pair.append(from,swap,to);swaps.push({kind,swap});
  }
  const whole=byId('tip-whole').closest('label'),tipRow=whole.closest('.form-row');
  const tipOptions=doc.createElement('div');tipOptions.className='form-row tip-options';
  tipRow.after(tipOptions);tipOptions.append(whole);
  function labels(){
    const ko=root.lang.startsWith('ko'),names=new Intl.DisplayNames([ko?'ko':'en'],{type:'currency'});
    for(const field of fields)for(const option of field.options){
      const name=extraNames[option.value]?.[ko?1:0]||names.of(option.value);
      option.textContent=`${option.value} (${name})`;
    }
    for(const {kind,swap} of swaps){
      const label=kind==='currency'?(ko?'통화 교체':'Swap currencies'):(ko?'단위 교체':'Swap units');
      swap.title=label;swap.setAttribute('aria-label',label);
    }
  }
  labels();
  const observer=new doc.defaultView.MutationObserver(labels);
  observer.observe(root,{attributes:true,attributeFilter:['lang']});
  return {dispose(){observer.disconnect();}};
}
