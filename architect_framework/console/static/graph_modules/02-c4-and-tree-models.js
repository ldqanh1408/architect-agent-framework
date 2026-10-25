  // ==========================================================================
  // C4 HIERARCHICAL MODEL BUILDER (C1 -> C2 -> Container Doc Tree — Clean V2.1)
  // ==========================================================================

  function buildDataBackedWorkspaceC4Model(graphData) {
    const docs = graphData.nodes || [];
    const wsTitle = safeText(graphData.workspace || "Workspace System");
    const hasExplicitC4 = docs.some(
      (d) => d.kind === "diagram" || /c1-|c2-|context|container/i.test(String(d.path || ""))
    );

    const groupMap = new Map();
    const extDocs = docs.filter((d) => {
      const p = String(d.path || "");
      return p.includes("/04-external/") || /external/i.test(String(d.kind || ""));
    });
    const extIds = new Set(extDocs.map((d) => d.id));
    const domainDocs = docs.filter((d) => {
      const p = String(d.path || "");
      return (d.band === "02-domains" || p.includes("02-domains/")) && !p.includes("02-domains/00-overview") && !extIds.has(d.id);
    });

    if (domainDocs.length > 0) {
      for (const d of domainDocs) {
        const rawParts = String(d.path || "").split("/").filter(Boolean);
        const domIdx = rawParts.indexOf("02-domains");
        const afterDom = domIdx >= 0 ? rawParts.slice(domIdx + 1) : rawParts;
        let ctxKey = d.bounded_context || "";
        if (!ctxKey) {
          if (afterDom.length >= 2 && !afterDom[0].startsWith("_") && !afterDom[0].startsWith("00-")) {
            ctxKey = afterDom[1].endsWith(".md") ? afterDom[0] : afterDom[1];
          } else if (afterDom.length >= 1) {
            ctxKey = afterDom[0].replace(/\.md$/i, "");
          } else {
            ctxKey = d.domain_family || d.group || "domain";
          }
        }
        if (!groupMap.has(ctxKey)) groupMap.set(ctxKey, []);
        groupMap.get(ctxKey).push(d);
      }
    } else {
      for (const d of docs) {
        const folderParts = String(d.folder || d.group || "root").split("/").filter(Boolean);
        const groupKey =
          d.bounded_context ||
          d.domain_family ||
          (folderParts.length >= 2 ? folderParts.slice(-2).join("/") : folderParts[0] || d.owner || "core");
        if (!groupMap.has(groupKey)) {
          groupMap.set(groupKey, []);
        }
        groupMap.get(groupKey).push(d);
      }
    }

    let entries = Array.from(groupMap.entries());
    if (entries.length === 1 && docs.length >= 6) {
      groupMap.clear();
      for (const d of docs) {
        const subKey = `${d.owner || "architect"} (${d.kind || "spec"})`;
        if (!groupMap.has(subKey)) groupMap.set(subKey, []);
        groupMap.get(subKey).push(d);
      }
      entries = Array.from(groupMap.entries());
    }

    // ISS-28 / WO-R5.3: Preserve distinct Bounded Context containers (up to 32) instead of dumping 300+ docs into topEntries[5]
    const topEntries = entries.slice(0, 32);

    const palette = ["var(--b00)", "var(--b01)", "var(--b02)", "var(--b03)", "var(--b04)", "var(--accent)"];
    const docIdToCtrId = new Map();

    const c2Containers = topEntries.map(([gKey, gDocs], idx) => {
      const ctrId = `ctr.ws-${idx + 1}`;
      for (const gd of gDocs) docIdToCtrId.set(gd.id, ctrId);
      const slotCounts = { M: 0, S: 0, C: 0, D: 0 };
      const clauseSet = new Set();
      for (const gd of gDocs) {
        const sc = gd.slot_code || inferV3SlotMeta(gd.path, gd.kind).slotCode;
        slotCounts[sc] = (slotCounts[sc] || 0) + 1;
        for (const cl of gd.clauses || []) clauseSet.add(cl.id);
      }
      const primaryOwner = gDocs[0]?.owner || "architect";
      const cleanName = humanizeSlug(gKey.split("/").pop() || gKey);
      return {
        id: ctrId,
        shortName: safeText(gKey),
        c4_type: "container",
        node_type: "c4-container",
        title: cleanName,
        display_title: cleanName,
        label: safeText(gKey),
        subtitle: `${primaryOwner}`,
        meta: `${gDocs.length} ${t("owned", "sở hữu")} · ${slotCounts.M || 0}[M] ${slotCounts.S || 0}[S]`,
        owner: primaryOwner,
        kind: "container",
        band_color: palette[idx % palette.length],
        v3FolderPath: gDocs[0]?.folder || "root",
        v3_subtree_docs: gDocs,
        path: gDocs[0]?.path || "",
        whitebox_doc: gDocs[0],
        owned_docs: gDocs,
        slotCounts,
        flowTags: ["all"],
        clauses: Array.from(clauseSet),
        upstream: [],
        downstream: [],
      };
    });

    const rawEdges = [];
    for (const ae of graphData.artifact_edges || []) {
      const fCtr = docIdToCtrId.get(ae.from);
      const tCtr = docIdToCtrId.get(ae.to);
      if (fCtr && tCtr && fCtr !== tCtr) {
        rawEdges.push({
          from: fCtr,
          to: tCtr,
          relations: ae.relations || [ae.primary_relation || "references"],
        });
      }
    }
    const c2Edges = consolidateEdges(rawEdges).map((e) => ({
      ...e,
      label: safeText(e.label).slice(0, 18),
      flowTags: ["all"],
    }));

    const pillarMap = new Map();
    for (const d of docs) {
      const bKey = d.band || d.group || "root";
      if (!pillarMap.has(bKey)) pillarMap.set(bKey, []);
      pillarMap.get(bKey).push(d);
    }
    const c2Pillars = Array.from(pillarMap.entries()).map(([bKey, bDocs], idx) => ({
      id: `pil.${bKey}`,
      shortName: safeText(bKey),
      c4_type: "pillar",
      node_type: "c4-pillar",
      title: `${safeText(bKey)}`,
      display_title: `${safeText(bKey)}`,
      label: safeText(bKey),
      subtitle: `${bDocs.length} ${t("registered specs", "tài liệu")}`,
      meta: `${bDocs.length} ${t("specs", "trang")}`,
      owner: bDocs[0]?.owner || "architect",
      kind: "pillar",
      band_color: palette[idx % palette.length],
      folderPath: bDocs[0]?.folder || "",
      v3FolderPath: bDocs[0]?.folder || "",
      v3_subtree_docs: bDocs,
      path: bDocs[0]?.path || "",
      whitebox_doc: bDocs[0],
      owned_docs: bDocs,
      clauses: [],
    }));

    const sysSlug = wsTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "workspace-core";
    const sysId = `sys.${sysSlug}`;
    const c2Externals = extDocs.slice(0, 16).map((ed, idx) => {
      const extId = `ext.ws-${idx + 1}`;
      docIdToCtrId.set(ed.id, extId);
      const extName = ed.display_title || ed.title || humanizeSlug(String(ed.label || ed.id).replace(/\.md$/i, ""));
      return {
        id: extId,
        shortName: safeText(ed.label || ed.id),
        c4_type: "external",
        node_type: "c4-external",
        title: extName,
        display_title: extName,
        label: safeText(ed.label || ed.id),
        subtitle: t("External Contract", "Hợp đồng Hệ thống Ngoài"),
        meta: `1 ${t("contract spec", "đặc tả tích hợp")}`,
        owner: ed.owner || "01-system-architect",
        kind: "external",
        band_color: "var(--b04)",
        path: ed.path || "",
        whitebox_doc: ed,
        owned_docs: [ed],
        clauses: (ed.clauses || []).map((c) => c.id),
        upstream: [sysId],
        downstream: [],
      };
    });
    for (const ae of graphData.artifact_edges || []) {
      const fCtr = docIdToCtrId.get(ae.from);
      const tCtr = docIdToCtrId.get(ae.to);
      if (fCtr && tCtr && fCtr !== tCtr && (fCtr.startsWith("ext.") || tCtr.startsWith("ext."))) {
        c2Edges.push({
          from: fCtr,
          to: tCtr,
          relation: "external",
          relations: ae.relations || [ae.primary_relation || "references"],
          label: "integration",
          flowTags: ["all"],
        });
      }
    }

    const c1Systems = [
      {
        id: sysId,
        shortName: wsTitle,
        c4_type: "system",
        node_type: "c4-container",
        title: wsTitle,
        display_title: `${wsTitle}`,
        label: wsTitle,
        subtitle: t(
          `Workspace System · ${c2Containers.length} C2 Groups`,
          `Hệ thống Workspace · ${c2Containers.length} Nhóm C2`
        ),
        meta: `${docs.length} ${t("registered specs", "tài liệu đã đăng ký")}`,
        owner: docs[0]?.owner || "01-system-architect",
        kind: "system",
        band_color: "var(--accent)",
        path: docs[0]?.path || "",
        whitebox_doc: docs[0],
        owned_docs: docs,
        clauses: (graphData.clause_nodes || []).map((c) => c.id),
        drillsToC2: true,
        upstream: [],
        downstream: c2Externals.map((ex) => ex.id),
      },
    ];

    const c2Map = new Map([...c1Systems, ...c2Containers, ...c2Externals, ...c2Pillars].map((n) => [n.id, n]));
    for (const e of c2Edges) {
      const f = c2Map.get(e.from);
      const tNode = c2Map.get(e.to);
      if (f && tNode) {
        if (!f.downstream.includes(tNode.id)) f.downstream.push(tNode.id);
        if (!tNode.upstream.includes(f.id)) tNode.upstream.push(f.id);
      }
    }

    return {
      isCompact: false,
      isDataBacked: true,
      hasExplicitC4,
      c4ProvenanceNote: hasExplicitC4
        ? ""
        : t(
            "Derived from registered document folders & ownership — no external C4 containers fabricated.",
            "Được tổng hợp trực tiếp từ thư mục & quyền sở hữu tài liệu thực tế — không tự suy diễn container giả."
          ),
      c1Systems,
      c2Containers,
      c2Externals,
      c2Pillars,
      c2Edges,
      c2Map,
    };
  }

  function buildC4Model(graphData) {
    const docs = graphData.nodes || [];
    const docById = new Map(docs.map((d) => [d.id, d]));
    const wsName = String(graphData.workspace || "").toUpperCase();
    const isOmniPayDemo =
      graphState.datasetMode === "v3-maximal" ||
      wsName.includes("OMNIPAY") ||
      (docs.length >= 10 &&
        docs.some((d) => d.id === "REQ-CORE" || d.id === "DOM-LEDGER-INV") &&
        docs.some((d) => String(d.path || "").includes("payment-orchestration")));

    const cacheKey = `${getLang()}:${graphState.datasetMode}`;
    if (graphData._c4Cache && graphData._c4CacheKey === cacheKey) {
      return graphData._c4Cache;
    }
    if (!isOmniPayDemo && docs.length >= 6) {
      const built = buildDataBackedWorkspaceC4Model(graphData);
      graphData._c4Cache = built;
      graphData._c4CacheKey = cacheKey;
      return built;
    }

    const isRichWorkspace = isOmniPayDemo && docs.length >= 10;

    if (!isRichWorkspace) {
      const c2Containers = docs.map((d) => ({
        id: d.id,
        c4_type: "container",
        node_type: "artifact",
        title: d.display_title || d.label || d.id,
        label: d.label || d.id,
        subtitle: `${d.owner} · ${d.kind}`,
        owner: d.owner,
        kind: d.kind,
        band_color: d.band_color || "var(--b00)",
        path: d.path,
        whitebox_doc: d,
        owned_docs: [d],
        clauses: (d.clauses || []).map((c) => c.id),
        upstream: d.upstream || [],
        downstream: d.downstream || [],
      }));
      return {
        isCompact: true,
        c2Containers,
        c2Externals: [],
        c2Pillars: [],
        c2Edges: consolidateEdges(
          (graphData.artifact_edges || []).map((e) => ({
            from: e.from,
            to: e.to,
            relations: e.relations || [e.primary_relation || "references"],
          }))
        ),
      };
    }

    const matchDocs = (predicate) => docs.filter(predicate);
    const pickWhitebox = (list, preferredId) =>
      (preferredId && docById.get(preferredId)) || list[0] || docs[0];

    const containerDefs = [
      {
        id: "ctr.edge-gateway",
        shortName: "edge-api-gateway",
        title: "Edge API Gateway",
        roleVi: "Envoy · Khóa Idempotency & WAF",
        roleEn: "Envoy · Idempotency & WAF",
        tech: "Envoy + Redis Lease",
        owner: "gateway-architect",
        band_color: "var(--b02)",
        preferredDocId: "GATEWAY",
        flowTags: ["checkout", "timeout-webhook"],
        clauses: ["REQ-022", "REQ-025"],
        filter: (d) =>
          ["GATEWAY", "XCUT-IDEMP", "VIEW-UC01", "DOM-BIZ-CAP"].includes(d.id) ||
          d.path.includes("gateway-architect") ||
          d.path.includes("edge-architect") ||
          d.path.includes("bff-architect") ||
          d.path.includes("idempotency"),
      },
      {
        id: "ctr.payment-orchestrator",
        shortName: "payment-orchestrator",
        title: "Payment Orchestrator",
        roleVi: "Go 1.23 · Điều phối Hexagonal",
        roleEn: "Go 1.23 · Hexagonal Port",
        tech: "Go 1.23 · Timeout <= 30s",
        owner: "api-architect",
        band_color: "var(--b00)",
        preferredDocId: "API",
        flowTags: ["checkout", "timeout-webhook", "fraud-ledger"],
        clauses: ["REQ-021", "REQ-022", "ADR-001"],
        filter: (d) =>
          ["API", "ADR-0001", "DOM-CTX-MAP", "STRAT-SOL", "REQ-CORE", "VIEW-C2", "VIEW-L2-MAP"].includes(d.id) ||
          d.path.includes("api-architect") ||
          d.path.includes("backend-service-architect") ||
          d.path.includes("payment-intents"),
      },
      {
        id: "ctr.fraud-risk-ai",
        shortName: "fraud-risk-inference",
        title: "Fraud Risk AI Engine",
        roleVi: "Rust · Chấm điểm AI <= 25ms",
        roleEn: "Rust · Inline AI <= 25ms",
        tech: "Rust + ONNX Runtime",
        owner: "ai-system-architect",
        band_color: "var(--b03)",
        preferredDocId: "DOM-AI-RISK",
        flowTags: ["fraud-ledger"],
        clauses: ["REQ-024"],
        filter: (d) =>
          ["DOM-AI-RISK", "GOV-RISK"].includes(d.id) ||
          d.path.includes("04_ai_architecture") ||
          d.path.includes("fraud-risk"),
      },
      {
        id: "ctr.zero-trust-iam",
        shortName: "zero-trust-perimeter",
        title: "Zero-Trust IAM & Passkey",
        roleVi: "SPIFFE mTLS 1.3 · FIDO2 Passkey",
        roleEn: "SPIFFE mTLS 1.3 · FIDO2 Passkey",
        tech: "SPIFFE + WebAuthn ES256",
        owner: "zero-trust-architect",
        band_color: "var(--b01)",
        preferredDocId: "DOM-SEC-AUTHN",
        flowTags: ["checkout"],
        clauses: ["REQ-025", "SEC-001"],
        filter: (d) =>
          ["DOM-SEC-AUTHN", "XCUT-SEC-THREAT", "NFR-QAS", "DELIV-AUDIT"].includes(d.id) ||
          d.path.includes("07_security_architecture") ||
          d.path.includes("02-security"),
      },
      {
        id: "ctr.webhook-reconciler",
        shortName: "webhook-reconciler",
        title: "Webhook Reconciler",
        roleVi: "Go · Kafka · Đối soát UNKNOWN",
        roleEn: "Go · Kafka · Resolves UNKNOWN",
        tech: "Go + Kafka + HMAC Guard",
        owner: "agent-workflow-design",
        band_color: "var(--b04)",
        preferredDocId: "FLOW",
        flowTags: ["timeout-webhook"],
        clauses: ["REQ-021", "SEC-001", "REQ-026"],
        filter: (d) =>
          ["FLOW", "XCUT-FIT-001", "DELIV-CANARY", "VIEW-CORR"].includes(d.id) ||
          d.path.includes("workflow-orchestration-architect") ||
          d.path.includes("06-runtime") ||
          d.path.includes("04-fitness-functions"),
      },
      {
        id: "ctr.ledger-settlement",
        shortName: "ledger-settlement-core",
        title: "Ledger Settlement Core",
        roleVi: "Sổ cái Bút toán kép · Outbox CDC",
        roleEn: "Double-Entry Ledger · Outbox CDC",
        tech: "Serializable ACID · RPO=0",
        owner: "aggregate-architect",
        band_color: "var(--b04)",
        preferredDocId: "DOM-LEDGER-INV",
        flowTags: ["timeout-webhook", "fraud-ledger"],
        clauses: ["REQ-023", "ADR-002", "REQ-026"],
        filter: (d) =>
          ["DOM-LEDGER-INV", "DOM-DATA-STORE", "ADR-0002", "DOM-INFRA-MESH"].includes(d.id) ||
          d.path.includes("02_domain_architecture") ||
          d.path.includes("05_data_architecture") ||
          d.path.includes("06_infrastructure_architecture"),
      },
    ];

    const v3AllNodes = getMaximalV3CatalogueModel().document_graph.nodes || [];
    const v3FolderByContainer = {
      "ctr.zero-trust-iam": "documents/architecture/02-domains/07_security_architecture/zero-trust-perimeter",
      "ctr.payment-orchestrator": "documents/architecture/02-domains/03_application_architecture/payment-orchestration",
      "ctr.fraud-risk-ai": "documents/architecture/02-domains/04_ai_architecture/fraud-risk-intelligence",
      "ctr.edge-gateway": "documents/architecture/02-domains/03_application_architecture/payment-orchestration/gateway-architect",
      "ctr.webhook-reconciler": "documents/architecture/00-system-views/06-runtime",
      "ctr.ledger-settlement": "documents/architecture/02-domains/02_domain_architecture/payment-kernel",
    };

    const c2Containers = containerDefs.map((def) => {
      const owned = matchDocs(def.filter);
      const v3FolderPath = v3FolderByContainer[def.id] || "documents/architecture/02-domains";
      const v3SubtreeDocs = v3AllNodes.filter((vn) => vn.path.startsWith(v3FolderPath));
      const wb = pickWhitebox(owned, def.preferredDocId);
      const slotCounts = { M: 0, S: 0, C: 0, D: 0 };
      for (const od of owned) {
        const sc = od.slot_code || inferV3SlotMeta(od.path, od.kind).slotCode;
        slotCounts[sc] = (slotCounts[sc] || 0) + 1;
      }
      return {
        id: def.id,
        shortName: def.shortName,
        c4_type: "container",
        node_type: "c4-container",
        title: def.title,
        display_title: def.title,
        label: def.shortName,
        subtitle: t(def.roleEn || def.tech, def.roleVi || def.tech),
        meta: `${owned.length} ${t("owned", "sở hữu")} · ${slotCounts.M || 0}[M] ${slotCounts.S || 0}[S]`,
        owner: def.owner,
        kind: "container",
        band_color: def.band_color,
        v3FolderPath,
        v3_subtree_docs: v3SubtreeDocs,
        path: wb ? wb.path : "",
        whitebox_doc: wb,
        owned_docs: owned.length ? owned : wb ? [wb] : [],
        slotCounts,
        flowTags: def.flowTags,
        clauses: def.clauses,
        upstream: [],
        downstream: [],
      };
    });

    const c2Externals = [
      {
        id: "ext.redis-cluster",
        shortName: "Redis Idempotency Cluster",
        c4_type: "external",
        node_type: "c4-external",
        title: "Redis Idempotency Lease",
        display_title: "Redis Idempotency Lease Cluster",
        label: "Redis Cluster",
        subtitle: t("Distributed SHA-256 Lock (35s)", "Khóa phân tán SHA-256 (Lease 35s)"),
        meta: t("REQ-022 · 24h lock", "REQ-022 · Khóa 24h"),
        owner: "cache-architect",
        kind: "external",
        band_color: "var(--b02)",
        path: (docById.get("XCUT-IDEMP") || docs[0])?.path || "",
        whitebox_doc: docById.get("XCUT-IDEMP") || docs[0],
        owned_docs: [docById.get("XCUT-IDEMP"), docById.get("GATEWAY")].filter(Boolean),
        flowTags: ["checkout"],
        clauses: ["REQ-022"],
      },
      {
        id: "ext.acquirer-rails",
        shortName: "Visa / Mastercard / NAPAS",
        c4_type: "external",
        node_type: "c4-external",
        title: "Visa / MC / NAPAS Rails",
        display_title: "Visa / Mastercard / NAPAS Rails",
        label: "Visa / MC / NAPAS",
        subtitle: t("External Acquirer · Signed Webhook", "Mạng thẻ/ngân hàng · Signed Webhook"),
        meta: t("REQ-021 · <= 30s SLA", "REQ-021 · SLA <= 30s"),
        owner: "integration-adapter-architect",
        kind: "external",
        band_color: "var(--line)",
        path: (docById.get("ADR-0001") || docs[0])?.path || "",
        whitebox_doc: docById.get("ADR-0001") || docs[0],
        owned_docs: [docById.get("ADR-0001"), docById.get("VIEW-C1")].filter(Boolean),
        flowTags: ["timeout-webhook"],
        clauses: ["REQ-021", "ADR-001", "SEC-001"],
      },
      {
        id: "ext.cockroach-ledger",
        shortName: "CockroachDB Serializable",
        c4_type: "external",
        node_type: "c4-external",
        title: "CockroachDB Ledger Store",
        display_title: "CockroachDB Serializable Ledger Store",
        label: "CockroachDB",
        subtitle: t("Multi-Region Raft · Serializable", "CSDL Sổ cái · RPO=0 Multi-Region"),
        meta: t("REQ-023 · RPO=0 WORM", "REQ-023 · RPO=0 WORM"),
        owner: "database-architect",
        kind: "external",
        band_color: "var(--b01)",
        path: (docById.get("DOM-DATA-STORE") || docs[0])?.path || "",
        whitebox_doc: docById.get("DOM-DATA-STORE") || docs[0],
        owned_docs: [docById.get("DOM-DATA-STORE"), docById.get("DOM-LEDGER-INV")].filter(Boolean),
        flowTags: ["fraud-ledger", "timeout-webhook"],
        clauses: ["REQ-023", "REQ-026", "ADR-002"],
      },
    ];

    const pillarDefs = [
      {
        id: "pil.00-system-views",
        folderPath: "documents/architecture/00-system-views",
        title: "00-system-views",
        subfolders: "00-viewpoints · 01-context · 02-functional · 03-structure · 06-runtime",
        band_color: "var(--b00)",
        preferredDocId: "VIEW-C1",
      },
      {
        id: "pil.01-global-strategy",
        folderPath: "documents/architecture/01-global-strategy",
        title: "01-global-strategy",
        subfolders: "01-requirements · 02-strategy · 04-risks · 05-governance",
        band_color: "var(--b01)",
        preferredDocId: "REQ-CORE",
      },
      {
        id: "pil.02-domains",
        folderPath: "documents/architecture/02-domains",
        title: "02-domains",
        subfolders: "00-overview · 01..10 domain architecture families",
        band_color: "var(--b02)",
        preferredDocId: "DOM-CTX-MAP",
      },
      {
        id: "pil.03-cross-cutting",
        folderPath: "documents/architecture/03-cross-cutting",
        title: "03-cross-cutting",
        subfolders: "01-mechanisms · 02-security · 04-fitness-functions",
        band_color: "var(--b03)",
        preferredDocId: "XCUT-SEC-THREAT",
      },
      {
        id: "pil.04-delivery",
        folderPath: "documents/architecture/04-delivery",
        title: "04-delivery",
        subfolders: "00-planning · 01-quality · 02-release · 03-ops · 04-audit",
        band_color: "var(--b04)",
        preferredDocId: "DELIV-CANARY",
      },
    ];

    const c2Pillars = pillarDefs.map((p) => {
      const pDocs = docs.filter((d) => d.path.startsWith(p.folderPath));
      const v3Docs = v3AllNodes.filter((vn) => vn.path.startsWith(p.folderPath));
      const wb = pickWhitebox(pDocs, p.preferredDocId);
      return {
        id: p.id,
        shortName: p.title,
        c4_type: "pillar",
        node_type: "c4-pillar",
        title: p.title,
        display_title: p.title,
        label: p.title,
        subtitle: p.subfolders,
        meta: `${pDocs.length} ${t("workspace specs", "tài liệu")} · ${v3Docs.length} V3 slots`,
        owner: "01-system-architect",
        kind: "pillar",
        band_color: p.band_color,
        folderPath: p.folderPath,
        v3FolderPath: p.folderPath,
        v3_subtree_docs: v3Docs,
        path: wb ? wb.path : "",
        whitebox_doc: wb,
        owned_docs: pDocs,
        clauses: [],
      };
    });

    // Concise C2 Edges (<= 18 chars by default)
    const c2Edges = [
      {
        from: "ctr.edge-gateway",
        to: "ctr.payment-orchestrator",
        relation: "emphasis",
        relations: ["implements_contract"],
        label: t("POST /v1/intents", "Gọi /v1/intents"),
        flowTags: ["checkout", "timeout-webhook"],
      },
      {
        from: "ctr.payment-orchestrator",
        to: "ctr.fraud-risk-ai",
        relation: "satisfies",
        relations: ["satisfies"],
        label: t("AI Risk <=25ms", "Chấm AI <=25ms"),
        flowTags: ["fraud-ledger"],
      },
      {
        from: "ctr.edge-gateway",
        to: "ctr.zero-trust-iam",
        relation: "implements_contract",
        relations: ["implements_contract"],
        label: t("mTLS + Passkey", "mTLS + Passkey"),
        flowTags: ["checkout"],
      },
      {
        from: "ctr.payment-orchestrator",
        to: "ctr.webhook-reconciler",
        relation: "emphasis",
        relations: ["satisfies"],
        label: t("Timeout -> UNKNOWN", "Timeout -> UNKNOWN"),
        flowTags: ["timeout-webhook"],
      },
      {
        from: "ctr.fraud-risk-ai",
        to: "ctr.ledger-settlement",
        relation: "implements_contract",
        relations: ["implements_contract"],
        label: t("Outbox CDC", "Outbox CDC"),
        flowTags: ["fraud-ledger"],
      },
      {
        from: "ctr.webhook-reconciler",
        to: "ctr.ledger-settlement",
        relation: "satisfies",
        relations: ["satisfies"],
        label: t("HMAC -> CAPTURED", "HMAC -> CAPTURED"),
        flowTags: ["timeout-webhook"],
      },
      {
        from: "ctr.zero-trust-iam",
        to: "ext.redis-cluster",
        relation: "external",
        relations: ["references"],
        label: t("SETNX 35s Lease", "Khóa SETNX 35s"),
        flowTags: ["checkout"],
      },
      {
        from: "ctr.webhook-reconciler",
        to: "ext.acquirer-rails",
        relation: "external",
        relations: ["references"],
        label: t("Signed Webhook", "Signed Webhook"),
        flowTags: ["timeout-webhook"],
      },
      {
        from: "ctr.ledger-settlement",
        to: "ext.cockroach-ledger",
        relation: "external",
        relations: ["implements_contract"],
        label: t("Commit RPO=0", "Ghi sổ RPO=0"),
        flowTags: ["fraud-ledger", "timeout-webhook"],
      },
    ];

    const c1Systems = [
      {
        id: "sys.omnipay-core",
        shortName: "OmniPay Global Checkout V3",
        c4_type: "system",
        node_type: "c4-container",
        title: "OmniPay Global Checkout V3",
        display_title: "OmniPay Global Checkout & AI Risk Cloud",
        label: "sys.omnipay-core",
        subtitle: t(
          "Core Payment & Settlement Cloud · 6 C2 Containers",
          "Hệ thống Thanh toán Trung tâm · 6 Container C2"
        ),
        meta: `${docs.length} ${t("system specs", "tài liệu hệ thống")}`,
        owner: "01-system-architect",
        kind: "system",
        band_color: "var(--accent)",
        path: "documents/architecture/00-system-views/01-context/c1-context.md",
        whitebox_doc: docs.find((d) => d.id === "VIEW-C1") || docs[0],
        owned_docs: docs,
        clauses: ["REQ-021", "REQ-022", "REQ-023", "REQ-024", "REQ-025", "REQ-026", "ADR-001", "ADR-002", "SEC-001"],
        drillsToC2: true,
        upstream: ["act.merchant-shopper", "act.human-reviewer"],
        downstream: ["ext.acquirer-rails-c1", "ext.regulatory-hsm-c1"],
      },
      {
        id: "ext.acquirer-rails-c1",
        shortName: "Visa / Mastercard / NAPAS Rails",
        c4_type: "external-system",
        node_type: "c4-external",
        title: "Global Card & Bank Rails",
        display_title: "Visa / Mastercard / NAPAS Acquirer Rails",
        label: "visa-mastercard-napas",
        subtitle: t("External Payment Network · ISO-8583 & Webhooks", "Mạng thẻ & Ngân hàng ngoài · ISO-8583 & Webhook"),
        meta: `7 ${t("linked specs", "tài liệu liên kết")}`,
        owner: "adr-authoring",
        kind: "external",
        band_color: "var(--b02)",
        path: "documents/architecture/01-global-strategy/05-governance/decisions/0001-hexagonal-payment-port.md",
        whitebox_doc: docs.find((d) => d.id === "ADR-0001") || docs[0],
        owned_docs: docs.filter((d) => ["ADR-0001", "VIEW-C1", "FLOW", "API", "XCUT-SEC-THREAT", "GOV-RISK", "XCUT-FIT-001"].includes(d.id)),
        clauses: ["REQ-021", "ADR-001", "SEC-001"],
        upstream: ["sys.omnipay-core"],
        downstream: [],
      },
      {
        id: "ext.regulatory-hsm-c1",
        shortName: "Central Bank Audit & HSM",
        c4_type: "external-system",
        node_type: "c4-external",
        title: "Central Bank Audit & HSM",
        display_title: "Regulatory WORM Ledger Archive & Cloud HSM",
        label: "regulatory-audit-hsm",
        subtitle: t("Compliance Archive & Key Enclave · PCI-DSS v4.0", "Lưu trữ Kiểm toán & HSM · PCI-DSS v4.0"),
        meta: `7 ${t("linked specs", "tài liệu liên kết")}`,
        owner: "database-architect",
        kind: "external",
        band_color: "var(--b04)",
        path: "documents/architecture/02-domains/05_data_architecture/financial-ledger-store/database-architect/01-journal-pipeline/12-storage/cockroach-journal-storage.md",
        whitebox_doc: docs.find((d) => d.id === "DOM-DATA-STORE") || docs[0],
        owned_docs: docs.filter((d) => ["DOM-DATA-STORE", "DOM-LEDGER-INV", "ADR-0002", "NFR-QAS", "XCUT-SEC-THREAT", "DELIV-AUDIT", "VIEW-C1"].includes(d.id)),
        clauses: ["REQ-023", "REQ-025", "REQ-026", "ADR-002"],
        upstream: ["sys.omnipay-core"],
        downstream: [],
      },
      {
        id: "act.merchant-shopper",
        shortName: "Shopper & Merchant Client",
        c4_type: "actor-system",
        node_type: "c4-container",
        title: "Shopper & Merchant Client",
        display_title: "Shopper & Merchant Checkout Client",
        label: "merchant-checkout-client",
        subtitle: t("Web / iOS / Android Checkout Client", "Ứng dụng Client & Người mua · Web / Mobile"),
        meta: `7 ${t("linked specs", "tài liệu liên kết")}`,
        owner: "00-requirement-clarifier",
        kind: "actor",
        band_color: "var(--b00)",
        path: "documents/architecture/00-system-views/02-functional/use-cases/UC-001-instant-checkout.md",
        whitebox_doc: docs.find((d) => d.id === "VIEW-UC01") || docs[0],
        owned_docs: docs.filter((d) => ["VIEW-UC01", "DOM-BIZ-CAP", "GATEWAY", "XCUT-IDEMP", "API", "REQ-CORE", "VIEW-C1"].includes(d.id)),
        clauses: ["REQ-021", "REQ-022"],
        upstream: [],
        downstream: ["sys.omnipay-core"],
      },
      {
        id: "act.human-reviewer",
        shortName: "Human Architect / Reviewer",
        c4_type: "actor-system",
        node_type: "c4-container",
        title: "Human Architect / Reviewer",
        display_title: "Principal Architect & SecOps Reviewer",
        label: "human-reviewer-passkey",
        subtitle: t("Governance Actor · WebAuthn FIDO2 Passkey", "Người duyệt cổng Human Gate · FIDO2 Passkey"),
        meta: `6 ${t("linked specs", "tài liệu liên kết")}`,
        owner: "zero-trust-architect",
        kind: "actor",
        band_color: "var(--b01)",
        path: "documents/architecture/02-domains/07_security_architecture/zero-trust-perimeter/zero-trust-architect/01-passkey-and-mtls/11-authn/webauthn-passkey-authn.md",
        whitebox_doc: docs.find((d) => d.id === "DOM-SEC-AUTHN") || docs[0],
        owned_docs: docs.filter((d) => ["DOM-SEC-AUTHN", "DELIV-AUDIT", "XCUT-SEC-THREAT", "NFR-QAS", "VIEW-CORR", "DELIV-CANARY"].includes(d.id)),
        clauses: ["REQ-025", "SEC-001"],
        upstream: [],
        downstream: ["sys.omnipay-core"],
      },
    ];

    const c2Map = new Map([...c1Systems, ...c2Containers, ...c2Externals, ...c2Pillars].map((n) => [n.id, n]));
    for (const e of c2Edges) {
      const f = c2Map.get(e.from);
      const tNode = c2Map.get(e.to);
      if (f && tNode) {
        if (!f.downstream) f.downstream = [];
        if (!tNode.upstream) tNode.upstream = [];
        if (!f.downstream.includes(tNode.id)) f.downstream.push(tNode.id);
        if (!tNode.upstream.includes(f.id)) tNode.upstream.push(f.id);
      }
    }

    return {
      isCompact: false,
      c1Systems,
      c2Containers,
      c2Externals,
      c2Pillars,
      c2Edges,
      c2Map,
    };
  }

  function buildSystemDocTreeModel(sysNode, graphData, c4) {
    const allDocs = (graphData && graphData.nodes) || [];
    const docById = new Map(allDocs.map((d) => [d.id, d]));
    if (!sysNode) {
      return {
        primaryDocs: [],
        relatedDocs: [],
        allSystemDocs: [],
        arc42Groups: [],
      };
    }

    if (sysNode.c4_type === "system" || String(sysNode.id || "").startsWith("sys.")) {
      const groupMap = new Map();
      for (const sec of ARC42_SECTIONS) {
        groupMap.set(sec.code, {
          section: sec,
          items: [],
        });
      }
      for (const d of allDocs) {
        const arc = inferArc42Section(d.path, d.kind);
        const g = groupMap.get(arc.code) || groupMap.get("§5");
        const isL2Domain = String(d.path || "").includes("02-domains/") && !String(d.path || "").includes("00-overview") && !String(d.path || "").includes("_shared-");
        g.items.push({
          doc: d,
          roleLabel: d.id === "VIEW-C1" ? "C1 Context" : isL2Domain ? "C2 Domain" : "System Spec",
          isOwned: !isL2Domain,
        });
      }
      const arc42Groups = Array.from(groupMap.values()).filter((g) => g.items.length > 0);
      return {
        primaryDocs: allDocs.filter((d) => !(String(d.path || "").includes("02-domains/") && !String(d.path || "").includes("00-overview"))),
        relatedDocs: allDocs.filter((d) => String(d.path || "").includes("02-domains/") && !String(d.path || "").includes("00-overview")),
        allSystemDocs: allDocs,
        arc42Groups,
      };
    }

    const primaryDocs = sysNode.owned_docs || [];
    const primaryIds = new Set(primaryDocs.map((d) => d.id));
    const relatedMap = new Map();
    const addRel = (docObj, reason) => {
      if (!docObj || primaryIds.has(docObj.id)) return;
      if (!relatedMap.has(docObj.id)) {
        relatedMap.set(docObj.id, { doc: docObj, reasons: [] });
      }
      const entry = relatedMap.get(docObj.id);
      if (reason && !entry.reasons.includes(reason)) entry.reasons.push(reason);
    };

    const sysClauses = new Set(sysNode.clauses || []);
    for (const cl of (graphData && graphData.clause_nodes) || []) {
      if (sysClauses.has(cl.id) || primaryIds.has(cl.artifact_id)) {
        const srcDoc = docById.get(cl.artifact_id);
        if (srcDoc) addRel(srcDoc, `${t("Clause", "Điều khoản")} ${cl.id}`);
        for (const dnId of cl.downstream || []) {
          const dnDoc = docById.get(dnId);
          if (dnDoc) addRel(dnDoc, `${t("Clause", "Cùng")} ${cl.id}`);
        }
      }
    }
    for (const pd of primaryDocs) {
      for (const upId of pd.upstream_artifacts || []) {
        const upDoc = docById.get(upId);
        if (upDoc) addRel(upDoc, `Upstream ← ${pd.id}`);
      }
      for (const dnId of pd.downstream_artifacts || []) {
        const dnDoc = docById.get(dnId);
        if (dnDoc) addRel(dnDoc, `Downstream → ${pd.id}`);
      }
    }

    const relatedDocs = Array.from(relatedMap.values()).map((r) => ({
      doc: r.doc,
      reasons: r.reasons,
      primaryReason: r.reasons.slice(0, 2).join(" · ") || t("Related system spec", "Tài liệu liên quan"),
    }));

    const groupMap = new Map();
    for (const sec of ARC42_SECTIONS) {
      groupMap.set(sec.code, { section: sec, items: [] });
    }
    for (const pd of primaryDocs) {
      const arc = inferArc42Section(pd.path, pd.kind);
      const g = groupMap.get(arc.code) || groupMap.get("§3");
      g.items.push({
        doc: pd,
        roleLabel: pd === sysNode.whitebox_doc ? t("Primary C1 Interface", "Tài liệu C1 Trọng tâm") : t("Direct System Spec", "Tài liệu Trực tiếp"),
        isOwned: true,
      });
    }
    for (const rItem of relatedDocs) {
      const arc = inferArc42Section(rItem.doc.path, rItem.doc.kind);
      const g = groupMap.get(arc.code) || groupMap.get("§5");
      g.items.push({
        doc: rItem.doc,
        roleLabel: rItem.primaryReason,
        isOwned: false,
      });
    }
    const arc42Groups = Array.from(groupMap.values()).filter((g) => g.items.length > 0);
    const allSystemDocs = [...primaryDocs, ...relatedDocs.map((r) => r.doc)];

    return {
      primaryDocs,
      relatedDocs,
      allSystemDocs,
      arc42Groups,
    };
  }

  function renderSystemDocTreeDom(sysNode, graphData, c4, onOpenDoc) {
    const sysModel = buildSystemDocTreeModel(sysNode, graphData, c4);
    const wrap = el("div", "", "aaf-container-doctree-box");

    for (const grp of sysModel.arc42Groups) {
      const secDet = el("details", "", "aaf-doctree-group");
      secDet.open = true;
      const secSum = el("summary", "", "aaf-doctree-group-summary");
      secSum.append(
        el("span", t(grp.section.titleEn, grp.section.titleVi)),
        el("span", `${grp.items.length}`, "doc-graph-kpi mono")
      );
      secDet.append(secSum);

      const ul = el("ul", "", "aaf-doctree-files");
      for (const item of grp.items) {
        const d = item.doc;
        const isCur = graphState.activeLeafPath === d.path;
        const sc = d.slot_code || inferV3SlotMeta(d.path, d.kind).slotCode;
        const li = el("li", "", "aaf-doctree-file-item" + (isCur ? " active-leaf" : ""));
        const badge = el("span", `[${sc}]`, "slot-badge", { "data-slot": sc });
        const btn = el(
          "button",
          `${d.display_title || humanizeSlug(d.label || d.id)}`,
          "aaf-hg1-related-link",
          {
            type: "button",
            title: `${d.path} · ${d.kind} · ${d.owner}`,
          }
        );
        btn.onclick = () => {
          graphState.activeLeafPath = d.path;
          graphState.activeLeafNode = d;
          if (onOpenDoc) onOpenDoc(d.path, d);
        };
        li.append(badge, btn);
        ul.append(li);
      }
      secDet.append(ul);
      wrap.append(secDet);
    }

    return wrap;
  }

  function buildContainerDocTreeModel(ctr, graphData, c4) {
    if (!ctr) {
      return {
        ownedDocs: [],
        folderBranches: [],
        ownedTree: { name: "root", path: "", nodes: [], dirs_list: [], deep: 0 },
        relatedDocs: [],
        relatedArc42Groups: [],
      };
    }
    const allDocs = (graphData && graphData.nodes) || [];
    const docById = new Map(allDocs.map((d) => [d.id, d]));
    const ownedDocs =
      graphState.datasetMode === "v3-maximal" && (ctr.v3_subtree_docs || []).length
        ? ctr.v3_subtree_docs.slice(0, 18)
        : ctr.owned_docs || [];
    const ownedIds = new Set(ownedDocs.map((d) => d.id));
    const ownedPaths = new Set(ownedDocs.map((d) => d.path));

    const branchMap = new Map();
    for (const od of ownedDocs) {
      const clean = String(od.path || "")
        .replace(/^documents\/architecture\//, "")
        .replace(/^\/+/, "");
      const segs = clean.split("/").filter(Boolean);
      const dirSegs = segs.length > 1 ? segs.slice(0, -1) : ["root"];
      const branchKey =
        dirSegs.length >= 2
          ? `${dirSegs[0]}/${dirSegs[1]}`
          : dirSegs[0] || "root";
      const fullFolderPath = String(od.path || "").split("/").slice(0, -1).join("/") || "root";
      if (!branchMap.has(branchKey)) {
        const shortLabel = safeText(branchKey.replace(/\//g, " / "));
        branchMap.set(branchKey, {
          id: `BRANCH:${ctr.id}:${branchKey}`,
          branchKey,
          shortTitle: shortLabel,
          fullBranchLabel: safeText(branchKey.replace(/\//g, " / ")),
          folderPath: fullFolderPath,
          docs: [],
          slotCounts: { M: 0, S: 0, C: 0, D: 0 },
        });
      }
      const b = branchMap.get(branchKey);
      b.docs.push(od);
      const sc = od.slot_code || inferV3SlotMeta(od.path, od.kind).slotCode;
      b.slotCounts[sc] = (b.slotCounts[sc] || 0) + 1;
    }

    const folderBranches = Array.from(branchMap.values());
    const ownedTree = buildFolderTreeFromNodes(ownedDocs);

    const relatedMap = new Map();
    const addRelated = (docObj, reason) => {
      if (!docObj || ownedIds.has(docObj.id) || ownedPaths.has(docObj.path)) return;
      if (!relatedMap.has(docObj.id)) {
        relatedMap.set(docObj.id, { doc: docObj, reasons: [] });
      }
      const entry = relatedMap.get(docObj.id);
      if (reason && !entry.reasons.includes(reason)) {
        entry.reasons.push(reason);
      }
    };

    const ctrClauses = new Set(ctr.clauses || []);
    for (const cl of (graphData && graphData.clause_nodes) || []) {
      if (ctrClauses.has(cl.id) || ownedIds.has(cl.artifact_id)) {
        const srcDoc = docById.get(cl.artifact_id);
        if (srcDoc) addRelated(srcDoc, `${t("Clause", "Điều khoản")} ${cl.id}`);
        for (const dnId of cl.downstream || []) {
          const dnDoc = docById.get(dnId);
          if (dnDoc) addRelated(dnDoc, `${t("Clause", "Cùng")} ${cl.id}`);
        }
      }
    }

    for (const od of ownedDocs) {
      for (const upId of od.upstream_artifacts || []) {
        const upDoc = docById.get(upId);
        if (upDoc) addRelated(upDoc, `Upstream ← ${od.id}`);
      }
      for (const dnId of od.downstream_artifacts || []) {
        const dnDoc = docById.get(dnId);
        if (dnDoc) addRelated(dnDoc, `Downstream → ${pd_id_safe(od.id)}`);
      }
    }

    function pd_id_safe(v) {
      return String(v || "");
    }

    if (c4 && Array.isArray(c4.c2Edges)) {
      for (const edge of c4.c2Edges) {
        if (edge.from === ctr.id) {
          const targetCtr = c4.c2Map && c4.c2Map.get(edge.to);
          if (targetCtr && targetCtr.whitebox_doc) {
            addRelated(targetCtr.whitebox_doc, `${t("C2 Call:", "Gọi C2:")} ${safeText(edge.label)}`);
          }
        } else if (edge.to === ctr.id) {
          const sourceCtr = c4.c2Map && c4.c2Map.get(edge.from);
          if (sourceCtr && sourceCtr.whitebox_doc) {
            addRelated(sourceCtr.whitebox_doc, `${t("C2 Caller:", "Nhận từ C2:")} ${safeText(edge.label)}`);
          }
        }
      }
    }

    const relatedDocs = Array.from(relatedMap.values()).map((r) => {
      const arc = inferArc42Section(r.doc.path, r.doc.kind);
      return {
        doc: r.doc,
        arc42: arc,
        reasons: r.reasons,
        primaryReason: r.reasons.slice(0, 2).join(" · ") || t("Related specification", "Tài liệu liên quan"),
      };
    });

    const relGroupMap = new Map();
    for (const sec of ARC42_SECTIONS) {
      relGroupMap.set(sec.code, { section: sec, items: [] });
    }
    for (const rItem of relatedDocs) {
      const g = relGroupMap.get(rItem.arc42.code) || relGroupMap.get("§5");
      g.items.push(rItem);
    }
    const relatedArc42Groups = Array.from(relGroupMap.values()).filter((g) => g.items.length > 0);

    return {
      ownedDocs,
      folderBranches,
      ownedTree,
      relatedDocs,
      relatedArc42Groups,
    };
  }

  function renderContainerDocTreeDom(ctr, graphData, c4, onOpenDoc, options) {
    const opts = options || {};
    const treeModel = buildContainerDocTreeModel(ctr, graphData, c4);
    const wrap = el("div", "", "aaf-container-doctree-box");

    // 1. Owned Specs · arc42 §5 (Clean 2-element items: [Slot] + Clean Title)
    const ownedSection = el("details", "", "aaf-doctree-group");
    ownedSection.open = true;
    const ownedSum = el("summary", "", "aaf-doctree-group-summary");
    ownedSum.append(
      el(
        "span",
        t(
          `Owned Specs · arc42 §5 (${treeModel.ownedDocs.length})`,
          `Tài liệu sở hữu · arc42 §5 (${treeModel.ownedDocs.length})`
        )
      )
    );
    ownedSection.append(ownedSum);

    const branchList = el("div", "", "aaf-doctree-branch-list");
    for (const branch of treeModel.folderBranches) {
      const bDet = el("details", "", "aaf-doctree-branch");
      bDet.open = true;
      const bSum = el("summary", "", "aaf-doctree-branch-summary");
      bSum.append(
        el("span", `${branch.fullBranchLabel}`, "mono"),
        el("span", `${branch.docs.length}`, "doc-graph-kpi mono")
      );
      bDet.append(bSum);

      const ul = el("ul", "", "aaf-doctree-files");
      const visibleBranchDocs = branch.docs.slice(0, 40);
      for (const od of visibleBranchDocs) {
        const isCur = graphState.activeLeafPath === od.path;
        const sc = od.slot_code || inferV3SlotMeta(od.path, od.kind).slotCode;
        const li = el("li", "", "aaf-doctree-file-item" + (isCur ? " active-leaf" : ""));
        const badge = el("span", `[${sc}]`, "slot-badge", { "data-slot": sc });
        const btn = el(
          "button",
          `${od.display_title || humanizeSlug(od.label || od.id)}`,
          "aaf-hg1-related-link",
          {
            type: "button",
            title: `${od.path} · ${od.kind} · ${od.owner}`,
          }
        );
        btn.onclick = () => {
          graphState.activeLeafPath = od.path;
          graphState.activeLeafNode = od;
          if (onOpenDoc) onOpenDoc(od.path, od);
        };
        li.append(badge, btn);
        ul.append(li);
      }
      if (branch.docs.length > 40) {
        const moreLi = el("li", "", "aaf-doctree-file-item");
        const moreBtn = el(
          "button",
          t(`Show all (+${branch.docs.length - 40})`, `Hiện tất cả (+${branch.docs.length - 40})`),
          "aaf-tree-chip-btn",
          { type: "button" }
        );
        moreBtn.onclick = () => {
          moreLi.remove();
          for (const od of branch.docs.slice(40)) {
            const sc = od.slot_code || inferV3SlotMeta(od.path, od.kind).slotCode;
            const li = el("li", "", "aaf-doctree-file-item");
            const badge = el("span", `[${sc}]`, "slot-badge", { "data-slot": sc });
            const btn = el("button", `${od.display_title || humanizeSlug(od.label || od.id)}`, "aaf-hg1-related-link", {
              type: "button",
              title: `${od.path} · ${od.kind} · ${od.owner}`,
            });
            btn.onclick = () => {
              graphState.activeLeafPath = od.path;
              graphState.activeLeafNode = od;
              if (onOpenDoc) onOpenDoc(od.path, od);
            };
            li.append(badge, btn);
            ul.append(li);
          }
        };
        moreLi.append(moreBtn);
        ul.append(moreLi);
      }
      bDet.append(ul);
      branchList.append(bDet);
    }
    ownedSection.append(branchList);
    wrap.append(ownedSection);

    // 2. Referenced Specs · arc42 §1..§11 (Clean 2-element items: [Slot] + Clean Title)
    if (treeModel.relatedDocs.length > 0) {
      const relSection = el("details", "", "aaf-doctree-group aaf-doctree-related");
      relSection.open = !opts.collapseRelated;
      const relSum = el("summary", "", "aaf-doctree-group-summary");
      relSum.append(
        el(
          "span",
          t(
            `Referenced Specs · arc42 §1..§11 (${treeModel.relatedDocs.length})`,
            `Tài liệu tham chiếu · arc42 §1..§11 (${treeModel.relatedDocs.length})`
          )
        )
      );
      relSection.append(relSum);

      const relBranchesWrap = el("div", "", "aaf-doctree-branch-list");
      for (const grp of treeModel.relatedArc42Groups) {
        const gDet = el("details", "", "aaf-doctree-branch");
        gDet.open = true;
        const gSum = el("summary", "", "aaf-doctree-branch-summary");
        gSum.append(
          el("span", t(grp.section.titleEn, grp.section.titleVi)),
          el("span", `${grp.items.length}`, "doc-graph-kpi mono")
        );
        gDet.append(gSum);

        const relUl = el("ul", "", "aaf-doctree-files");
        for (const rItem of grp.items) {
          const rDoc = rItem.doc;
          const isCur = graphState.activeLeafPath === rDoc.path;
          const sc = rDoc.slot_code || inferV3SlotMeta(rDoc.path, rDoc.kind).slotCode;
          const li = el("li", "", "aaf-doctree-file-item" + (isCur ? " active-leaf" : ""));
          const badge = el("span", `[${sc}]`, "slot-badge", { "data-slot": sc });
          const btn = el(
            "button",
            `${rDoc.display_title || humanizeSlug(rDoc.label || rDoc.id)}`,
            "aaf-hg1-related-link",
            {
              type: "button",
              title: `${rDoc.path} · ${rItem.primaryReason} · ${rDoc.owner}`,
            }
          );
          btn.onclick = () => {
            graphState.activeLeafPath = rDoc.path;
            graphState.activeLeafNode = rDoc;
            if (onOpenDoc) onOpenDoc(rDoc.path, rDoc);
          };
          li.append(badge, btn);
          relUl.append(li);
        }
        gDet.append(relUl);
        relBranchesWrap.append(gDet);
      }
      relSection.append(relBranchesWrap);
      wrap.append(relSection);
    }

    return wrap;
  }

  function computeC4Layout(graphData) {
    const c4 = buildC4Model(graphData);
    const NODE_W = 248;
    const NODE_H = 88;
    const positions = new Map();
    const nodeLayerIndex = new Map();
    const clusterBoxes = [];
    const customNodesMap = new Map();
    const outlineItems = [];
    const treeSpinePaths = [];

    if (c4.isCompact) {
      return computeGraphLayout(
        graphData,
        "doc-dag",
        graphState.showClauses,
        graphState.ownerFilter,
        graphState.slotFilter
      );
    }

    if (graphState.c4Level !== "C1" && graphState.c4Level !== "C2" && graphState.c4Level !== "CONTAINER_DOCS") {
      graphState.c4Level = "CONTAINER_DOCS";
    }

    // ------------------------------------------------------------------------
    // LEVEL 1: C1 SYSTEM CONTEXT (Clean 3-line nodes, pure EN/VI cluster labels)
    // ------------------------------------------------------------------------
    if (graphState.c4Level === "C1") {
      const canvasW = 880;
      const C1_H = 88;
      const c1Nodes = (c4.c1Systems || []).map((sysItem) => {
        const sysTree = buildSystemDocTreeModel(sysItem, graphData, c4);
        return {
          ...sysItem,
          meta: `${sysTree.allSystemDocs.length} ${t("linked specs", "tài liệu liên kết")} · ${sysTree.arc42Groups.length} arc42`,
        };
      });

      for (const n of c1Nodes) customNodesMap.set(n.id, n);

      clusterBoxes.push(
        {
          id: "c1-actors",
          label: t("EXTERNAL ACTORS", "TÁC NHÂN NGOÀI"),
          x: 110,
          y: 20,
          width: 660,
          height: 136,
          count: 2,
        },
        {
          id: "c1-system",
          label: t("SYSTEM BOUNDARY", "RANH GIỚI HỆ THỐNG"),
          x: 240,
          y: 196,
          width: 400,
          height: 136,
          count: 1,
        },
        {
          id: "c1-externals",
          label: t("EXTERNAL SYSTEMS", "HỆ THỐNG ĐỐI TÁC"),
          x: 110,
          y: 372,
          width: 660,
          height: 136,
          count: 2,
        }
      );

      if (c4.isDataBacked) {
        c1Nodes.forEach((n, idx) => {
          positions.set(n.id, { x: 316, y: 100 + idx * 124, w: NODE_W, h: C1_H });
          nodeLayerIndex.set(n.id, idx);
        });
        return {
          positions,
          nodeLayerIndex,
          clusterBoxes: [{
            id: "c1-system",
            label: t("SYSTEM BOUNDARY", "RANH GIỚI HỆ THỐNG"),
            x: 200,
            y: 56,
            width: 480,
            height: 164,
            count: c1Nodes.length,
          }],
          width: canvasW,
          height: 260,
          NODE_W,
          NODE_H: C1_H,
          customNodesMap,
          customEdges: [],
          tableEdges: [],
          outlineItems,
          treeSpinePaths,
        };
      }
      positions.set("act.merchant-shopper", { x: 150, y: 52, w: NODE_W, h: C1_H });
      positions.set("act.human-reviewer", { x: 480, y: 52, w: NODE_W, h: C1_H });
      positions.set("sys.omnipay-core", { x: 316, y: 228, w: NODE_W, h: C1_H });
      positions.set("ext.acquirer-rails-c1", { x: 150, y: 404, w: NODE_W, h: C1_H });
      positions.set("ext.regulatory-hsm-c1", { x: 480, y: 404, w: NODE_W, h: C1_H });

      nodeLayerIndex.set("act.merchant-shopper", 0);
      nodeLayerIndex.set("act.human-reviewer", 0);
      nodeLayerIndex.set("sys.omnipay-core", 1);
      nodeLayerIndex.set("ext.acquirer-rails-c1", 2);
      nodeLayerIndex.set("ext.regulatory-hsm-c1", 2);

      const c1Edges = [
        {
          from: "act.merchant-shopper",
          to: "sys.omnipay-core",
          relation: "emphasis",
          relations: ["satisfies"],
          label: t("TLS 1.3 + Idemp.", "TLS 1.3 + Idemp."),
        },
        {
          from: "act.human-reviewer",
          to: "sys.omnipay-core",
          relation: "implements_contract",
          relations: ["implements_contract"],
          label: t("FIDO2 Passkey", "FIDO2 Passkey"),
        },
        {
          from: "sys.omnipay-core",
          to: "ext.acquirer-rails-c1",
          relation: "external",
          relations: ["references"],
          label: t("ISO-8583 / Webhook", "ISO-8583 / Webhook"),
        },
        {
          from: "sys.omnipay-core",
          to: "ext.regulatory-hsm-c1",
          relation: "external",
          relations: ["implements_contract"],
          label: t("WORM Ledger RPO=0", "Sổ cái WORM RPO=0"),
        },
      ];

      return {
        positions,
        nodeLayerIndex,
        clusterBoxes,
        width: canvasW,
        height: 530,
        NODE_W,
        NODE_H: C1_H,
        customNodesMap,
        customEdges: c1Edges,
        tableEdges: c1Edges,
        outlineItems,
        treeSpinePaths,
      };
    }

    // ------------------------------------------------------------------------
    // LEVEL 3: CONTAINER DOCUMENT TREE GRAPH (Clean labels, <= 3 <text> per node)
    // ------------------------------------------------------------------------
    if (graphState.c4Level === "CONTAINER_DOCS") {
      const parentCtr =
        c4.c2Map.get(graphState.c4FocusedContainer) || c4.c2Containers[1] || c4.c2Containers[0];
      const docTree = buildContainerDocTreeModel(parentCtr, graphData, c4);
      const canvasW = 880;
      const docs = graphData.nodes || [];
      const tableEdges = [];

      const topY = 16;
      const topH = 132;
      clusterBoxes.push({
        id: "doctree-c1-c2-header",
        label: t("CONTAINER CONTEXT", "NGỮ CẢNH CONTAINER"),
        x: 14,
        y: topY,
        width: 852,
        height: topH,
        count: 2,
      });

      const primarySysId = (c4.c1Systems && c4.c1Systems[0] && c4.c1Systems[0].id) || "sys.omnipay-core";
      const c1SysNode = {
        id: primarySysId,
        node_type: "c4-container",
        title: `C1: ${safeText(graphData.workspace || "OmniPay Checkout V3")}`,
        display_title: `C1: ${safeText(graphData.workspace || "OmniPay Global Checkout V3")}`,
        label: primarySysId,
        subtitle: t("C1 Software System · 6 C2 Containers", "Hệ thống C1 · 6 Container C2"),
        meta: `${docs.length} ${t("system specs", "tài liệu hệ thống")}`,
        owner: "01-system-architect",
        kind: "system",
        band_color: "var(--b01)",
        path: "documents/architecture/00-system-views/01-context/c1-context.md",
        whitebox_doc: docs.find((d) => d.id === "VIEW-C1") || docs[0],
        owned_docs: docs,
        drillsToC2: true,
      };
      const c2RootNode = {
        ...parentCtr,
        id: parentCtr.id,
        node_type: "c4-container",
        title: `C2: ${parentCtr.title}`,
        subtitle: `${parentCtr.subtitle} (${parentCtr.owner})`,
        meta: `${docTree.ownedDocs.length} ${t("owned", "sở hữu")} · ${docTree.relatedDocs.length} ${t("linked", "liên kết")}`,
      };

      customNodesMap.set(c1SysNode.id, c1SysNode);
      customNodesMap.set(c2RootNode.id, c2RootNode);
      positions.set(c1SysNode.id, { x: 34, y: topY + 32, w: 336, h: 84 });
      positions.set(c2RootNode.id, { x: 462, y: topY + 32, w: 384, h: 84 });
      nodeLayerIndex.set(c1SysNode.id, 0);
      nodeLayerIndex.set(c2RootNode.id, 0);

      const hY = topY + 32 + 42;
      treeSpinePaths.push({
        d: `M 370 ${hY} L 462 ${hY}`,
        color: "var(--accent)",
        arrow: "url(#aaf-arrow-active)",
        label: "C1 -> C2",
        lx: 416,
        ly: hY - 12,
      });
      tableEdges.push({
        from: c1SysNode.id,
        to: c2RootNode.id,
        label: "C1 System -> C2 Container",
        flowTags: ["c1-c2"],
      });

      const treeZoneY = topY + topH + 24;
      const branches = docTree.folderBranches || [];
      const relList = (docTree.relatedDocs || []).slice(0, 9);

      const BRANCH_H = 54;
      const DOC_H = 76;
      const GAP_Y = 12;

      let leftCurY = treeZoneY + 38;
      const leftTrunkX = 30;
      const branchBoxX = 48;
      const branchBoxW = 372;
      const ownedTrunkX = 66;
      const ownedBoxX = 86;
      const ownedBoxW = 334;
      const branchMidYs = [];

      for (const b of branches) {
        const bMidY = leftCurY + Math.round(BRANCH_H / 2);
        branchMidYs.push(bMidY);
        const bNode = {
          id: b.id,
          node_type: "folder",
          path: b.folderPath,
          label: b.shortTitle,
          display_title: `${b.shortTitle}`,
          kind: "container-branch",
          owner: parentCtr.shortName,
          band_color: parentCtr.band_color,
          deep: b.docs.length,
          slotCounts: b.slotCounts,
          subPreview: b.fullBranchLabel,
          whitebox_doc: b.docs[0],
        };
        customNodesMap.set(b.id, bNode);
        positions.set(b.id, { x: branchBoxX, y: leftCurY, w: branchBoxW, h: BRANCH_H });
        nodeLayerIndex.set(b.id, 1);
        tableEdges.push({
          from: c2RootNode.id,
          to: b.id,
          label: t(`Folder branch (${b.docs.length})`, `Nhánh thư mục (${b.docs.length})`),
          flowTags: ["owned-tree"],
        });

        const branchBottomY = leftCurY + BRANCH_H;
        leftCurY += BRANCH_H + 10;

        const docMidYs = [];
        for (const od of b.docs) {
          const dMidY = leftCurY + Math.round(DOC_H / 2);
          docMidYs.push(dMidY);
          const isCurrent = graphState.activeLeafPath === od.path;
          const odCopy = {
            ...od,
            node_type: "artifact",
            is_active_leaf: isCurrent,
            display_title: `${od.display_title || humanizeSlug(od.label || od.id)}`,
          };
          customNodesMap.set(od.id, odCopy);
          positions.set(od.id, { x: ownedBoxX, y: leftCurY, w: ownedBoxW, h: DOC_H });
          nodeLayerIndex.set(od.id, 2);
          tableEdges.push({
            from: b.id,
            to: od.id,
            label: `[${od.slot_code || "M"}] ${t("Owned spec", "Tài liệu sở hữu")}`,
            flowTags: [od.slot_code || "M"],
          });
          leftCurY += DOC_H + GAP_Y;
        }

        if (docMidYs.length > 0) {
          const lastDocY = docMidYs[docMidYs.length - 1];
          treeSpinePaths.push({
            d: `M ${ownedTrunkX} ${branchBottomY} L ${ownedTrunkX} ${lastDocY}`,
            color: "var(--accent)",
          });
          for (const dY of docMidYs) {
            treeSpinePaths.push({
              d: `M ${ownedTrunkX} ${dY} L ${ownedBoxX} ${dY}`,
              color: "var(--accent)",
              arrow: "url(#aaf-arrow-active)",
            });
          }
        }
        leftCurY += 6;
      }

      if (branchMidYs.length > 0) {
        const lastBranchY = branchMidYs[branchMidYs.length - 1];
        treeSpinePaths.push({
          d: `M ${leftTrunkX} ${treeZoneY + 24} L ${leftTrunkX} ${lastBranchY}`,
          color: "var(--accent)",
        });
        for (const bY of branchMidYs) {
          treeSpinePaths.push({
            d: `M ${leftTrunkX} ${bY} L ${branchBoxX} ${bY}`,
            color: "var(--accent)",
            arrow: "url(#aaf-arrow-active)",
          });
        }
      }

      let rightCurY = treeZoneY + 38;
      const rightTrunkX = 462;
      const relBoxX = 484;
      const relBoxW = 368;
      const relMidYs = [];

      for (const rItem of relList) {
        const rDoc = rItem.doc;
        const rMidY = rightCurY + Math.round(DOC_H / 2);
        relMidYs.push(rMidY);
        const isCurrent = graphState.activeLeafPath === rDoc.path;
        const relCopy = {
          ...rDoc,
          node_type: "artifact",
          is_active_leaf: isCurrent,
          is_sibling_peer: !isCurrent,
          display_title: `${rDoc.display_title || humanizeSlug(rDoc.label || rDoc.id)}`,
          summary: `${rItem.primaryReason} · ${summarizeArtifactNode(rDoc)}`,
        };
        customNodesMap.set(rDoc.id, relCopy);
        positions.set(rDoc.id, { x: relBoxX, y: rightCurY, w: relBoxW, h: DOC_H });
        nodeLayerIndex.set(rDoc.id, 2);
        tableEdges.push({
          from: c2RootNode.id,
          to: rDoc.id,
          label: rItem.primaryReason,
          flowTags: ["related-doc"],
        });
        rightCurY += DOC_H + GAP_Y;
      }

      if (relMidYs.length > 0) {
        const lastRelY = relMidYs[relMidYs.length - 1];
        treeSpinePaths.push({
          d: `M ${rightTrunkX} ${treeZoneY + 24} L ${rightTrunkX} ${lastRelY}`,
          color: "var(--b02)",
        });
        for (const rY of relMidYs) {
          treeSpinePaths.push({
            d: `M ${rightTrunkX} ${rY} L ${relBoxX} ${rY}`,
            color: "var(--b02)",
            arrow: "url(#aaf-arrow-ok)",
          });
        }
      }

      const c2BotX = 462 + 192;
      const c2BotY = topY + 32 + 84;
      const splitBarY = treeZoneY - 10;
      treeSpinePaths.push({
        d: `M ${c2BotX} ${c2BotY} L ${c2BotX} ${splitBarY} L ${leftTrunkX} ${splitBarY} L ${leftTrunkX} ${treeZoneY + 24}`,
        color: "var(--accent)",
      });
      treeSpinePaths.push({
        d: `M ${c2BotX} ${splitBarY} L ${rightTrunkX} ${splitBarY} L ${rightTrunkX} ${treeZoneY + 24}`,
        color: "var(--b02)",
      });

      const leftBoxH = Math.max(160, leftCurY - treeZoneY + 12);
      const rightBoxH = Math.max(160, rightCurY - treeZoneY + 12);
      const maxZoneH = Math.max(leftBoxH, rightBoxH);

      clusterBoxes.push(
        {
          id: "doctree-left-owned",
          label: t(
            `OWNED SPECS (${docTree.ownedDocs.length})`,
            `TÀI LIỆU SỞ HỮU (${docTree.ownedDocs.length})`
          ),
          x: 14,
          y: treeZoneY,
          width: 420,
          height: maxZoneH,
          count: docTree.ownedDocs.length,
        },
        {
          id: "doctree-right-related",
          label: t(
            `LINKED SPECS (${relList.length})`,
            `TÀI LIỆU LIÊN KẾT (${relList.length})`
          ),
          x: 446,
          y: treeZoneY,
          width: 420,
          height: maxZoneH,
          count: relList.length,
        }
      );

      return {
        positions,
        nodeLayerIndex,
        clusterBoxes,
        width: canvasW,
        height: treeZoneY + maxZoneH + 20,
        NODE_W: 360,
        NODE_H: DOC_H,
        customNodesMap,
        customEdges: [],
        tableEdges,
        outlineItems,
        treeSpinePaths,
      };
    }

    // ------------------------------------------------------------------------
    // LEVEL 2 (DEFAULT): C2 CONTAINERS (Clean 248x88px nodes, max 3 <text> lines)
    // ------------------------------------------------------------------------
    const canvasW = 880;
    const colGap = 32;
    const contentW3 = 3 * NODE_W + 2 * colGap; // 808px
    const boxW = contentW3 + 44; // 852px
    const boxX = Math.round((canvasW - boxW) / 2); // 14px
    const startX = Math.round(boxX + (boxW - contentW3) / 2); // 36px
    const rowGapC2 = 58;

    const z1Y = 18;
    const z1H = 2 * NODE_H + rowGapC2 + 52;
    clusterBoxes.push({
      id: "zone-internal",
      label: t("SYSTEM BOUNDARY · C2", "RANH GIỚI HỆ THỐNG · C2"),
      x: boxX,
      y: z1Y,
      width: boxW,
      height: z1H,
      count: c4.c2Containers.length,
    });

    c4.c2Containers.forEach((ctr, idx) => {
      const col = idx % 3;
      const row = Math.floor(idx / 3);
      const treeInfo = buildContainerDocTreeModel(ctr, graphData, c4);
      ctr.meta = `${treeInfo.ownedDocs.length} ${t("owned", "sở hữu")} · ${treeInfo.relatedDocs.length} ${t("linked", "liên kết")}`;
      nodeLayerIndex.set(ctr.id, row);
      positions.set(ctr.id, {
        x: startX + col * (NODE_W + colGap),
        y: z1Y + 34 + row * (NODE_H + rowGapC2),
        w: NODE_W,
        h: NODE_H,
      });
      customNodesMap.set(ctr.id, ctr);
    });

    const EXT_H = 88;
    const z2Y = z1Y + z1H + 34;
    const z2H = c4.c2Externals.length ? EXT_H + 50 : 0;
    if (c4.c2Externals.length) {
      clusterBoxes.push({
        id: "zone-external",
        label: t("EXTERNAL SYSTEMS", "HỆ THỐNG NGOÀI"),
        x: boxX,
        y: z2Y,
        width: boxW,
        height: z2H,
        count: c4.c2Externals.length,
      });
    }

    c4.c2Externals.forEach((ext, idx) => {
      nodeLayerIndex.set(ext.id, 2);
      positions.set(ext.id, {
        x: startX + idx * (NODE_W + colGap),
        y: z2Y + 34,
        w: NODE_W,
        h: EXT_H,
      });
      customNodesMap.set(ext.id, ext);
    });

    const filteredEdges = c4.c2Edges
      .filter((e) => {
        if (graphState.c4GuidedFlow === "all") return true;
        return (e.flowTags || []).includes(graphState.c4GuidedFlow);
      })
      .map((e, idx) => ({
        ...e,
        label:
          graphState.c4GuidedFlow === "all"
            ? safeText(e.label).slice(0, 18)
            : `${idx + 1}. ${safeText(e.label)}`.slice(0, 18),
      }));

    return {
      positions,
      nodeLayerIndex,
      clusterBoxes,
      width: canvasW,
      height: z2Y + z2H + 20,
      NODE_W,
      NODE_H,
      customNodesMap,
      customEdges: filteredEdges,
      tableEdges: c4.c2Edges,
      outlineItems,
      treeSpinePaths,
    };
  }
