"use strict";
function languageReviewPanel(parent) {
 const vi=lang==="vi", section=el("section",null,{"aria-label":vi?"Review bằng Jev":"Jev document review"});
 section.append(el("h2",vi?"Nội dung và văn phong":"Content and language"));

 const adapt=packet.skill_adaptation;
 if(adapt&&Array.isArray(adapt.skills)&&adapt.skills.length){
  const adaptBox=el("details",null);
  adaptBox.append(el("summary",vi?"Thích ứng Động UI Console & Jev theo Agent Skill ("+adapt.skills.length+" skills)":"Dynamic Skill-Pack UI & Jev Adaptation ("+adapt.skills.length+" skills)"));
  for(const sk of adapt.skills){
   adaptBox.append(el("p",sk.skill_id+" ["+sk.tier+"] → view_mode: "+sk.view_mode+" · panels: "+sk.primary_panels.join(", ")+" · Jev ("+sk.jev_question_ids.length+" questions / "+sk.packed_http_requests_per_cluster+" call)"));
  }
  section.append(adaptBox);
 }
 const judge=packet.judge||{}, job=packet.language_review;
 section.append(el("p",judge.model?
  (vi?"Model: ":"Model: ")+judge.model+" · "+(vi?"Hạn mức chung cho bản nháp và các vòng sửa: USD ":"Shared draft and repair reservation ceiling: USD ")+judge.max_cost_usd:
  (vi?"Chưa cấu hình model review. Chủ workspace cần cấu hình Jev để chạy kiểm tra trực tuyến.":"No document reviewer configured. Ask the workspace owner to configure Jev for online review.")));
 section.append(el("p",vi?"Review trực tuyến gửi tài liệu liên quan đến nhà cung cấp đã cấu hình. Kết quả không thay thế quyết định chấp nhận của người dùng.":"Online review sends related documents to the configured provider. Results do not replace human acceptance."));
 const local=el("button",vi?"Kiểm tra local":"Run local checks"), online=el("button",vi?"Review với Jev":"Review with Jev");
 local.disabled=!packet.change_id; online.disabled=!packet.change_id||!judge.model;
 function submit(live) { return run(async()=>{const done=await post("review",{change_id:packet.change_id,live});packet=done.model;render();msg((vi?"Kết quả review: ":"Review result: ")+done.result.status);}); }
 local.onclick=()=>submit(false);online.onclick=()=>submit(true);section.append(local,online);
 if(!job){section.append(el("p",vi?"Chưa có đánh giá văn phong còn hiệu lực cho đúng phiên bản này.":"No current language assessment for this exact revision."));parent.append(section);return;}
 section.append(el("p",(vi?"Trạng thái: ":"Status: ")+job.status+" · "+job.job_id));
 const denominator=job.denominator, numerator=job.model_assessed_numerator;
 section.append(el("p",(vi?"Câu đạt toàn bộ quy tắc đã đánh giá: ":"Sentences passing every assessed rule: ")+numerator+" / "+(denominator===null?"UNKNOWN":denominator)+
  (vi?". UNKNOWN vẫn nằm trong mẫu số. Đây là kết quả tham khảo, chưa chứng nhận ASD-STE100.":". UNKNOWN remains in the denominator. Advisory results; no ASD-STE100 certification.")));
 if(job.error){const guidance={PROVIDER_NOT_CONFIGURED:vi?"Chủ workspace cần cấu hình credential trên máy chạy plugin.":"The workspace owner must configure the server credential.",BUDGET_EXHAUSTED:vi?"Đã hết ngân sách chung. Giữ bản nháp và yêu cầu review thủ công.":"Shared budget exhausted. Keep the draft and request manual review.",CONTEXT_LIMIT:vi?"Vượt giới hạn ngữ cảnh. Cần chia phạm vi rõ ràng và giữ các nghĩa vụ chưa kiểm.":"Context limit exceeded. Explicitly split the scope and retain unresolved obligations."};section.append(el("p",guidance[job.error.code]||job.error.code,{role:"status"}));}
 if(job.budget)section.append(el("p",(vi?"Đã đặt trước: USD ":"Reserved: USD ")+job.budget.reserved_usd+" / "+job.budget.ceiling_usd));
 for(const row of job.artifacts||[]) {
  const details=el("details",null), assessment=row.assessment||{};
  details.append(el("summary",row.artifact_id+" — "+(assessment.assessment_status||assessment.status)));
  details.append(el("p",(vi?"Phiên bản: ":"Revision: ")+row.revision));
  if(row.repair_round)details.append(el("p",(vi?"Vòng sửa: ":"Repair round: ")+row.repair_round+" · "+(vi?"Giữ nghĩa: ":"Meaning preservation: ")+row.semantic_preservation.status));
  for(const finding of (row.local||{}).findings||[])details.append(el("p",finding.text+" — "+finding.rules.join(", ")));
  for(const sentence of (assessment.rule_evidence||{}).sentences||[]) {
   const problems=sentence.rules.filter(rule=>rule.status!=="PASS");
   for(const rule of problems)details.append(el("p",rule.quote+" — "+rule.id+": "+rule.status));
  }
  if((assessment.unknown_rules||[]).length)details.append(el("p",(vi?"Quy tắc chưa đủ bằng chứng: ":"Rules missing evidence: ")+assessment.unknown_rules.join(", ")));
  section.append(details);
 }
 const request=el("details",null);request.append(el("summary",vi?"Yêu cầu agent sửa đúng phạm vi":"Request a targeted author repair"));
 request.append(el("p",vi?"Đưa nội dung dưới đây cho agent đang soạn tài liệu. Bản sửa được tạo riêng, kiểm tra lại và vẫn cần người chấp nhận.":"Give this request to the document author. The repair is proposed separately, rechecked, and still requires human acceptance."));
 const text=el("textarea",(vi?"Sửa các câu bị FAIL theo review ":"Repair the FAIL sentences in review ")+job.job_id+
  ". Candidate: "+packet.change_id+". Preserve all protected facts. Use architect_language_repair with the current origin snapshot and granted author skill; then architect_candidate_review. Missing authority stays UNKNOWN.",{"aria-label":vi?"Yêu cầu sửa bản nháp":"Author repair request",readonly:"readonly"});
 request.append(text);section.append(request);parent.append(section);
}
