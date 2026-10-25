  function appendInlineMarkdown(parent, rawText) {
    const cleaned = safeText(rawText);
    const tokenRegex = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
    let lastIndex = 0;
    let match;
    while ((match = tokenRegex.exec(cleaned)) !== null) {
      if (match.index > lastIndex) {
        parent.append(document.createTextNode(cleaned.slice(lastIndex, match.index)));
      }
      const token = match[0];
      if (token.startsWith("**") && token.endsWith("**")) {
        parent.append(el("strong", token.slice(2, -2)));
      } else if (token.startsWith("`") && token.endsWith("`")) {
        parent.append(el("code", token.slice(1, -1)));
      } else if (token.startsWith("[")) {
        const m = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
        if (m) {
          const span = el("span", `${m[1]} (${m[2]})`, "mono");
          span.style.color = "var(--accent)";
          parent.append(span);
        } else {
          parent.append(document.createTextNode(token));
        }
      }
      lastIndex = tokenRegex.lastIndex;
    }
    if (lastIndex < cleaned.length) {
      parent.append(document.createTextNode(cleaned.slice(lastIndex)));
    }
  }

  function renderMarkdownToDom(markdownText) {
    const container = el("div", "", "aaf-reader-rendered");
    container.setAttribute("aria-label", t("Formatted document preview", "Bản xem tài liệu đã định dạng"));
    const raw = String(markdownText || "").replace(/\r\n/g, "\n");
    let body = raw;
    // Strip YAML frontmatter so metadata is never repeated inside the rendered specification body 
    const fmMatch = raw.match(/^---\n([\s\S]*?)\n---\n/);
    if (fmMatch) {
      body = raw.slice(fmMatch[0].length);
    }

    const lines = body.split("\n");
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      if (!line.trim()) {
        i += 1;
        continue;
      }
      if (line.trim().startsWith("```")) {
        const codeLines = [];
        i += 1;
        while (i < lines.length && !lines[i].trim().startsWith("```")) {
          codeLines.push(lines[i]);
          i += 1;
        }
        i += 1;
        container.append(el("pre", codeLines.join("\n")));
        continue;
      }
      if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
        const tableLines = [];
        while (i < lines.length && lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) {
          tableLines.push(lines[i].trim());
          i += 1;
        }
        if (tableLines.length >= 2) {
          const table = el("table");
          const parseRow = (r) =>
            r
              .slice(1, -1)
              .split("|")
              .map((c) => c.trim());
          const headers = parseRow(tableLines[0]);
          const thead = el("thead");
          const trHead = el("tr");
          for (const h of headers) {
            const th = el("th");
            appendInlineMarkdown(th, h);
            trHead.append(th);
          }
          thead.append(trHead);
          table.append(thead);

          const tbody = el("tbody");
          for (let rIdx = 1; rIdx < tableLines.length; rIdx++) {
            const rowStr = tableLines[rIdx];
            if (/^\|[\s:|-]+\|$/.test(rowStr)) continue;
            const cells = parseRow(rowStr);
            const tr = el("tr");
            for (const c of cells) {
              const td = el("td");
              appendInlineMarkdown(td, c);
              tr.append(td);
            }
            tbody.append(tr);
          }
          table.append(tbody);
          const wrap = el("div", "", "scroll", { tabindex: "0", role: "region", "aria-label": t("Scrollable document table", "Bảng tài liệu có thể cuộn") });
          wrap.append(table);
          container.append(wrap);
          continue;
        }
      }
      if (line.trim().startsWith(">")) {
        const bqLines = [];
        while (i < lines.length && lines[i].trim().startsWith(">")) {
          bqLines.push(lines[i].trim().replace(/^>\s?/, ""));
          i += 1;
        }
        const bq = el("blockquote");
        appendInlineMarkdown(bq, bqLines.join(" "));
        container.append(bq);
        continue;
      }
      const hMatch = line.match(/^(#{1,6})\s+(.*)$/);
      if (hMatch) {
        const level = hMatch[1].length;
        const p = el("p", "", "md-heading");
        p.style.fontWeight = "700";
        p.style.fontSize = level === 1 ? "16px" : level === 2 ? "14.5px" : "13.5px";
        p.style.marginTop = "10px";
        p.style.marginBottom = "4px";
        appendInlineMarkdown(p, hMatch[2]);
        container.append(p);
        i += 1;
        continue;
      }
      if (/^\s*[-*+]\s+/.test(line)) {
        const ul = el("ul");
        while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
          const li = el("li");
          appendInlineMarkdown(li, lines[i].replace(/^\s*[-*+]\s+/, ""));
          ul.append(li);
          i += 1;
        }
        container.append(ul);
        continue;
      }
      const para = [];
      while (
        i < lines.length &&
        lines[i].trim() &&
        !lines[i].trim().startsWith("```") &&
        !(lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) &&
        !lines[i].trim().startsWith(">") &&
        !/^(#{1,6})\s+/.test(lines[i]) &&
        !/^\s*[-*+]\s+/.test(lines[i])
      ) {
        para.push(lines[i].trim());
        i += 1;
      }
      if (para.length) {
        const p = el("p");
        appendInlineMarkdown(p, para.join(" "));
        container.append(p);
      }
    }
    return container;
  }

  function findSubtreeAtPath(rootTree, targetPath) {
    if (!targetPath) return rootTree;
    const queue = [rootTree];
    while (queue.length > 0) {
      const cur = queue.shift();
      if (cur.path === targetPath) return cur;
      for (const child of cur.dirs_list || []) {
        if (targetPath === child.path) return child;
        queue.push(child);
      }
    }
    return rootTree;
  }

  function computeDrilldownLayout(graphData, filterOwner, filterSlot) {
    const filteredArtifacts = graphData.nodes.filter((n) => {
      if (filterOwner !== "all" && n.owner !== filterOwner) return false;
      const sc = n.slot_code || inferV3SlotMeta(n.path, n.kind).slotCode;
      if (filterSlot !== "all" && sc !== filterSlot) return false;
      return true;
    });
    const folderTree = buildFolderTreeFromNodes(filteredArtifacts);
    const activeBranch = findSubtreeAtPath(folderTree, graphState.drillPath);
    if (activeBranch === folderTree && graphState.drillPath) {
      graphState.drillPath = "";
    }

    const items = [];
    for (const childDir of activeBranch.dirs_list || []) {
      const meta = inferV3SlotMeta(childDir.path, "folder");
      const subNames = [
        ...(childDir.dirs_list || []).map((d) => humanizeSlug(d.name.split("/").pop())),
        ...(childDir.nodes || []).map((f) => f.display_title || humanizeSlug(f.label)),
      ].slice(0, 3);
      items.push({
        id: `DIR:${childDir.path}`,
        node_type: "folder",
        path: childDir.path,
        label: safeText(childDir.name),
        display_title: safeText(childDir.name),
        kind: "folder",
        owner: `${childDir.deep} ${t("specs", "tài liệu")}`,
        band: meta.band,
        band_color: meta.bandColor,
        band_label: meta.bandLabel,
        deep: childDir.deep,
        slotCounts: childDir.slotCounts || { M: 0, C: 0, D: 0, S: 0 },
        subPreview: subNames.join(" · ") || childDir.path,
      });
    }
    for (const docNode of activeBranch.nodes || []) {
      const isCurLeaf = graphState.activeLeafPath === docNode.path;
      items.push({
        ...docNode,
        node_type: "artifact",
        is_active_leaf: isCurLeaf,
      });
    }
    if ((activeBranch.dirs_list || []).length === 0 && (activeBranch.nodes || []).length > 0) {
      const primaryLeaf = activeBranch.nodes[0];
      const sibInfo = getSiblingDocuments(primaryLeaf, graphData);
      const existingPaths = new Set(items.map((it) => it.path));
      for (const sib of sibInfo.siblings || []) {
        if (!existingPaths.has(sib.path)) {
          existingPaths.add(sib.path);
          items.push({
            ...sib,
            node_type: "artifact",
            is_sibling_peer: true,
          });
        }
      }
    }

    const totalItems = items.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / graphState.pageSize));
    if (graphState.page >= totalPages) graphState.page = 0;
    const pagedItems = items.slice(
      graphState.page * graphState.pageSize,
      (graphState.page + 1) * graphState.pageSize
    );

    const NODE_W = 368;
    const NODE_H = 88;
    const positions = new Map();
    const nodeLayerIndex = new Map();
    const clusterBoxes = [];
    const itemMap = new Map(pagedItems.map((it) => [it.id, it]));

    const groups = new Map();
    for (const it of pagedItems) {
      const gKey =
        it.node_type === "folder"
          ? t("ARCHITECTURE BRANCHES", "NHÁNH KIẾN TRÚC")
          : it.is_sibling_peer
          ? t("SIBLING SPECIFICATIONS", "TÀI LIỆU CÙNG CẤP")
          : t("LEAF SPECIFICATIONS", "TÀI LIỆU CHI TIẾT");
      if (!groups.has(gKey)) groups.set(gKey, []);
      groups.get(gKey).push(it);
    }

    let curY = 20;
    const canvasW = 820;
    let gIdx = 0;
    for (const [gLabel, members] of groups.entries()) {
      const cols = Math.min(2, Math.max(1, members.length));
      const rows = Math.ceil(members.length / cols);
      const contentW = cols * NODE_W + (cols - 1) * 28;
      const boxW = Math.max(420, contentW + 40);
      const boxH = rows * NODE_H + (rows - 1) * 24 + 50;
      const boxX = Math.round((canvasW - boxW) / 2);

      clusterBoxes.push({
        id: `drill-group-${gIdx}`,
        label: gLabel,
        x: boxX,
        y: curY,
        width: boxW,
        height: boxH,
        count: members.length,
      });

      const startX = Math.round(boxX + (boxW - contentW) / 2);
      members.forEach((m, idx) => {
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        nodeLayerIndex.set(m.id, gIdx * 2 + row);
        positions.set(m.id, {
          x: startX + col * (NODE_W + 28),
          y: curY + 32 + row * (NODE_H + 24),
        });
      });
      curY += boxH + 28;
      gIdx += 1;
    }

    const rolledEdges = [];
    const nodeIdToPath = new Map(graphData.nodes.map((n) => [n.id, n.path]));
    for (const edge of graphData.artifact_edges || []) {
      const fromPath = nodeIdToPath.get(edge.from) || "";
      const toPath = nodeIdToPath.get(edge.to) || "";
      const matchItem = (p) => {
        for (const it of pagedItems) {
          if (it.node_type === "artifact" && it.path === p) return it.id;
          if (it.node_type === "folder" && (p === it.path || p.startsWith(it.path + "/"))) return it.id;
        }
        return null;
      };
      const fId = matchItem(fromPath);
      const tId = matchItem(toPath);
      if (fId && tId && fId !== tId) {
        rolledEdges.push({
          from: fId,
          to: tId,
          relations: edge.relations || [edge.primary_relation || "references"],
        });
      }
    }

    return {
      positions,
      nodeLayerIndex,
      clusterBoxes,
      width: canvasW,
      height: Math.max(260, curY),
      NODE_W,
      NODE_H,
      customNodesMap: itemMap,
      customEdges: consolidateEdges(
        rolledEdges.filter((e) => !String(e.from).startsWith("DIR:") && !String(e.to).startsWith("DIR:"))
      ),
      tableEdges: consolidateEdges(rolledEdges),
      totalItems,
      totalPages,
      activeBranch,
    };
  }

  function computeGraphLayout(graphData, mode, includeClauses, filterOwner, filterSlot) {
    if (mode === "c4-map") {
      return computeC4Layout(graphData);
    }
    if (mode === "drilldown") {
      return computeDrilldownLayout(graphData, filterOwner, filterSlot);
    }

    const allFilteredArtifacts = graphData.nodes.filter((n) => {
      if (filterOwner !== "all" && n.owner !== filterOwner) return false;
      const sc = n.slot_code || inferV3SlotMeta(n.path, n.kind).slotCode;
      if (filterSlot !== "all" && sc !== filterSlot) return false;
      if (graphState.drillPath && !n.path.startsWith(graphState.drillPath)) return false;
      return true;
    });

    const totalItems = allFilteredArtifacts.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / graphState.pageSize));
    if (graphState.page >= totalPages) graphState.page = 0;

    const artifactNodes =
      totalItems > graphState.pageSize
        ? allFilteredArtifacts.slice(
            graphState.page * graphState.pageSize,
            (graphState.page + 1) * graphState.pageSize
          )
        : allFilteredArtifacts;

    const allowedArtifactIds = new Set(artifactNodes.map((n) => n.id));
    const clauseNodes = includeClauses
      ? (graphData.clause_nodes || []).filter((c) => allowedArtifactIds.has(c.artifact_id))
      : [];
    const allNodes = [...artifactNodes, ...clauseNodes];
    const positions = new Map();
    const nodeLayerIndex = new Map();
    const clusterBoxes = [];
    const NODE_W = 236;
    const NODE_H = 88;

    if (!allNodes.length) {
      return { positions, nodeLayerIndex, clusterBoxes, width: 680, height: 220, NODE_W, NODE_H, totalItems, totalPages };
    }

    if (mode === "radial") {
      const width = 800;
      const height = 500;
      const cx = Math.round(width / 2 - NODE_W / 2);
      const cy = Math.round(height / 2 - NODE_H / 2);
      const centerId =
        graphState.selectedNodeId && allNodes.some((n) => n.id === graphState.selectedNodeId)
          ? graphState.selectedNodeId
          : allNodes[0].id;
      const centerNode = allNodes.find((n) => n.id === centerId) || allNodes[0];
      const others = allNodes.filter((n) => n.id !== centerNode.id).slice(0, 10);
      positions.set(centerNode.id, graphState.customPositions.get(`radial:${centerNode.id}`) || { x: cx, y: cy });
      nodeLayerIndex.set(centerNode.id, 0);
      const radiusX = 255;
      const radiusY = 175;
      others.forEach((n, idx) => {
        const angle = (2 * Math.PI * idx) / Math.max(1, others.length) - Math.PI / 2;
        nodeLayerIndex.set(n.id, 1);
        const custom = graphState.customPositions.get(`radial:${n.id}`);
        positions.set(n.id, custom || {
          x: Math.round(cx + Math.cos(angle) * radiusX),
          y: Math.round(cy + Math.sin(angle) * radiusY),
        });
      });
      return { positions, nodeLayerIndex, clusterBoxes, width, height, NODE_W, NODE_H, totalItems, totalPages };
    }

    const layers = new Map();
    for (const n of artifactNodes) {
      const baseRank = (n.rank || 0) * (clauseNodes.length ? 2 : 1);
      if (!layers.has(baseRank)) layers.set(baseRank, []);
      layers.get(baseRank).push(n);
    }
    for (const c of clauseNodes) {
      const parent = artifactNodes.find((a) => a.id === c.artifact_id);
      const cRank = (parent?.rank || 0) * 2 + 1;
      if (!layers.has(cRank)) layers.set(cRank, []);
      layers.get(cRank).push(c);
    }

    const sortedRanks = Array.from(layers.keys()).sort((a, b) => a - b);
    const maxCols = Math.max(1, ...sortedRanks.map((r) => Math.min(3, (layers.get(r) || []).length)));
    const canvasW = Math.max(700, maxCols * (NODE_W + 40) + 180);
    let curY = 24;
    const layerNames = [
      t("L0 · STRATEGY & REQUIREMENTS", "TẦNG 0 · CHIẾN LƯỢC & YÊU CẦU"),
      t("L1 · SYSTEM VIEWS", "TẦNG 1 · GÓC NHÌN HỆ THỐNG"),
      t("L2 · DOMAIN & API SPECS", "TẦNG 2 · PHÂN HỆ & HỢP ĐỒNG API"),
      t("L3 · RUNTIME & DELIVERY", "TẦNG 3 · THỰC THI & BÀN GIAO"),
    ];

    sortedRanks.forEach((r, layerIdx) => {
      const rowNodes = layers.get(r) || [];
      const cols = Math.min(3, Math.max(1, rowNodes.length));
      const rows = Math.ceil(rowNodes.length / cols);
      const contentW = cols * NODE_W + (cols - 1) * 38;
      const boxW = Math.max(340, contentW + 52);
      const boxH = rows * NODE_H + (rows - 1) * 24 + 46;
      const boxX = Math.round((canvasW - boxW) / 2);

      clusterBoxes.push({
        id: `layer-${r}`,
        label: layerNames[Math.min(layerIdx, layerNames.length - 1)],
        x: boxX,
        y: curY,
        width: boxW,
        height: boxH,
        count: rowNodes.length,
      });

      const startX = Math.round(boxX + (boxW - contentW) / 2);
      rowNodes.forEach((n, idx) => {
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        nodeLayerIndex.set(n.id, layerIdx);
        const custom = graphState.customPositions.get(`layered:${n.id}`);
        positions.set(n.id, custom || {
          x: startX + col * (NODE_W + 38),
          y: curY + 32 + row * (NODE_H + 24),
        });
      });
      curY += boxH + 40;
    });

    return { positions, nodeLayerIndex, clusterBoxes, width: canvasW, height: Math.max(260, curY), NODE_W, NODE_H, totalItems, totalPages };
  }

  function consolidateEdges(rawList) {
    const map = new Map();
    for (const item of rawList) {
      const key = `${item.from}-->${item.to}`;
      if (!map.has(key)) {
        map.set(key, {
          from: item.from,
          to: item.to,
          relations: [],
        });
      }
      const entry = map.get(key);
      for (const r of item.relations) {
        if (r && !entry.relations.includes(r)) {
          entry.relations.push(r);
        }
      }
    }
    return Array.from(map.values()).map((e) => {
      const primary = e.relations.includes("satisfies")
        ? "satisfies"
        : e.relations.includes("implements_contract")
        ? "implements_contract"
        : e.relations[0] || "references";
      return {
        from: e.from,
        to: e.to,
        relations: e.relations,
        relation: primary,
        label: e.relations.join(" · "),
      };
    });
  }
