namespace AAFWorkbench {
  type Data = Record<string, any>;
  function storageGet(key: string): string | null {
    try { return localStorage.getItem(key); } catch { return null; }
  }
  function storageSet(key: string, val: string): void {
    try { localStorage.setItem(key, val); } catch {}
  }
  let model: Data = JSON.parse(document.getElementById("core-model")!.textContent || "{}");
  let language = storageGet("aaf-language") || "en";
  let pausedView = false;
  let cursor = model.runs?.next_cursor || 0;
  let database = model.runs?.database_id || null;
  let pendingEvents = 0;
  let polling = false;
  let interactionRevision = 0;
  let refreshRevision = 0;
  let gateDraft = false;
  let afterOperationFocus: HTMLElement | null = null;
  const main = document.getElementById("main")!;
  const messages = document.getElementById("message")!;
  const labels: Record<string, string[]> = {
    overview: ["Overview", "Tổng quan"], runs: ["Runs", "Lượt chạy"], gates: ["Gate inbox", "Hộp duyệt task"], documents: ["Documents", "Tài liệu"], settings: ["Settings", "Thiết lập"],
    refresh: ["Refresh task state", "Làm mới trạng thái"], review: ["Document review / acceptance", "Review / duyệt tài liệu"],
    pauseView: ["Pause live view", "Dừng cập nhật màn hình"], resumeView: ["Resume live view", "Tiếp tục cập nhật màn hình"],
    reason: ["Reason for this decision", "Lý do quyết định"], who: ["Human reviewer", "Người duyệt"],
    read: ["I reviewed this exact task scope and its questions", "Tôi đã đọc đúng phạm vi và câu hỏi của task này"],
    approve: ["Approve dispatch", "Duyệt thực hiện task"], reject: ["Reject task", "Từ chối task"], request_changes: ["Request changes", "Yêu cầu sửa"],
    noRun: ["No run yet. Ask the host to prepare a bounded task plan.", "Chưa có lượt chạy. Yêu cầu host chuẩn bị kế hoạch task có giới hạn."],
    unknown: ["Unknown", "Chưa biết"], done: ["Decision recorded. Task state refreshed.", "Đã ghi quyết định và cập nhật trạng thái."],
    wait: ["Waiting for passkey signature…", "Đang chờ chữ ký passkey…"], noGate: ["No current task gate awaits a human.", "Không có task gate đang chờ người duyệt."],
  };
  const isPreview = (window as Window & { __aafStandaloneCanvas?: boolean }).__aafStandaloneCanvas === true;
  const text = (key: string) => (labels[key] || [key, key])[language === "vi" ? 1 : 0];
  function node<K extends keyof HTMLElementTagNameMap>(tag: K, value = "", className = ""): HTMLElementTagNameMap[K] {
    const result = document.createElement(tag); result.textContent = value; result.className = className; return result;
  }
  function button(label: string, action: () => void | Promise<void>): HTMLButtonElement {
    const result = node("button", label); result.type = "button";
    result.onclick = () => {
      if (main.hasAttribute("aria-busy")) return;
      result.disabled = true; result.setAttribute("aria-busy", "true");
      void perform(action).finally(() => { result.disabled = false; result.removeAttribute("aria-busy"); });
    }; return result;
  }
  function message(value: string): void { messages.textContent = value; }
  async function request(path: string, body?: Data): Promise<Data> {
    if (isPreview && body) throw Error(language === "vi" ? "Bản xem thử không ghi dữ liệu. Mở console cục bộ để thực hiện thao tác này." : "This preview cannot save changes. Open the local console to perform this action.");
    const controller = new AbortController(); const timer = window.setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(path, { method: body ? "POST" : "GET", signal: controller.signal,
        headers: body ? { "Content-Type": "application/json" } : {}, ...(body ? { body: JSON.stringify(body) } : {}) });
      const result = await response.json(); if (!response.ok) throw Error(result.error || `HTTP ${response.status}`); return result;
    } finally { clearTimeout(timer); }
  }
  async function perform(action: () => void | Promise<void>): Promise<void> {
    if (main.hasAttribute("aria-busy")) return;
    interactionRevision += 1;
    main.inert = true; main.setAttribute("aria-busy", "true");
    try { await action(); } catch (error) { message(error instanceof Error ? error.message : String(error)); }
    finally {
      main.inert = false; main.removeAttribute("aria-busy");
      if (afterOperationFocus?.isConnected) afterOperationFocus.focus();
      afterOperationFocus = null;
    }
  }
  async function refresh(background = false): Promise<boolean> {
    if (background && (main.hasAttribute("aria-busy") || gateDraft || pausedView)) return false;
    const ticket = ++refreshRevision, interaction = interactionRevision, view = route();
    // Gate polling needs current, authority-checked tasks rather than document metadata.
    const next = background && view === "gates"
      ? { ...model, runs: await request("/api/runs?snapshot=1") }
      : (await request("/api/model?surface=workbench")).review;
    if (ticket !== refreshRevision) return false;
    // A response requested before human input cannot rebuild that person's form.
    if (background && (main.hasAttribute("aria-busy") || gateDraft || pausedView || interaction !== interactionRevision || view !== route() || (main.contains(document.activeElement) && document.activeElement !== main))) return false;
    model = next;
    // Snapshots carry their first page; retain progress within the same store.
    cursor = model.runs?.database_id === database
      ? Math.max(cursor, model.runs?.next_cursor || 0) : model.runs?.next_cursor || 0;
    database = model.runs?.database_id || null;
    pendingEvents = 0; render(); message(language === "vi" ? "Đã cập nhật trạng thái hiện tại." : "Current state refreshed.");
    return true;
  }
  function field(parent: HTMLElement, label: string, input: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement): void {
    const wrapper = node("label", label); input.name = label.toLowerCase().replace(/[^a-z0-9]+/g, "-");
    input.autocomplete = "off"; wrapper.append(input); parent.append(wrapper);
  }
  function badge(state: string): HTMLElement { const result = node("span", state, "pill"); result.dataset.state = state; return result; }
  function askConfirm(msg: string): boolean {
    if (isPreview || model.preview_mode) return true;
    const fn = globalThis.confirm;
    return typeof fn === "function" ? fn.call(globalThis, msg) : true;
  }
  function confirmDraft(): boolean {
    return !gateDraft || askConfirm(language === "vi" ? "Bạn chưa gửi quyết định. Bỏ các câu trả lời đang nhập?" : "This decision has not been submitted. Discard your draft answers?");
  }
  let renderedView = "overview";
  function route(): string { return new URLSearchParams(location.hash.slice(1)).get("view") || "overview"; }
  function header(): void {
    const element = document.getElementById("header")!; element.replaceChildren();
    const title = node("div", "", "workbench-brand");
    const mark = node("span", "", "workbench-mark"); mark.setAttribute("aria-hidden", "true");
    // Authored geometry echoes the document graph's linked nodes.
    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg"); icon.setAttribute("viewBox", "0 0 32 32");
    const line = document.createElementNS(icon.namespaceURI, "path"); line.setAttribute("d", "M8 9L24 16L8 23M8 9V23");
    icon.append(line); for (const [x, y] of [[8,9],[24,16],[8,23]]) { const circle = document.createElementNS(icon.namespaceURI, "circle"); circle.setAttribute("cx", String(x)); circle.setAttribute("cy", String(y)); circle.setAttribute("r", "3"); icon.append(circle); }
    mark.append(icon); const identity = node("div"); identity.append(node("h1", "Architect workbench"), node("small", model.workspace || "")); title.append(mark, identity); element.append(title);
    const controls = node("div", "", "tools"); const lang = node("select"); lang.setAttribute("aria-label", "Language / Ngôn ngữ");
    for (const value of ["en", "vi"]) { const option = node("option", value.toUpperCase()); option.value = value; option.selected = value === language; lang.append(option); }
    lang.onchange = () => { if (!confirmDraft()) { lang.value = language; return; } language = lang.value; storageSet("aaf-language", language); header(); render(); document.querySelector<HTMLElement>('[aria-label="Language / Ngôn ngữ"]')?.focus(); }; controls.append(lang);
    const theme = node("select"); theme.setAttribute("aria-label", "Theme / Giao diện");
    const currentTheme = document.documentElement.dataset.theme || "light";
    for (const value of ["light", "dark"]) { const option = node("option", value); option.value = value; option.selected = value === currentTheme; theme.append(option); }
    theme.onchange = () => { document.documentElement.dataset.theme = theme.value; storageSet("aaf-theme", theme.value); }; controls.append(theme);
    const refreshControl = button(text("refresh"), async () => { if (confirmDraft()) await refresh(); }); refreshControl.className = "refresh-control";
    controls.append(refreshControl); element.append(controls);
    const nav = document.getElementById("nav")!; nav.replaceChildren();
    for (const view of ["overview", "runs", "gates", "documents", "settings"]) {
      const entry = node("a", text(view), "nav-link"); entry.href = "#" + new URLSearchParams({ view }).toString(); entry.dataset.view = view;
      if (view === "gates") updateGateBadge(entry);
      nav.append(entry);
    }
    const link = node("a", text("review"), "control"); link.href = "/";
    if (isPreview) { link.href = "#view=gates"; link.textContent = language === "vi" ? "Xem task chờ duyệt" : "View pending gates"; }
    nav.append(link);
  }
  function card(title: string): HTMLElement { const section = node("section", "", "card"); section.append(node("h2", title)); return section; }
  function taskStateAvailable(): boolean { return model.runs?.status !== "ERROR"; }
  function updateGateBadge(entry: HTMLElement): void {
    entry.querySelector(".nav-count")?.remove();
    if (!taskStateAvailable()) { entry.title = text("unknown"); return; }
    const count = (model.runs?.runs || []).flatMap((run: Data) => run.tasks || [])
      .filter((task: Data) => ["waiting-for-human", "notify"].includes(task.state)).length;
    if (count) { const counter = node("span", String(count), "nav-count"); counter.setAttribute("aria-hidden", "true"); entry.append(counter); }
    entry.title = `${count} ${language === "vi" ? "task chờ duyệt" : "tasks awaiting review"}`;
  }

  function overview(): void {
    const tiles = node("div", "", "cards"); const list: Data[] = model.runs?.runs || [];
    const total = list.reduce((sum, run) => sum + run.tasks.length, 0);
    const checked = list.reduce((sum, run) => sum + run.tasks.filter((task: Data) => task.state === "complete").length, 0);
    const waitingCount = list.reduce((sum, run) => sum + (run.tasks || []).filter((task: Data) => ["waiting-for-human", "notify"].includes(task.state)).length, 0);
    const totalDocs = (model.artifacts || []).length;
    const changedDocs = Object.keys(model.diffs || {}).length || (model.document_graph?.stats?.changed || 0);
    for (const [name, value] of [
      ["Checked task candidates", taskStateAvailable() ? `${checked} / ${total}` : text("unknown")],
      [language === "vi" ? "Cổng chờ duyệt" : "Pending human gates", taskStateAvailable() ? `${waitingCount} ${language === "vi" ? "chờ passkey" : "awaiting passkey"}` : text("unknown")],
      [language === "vi" ? "Tài liệu đã đăng ký" : "Registered specs", `${totalDocs} ${language === "vi" ? "tài liệu" : "docs"}${changedDocs ? ` · ${changedDocs} ${language === "vi" ? "thay đổi" : "changed"}` : ""}`],
    ]) {
      const tile = card(name); tile.append(node("p", value, "number")); tiles.append(tile);
    }
    main.append(tiles);
    main.append(node("p", language === "vi" ? "Phạm vi quan sát: Chi phí host và tool trace không được runtime công bố." : "Observation scope: Host cost and tool traces are not exposed by the runtime.", "muted"));
    const status = card("Document readiness"); status.append(badge(model.report?.status || "INCOMPLETE"));
    status.append(node("p", "Task checks, semantic review, and human document acceptance are separate."));
    status.append(node("p", model.report?.next_action || "Read source obligations and current findings.")); main.append(status);
    if (taskStateAvailable() && list.length) {
      const waitingTasks = list.flatMap((r: Data) => (r.tasks || []).filter((t: Data) => ["waiting-for-human", "notify"].includes(t.state)));
      const failedTasks = list.flatMap((r: Data) => (r.tasks || []).filter((t: Data) => ["failed", "rejected"].includes(t.state)));
      if (waitingTasks.length || failedTasks.length) {
        const attn = card(language === "vi" ? "Việc cần xử lý ngay" : "Immediate actions required");
        if (waitingTasks.length) {
          attn.append(node("p", language === "vi"
            ? `${waitingTasks.length} task gate đang chờ chữ ký passkey của người duyệt (${waitingTasks.map((t: Data) => t.id).join(", ")}).`
            : `${waitingTasks.length} task gate(s) awaiting human passkey decision (${waitingTasks.map((t: Data) => t.id).join(", ")}).`));
        }
        if (failedTasks.length) {
          attn.append(node("p", language === "vi"
            ? `${failedTasks.length} task bị lỗi hoặc từ chối cần kiểm tra lại (${failedTasks.map((t: Data) => t.id).join(", ")}).`
            : `${failedTasks.length} failed or rejected task(s) require attention (${failedTasks.map((t: Data) => t.id).join(", ")}).`));
        }
        const actions = node("div", "", "tools");
        if (waitingTasks.length) {
          const gateLink = node("a", language === "vi" ? "Mở hộp duyệt task" : "Open gate inbox", "control primary");
          gateLink.href = "#view=gates"; actions.append(gateLink);
        }
        const runLink = node("a", language === "vi" ? "Xem chi tiết lượt chạy" : "Inspect run tasks", "control");
        runLink.href = "#view=runs"; actions.append(runLink);
        attn.append(actions); main.append(attn);
      }
    }
    if (taskStateAvailable() && !list.length) main.append(node("p", text("noRun")));
  }
  function graph(run: Data): HTMLElement {
    const details = node("details"); details.append(node("summary", "Dependency graph — table remains the complete view"));
    if (run.tasks.length > 50) { details.append(node("p", "Use the table for plans above 50 tasks.")); return details; }
    const levels = new Map<string, number>();
    for (let round = 0; round < run.tasks.length; round++) for (const task of run.tasks) {
      if (task.depends_on.every((id: string) => levels.has(id))) levels.set(task.id, task.depends_on.length ? 1 + Math.max(...task.depends_on.map((id: string) => levels.get(id)!)) : 0);
    }
    const positions = new Map<string, { x: number; y: number }>(); let row = 0;
    for (const level of [...new Set(levels.values())].sort((a, b) => a - b)) {
      const layer = run.tasks.filter((task: Data) => levels.get(task.id) === level);
      layer.forEach((task: Data, index: number) => positions.set(task.id, { x: 20 + index % 5 * 230, y: 20 + (row + Math.floor(index / 5)) * 130 })); row += Math.ceil(layer.length / 5);
    }
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg"); svg.setAttribute("viewBox", `0 0 1180 ${Math.max(160, row * 130)}`); svg.setAttribute("role", "group"); svg.setAttribute("aria-label", "Task dependency graph");
    for (const task of run.tasks) for (const parent of task.depends_on) {
      const first = positions.get(parent), last = positions.get(task.id); if (!first || !last) continue;
      const edge = document.createElementNS(svg.namespaceURI, "path"); edge.setAttribute("d", `M${first.x + 100} ${first.y + 90} L${last.x + 100} ${last.y}`); svg.append(edge);
    }
    for (const task of run.tasks) {
      const position = positions.get(task.id); if (!position) continue;
      const group = document.createElementNS(svg.namespaceURI, "g"); group.setAttribute("role", "button"); group.setAttribute("tabindex", "0"); group.setAttribute("aria-label", `${task.id}: ${task.state}`);
      const rectangle = document.createElementNS(svg.namespaceURI, "rect"); for (const [key, value] of Object.entries({ x: position.x, y: position.y, width: 205, height: 90, rx: 8 })) rectangle.setAttribute(key, String(value)); group.append(rectangle);
      for (const [index, value] of [String(task.id).slice(0, 24), task.state].entries()) { const label = document.createElementNS(svg.namespaceURI, "text"); label.setAttribute("x", String(position.x + 12)); label.setAttribute("y", String(position.y + 30 + index * 28)); label.textContent = value; group.append(label); }
      const focus = () => document.getElementById(`task-${run.run_id}-${task.id}`)?.focus(); group.addEventListener("click", focus); group.addEventListener("keydown", (event) => { if ((event as KeyboardEvent).key === "Enter" || (event as KeyboardEvent).key === " ") { event.preventDefault(); focus(); } }); svg.append(group);
    }
    const wrapper = node("div", "", "scroll graph"); wrapper.append(svg); details.append(wrapper); return details;
  }
  function runs(): void {
    if (!taskStateAvailable()) return;
    const tools = node("div", "", "tools"); tools.append(button(text(pausedView ? "resumeView" : "pauseView"), () => { pausedView = !pausedView; render(); })); main.append(tools);
    main.append(node("p", "A view pause stops screen updates. A scheduling pause stops new dispatch. Running host workers can continue."));
    const list: Data[] = model.runs?.runs || []; if (!list.length) main.append(node("p", text("noRun")));
    for (const run of list) {
      const section = card(run.run_id); section.append(badge(run.state), node("p", `${run.progress.complete} / ${run.progress.total} checked candidates · cost: ${text("unknown")}`));
      const controls = node("div", "", "tools");
      for (const action of [run.paused ? "resume" : "pause", "cancel"]) controls.append(button(action === "pause" ? "Pause scheduling" : action === "resume" ? "Resume scheduling" : "Cancel scheduling", async () => { if (action === "cancel" && !askConfirm(language === "vi" ? "Hủy lập lịch task mới cho lượt chạy này? Worker đang chạy có thể tiếp tục." : "Cancel scheduling new tasks for this run? Running workers may continue.")) return;
        await request("/api/runs/control", { run_id: run.run_id, action }); await refresh(); }));
      section.append(node("p", `Deadline: ${run.deadline_at || text("unknown")}`), controls, graph(run)); const scroll = node("div", "", "scroll"); scroll.tabIndex = 0; scroll.setAttribute("role", "region"); scroll.setAttribute("aria-label", "Scrollable task table");
      const table = node("table"); table.append(node("caption", "Task state and dependencies")); const head = node("thead"); const headerRow = node("tr");
      for (const value of ["Task / skill", "State", "Dependencies", "Writes / required outputs", "Next action"]) headerRow.append(node("th", value)); head.append(headerRow); table.append(head);
      const body = node("tbody");
      for (const task of run.tasks) {
        const row = node("tr"); row.id = `task-${run.run_id}-${task.id}`; row.tabIndex = -1;
        const identity = node("td", `${task.id}\n${task.skill}`); identity.append(node("p", task.objective || "", "muted"));
        const state = node("td"); state.append(badge(task.state), node("p", `Attempt ${task.attempts}`));
        if (task.worker_outcome) state.append(node("p", task.worker_outcome, "muted"));
        const writes = node("td");
        const chipList = node("div", "", "file-chip-list");
        for (const wPath of (task.writes || [])) {
          const shortName = String(wPath).split("/").pop() || String(wPath);
          const chip = node("span", shortName, "file-chip mono");
          chip.title = String(wPath);
          chipList.append(chip);
        }
        writes.append(chipList);
        if (task.required_outputs?.length) writes.append(node("p", "Required: " + task.required_outputs.map((output: Data) => output.path.split("/").pop() || output.path).join(", ")));
        const next = node("td", task.reason || ""); if (["failed", "rejected"].includes(task.state)) next.append(button("Retry with new gate", async () => { await request("/api/runs/control", { run_id: run.run_id, task_id: task.id, action: "retry" }); await refresh(); }));
        row.append(identity, state, node("td", task.depends_on.join(", ") || "—"), writes, next); body.append(row);
      }
      table.append(body); scroll.append(table); section.append(scroll); main.append(section);
    }
    const timeline = card("Recent task events"); const listElement = node("ol", "", "events");
    const allEvents: Data[] = (model.runs?.events || []).slice(-50);
    const recentEvents = allEvents.slice(-10);
    const olderEvents = allEvents.slice(0, Math.max(0, allEvents.length - 10));
    for (const event of recentEvents) listElement.append(node("li", `${event.occurred_at} · ${event.event_type} · ${event.task_id || event.run_id} · ${event.state || event.action || ""}`));
    timeline.append(listElement);
    if (olderEvents.length) {
      const olderDetails = node("details", "", "older-events");
      olderDetails.append(node("summary", language === "vi" ? `Xem sự kiện cũ hơn (${olderEvents.length})` : `Show older events (${olderEvents.length})`));
      const olderList = node("ol", "", "events");
      for (const event of olderEvents) olderList.append(node("li", `${event.occurred_at} · ${event.event_type} · ${event.task_id || event.run_id} · ${event.state || event.action || ""}`));
      olderDetails.append(olderList);
      timeline.append(olderDetails);
    }
    main.append(timeline);
  }
  function unb64(value: string): ArrayBuffer { return Uint8Array.from(atob(value.replace(/-/g, "+").replace(/_/g, "/")), char => char.charCodeAt(0)).buffer; }
  function b64(value: ArrayBuffer): string { return btoa(String.fromCharCode(...new Uint8Array(value))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); }
  async function sign(body: Data): Promise<void> {
    message(text("wait")); const draft = await request("/api/challenge", body);
    const credential = await navigator.credentials.get({ publicKey: { challenge: unb64(draft.challenge), rpId: location.hostname, userVerification: "required", timeout: 120000,
      allowCredentials: draft.credentials.map((id: string) => ({ type: "public-key", id: unb64(id) })) } }) as PublicKeyCredential | null;
    if (!credential) throw Error("No passkey assertion returned"); const response = credential.response as AuthenticatorAssertionResponse;
    await request("/api/decide", { draft: draft.draft, credential_id: b64(credential.rawId), client_data_json: b64(response.clientDataJSON), authenticator_data: b64(response.authenticatorData), signature: b64(response.signature) });
    await refresh(); message(text("done"));
  }
  function gates(): void {
    if (!taskStateAvailable()) return;
    let found = false;
    for (const run of (model.runs?.runs || [])) for (const task of run.tasks) {
      if (!["waiting-for-human", "notify"].includes(task.state)) continue; found = true;
      const section = card(`${task.id} · ${task.skill}`); section.append(node("p", task.objective || ""), badge(task.state), node("p", "Writes: " + task.writes.join(", ")));
      section.append(node("p", "Dispatch approval permits one attempt. Document acceptance remains a separate decision."));
      const bindings = node("details"); bindings.append(node("summary", "Exact gate bindings"), node("pre", JSON.stringify({ run: run.run_id, origin: run.origin_snapshot, plan: run.plan_digest, baseline: run.base_acceptance, next_attempt: task.attempts + 1 }, null, 2))); section.append(bindings);
      const who = node("select"); for (const reviewer of model.reviewers || []) { const option = node("option", reviewer.name); option.value = reviewer.name; who.append(option); }
      const hasReviewer = who.options.length > 0;
      if (!hasReviewer) {
        section.append(node("p", language === "vi" ? "Chưa đăng ký khóa người duyệt. Người dùng bật enrollment từ terminal, rồi đăng ký reviewer trong màn hình duyệt tài liệu." : "No reviewer key is registered. The person enables enrollment in their terminal, then registers the configured reviewer in document review."));
        const setup = node("a", language === "vi" ? "Mở màn hình thiết lập người duyệt" : "Open reviewer setup", "control"); setup.href = "/"; section.append(setup);
        const option = node("option", language === "vi" ? "Chưa có người duyệt" : "No registered reviewer"); who.append(option); who.disabled = true;
      }
      field(section, text("who"), who);
      const answers = new Map<string, HTMLInputElement>();
      for (const question of task.questions || []) {
        const input = node("input");
        if (question.options?.length) input.placeholder = question.options.join(" / ");
        field(section, question.prompt, input);
        if (question.options?.length) {
          const optRow = node("div", "", "tools");
          for (const optVal of question.options) {
            const chip = node("button", String(optVal), "aaf-tree-chip-btn");
            chip.type = "button";
            chip.onclick = () => { input.value = String(optVal); gateDraft = true; input.dispatchEvent(new Event("input", { bubbles: true })); };
            optRow.append(chip);
          }
          section.append(optRow);
        }
        answers.set(question.id, input);
      }
      const reason = node("textarea"); reason.placeholder = language === "vi" ? "Ghi rõ căn cứ cho quyết định…" : "Explain the basis for your decision…"; field(section, text("reason"), reason); const checked = node("input"); checked.type = "checkbox"; const label = node("label", text("read"), "check"); label.prepend(checked); section.append(label);
      const actions = node("div", "", "tools");
      for (const action of ["approve", "reject", "request_changes"]) {
        const control = button(text(action), async () => { reason.removeAttribute("aria-invalid"); checked.removeAttribute("aria-invalid");
          if (!reason.value.trim() || !checked.checked) {
            const invalid = !reason.value.trim() ? reason : checked; invalid.setAttribute("aria-invalid", "true"); afterOperationFocus = invalid;
            throw Error(!reason.value.trim() ? text("reason") : text("read"));
          }
          await sign({ kind: "run-gate", run_id: run.run_id, task_id: task.id, actor: who.value, action, reason: reason.value,
            answers: Object.fromEntries([...answers].map(([id, input]) => [id, input.value])) }); });
        control.className = action === "approve" ? "primary" : action === "reject" ? "destructive" : "";
        control.disabled = isPreview || !hasReviewer || run.state === "stale"; actions.append(control);
      }
      if (run.state === "stale") section.append(node("p", "Source or baseline changed. Preserve this run and prepare a new plan."));
      section.append(actions); main.append(section);
    }
    if (!found) main.append(node("p", text("noGate")));
  }
  function settings(): void {
    const section = card("Human keys and runtime scope");
    section.append(node("p", "The person starts console serve --enroll in their own terminal. Register a configured reviewer key in document review and confirm its fingerprint there."));
    section.append(node("p", "Observation is partial. Host tool traces, usage, and cost are unavailable. MCP has no human approval or document acceptance tool."));
    main.append(section);
    const labels = card("Independent corpus label review");
    labels.append(node("p", "Stage a corpus with sdd eval --corpus corpus.json --stage-labels. Two verified human reviewers must inspect each frozen case. Label signatures do not qualify a model or accept documents."));
    for (const error of model.label_manifest_errors || []) {
      labels.append(node("p", `${error.manifest_id}: ${error.code}. Label state is unavailable. Preserve the manifest before recovery.`));
    }
    const panel = node("div");
    for (const manifest of model.label_manifests || []) {
      const entry = node("div"); entry.append(node("p", `${manifest.case_count} cases · ${manifest.independently_reviewed} reviewed by two humans · ${manifest.manifest_id}`, "mono"));
      let offset = 0; const selected = new Set<string>();
      const load = async (): Promise<void> => {
        const packet = await request(`/api/evaluation-labels?manifest=${encodeURIComponent(manifest.manifest_id)}&offset=${offset}`);
        panel.replaceChildren(); panel.append(node("h3", `Cases ${offset + 1}–${Math.min(offset + 20, packet.total)} of ${packet.total}`));
        for (const item of packet.cases) {
          const details = node("details"); details.append(node("summary", item.id));
          details.append(node("pre", JSON.stringify(item.label, null, 2)), node("p", "Verified reviewers: " + (item.verified_reviewers.join(", ") || "none")));
          const files: Record<string, string> = item.files || {}; const truncated = Object.values(files).some(value => value.length > 20000);
          for (const [path, value] of Object.entries(files)) { details.append(node("h3", path), node("pre", value.slice(0, 20000))); }
          const checked = node("input"); checked.type = "checkbox"; checked.checked = selected.has(item.id); checked.disabled = truncated;
          checked.onchange = () => { if (checked.checked) selected.add(item.id); else selected.delete(item.id); };
          const label = node("label", "I inspected these source documents and this proposed label", "check"); label.prepend(checked); details.append(label);
          if (truncated) details.append(node("p", "Source display is truncated. This case cannot be signed from this view."));
          panel.append(details);
        }
        const who = node("select"); for (const reviewer of model.reviewers || []) { const option = node("option", reviewer.name); option.value = reviewer.name; who.append(option); } field(panel, text("who"), who);
        const reason = node("textarea"); field(panel, "Label review reason", reason);
        const actions = node("div", "", "tools");
        if (offset > 0) actions.append(button("Previous cases", async () => { offset = Math.max(0, offset - 20); await load(); }));
        if (offset + 20 < packet.total) actions.append(button("Next cases", async () => { offset += 20; await load(); }));
        const signLabels = button("Sign selected labels", async () => {
          if (!selected.size || selected.size > 20 || !reason.value.trim()) throw Error("Select 1..20 inspected cases and explain the review.");
          await sign({ kind: "eval-labels", manifest_id: manifest.manifest_id, actor: who.value, reason: reason.value, case_ids: [...selected] }); selected.clear();
        }); signLabels.disabled = !who.options.length; actions.append(signLabels); panel.append(actions);
      };
      entry.append(button("Inspect frozen label cases", load)); labels.append(entry);
    }
    labels.append(panel); main.append(labels);
  }
  function documents(): void {
    const section = card(language === "vi" ? "Tài liệu đã đăng ký" : "Registered documents");
    section.append(node("p", "Read exact document revisions. Reading starts no task and grants no approval."));
    section.append(node("p", model.change_id ? `Reading candidate ${model.change_id}. Acceptance remains a separate decision.` : "Reading live registered documents."));
    const search = node("input"); search.type = "search"; search.placeholder = language === "vi" ? "Tìm tài liệu…" : "Find a document…"; field(section,"Filter by path, kind, or owner",search);
    const list = node("ul"); const reader = node("section", "", "card"); reader.setAttribute("aria-label","Document reader");
    const fold = (value: string) => value.toLocaleLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g,"d").replace(/[-_\/]+/g," ");
    for (const a of (model.artifacts || [])) {
      if (!a._foldKey) a._foldKey = fold(`${a.id} ${a.path} ${a.kind} ${a.owner}`);
    }
    const draw = (): void => {
      list.replaceChildren();
      const q = fold(search.value);
      const matched = (model.artifacts || []).filter((a: Data) => !q || a._foldKey.includes(q));
      const items = matched.length > 120 ? matched.slice(0, 120) : matched;
      if (!items.length) list.append(node("li","No matching document. Clear the filter to see registered artifacts."));
      const entries = new Map<string, HTMLElement>();
      for (const artifact of items) {
        const entry = node("li"); entry.append(button(artifact.path, async()=>{
          const query = new URLSearchParams({id:artifact.id,revision:artifact.revision}); if(model.change_id)query.set("change",model.change_id);
          const content = await request("/api/artifact?"+query.toString()); reader.replaceChildren();
          reader.append(node("h3",artifact.path),node("p",`${artifact.id} · ${artifact.kind} · ${artifact.owner}`),node("p",content.revision,"mono"),node("pre",content.text));
          if(content.has_more)reader.append(node("p","This display is truncated. Use the complete source before review."));
          if(model.diffs?.[artifact.path]){const diff=node("details");diff.append(node("summary","Changes from accepted baseline"),node("pre",model.diffs[artifact.path]));reader.append(diff);}
          reader.tabIndex=-1;afterOperationFocus=reader;
        }),node("span",`${artifact.kind} · ${artifact.owner}`,"muted")); entries.set(artifact.path,entry);
      }
      const appendTree = (branch: Data, parent: HTMLElement): void => {
        for (const path of branch.files || []) { const entry=entries.get(path); if(entry)parent.append(entry); }
        for (const child of branch.dirs_list || []) {
          const group=node("li"), details=node("details"), nested=node("ul"); details.open=Boolean(search.value); details.append(node("summary",child.name));
          appendTree(child,nested); if(nested.childElementCount){details.append(nested);group.append(details);parent.append(group);}
        }
      };
      if(model.document_tree) appendTree(model.document_tree,list); else for(const entry of entries.values()) list.append(entry);
        };search.oninput=draw;draw();section.append(list);main.append(section,reader);
  }
  function render(): void {
    interactionRevision += 1; gateDraft = false; renderedView = route();
    document.documentElement.lang = language; main.replaceChildren();
    if (model.runs?.status === "ERROR") { const warning = card("Task observation unavailable"); warning.append(node("p",`${model.runs.error?.code}: ${model.runs.error?.message}`),node("p","Task states and pending gates are unknown. Preserve the store before recovery.")); main.append(warning); }
    document.querySelectorAll<HTMLAnchorElement>("nav a[data-view]").forEach(entry => { if (entry.dataset.view === route()) entry.setAttribute("aria-current", "page"); else entry.removeAttribute("aria-current"); });
    const gateEntry = document.querySelector<HTMLAnchorElement>('nav a[data-view="gates"]');
    if (gateEntry) updateGateBadge(gateEntry);
    main.dataset.view = route();
    const heading = node("div", "", "page-heading"); const headingText = node("div"); headingText.append(node("h2", text(route())));
    const descriptions: Record<string, string[]> = {
      overview: ["Track execution, document readiness, and decisions that need you.", "Theo dõi tiến độ, tài liệu và các quyết định cần bạn duyệt."],
      documents: ["Explore the architecture. Follow its sources. Read the exact revision.", "Khám phá kiến trúc, truy vết nguồn và đọc đúng phiên bản tài liệu."],
      runs: ["Follow each task from approved scope to checked candidate.", "Theo dõi từng task từ phạm vi đã duyệt đến kết quả kiểm tra."],
      gates: ["Review the scope and questions before authorizing one task attempt.", "Đọc phạm vi và câu hỏi trước khi duyệt một lần thực hiện task."],
      settings: ["Manage reviewer keys and independent corpus review.", "Quản lý khóa người duyệt và đánh giá độc lập corpus."]
    }; headingText.append(node("p", (descriptions[route()] || descriptions.overview)[language === "vi" ? 1 : 0], "muted")); heading.append(headingText);
    if (isPreview) { const preview = node("span", language === "vi" ? "Bản xem thử · chỉ đọc" : "Preview · read only", "preview-label"); preview.title = language === "vi" ? "Quyết định và chữ ký passkey chỉ thực hiện trong console cục bộ." : "Decisions and passkey signing require the local console."; heading.append(preview); } main.append(heading);
    if (route() === "runs") runs(); else if (route() === "gates") gates(); else if (route() === "documents") documents(); else if (route() === "settings") settings(); else overview();
  }
  async function poll(): Promise<void> {
    if (isPreview || polling || main.hasAttribute("aria-busy") || pausedView || document.hidden || model.runs?.status === "ERROR") return;
    polling = true;
    const observedRefresh = refreshRevision;
    try { const events = await request(`/api/runs?after=${cursor}${database ? "&database_id=" + encodeURIComponent(database) : ""}`);
      if (main.hasAttribute("aria-busy") || pausedView || observedRefresh !== refreshRevision) return;
      if (events.cursor_reset) { message("Event store changed. Refresh task state."); database = events.database_id; cursor = events.next_cursor; return; }
      database = events.database_id; cursor = events.next_cursor; pendingEvents += events.events.length;
      if (pendingEvents && !gateDraft && (!main.contains(document.activeElement) || document.activeElement === main) && ["overview","runs","gates"].includes(route())) { if (await refresh(true)) return; }
      if (pendingEvents) message(language === "vi" ? `${pendingEvents} sự kiện mới. Làm mới khi sẵn sàng.` : `${pendingEvents} new task events. Refresh when ready.`);
    } catch { message(language === "vi" ? "Mất kết nối. Đang thử lại." : "Connection lost. Retrying."); } finally { polling = false; }
  }
  document.documentElement.dataset.theme = storageGet("aaf-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  for (const event of ["focusin", "input", "change", "pointerdown", "keydown"]) main.addEventListener(event, () => {
    interactionRevision += 1;
    if (route() === "gates" && ["input", "change"].includes(event)) gateDraft = true;
  });
  header(); render();
  window.addEventListener("hashchange", () => {
    if (!confirmDraft()) { history.replaceState(null, "", "#view=" + renderedView); return; }
    render(); main.focus({ preventScroll: true }); window.scrollTo(0, 0);
  });
  window.addEventListener("beforeunload", event => { if (gateDraft) { event.preventDefault(); event.returnValue = ""; } });
  // Reserve time in the one-second observation budget for creation and rendering.
  window.setInterval(() => { void poll(); }, 200);
}
