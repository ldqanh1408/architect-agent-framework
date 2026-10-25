"use strict";
function manualEvidenceEditor(form,kind,scope,details){
 const panel=document.createElement('section');form.append(panel);let records=[],review=null;
 function node(tag,text){const element=document.createElement(tag);element.textContent=text;return element;}
 function draw(){
  panel.replaceChildren();records=[];review=null;scope.disabled=kind.value==='manual_review';
  details.parentElement.hidden=['accept','manual_review'].includes(kind.value);
  if(kind.value==='manual_review'){
   panel.append(node('h3','Inspect exact source evidence / Đọc đúng bằng chứng nguồn'));
   const label=node('label','Review obligation / Nghĩa vụ cần review'),select=document.createElement('select');select.setAttribute('aria-label','Review obligation');
   const packets=(packet.review_packets||[]).filter(p=>!p.error);
   for(const item of packets){const option=node('option',item.obligations[0].id);option.value=item.obligations[0].id;select.append(option);}label.append(select);panel.append(label);
   const documents=document.createElement('div');panel.append(documents);
   function show(){
    documents.replaceChildren();records=[];review=packets.find(p=>p.obligations[0].id===select.value);scope.value=select.value;
    if(!review){documents.append(node('p','Complete source evidence is unavailable. Review remains incomplete.'));return;}
    documents.append(node('p',review.obligations[0].rubric));
    for(const source of review.documents){
     const detail=document.createElement('details');detail.append(node('summary',source.path+' · '+source.side),node('small',source.artifact_id+' · '+source.revision),node('pre',[...source.text].slice(0,20000).join('')));
     const truncated=[...source.text].length>20000;const checked=document.createElement('input');checked.type='checkbox';checked.disabled=truncated;
     const label=node('label','I inspected this exact document and revision ('+source.path+' · '+source.side+')');label.prepend(checked);detail.append(label);
     if(checked.disabled)detail.append(node('p','This display is truncated. Split the review boundary before signing.'));
     documents.append(detail);records.push({source,checked,truncated});
    }
   }
   select.onchange=show;show();
   return;
  }
  if(kind.value!=='accept'){
   const helper=document.createElement('div');helper.className='sdd-structured-helper';
   helper.append(node('h4',lang==='vi'?'Trường trợ giúp theo loại quyết định (tự động cập nhật JSON)':'Structured decision parameters (auto-syncs JSON)'));
   const syncJson=(patch)=>{
    let cur={};try{cur=JSON.parse(details.value||'{}');}catch{}
    details.value=JSON.stringify({...cur,...patch});
   };
   if(kind.value==='waiver'){
    const expLbl=node('label',lang==='vi'?'Thời hạn rủi ro (ISO-8601 expires_at)':'Waiver expiration (ISO-8601 expires_at)'),expInp=document.createElement('input');
    expInp.placeholder='2026-12-31T23:59:59Z';expInp.oninput=()=>syncJson({expires_at:expInp.value.trim()||undefined});
    expLbl.append(expInp);helper.append(expLbl);
   }else if(kind.value==='false_positive'){
    const fLbl=node('label',lang==='vi'?'Mã phát hiện cần bác bỏ (finding_ids, cách dấu phẩy)':'Finding IDs to dismiss (comma-separated)'),fInp=document.createElement('input');
    fInp.placeholder='FND-001, FND-002';fInp.oninput=()=>syncJson({finding_ids:fInp.value.split(',').map(s=>s.trim()).filter(Boolean)});
    fLbl.append(fInp);helper.append(fLbl);
   }else if(kind.value==='confirm_source'){
    const vLbl=node('label',lang==='vi'?'Phiên bản nguồn ngoài (source_version)':'External source version (source_version)'),vInp=document.createElement('input');
    vInp.placeholder='v1.0';vInp.oninput=()=>syncJson({source_version:vInp.value.trim()||undefined});
    vLbl.append(vInp);helper.append(vLbl);
   }
   panel.append(helper);
  }
 }
 kind.onchange=draw;draw();
 return()=>{
  if(kind.value!=='manual_review')return;
  if(!review||!records.length||records.some(r=>!r.checked.checked||r.truncated))throw Error('Inspect each exact source and consumer before signing.');
  details.value=JSON.stringify({evidence:records.map(({source:d})=>({artifact_id:d.artifact_id,revision:d.revision,start:0,end:[...d.text].length,quote:d.text}))});
 };
}
