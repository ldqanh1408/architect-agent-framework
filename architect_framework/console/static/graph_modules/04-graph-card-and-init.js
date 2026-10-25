  function buildDocumentGraphCard(model, onSelectArtifact, onDatasetModeChange) {
    const card = el("section", "", "doc-graph-card", {
      "aria-label": t("Document architecture graph", "Đồ thị kiến trúc tài liệu"),
    });

    const head = el("div", "", "doc-graph-header");
    const titleGroup = el("div", "", "doc-graph-title-group");
    titleGroup.append(
      el("h3", t("Architecture map", "Bản đồ kiến trúc")),
      el(
        "p",
        t(
          "Select a system or container to inspect its specifications.",
          "Chọn một hệ thống hoặc container để xem tài liệu."
        )
      )
    );
    const kpis = el("div", "", "doc-graph-kpis");
    head.append(titleGroup, kpis);
    card.append(head);

    // Unified Single Toolbar 
    const unifiedToolbar = el("div", "", "doc-graph-unified-toolbar");
    const leftLevels = el("div", "", "doc-graph-mode-group");
    const centerPopovers = el("div", "", "doc-graph-mode-group");
    const rightZoom = el("div", "", "doc-graph-mode-group zoom-group");

    // 1. Runtime Flows Popover
    const flowPopover = el("details", "", "aaf-toolbar-popover");
    flowPopover.append(el("summary", t("Runtime flows", "Luồng thực thi")));
    const flowBody = el("div", "", "aaf-toolbar-popover-body");
    flowPopover.append(flowBody);

    // 2. Map Options & Filters Popover (preserves exact summary text for test_f06_f07)
    const advDetails = el("details", "", "aaf-toolbar-popover aaf-advanced-filters");
    advDetails.append(
      el("summary", t("Map options & filters", "Tùy chọn & bộ lọc bản đồ"))
    );
    const advBody = el("div", "", "aaf-toolbar-popover-body");

    const modeBar = el("div", "", "doc-graph-mode-bar");
    const modeLeft = el("div", "", "doc-graph-mode-group");
    modeLeft.append(el("strong", t("Dataset:", "Bộ dữ liệu:")));

    const wsModeBtn = el(
      "button",
      t("Active Enterprise Workspace", "Workspace Dự án Hiện tại"),
      "aaf-tree-chip-btn",
      {
        type: "button",
        "aria-pressed": String(graphState.datasetMode === "workspace"),
      }
    );
    const v3ModeBtn = el(
      "button",
      t("Full Maximal V3 Catalogue (690 Slots · 10 Domains)", "Danh mục V3 Maximal Đầy đủ (690 Slots · 10 Domains)"),
      "aaf-tree-chip-btn",
      {
        type: "button",
        "aria-pressed": String(graphState.datasetMode === "v3-maximal"),
      }
    );
    modeLeft.append(wsModeBtn, v3ModeBtn);

    const slotGroup = el("div", "", "doc-graph-mode-group");
    slotGroup.append(el("span", t("Contract:", "Hợp đồng:"), "muted"));
    const slotButtons = [];
    for (const [code, labelEn, labelVi] of [
      ["all", "All", "Tất cả"],
      ["M", "[M] Mandatory", "[M] Bắt buộc"],
      ["S", "[S] Seam", "[S] Nghĩa vụ"],
      ["C", "[C] Conditional", "[C] Có ĐK"],
      ["D", "[D] Derived", "[D] Tự sinh"],
    ]) {
      const b = el("button", t(labelEn, labelVi), "aaf-tree-chip-btn", {
        type: "button",
        "aria-pressed": String(graphState.slotFilter === code),
      });
      b.onclick = () => {
        graphState.slotFilter = code;
        graphState.page = 0;
        for (const item of slotButtons) {
          item.btn.setAttribute("aria-pressed", String(item.code === graphState.slotFilter));
        }
        renderCanvasAndPassport();
        if (onDatasetModeChange) onDatasetModeChange();
      };
      slotButtons.push({ code, btn: b });
      slotGroup.append(b);
    }
    modeBar.append(modeLeft, slotGroup);

    const toolbar = el("div", "", "doc-graph-toolbar");
    const layoutLabel = el("label", t("Architecture model", "Mô hình hiển thị"));
    const layoutSelect = el("select", "", "", {
      "aria-label": t("Graph layout", "Bố cục Graph"),
    });
    for (const [val, labelEn, labelVi] of [
      ["c4-map", "C4 Model (C1 / C2 / Doc Tree)", "Mô hình C4 (C1 / C2 / Cây Tài liệu)"],
      ["drilldown", "Folder Tree Drill-Down", "Cây Thư mục Đệ quy"],
      ["doc-dag", "Document Dependency DAG", "Đồ thị Phụ thuộc Tài liệu"],
      ["radial", "Radial Hub Network", "Mạng Tâm điểm"],
    ]) {
      const opt = el("option", t(labelEn, labelVi), "", { value: val });
      opt.selected = graphState.layoutMode === val;
      layoutSelect.append(opt);
    }
    layoutLabel.append(layoutSelect);

    const traceLabel = el("label", t("Trace lens", "Truy vết"));
    const traceSelect = el("select", "", "", {
      "aria-label": t("Trace lens", "Truy vết"),
    });
    for (const [val, labelEn, labelVi] of [
      ["all", "All connections", "Tất cả liên kết"],
      ["upstream", "Upstream authority (Sources)", "Nguồn gốc (Upstream)"],
      ["downstream", "Downstream impact (Consumers)", "Ảnh hưởng xuôi (Downstream)"],
    ]) {
      const opt = el("option", t(labelEn, labelVi), "", { value: val });
      opt.selected = graphState.traceMode === val;
      traceSelect.append(opt);
    }
    traceLabel.append(traceSelect);

    const relLabel = el("label", t("Relation filter", "Lọc quan hệ"));
    const relSelect = el("select", "", "", {
      "aria-label": t("Relation filter", "Lọc quan hệ"),
    });
    relLabel.append(relSelect);

    const ownerLabel = el("label", t("Owner skill", "Skill sở hữu"));
    const ownerSelect = el("select", "", "", {
      "aria-label": t("Owner skill", "Skill sở hữu"),
    });
    ownerLabel.append(ownerSelect);

    toolbar.append(layoutLabel, traceLabel, relLabel, ownerLabel);
    advBody.append(modeBar, toolbar);
    advDetails.append(advBody);

    centerPopovers.append(flowPopover, advDetails);

    // 3. Zoom & Wide Controls
    const zoomOutBtn = el("button", "−", "doc-graph-crumb-btn", {
      type: "button",
      "aria-label": t("Zoom out graph", "Thu nhỏ đồ thị"),
    });
    const zoomResetBtn = el("button", `${Math.round(graphState.zoom * 100)}%`, "doc-graph-crumb-btn", {
      type: "button",
      "aria-label": t("Reset graph zoom", "Đặt lại tỷ lệ đồ thị"),
    });
    const zoomInBtn = el("button", "+", "doc-graph-crumb-btn", {
      type: "button",
      "aria-label": t("Zoom in graph", "Phóng to đồ thị"),
    });
    const wideBtn = el("button", t("Wide", "Mở rộng"), "doc-graph-crumb-btn", {
      type: "button",
    });
    rightZoom.append(zoomOutBtn, zoomResetBtn, zoomInBtn, wideBtn);

    unifiedToolbar.append(leftLevels, centerPopovers, rightZoom);
    card.append(unifiedToolbar);

    const paginationHost = el("div");
    const stage = el("div", "", "doc-graph-stage" + (graphState.expandedCanvas ? " expanded" : ""), {
      role: "region",
      tabindex: "0",
      "aria-label": t("Scrollable document graph canvas", "Khung cuộn đồ thị tài liệu"),
    });

    const adjacencyDetails = el("details");
    adjacencyDetails.append(
      el(
        "summary",
        t(
          "Document relationship & obligation matrix (accessible table view)",
          "Bảng ma trận quan hệ C4 & nghĩa vụ tài liệu (chế độ bảng truy cập)"
        )
      )
    );
    const adjacencyScroll = el("div", "", "scroll", {
      role: "region",
      tabindex: "0",
      "aria-label": t("Document relationship table", "Bảng quan hệ tài liệu"),
    });
    adjacencyDetails.append(adjacencyScroll);

    function rebuildDropdownOptions(graphData) {
      relSelect.replaceChildren();
      const relOptions = [["all", t("All relations", "Mọi quan hệ")]];
      for (const r of graphData.stats.relations || []) {
        relOptions.push([r, safeText(r)]);
      }
      for (const [val, label] of relOptions) {
        const opt = el("option", label, "", { value: val });
        opt.selected = graphState.relationFilter === val;
        relSelect.append(opt);
      }

      ownerSelect.replaceChildren();
      const ownerOptions = [["all", t("All owners", "Mọi skill")]];
      for (const o of graphData.stats.owners || []) {
        ownerOptions.push([o, safeText(o)]);
      }
      for (const [val, label] of ownerOptions) {
        const opt = el("option", label, "", { value: val });
        opt.selected = graphState.ownerFilter === val;
        ownerSelect.append(opt);
      }
    }

    function renderCanvasAndPassport() {
      const graphData = extractGraphData(model);
      rebuildDropdownOptions(graphData);

      kpis.replaceChildren();
      kpis.append(
        el("span", `${graphData.stats.artifacts} ${t("specs", "tài liệu")}`, "doc-graph-kpi"),
        el("span", `${graphData.stats.clauses} ${t("clauses", "điều khoản")}`, "doc-graph-kpi")
      );

      leftLevels.replaceChildren();
      flowBody.replaceChildren();
      paginationHost.replaceChildren();
      stage.replaceChildren();
      adjacencyScroll.replaceChildren();
      zoomResetBtn.textContent = `${Math.round(graphState.zoom * 100)}%`;
      layoutSelect.value = graphState.layoutMode;
      wideBtn.textContent = document.querySelector(".aaf-docs-workspace.wide-graph-mode")
        ? t("Sidebar", "Hiện Sidebar")
        : t("Wide", "Mở rộng");

      if (graphState.layoutMode === "c4-map") {
        for (const [lvl, enLbl, viLbl] of [
          ["C1", "C1 · System context", "C1 · System context"],
          ["C2", "C2 · Containers", "C2 · Containers"],
          ["CONTAINER_DOCS", "Doc Tree", "Cây Tài liệu"],
        ]) {
          const b = el("button", lvl === "CONTAINER_DOCS" ? t("Doc Tree", "Cây tài liệu") : lvl, "aaf-tree-chip-btn", {
            type: "button",
            "aria-label": t(enLbl, viLbl),
            title: t(enLbl, viLbl),
            "aria-pressed": String(graphState.c4Level === lvl),
          });
          b.onclick = () => {
            graphState.c4Level = lvl;
            if (lvl === "C1") {
              graphState.sidebarScope = "system";
              graphState.selectedNodeId = graphState.c1FocusedSystem || "sys.omnipay-core";
            } else {
              graphState.sidebarScope = "container";
              graphState.selectedNodeId = graphState.c4FocusedContainer || "ctr.payment-orchestrator";
            }
            renderCanvasAndPassport();
            if (onDatasetModeChange) onDatasetModeChange();
          };
          leftLevels.append(b);
        }

        for (const [fKey, fEn, fVi] of [
          ["all", "All Connections", "Tất cả kết nối"],
          ["checkout", "01 · Checkout & Idempotency (REQ-022)", "01 · Checkout & Idempotency (REQ-022)"],
          ["timeout-webhook", "02 · 30s Timeout & Webhook (REQ-021)", "02 · Timeout 30s & Webhook (REQ-021)"],
          ["fraud-ledger", "03 · AI Fraud <=25ms & Ledger (REQ-023)", "03 · AI Fraud <=25ms & Sổ cái (REQ-023)"],
        ]) {
          const fb = el("button", t(fEn, fVi), "aaf-tree-chip-btn", {
            type: "button",
            "aria-pressed": String(graphState.c4GuidedFlow === fKey),
          });
          fb.onclick = () => {
            graphState.c4GuidedFlow = fKey;
            flowPopover.open = false;
            renderCanvasAndPassport();
          };
          flowBody.append(fb);
        }
      } else {
        const backC4Btn = el("button", t("← C2 Map", "← Bản đồ C2"), "doc-graph-crumb-btn", {
          type: "button",
        });
        backC4Btn.onclick = () => {
          graphState.layoutMode = "c4-map";
          graphState.c4Level = "C2";
          graphState.drillPath = "";
          renderCanvasAndPassport();
        };
        leftLevels.append(backC4Btn);
        if (graphState.drillPath) {
          const upBtn = el("button", t("← Up 1 Level", "← Lùi 1 cấp"), "doc-graph-crumb-btn", {
            type: "button",
          });
          upBtn.onclick = () => {
            const parts = graphState.drillPath.split("/").filter(Boolean);
            parts.pop();
            graphState.drillPath = parts.join("/");
            graphState.page = 0;
            renderCanvasAndPassport();
          };
          leftLevels.append(upBtn);
        }
      }

      const layout = computeGraphLayout(
        graphData,
        graphState.layoutMode,
        graphState.showClauses,
        graphState.ownerFilter,
        graphState.slotFilter
      );
      const {
        positions,
        nodeLayerIndex,
        clusterBoxes,
        width,
        height,
        NODE_W,
        NODE_H,
        customNodesMap,
        customEdges,
        totalItems,
        totalPages,
      } = layout;

      if (totalPages && totalPages > 1) {
        const pagBar = el("div", "", "doc-graph-mode-group");
        pagBar.style.marginBottom = "6px";
        pagBar.append(
          el(
            "span",
            t(
              `Page ${graphState.page + 1}/${totalPages} (${totalItems} specs)`,
              `Trang ${graphState.page + 1}/${totalPages} (${totalItems} tài liệu)`
            ),
            "mono muted"
          )
        );
        const prevBtn = el("button", t("← Prev", "← Trước"), "doc-graph-crumb-btn", {
          type: "button",
        });
        prevBtn.disabled = graphState.page <= 0;
        prevBtn.onclick = () => {
          graphState.page = Math.max(0, graphState.page - 1);
          renderCanvasAndPassport();
        };
        const nextBtn = el("button", t("Next →", "Tiếp →"), "doc-graph-crumb-btn", {
          type: "button",
        });
        nextBtn.disabled = graphState.page + 1 >= totalPages;
        nextBtn.onclick = () => {
          graphState.page = Math.min(totalPages - 1, graphState.page + 1);
          renderCanvasAndPassport();
        };
        pagBar.append(prevBtn, nextBtn);
        paginationHost.append(pagBar);
      }

      const allMap = new Map();
      for (const n of graphData.nodes) allMap.set(n.id, n);
      for (const c of graphData.clause_nodes || []) allMap.set(c.id, c);
      if (customNodesMap) {
        for (const [k, v] of customNodesMap.entries()) allMap.set(k, v);
      }

      if (!graphState.selectedNodeId || !allMap.has(graphState.selectedNodeId)) {
        const firstPosId = positions.keys().next().value;
        graphState.selectedNodeId = positions.has(graphState.c4FocusedContainer)
          ? graphState.c4FocusedContainer
          : firstPosId || (graphData.nodes[0] && graphData.nodes[0].id);
      }
      const activeNodeId = graphState.hoveredNodeId || graphState.selectedNodeId;
      const activeNode = activeNodeId ? allMap.get(activeNodeId) : null;

      let consolidated = [];
      if (customEdges) {
        consolidated = customEdges;
      } else {
        const rawPairs = graphState.showClauses
          ? (graphData.edges || []).map((e) => ({
              from: e.from,
              to: e.to,
              relations: [e.relation],
            }))
          : (graphData.artifact_edges || []).map((e) => ({
              from: e.from,
              to: e.to,
              relations: e.relations || [e.primary_relation || "references"],
            }));
        consolidated = consolidateEdges(rawPairs);
      }

      const visibleEdges = consolidated.filter((e) => {
        if (!positions.has(e.from) || !positions.has(e.to)) return false;
        if (
          graphState.relationFilter !== "all" &&
          !(e.relations || []).includes(graphState.relationFilter)
        )
          return false;
        return true;
      });

      const highlightedNodes = new Set();
      if (activeNode) {
        highlightedNodes.add(activeNode.id);
        if (graphState.traceMode === "all" || graphState.traceMode === "upstream") {
          for (const u of activeNode.upstream || []) highlightedNodes.add(u);
          for (const u of activeNode.upstream_artifacts || []) highlightedNodes.add(u);
        }
        if (graphState.traceMode === "all" || graphState.traceMode === "downstream") {
          for (const d of activeNode.downstream || []) highlightedNodes.add(d);
          for (const d of activeNode.downstream_artifacts || []) highlightedNodes.add(d);
        }
      }

      const svg = svgEl("svg", {
        viewBox: `0 0 ${width} ${height}`,
        role: "group",
        "aria-label": t("Interactive document architecture graph", "Đồ thị kiến trúc tài liệu tương tác"),
      });
      svg.style.minWidth = `${Math.round(560 * graphState.zoom)}px`;
      svg.style.width = `${Math.round(100 * graphState.zoom)}%`;

      const defs = svgEl("defs");
      for (const [id, colorVar] of [
        ["aaf-arrow-default", "var(--line)"],
        ["aaf-arrow-active", "var(--accent)"],
        ["aaf-arrow-ok", "var(--ok)"],
      ]) {
        const marker = svgEl("marker", {
          id,
          viewBox: "0 0 10 10",
          refX: "9",
          refY: "5",
          markerWidth: "6",
          markerHeight: "6",
          orient: "auto-start-reverse",
        });
        marker.append(
          svgEl("path", {
            d: "M 0 1 L 10 5 L 0 9 z",
            fill: colorVar,
          })
        );
        defs.append(marker);
      }
      svg.append(defs);

      for (const box of clusterBoxes) {
        const g = svgEl("g");
        g.append(
          svgEl("rect", {
            x: box.x,
            y: box.y,
            width: box.width,
            height: box.height,
            rx: 10,
            class: "doc-graph-cluster-rect",
          }),
          svgEl(
            "text",
            {
              x: box.x + 14,
              y: box.y + 20,
              class: "doc-graph-cluster-label",
            },
            `${box.label}`
          )
        );
        svg.append(g);
      }

      const edgesPathLayer = svgEl("g", { class: "aaf-layer-edge-paths" });
      const nodesLayer = svgEl("g", { class: "aaf-layer-nodes" });
      const edgeLabelsLayer = svgEl("g", { class: "aaf-layer-edge-labels" });

      for (const sp of layout.treeSpinePaths || []) {
        edgesPathLayer.append(
          svgEl("path", {
            d: sp.d,
            fill: "none",
            stroke: sp.color || "var(--accent)",
            "stroke-width": "2.2",
            "marker-end": sp.arrow || undefined,
          })
        );
        if (sp.label) {
          const pillW = Math.max(54, Math.round(sp.label.length * 6.0 + 14));
          edgeLabelsLayer.append(
            svgEl("rect", {
              x: sp.lx - Math.round(pillW / 2),
              y: sp.ly - 9,
              width: pillW,
              height: 18,
              rx: 9,
              class: "doc-graph-edge-pill",
            }),
            svgEl(
              "text",
              {
                x: sp.lx,
                y: sp.ly + 3.5,
                "text-anchor": "middle",
                class: "doc-graph-edge-text",
              },
              sp.label.slice(0, 18)
            )
          );
        }
      }

      let sideArcCount = 0;
      visibleEdges.forEach((edge) => {
        const pFrom = positions.get(edge.from);
        const pTo = positions.get(edge.to);
        if (!pFrom || !pTo) return;

        const isEdgeHighlighted =
          activeNode &&
          (edge.from === activeNode.id ||
            edge.to === activeNode.id ||
            (highlightedNodes.has(edge.from) && highlightedNodes.has(edge.to)));

        const sameRow = Math.abs(pFrom.y - pTo.y) < 16;
        const lFrom = nodeLayerIndex.get(edge.from) ?? 0;
        const lTo = nodeLayerIndex.get(edge.to) ?? 0;
        const isLongSkip =
          graphState.layoutMode !== "radial" &&
          Math.abs(lFrom - lTo) > 1 &&
          Math.abs(pFrom.x - pTo.x) < 60;

        let dPath = "";
        let labelX = 0;
        let labelY = 0;

        const fw = pFrom.w || NODE_W;
        const fh = pFrom.h || NODE_H;
        const tw = pTo.w || NODE_W;
        const th = pTo.h || NODE_H;
        if (sameRow && Math.abs(pFrom.x - pTo.x) > fw - 10) {
          const goingRight = pFrom.x < pTo.x;
          const x1 = goingRight ? pFrom.x + fw : pFrom.x;
          const y1 = pFrom.y + Math.round(fh / 2);
          const x2 = goingRight ? pTo.x : pTo.x + tw;
          const y2 = pTo.y + Math.round(th / 2);
          dPath = `M ${x1} ${y1} L ${x2} ${y2}`;
          labelX = Math.round((x1 + x2) / 2);
          labelY = pFrom.y + fh + 12;
        } else if (isLongSkip) {
          const sideSign = sideArcCount % 2 === 0 ? 1 : -1;
          sideArcCount += 1;
          const x1 = sideSign > 0 ? pFrom.x + fw : pFrom.x;
          const y1 = pFrom.y + fh / 2;
          const x2 = sideSign > 0 ? pTo.x + tw : pTo.x;
          const y2 = pTo.y + th / 2;
          const ctrlX = sideSign > 0 ? Math.max(x1, x2) + 52 : Math.min(x1, x2) - 52;
          dPath = `M ${x1} ${y1} C ${ctrlX} ${y1}, ${ctrlX} ${y2}, ${x2} ${y2}`;
          labelX = Math.round(0.35 * x1 + 0.65 * ctrlX);
          labelY = Math.round((y1 + y2) / 2);
        } else {
          const goingDown = pFrom.y <= pTo.y;
          const x1 = pFrom.x + fw / 2;
          const y1 = goingDown ? pFrom.y + fh : pFrom.y;
          const x2 = pTo.x + tw / 2;
          const y2 = goingDown ? pTo.y : pTo.y + th;
          const midY = Math.round((y1 + y2) / 2);
          dPath = `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
          labelX = Math.round((x1 + x2) / 2);
          const stagger = Math.abs(x1 - x2) > 80 ? (x1 < x2 ? -10 : 10) : 0;
          labelY = Math.abs(x1 - x2) < 10 && y2 - y1 > 110 ? y1 + 36 : midY + stagger;
        }

        const pathEl = svgEl("path", {
          d: dPath,
          class: "doc-graph-edge-path" + (isEdgeHighlighted ? " highlighted" : ""),
          "data-rel": edge.relation,
          "marker-end": isEdgeHighlighted
            ? "url(#aaf-arrow-active)"
            : edge.relation === "satisfies" || edge.relation === "emphasis"
            ? "url(#aaf-arrow-ok)"
            : "url(#aaf-arrow-default)",
        });
        edgesPathLayer.append(pathEl);

        const labelText = safeText(edge.label).slice(0, 18);
        const pillW = Math.max(54, Math.round(labelText.length * 5.8 + 12));
        const edgeGroup = svgEl("g");
        edgeGroup.append(
          svgEl("rect", {
            x: labelX - Math.round(pillW / 2),
            y: labelY - 9,
            width: pillW,
            height: 18,
            rx: 9,
            class: "doc-graph-edge-pill",
          }),
          svgEl(
            "text",
            {
              x: labelX,
              y: labelY + 3.5,
              "text-anchor": "middle",
              class: "doc-graph-edge-text",
            },
            labelText
          )
        );
        edgeLabelsLayer.append(edgeGroup);
      });

      // Strictly <= 3 <text> elements per SVG node 
      for (const [nodeId, pos] of positions.entries()) {
        const nodeObj = allMap.get(nodeId);
        if (!nodeObj) continue;
        const isSelected = graphState.selectedNodeId === nodeId;
        const isUpstream = activeNode && nodeId !== activeNode.id && (activeNode.upstream || []).includes(nodeId);
        const isDownstream = activeNode && nodeId !== activeNode.id && (activeNode.downstream || []).includes(nodeId);
        const isFlowDimmed =
          graphState.layoutMode === "c4-map" &&
          graphState.c4Level === "C2" &&
          graphState.c4GuidedFlow !== "all" &&
          nodeObj.flowTags &&
          !nodeObj.flowTags.includes(graphState.c4GuidedFlow);

        let cls = "doc-graph-node";
        if (nodeObj.node_type === "c4-container") cls += " c4-container-node";
        else if (nodeObj.node_type === "c4-external") cls += " c4-external-node";
        else if (nodeObj.node_type === "c4-pillar") cls += " c4-pillar-node";
        else if (nodeObj.node_type === "folder") cls += " folder-node";

        if (nodeObj.is_active_leaf) cls += " leaf-active-node selected";
        else if (nodeObj.is_sibling_peer) cls += " sibling-peer-node";
        else if (isSelected) cls += " selected";
        else if (isUpstream) cls += " trace-upstream";
        else if (isDownstream) cls += " trace-downstream";
        else if (isFlowDimmed) cls += " dimmed";

        const ariaLabel = `Graph node ${nodeObj.id}: ${nodeObj.title || nodeObj.path} (${nodeObj.kind} · ${nodeObj.owner})`;

        const g = svgEl("g", {
          class: cls,
          role: "button",
          tabindex: "0",
          "aria-label": ariaLabel,
          "data-node-id": nodeObj.id,
        });

        const curW = pos.w || NODE_W;
        const curH = pos.h || NODE_H;

        g.append(
          svgEl("rect", {
            x: pos.x,
            y: pos.y,
            width: curW,
            height: curH,
            rx: nodeObj.node_type === "clause" ? 18 : 8,
            class: "doc-graph-node-box",
          })
        );

        const accentColor = nodeObj.band_color || "var(--accent)";
        g.append(
          svgEl("rect", {
            x: pos.x + 2,
            y: pos.y + 2,
            width: curW - 4,
            height: 4,
            rx: 3,
            fill: accentColor,
          })
        );

        let titleLine = "";
        let subLine = "";
        let metaLine = "";

        const trimWord = (str, lim) => {
          const s = String(str || "");
          if (s.length <= lim) return s;
          const cut = s.slice(0, lim - 1);
          const sp = cut.lastIndexOf(" ");
          return (sp > lim * 0.55 ? cut.slice(0, sp) : cut) + "…";
        };
        const maxT = curW >= 330 ? 44 : 29;
        const maxS = curW >= 330 ? 50 : 35;
        const maxM = curW >= 330 ? 48 : 35;

        if (nodeObj.node_type === "c4-container" || nodeObj.node_type === "c4-external" || nodeObj.node_type === "c4-pillar") {
          titleLine = trimWord(`${nodeObj.title}`, maxT);
          subLine = trimWord(nodeObj.subtitle || "", maxS);
          metaLine = trimWord(nodeObj.meta || "", maxM);
        } else if (nodeObj.node_type === "folder") {
          titleLine = trimWord(`${nodeObj.display_title || nodeObj.label}`, maxT);
          subLine = trimWord(nodeObj.subPreview || nodeObj.path, maxS);
          const sc = nodeObj.slotCounts || { M: 0, S: 0, C: 0, D: 0 };
          metaLine = `${nodeObj.deep} ${t("specs", "tài liệu")} ([M]:${sc.M || 0} [S]:${sc.S || 0})`;
        } else if (nodeObj.node_type === "clause") {
          titleLine = `${nodeObj.id} · ${humanizeSlug(nodeObj.anchor || "clause")}`.slice(0, maxT);
          subLine = String(nodeObj.summary || `${nodeObj.path}#${nodeObj.anchor || ""}`).slice(0, maxS);
          metaLine = `${nodeObj.artifact_id} -> ${(nodeObj.downstream || []).length} ${t("consumers", "đích")}`;
        } else {
          const slotTag = nodeObj.slot_code ? `[${nodeObj.slot_code}] ` : "";
          const niceTitle = nodeObj.display_title || humanizeSlug(nodeObj.label || nodeObj.id);
          titleLine = trimWord(`${slotTag}${niceTitle}`, maxT);
          subLine = trimWord(summarizeArtifactNode(nodeObj), maxS);
          metaLine = trimWord(`${nodeObj.kind} · ${nodeObj.owner}`, maxM);
        }

        if (curH <= 60) {
          g.append(
            svgEl("text", { x: pos.x + 12, y: pos.y + 22, class: "doc-graph-node-title" }, titleLine),
            svgEl("text", { x: pos.x + 12, y: pos.y + 41, class: "doc-graph-node-meta" }, metaLine)
          );
        } else {
          g.append(
            svgEl("text", { x: pos.x + 12, y: pos.y + 25, class: "doc-graph-node-title" }, titleLine),
            svgEl("text", { x: pos.x + 12, y: pos.y + 46, class: "doc-graph-node-sub" }, subLine),
            svgEl("text", { x: pos.x + 12, y: pos.y + 68, class: "doc-graph-node-meta" }, metaLine)
          );
        }

        const activateNode = () => {
          if (graphState.layoutMode === "c4-map" && graphState.c4Level === "C1") {
            graphState.selectedNodeId = nodeObj.id;
            graphState.c1FocusedSystem = nodeObj.id;
            graphState.sidebarScope = "system";
            const wbDoc = nodeObj.whitebox_doc;
            if (wbDoc) {
              graphState.activeLeafPath = wbDoc.path;
              graphState.activeLeafNode = wbDoc;
              if (onSelectArtifact) onSelectArtifact(wbDoc.path, wbDoc);
            }
            if (onDatasetModeChange) onDatasetModeChange();
            window.setTimeout(() => renderCanvasAndPassport(), 0);
            return;
          }
          if (nodeObj.drillsToC2) {
            graphState.c4Level = "C2";
            graphState.sidebarScope = "container";
            graphState.selectedNodeId = graphState.c4FocusedContainer || "ctr.payment-orchestrator";
            renderCanvasAndPassport();
            if (onDatasetModeChange) onDatasetModeChange();
            return;
          }
          if (nodeObj.node_type === "c4-pillar") {
            graphState.layoutMode = "drilldown";
            graphState.drillPath = nodeObj.folderPath;
            graphState.page = 0;
            renderCanvasAndPassport();
            return;
          }
          if (nodeObj.node_type === "folder") {
            if (nodeObj.whitebox_doc) {
              graphState.activeLeafPath = nodeObj.whitebox_doc.path;
              graphState.activeLeafNode = nodeObj.whitebox_doc;
              if (onSelectArtifact) onSelectArtifact(nodeObj.whitebox_doc.path, nodeObj.whitebox_doc);
              renderCanvasAndPassport();
              return;
            }
            graphState.layoutMode = "drilldown";
            graphState.drillPath = nodeObj.path;
            graphState.page = 0;
            renderCanvasAndPassport();
            return;
          }
          if (nodeObj.node_type === "c4-container" || nodeObj.node_type === "c4-external") {
            graphState.selectedNodeId = nodeObj.id;
            graphState.c4FocusedContainer = nodeObj.id;
            graphState.sidebarScope = "container";
            const wbDoc = nodeObj.whitebox_doc;
            if (wbDoc) {
              graphState.activeLeafPath = wbDoc.path;
              graphState.activeLeafNode = wbDoc;
              if (onSelectArtifact) onSelectArtifact(wbDoc.path, wbDoc);
            }
            if (onDatasetModeChange) onDatasetModeChange();
            window.setTimeout(() => renderCanvasAndPassport(), 0);
            return;
          }
          graphState.selectedNodeId = nodeObj.id;
          const leafDoc = nodeObj.whitebox_doc || nodeObj;
          if (leafDoc && leafDoc.path) {
            graphState.activeLeafPath = leafDoc.path;
            graphState.activeLeafNode = leafDoc;
          }
          const targetPath = nodeObj.path;
          if (onSelectArtifact && targetPath) {
            onSelectArtifact(targetPath, leafDoc);
          }
          window.setTimeout(() => renderCanvasAndPassport(), 0);
        };

        const drillNodeOnDblClick = () => {
          if (graphState.layoutMode === "c4-map" && graphState.c4Level === "C1" && nodeObj.drillsToC2) {
            graphState.c4Level = "C2";
            graphState.sidebarScope = "container";
            graphState.selectedNodeId = graphState.c4FocusedContainer || "ctr.payment-orchestrator";
            renderCanvasAndPassport();
            if (onDatasetModeChange) onDatasetModeChange();
            return;
          }
          if (graphState.layoutMode === "c4-map" && graphState.c4Level === "C2" && (nodeObj.node_type === "c4-container" || nodeObj.node_type === "c4-external")) {
            graphState.c4FocusedContainer = nodeObj.id;
            graphState.selectedNodeId = nodeObj.id;
            graphState.c4Level = "CONTAINER_DOCS";
            graphState.sidebarScope = "container";
            renderCanvasAndPassport();
            if (onDatasetModeChange) onDatasetModeChange();
          }
        };

        g.addEventListener("click", activateNode);
        g.addEventListener("dblclick", drillNodeOnDblClick);
        g.addEventListener("keydown", (ev) => {
          if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            activateNode();
          }
        });

        nodesLayer.append(g);
      }
      svg.append(edgesPathLayer, nodesLayer, edgeLabelsLayer);
      stage.append(svg);

      const table = el("table");
      table.append(
        el(
          "caption",
          t(
            "C4 & Document dependencies, references, and obligation links",
            "Danh sách liên kết C4, tham chiếu và nghĩa vụ"
          )
        )
      );
      const thead = el("thead");
      const hRow = el("tr");
      for (const col of [
        t("Consumer / Source (From)", "Thành phần gọi (Từ)"),
        t("Relation / Protocol", "Quan hệ / Giao thức"),
        t("Target / Authority (To)", "Thành phần đích (Tới)"),
        t("Obligation / Clause", "Nghĩa vụ / Điều khoản"),
      ]) {
        hRow.append(el("th", col));
      }
      thead.append(hRow);
      table.append(thead);
      const tbody = el("tbody");
      const allMatrixEdges = layout.tableEdges || visibleEdges;
      const matrixEdges = allMatrixEdges.length > 120 ? allMatrixEdges.slice(0, 120) : allMatrixEdges;
      for (const edge of matrixEdges) {
        const tr = el("tr");
        const fromNode = allMap.get(edge.from);
        const toNode = allMap.get(edge.to);
        tr.append(
          el("td", fromNode ? `${fromNode.id} (${fromNode.label || fromNode.path})` : edge.from, "mono"),
          el("td", safeText(edge.label)),
          el("td", toNode ? `${toNode.id} (${toNode.label || toNode.path})` : edge.to, "mono"),
          el("td", (edge.flowTags || []).join(", ") || "—", "mono")
        );
        tbody.append(tr);
      }
      table.append(tbody);
      adjacencyScroll.append(table);
    }

    wsModeBtn.onclick = () => {
      graphState.datasetMode = "workspace";
      graphState.layoutMode = "c4-map";
      graphState.c4Level = "C2";
      graphState.drillPath = "";
      graphState.page = 0;
      graphState.selectedNodeId = "ctr.payment-orchestrator";
      wsModeBtn.setAttribute("aria-pressed", "true");
      v3ModeBtn.setAttribute("aria-pressed", "false");
      advDetails.open = false;
      renderCanvasAndPassport();
      if (onDatasetModeChange) onDatasetModeChange();
    };

    v3ModeBtn.onclick = () => {
      graphState.datasetMode = "v3-maximal";
      graphState.layoutMode = "c4-map";
      graphState.c4Level = "C2";
      graphState.drillPath = "documents/architecture";
      graphState.page = 0;
      graphState.selectedNodeId = "ctr.payment-orchestrator";
      wsModeBtn.setAttribute("aria-pressed", "false");
      v3ModeBtn.setAttribute("aria-pressed", "true");
      advDetails.open = false;
      renderCanvasAndPassport();
      if (onDatasetModeChange) onDatasetModeChange();
    };

    layoutSelect.onchange = () => {
      graphState.layoutMode = layoutSelect.value;
      graphState.page = 0;
      renderCanvasAndPassport();
    };
    traceSelect.onchange = () => {
      graphState.traceMode = traceSelect.value;
      renderCanvasAndPassport();
    };
    relSelect.onchange = () => {
      graphState.relationFilter = relSelect.value;
      renderCanvasAndPassport();
    };
    ownerSelect.onchange = () => {
      graphState.ownerFilter = ownerSelect.value;
      graphState.page = 0;
      renderCanvasAndPassport();
    };
    zoomOutBtn.onclick = () => {
      graphState.zoom = Math.max(0.75, Math.round((graphState.zoom - 0.15) * 100) / 100);
      renderCanvasAndPassport();
    };
    zoomInBtn.onclick = () => {
      graphState.zoom = Math.min(1.6, Math.round((graphState.zoom + 0.15) * 100) / 100);
      renderCanvasAndPassport();
    };
    zoomResetBtn.onclick = () => {
      graphState.zoom = 1;
      graphState.customPositions.clear();
      renderCanvasAndPassport();
    };
    wideBtn.onclick = () => {
      const ws = document.querySelector(".aaf-docs-workspace");
      if (ws) ws.classList.toggle("wide-graph-mode");
      renderCanvasAndPassport();
    };

    stage.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") {
        if (graphState.layoutMode === "c4-map" && graphState.c4Level === "CONTAINER_DOCS") {
          ev.preventDefault();
          graphState.c4Level = "C2";
          renderCanvasAndPassport();
        } else if (graphState.layoutMode === "c4-map" && graphState.c4Level === "C2") {
          ev.preventDefault();
          graphState.c4Level = "C1";
          renderCanvasAndPassport();
        } else if (graphState.drillPath) {
          ev.preventDefault();
          const parts = graphState.drillPath.split("/").filter(Boolean);
          parts.pop();
          graphState.drillPath = parts.join("/");
          graphState.page = 0;
          renderCanvasAndPassport();
        }
      }
    });

    renderCanvasAndPassport();

    const footer = el("div", "", "doc-graph-footer");
    const legend = el("div", "", "doc-graph-legend");
    for (const [labelEn, labelVi, borderColor] of [
      ["C2 Container", "Container C2", "var(--b00)"],
      ["Zero-Trust / Strategy", "Bảo mật / Chiến lược", "var(--b01)"],
      ["Edge / Seam [S]", "Cổng biên / Nghĩa vụ [S]", "var(--b02)"],
      ["AI Risk Engine", "AI Chấm điểm Rủi ro", "var(--b03)"],
      ["Ledger & Reconcile", "Sổ cái & Đối soát", "var(--b04)"],
    ]) {
      const item = el("span", "", "doc-graph-legend-item");
      const sw = el("span", "", "doc-graph-swatch");
      sw.style.borderColor = borderColor;
      item.append(sw, el("span", t(labelEn, labelVi)));
      legend.append(item);
    }
    footer.append(legend);

    card.append(paginationHost, stage, footer, adjacencyDetails);
    return { card, refreshGraph: renderCanvasAndPassport };
  }

  function enhanceLeftDocumentTree(docSection, model, reader, onSelectV3Node, refreshGraph, onOpenDocByPath) {
    if (!docSection) return;
    Array.from(docSection.querySelectorAll(":scope > p")).forEach((pEl) => {
      pEl.hidden = true;
    });

    const graphData = extractGraphData(model);
    const c4 = buildC4Model(graphData);
    const v3HostId = "aaf-v3-tree-host";
    let v3Host = docSection.querySelector(`#${v3HostId}`);
    const nativeUl = Array.from(docSection.querySelectorAll(":scope > ul")).find((u) => u.id !== v3HostId);

    const searchInputEarly = docSection.querySelector('input[type="search"]');
    const queryEarly = (searchInputEarly?.value || "").trim();
    const shouldFormatNativeUl = (c4.isCompact && graphState.datasetMode === "workspace") || Boolean(queryEarly);
    if (nativeUl && shouldFormatNativeUl) {
      nativeUl.querySelectorAll(":scope > li > details").forEach((d, idx) => {
        if (idx < 4 && !d.dataset.aafInitOpen) {
          d.open = true;
          d.dataset.aafInitOpen = "1";
        }
      });
      nativeUl.querySelectorAll("summary").forEach((s) => {
        s.textContent = safeText(s.textContent || "");
      });
      nativeUl.querySelectorAll("li").forEach((li) => {
        const btn = li.querySelector(":scope > button");
        if (btn) {
          if (!btn.dataset.rawPath) btn.dataset.rawPath = (btn.textContent || "").trim();
          btn.textContent = safeText(btn.dataset.rawPath);
        }
        if (btn && !li.querySelector(".slot-badge")) {
          const p = (btn.textContent || "").trim();
          const meta = inferV3SlotMeta(p, "");
          const badge = el("span", `[${meta.slotCode}]`, "slot-badge", {
            "data-slot": meta.slotCode,
          });
          btn.after(badge);
        }
      });
    }

    if (c4.isCompact && graphState.datasetMode === "workspace") {
      if (v3Host) v3Host.hidden = true;
      if (nativeUl) nativeUl.hidden = false;
      return;
    }

    let controlsBar = docSection.querySelector(".aaf-tree-controls");
    if (!controlsBar) {
      controlsBar = el("div", "", "aaf-tree-controls");
      const ul = docSection.querySelector("ul");
      if (ul) ul.before(controlsBar);
      else docSection.append(controlsBar);
    }
    controlsBar.replaceChildren();

    const scopeHeader = el("div", "", "aaf-sidebar-scope-bar");
    const scopeTabs = el("div", "", "aaf-tree-actions-row");
    for (const [scKey, scEn, scVi] of [
      ["system", "C1 System", "C1 System"],
      ["container", "C2 Container", "C2 Container"],
      ["hg1", "HG-1 (9)", "HG-1 (9)"],
    ]) {
      const b = el("button", t(scEn, scVi), "aaf-tree-chip-btn", {
        type: "button",
        "aria-pressed": String(graphState.sidebarScope === scKey),
      });
      b.onclick = () => {
        graphState.sidebarScope = scKey;
        if (scKey === "system" && graphState.layoutMode === "c4-map" && graphState.c4Level !== "C1") {
          graphState.c4Level = "C1";
          graphState.selectedNodeId = graphState.c1FocusedSystem || "sys.omnipay-core";
          if (refreshGraph) refreshGraph();
        } else if (scKey === "container" && graphState.layoutMode === "c4-map" && graphState.c4Level === "C1") {
          graphState.c4Level = "C2";
          graphState.selectedNodeId = graphState.c4FocusedContainer || "ctr.payment-orchestrator";
          if (refreshGraph) refreshGraph();
        }
        enhanceLeftDocumentTree(docSection, model, reader, onSelectV3Node, refreshGraph, onOpenDocByPath);
      };
      scopeTabs.append(b);
    }
    scopeHeader.append(scopeTabs);
    controlsBar.append(scopeHeader);

    const row1 = el("div", "", "aaf-tree-actions-row");
    const expandAllBtn = el("button", t("Expand All", "Mở hết"), "aaf-tree-chip-btn", {
      type: "button",
    });
    const collapseAllBtn = el("button", t("Collapse All", "Thu gọn"), "aaf-tree-chip-btn", {
      type: "button",
    });
    expandAllBtn.onclick = () => {
      docSection.querySelectorAll("details").forEach((d) => {
        d.open = true;
      });
    };
    collapseAllBtn.onclick = () => {
      docSection.querySelectorAll("details").forEach((d) => {
        d.open = false;
      });
    };
    const clearFiltersBtn = el("button", t("Clear filters", "Xóa bộ lọc"), "aaf-tree-chip-btn", {
      type: "button",
    });
    clearFiltersBtn.onclick = () => {
      const sInp = docSection.querySelector('input[type="search"]');
      if (sInp && sInp.value) {
        sInp.value = "";
        sInp.dispatchEvent(new Event("input", { bubbles: true }));
      }
      graphState.slotFilter = "all";
      graphState.ownerFilter = "all";
      graphState.relationFilter = "all";
      graphState.c4GuidedFlow = "all";
      graphState.page = 0;
      enhanceLeftDocumentTree(docSection, model, reader, onSelectV3Node, refreshGraph, onOpenDocByPath);
      if (refreshGraph) refreshGraph();
    };
    row1.append(expandAllBtn, collapseAllBtn, clearFiltersBtn);
    controlsBar.append(row1);

    const searchInput = docSection.querySelector('input[type="search"]');
    const query = (searchInput?.value || "").trim().toLowerCase();

    if (!v3Host) {
      v3Host = el("div", "", "aaf-sidebar-custom-host", { id: v3HostId });
      docSection.append(v3Host);
    }

    if (query && graphState.datasetMode === "workspace") {
      if (nativeUl) nativeUl.hidden = false;
      v3Host.hidden = true;
      return;
    }

    if (nativeUl) nativeUl.hidden = true;
    v3Host.hidden = false;
    v3Host.replaceChildren();

    const handleOpenDoc = (docPath, docNode) => {
      if (graphState.datasetMode === "v3-maximal" && docNode) {
        onSelectV3Node(docNode);
      } else if (onOpenDocByPath) {
        onOpenDocByPath(docPath, docNode);
      } else if (docNode) {
        onSelectV3Node(docNode);
      }
    };

    if (graphState.sidebarScope === "system") {
      const allC1Systems = c4.c1Systems || [];
      const focusedSys =
        allC1Systems.find((s) => s.id === graphState.c1FocusedSystem) ||
        allC1Systems.find((s) => s.id === graphState.selectedNodeId) ||
        allC1Systems[0];

      const selWrap = el("div", "", "aaf-sidebar-ctr-selector");
      const selLabel = el("label", t("System / Actor:", "Hệ thống / Tác nhân:"));
      const selEl = el("select", "", "", {
        "aria-label": t("Select C1 System for Document Tree", "Chọn System ở C1 để xem tài liệu"),
      });
      for (const sysItem of allC1Systems) {
        const sModel = buildSystemDocTreeModel(sysItem, graphData, c4);
        const opt = el(
          "option",
          `${sysItem.title} (${sModel.allSystemDocs.length} ${t("specs", "tài liệu")} · ${sModel.arc42Groups.length} arc42)`,
          "",
          { value: sysItem.id }
        );
        opt.selected = focusedSys && sysItem.id === focusedSys.id;
        selEl.append(opt);
      }
      selEl.onchange = () => {
        graphState.c1FocusedSystem = selEl.value;
        graphState.selectedNodeId = selEl.value;
        const chosen = allC1Systems.find((s) => s.id === selEl.value);
        if (chosen && chosen.whitebox_doc) {
          handleOpenDoc(chosen.whitebox_doc.path, chosen.whitebox_doc);
        }
        enhanceLeftDocumentTree(docSection, model, reader, onSelectV3Node, refreshGraph, onOpenDocByPath);
        if (refreshGraph) refreshGraph();
      };
      selLabel.append(selEl);
      selWrap.append(selLabel);
      if (focusedSys) {
        const sysModel = buildSystemDocTreeModel(focusedSys, graphData, c4);
        selWrap.append(
          el(
            "small",
            `${sysModel.primaryDocs.length} ${t("direct", "trực tiếp")} · ${sysModel.relatedDocs.length} ${t("referenced", "tham chiếu")} · ${sysModel.allSystemDocs.length} ${t("unique specs", "tài liệu duy nhất")}`,
            "aaf-sidebar-stats mono"
          )
        );
      }
      v3Host.append(selWrap);

      if (focusedSys) {
        v3Host.append(renderSystemDocTreeDom(focusedSys, graphData, c4, handleOpenDoc));
      }
    } else if (graphState.sidebarScope === "hg1") {
      const clauseList = el("div", "", "aaf-hg1-clause-list");
      const clauses = graphData.clause_nodes || [];
      const docById = new Map((graphData.nodes || []).map((d) => [d.id, d]));
      for (const c of clauses) {
        const card = el("div", "", "aaf-hg1-clause-card");
        const head = el("div", "", "doc-graph-header");
        head.append(el("strong", `${c.id}`, "mono"), el("span", safeText(c.owner), "doc-graph-kpi mono"));
        card.append(head, el("p", c.summary || c.id));
        const relRow = el("div", "", "doc-graph-mode-group");
        const relatedIds = [c.artifact_id, ...(c.downstream || [])].filter(Boolean);
        const seenPaths = new Set();
        for (const rid of relatedIds) {
          const docNode = docById.get(rid);
          if (!docNode || seenPaths.has(docNode.path)) continue;
          seenPaths.add(docNode.path);
          const linkBtn = el("button", docNode.label || docNode.id, "doc-chip-btn", {
            type: "button",
            title: docNode.path,
          });
          linkBtn.onclick = () => handleOpenDoc(docNode.path, docNode);
          relRow.append(linkBtn);
        }
        card.append(relRow);
        clauseList.append(card);
      }
      v3Host.append(clauseList);
    } else {
      const allC2Nodes = [...(c4.c2Containers || []), ...(c4.c2Externals || [])];
      const focusedCtr =
        allC2Nodes.find((c) => c.id === graphState.c4FocusedContainer) ||
        allC2Nodes.find((c) => c.id === graphState.selectedNodeId) ||
        c4.c2Containers[1] ||
        c4.c2Containers[0];

      const selWrap = el("div", "", "aaf-sidebar-ctr-selector");
      const selLabel = el("label", t("Container:", "Container:"));
      const selEl = el("select", "", "", {
        "aria-label": t("Select Container for Document Tree", "Chọn Container ở C2 để xem tài liệu"),
      });
      for (const ctrItem of allC2Nodes) {
        const tModel = buildContainerDocTreeModel(ctrItem, graphData, c4);
        const opt = el(
          "option",
          `${ctrItem.title} (${tModel.ownedDocs.length} ${t("owned", "sở hữu")} · ${tModel.relatedDocs.length} ${t("linked", "liên kết")})`,
          "",
          { value: ctrItem.id }
        );
        opt.selected = focusedCtr && ctrItem.id === focusedCtr.id;
        selEl.append(opt);
      }
      selEl.onchange = () => {
        graphState.c4FocusedContainer = selEl.value;
        graphState.selectedNodeId = selEl.value;
        const chosen = allC2Nodes.find((c) => c.id === selEl.value);
        if (chosen && chosen.whitebox_doc) {
          handleOpenDoc(chosen.whitebox_doc.path, chosen.whitebox_doc);
        }
        enhanceLeftDocumentTree(docSection, model, reader, onSelectV3Node, refreshGraph, onOpenDocByPath);
        if (refreshGraph) refreshGraph();
      };
      selLabel.append(selEl);
      selWrap.append(selLabel);
      if (focusedCtr) {
        const treeModel = buildContainerDocTreeModel(focusedCtr, graphData, c4);
        const uniqueIds = new Set([
          ...treeModel.ownedDocs.map((d) => d.id),
          ...treeModel.relatedDocs.map((r) => r.doc.id),
        ]);
        selWrap.append(
          el(
            "small",
            `${treeModel.ownedDocs.length} ${t("owned", "sở hữu")} · ${treeModel.relatedDocs.length} ${t("referenced", "tham chiếu")} · ${uniqueIds.size} ${t("unique specs", "tài liệu duy nhất")}`,
            "aaf-sidebar-stats mono"
          )
        );
      }
      v3Host.append(selWrap);

      if (focusedCtr) {
        v3Host.append(renderContainerDocTreeDom(focusedCtr, graphData, c4, handleOpenDoc));
      }
    }
  }

  function enhanceDocumentReader(reader, model, onNavigatePath) {
    if (!reader) return false;
    if (reader.querySelector(".aaf-reader-header") || reader.querySelector(".aaf-reader-empty")) {
      return false;
    }
    const h3 = reader.querySelector("h3");
    const rawPre = reader.querySelector("pre");
    if (!h3) {
      const emptyBox = el("div", "", "aaf-reader-empty");
      emptyBox.append(
        el(
          "p",
          t(
            "Choose a document from the browser or map to read its specification here.",
            "Chọn tài liệu từ cây hoặc bản đồ để đọc nội dung tại đây."
          )
        )
      );
      reader.append(emptyBox);
      return true;
    }

    const docPath = (h3.dataset.rawPath || h3.textContent || "").trim();
    const graphData = extractGraphData(model);
    const v3Nodes = getMaximalV3CatalogueModel().document_graph.nodes || [];
    const nodeObj =
      (graphData.nodes || []).find((n) => n.path === docPath) ||
      v3Nodes.find((n) => n.path === docPath);
    if (nodeObj) {
      graphState.activeLeafPath = nodeObj.path;
      graphState.activeLeafNode = nodeObj;
    } else if (docPath) {
      graphState.activeLeafPath = docPath;
    }

    // Extract original metadata & revision before removing duplicate raw <p> elements 
    const rawParas = Array.from(reader.querySelectorAll(":scope > p"));
    const metaPara = rawParas.find((p) => !p.classList.contains("mono"));
    const revPara = rawParas.find((p) => p.classList.contains("mono"));
    const fullRev = (revPara?.textContent || nodeObj?.revision || "live").trim();
    const shortRev = fullRev.length > 10 ? fullRev.slice(0, 8) : fullRev;
    const rawMetaText = (metaPara?.textContent || "").trim();

    for (const pEl of rawParas) {
      if (pEl.textContent && pEl.textContent.includes("truncated")) continue;
      pEl.remove();
    }

    const existingProv = reader.querySelector(".aaf-provenance-banner");
    const isSynth = existingProv?.getAttribute("data-origin") === "synthetic" || graphState.datasetMode === "v3-maximal";
    const isCand = Boolean(model && model.change_id);
    const isPrev = window.__aafStandaloneCanvas === true;
    const originType = isSynth ? "synthetic" : isPrev ? "preview" : isCand ? "candidate" : "live";
    if (existingProv) existingProv.remove();

    const slotCode = nodeObj?.slot_code || inferV3SlotMeta(docPath, nodeObj?.kind || "").slotCode;
    const basename = docPath.split("/").pop() || docPath;
    const humanTitle = nodeObj?.display_title || humanizeSlug(basename);

    const headerBox = el("div", "", "aaf-reader-header");
    const metaRow = el("div", "", "aaf-reader-meta-row");
    const provLabel = isSynth
      ? t("Synthetic V3 Catalogue Template", "Mẫu danh mục V3 tổng hợp")
      : isPrev
      ? t("Preview sample · Read-only", "Bản xem thử · Chỉ đọc")
      : isCand
      ? t(`Candidate · ${model.change_id}`, `Dự thảo · ${model.change_id}`)
      : t("Live workspace source", "Nguồn thực tế đã đăng ký");

    metaRow.append(
      el("span", provLabel, "doc-graph-kpi aaf-provenance-banner", { "data-origin": originType }),
      el("span", `[${slotCode}]`, "slot-badge", { "data-slot": slotCode }),
      el("code", `rev: ${shortRev}`, "aaf-rev-short mono", { title: fullRev })
    );

    h3.dataset.rawPath = docPath;
    h3.textContent = safeText(humanTitle);
    h3.title = docPath;

    const subText = nodeObj
      ? `${basename} · ${nodeObj.id} · ${nodeObj.kind} · ${nodeObj.owner}`
      : `${basename} · ${rawMetaText}`;
    const subLine = el("p", subText, "aaf-reader-sub muted", { title: docPath });

    headerBox.append(metaRow, h3, subLine);
    reader.prepend(headerBox);

    if (rawPre) rawPre.textContent = safeText(rawPre.textContent || "");

    // Single compact Toolbar + Traceability Strip 
    const toolbar = el("div", "", "aaf-reader-toolbar");
    const modeGroup = el("div", "", "doc-graph-mode-group");
    const renderedBox = renderMarkdownToDom(rawPre ? rawPre.textContent || "" : "");
    const modeBtns = [];

    const applyMode = (mode) => {
      graphState.readerMode = mode;
      renderedBox.hidden = mode === "raw";
      if (rawPre) {
        rawPre.hidden = mode === "rendered";
      }
      for (const item of modeBtns) {
        item.btn.setAttribute("aria-pressed", String(item.key === mode));
      }
    };

    for (const [mKey, mEn, mVi] of [
      ["rendered", "Rendered", "Bản đọc"],
      ["raw", "Markdown", "Mã nguồn"],
      ["split", "Split", "Cả hai"],
    ]) {
      const btn = el("button", t(mEn, mVi), "doc-chip-btn", {
        type: "button",
        "aria-pressed": String(graphState.readerMode === mKey),
      });
      btn.onclick = () => applyMode(mKey);
      modeBtns.push({ key: mKey, btn });
      modeGroup.append(btn);
    }
    toolbar.append(modeGroup);

    const traceGroup = el("div", "", "doc-graph-mode-group");
    if (nodeObj) {
      for (const upId of (nodeObj.upstream_artifacts || []).slice(0, 2)) {
        const target = (graphData.nodes || []).find((n) => n.id === upId);
        if (target) {
          const b = el("button", `↑ ${target.id}`, "doc-chip-btn", {
            type: "button",
            title: target.path,
            "aria-label": `Open upstream document ${target.path}`,
          });
          b.onclick = () => onNavigatePath && onNavigatePath(target.path, target);
          traceGroup.append(b);
        }
      }
      for (const downId of (nodeObj.downstream_artifacts || []).slice(0, 2)) {
        const target = (graphData.nodes || []).find((n) => n.id === downId);
        if (target) {
          const b = el("button", `↓ ${target.id}`, "doc-chip-btn", {
            type: "button",
            title: target.path,
            "aria-label": `Open downstream document ${target.path}`,
          });
          b.onclick = () => onNavigatePath && onNavigatePath(target.path, target);
          traceGroup.append(b);
        }
      }
    }

    const sibInfo = getSiblingDocuments(nodeObj || docPath, graphData);
    if (sibInfo.siblings && sibInfo.siblings.length > 1) {
      const prevSib =
        sibInfo.siblings[
          (sibInfo.currentIndex - 1 + sibInfo.siblings.length) % sibInfo.siblings.length
        ];
      const nextSib =
        sibInfo.siblings[(sibInfo.currentIndex + 1) % sibInfo.siblings.length];
      const prevBtn = el("button", "←", "doc-chip-btn", {
        type: "button",
        title: prevSib ? prevSib.path : "",
        "aria-label": t("Previous sibling specification", "Tài liệu cùng cấp trước"),
      });
      prevBtn.onclick = () => prevSib && onNavigatePath && onNavigatePath(prevSib.path, prevSib);
      const nextBtn = el("button", "→", "doc-chip-btn", {
        type: "button",
        title: nextSib ? nextSib.path : "",
        "aria-label": t("Next sibling specification", "Tài liệu cùng cấp tiếp"),
      });
      nextBtn.onclick = () => nextSib && onNavigatePath && onNavigatePath(nextSib.path, nextSib);
      traceGroup.append(prevBtn, nextBtn);
    }

    if (traceGroup.childElementCount) {
      toolbar.append(traceGroup);
    }

    if (rawPre) {
      rawPre.before(toolbar, renderedBox);
      applyMode(graphState.readerMode);
    }
    return true;
  }

  function initWorkbenchEnhancer() {
    const main = document.getElementById("main");
    const coreModelEl = document.getElementById("core-model");
    if (!main || !coreModelEl) return;

    let currentModel = {};
    try {
      currentModel = JSON.parse(coreModelEl.textContent || "{}");
    } catch {
      currentModel = {};
    }

    const prevFetch = window.fetch;
    if (prevFetch && !window.__aafFetchWrapped) {
      window.__aafFetchWrapped = true;
      window.fetch = async function (input, ...args) {
        const urlStr = String(input || "");
        if (window.__aafStandaloneCanvas === true) {
          if (urlStr.includes("/api/runs")) {
            return new Response(JSON.stringify(currentModel.runs || { last_seq: 0, events: [] }), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            });
          }
          if (urlStr.includes("/api/model")) {
            return new Response(JSON.stringify({ site: null, review: currentModel }), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            });
          }
        }
        const response = await prevFetch.call(this, input, ...args);
        try {
          const url = String(input || "");
          if (url.includes("/api/model")) {
            const clone = response.clone();
            clone
              .json()
              .then((data) => {
                if (data && data.review) {
                  currentModel = data.review;
                }
              })
              .catch(() => {});
          }
        } catch {
          // ignore
        }
        return response;
      };
    }

    let enhancing = false;
    function syncStateFromUrlHash() {
      const params = new URLSearchParams(location.hash.slice(1));
      const c4Param = params.get("c4");
      if (c4Param && ["C1", "C2", "CONTAINER_DOCS"].includes(c4Param)) {
        graphState.c4Level = c4Param;
        graphState.sidebarScope = c4Param === "C1" ? "system" : "container";
      }
      const nodeParam = params.get("node");
      if (nodeParam) {
        graphState.selectedNodeId = nodeParam;
        if (nodeParam.startsWith("ctr.") || nodeParam.startsWith("ext.")) {
          graphState.c4FocusedContainer = nodeParam;
        } else if (nodeParam.startsWith("sys.") || nodeParam.startsWith("act.")) {
          graphState.c1FocusedSystem = nodeParam;
        }
      }
      const dsParam = params.get("dataset");
      if (dsParam && ["workspace", "v3-maximal"].includes(dsParam)) {
        graphState.datasetMode = dsParam;
      }
      const slotParam = params.get("slot");
      if (slotParam && ["all", "M", "S", "C", "D"].includes(slotParam)) {
        graphState.slotFilter = slotParam;
      }
    }
    syncStateFromUrlHash();
    window.addEventListener("hashchange", syncStateFromUrlHash);

    function enhanceCurrentMain() {
      if (enhancing) return;
      const route = new URLSearchParams(location.hash.slice(1)).get("view") || "overview";

      // Do NOT embed a duplicate C4 Architecture Map on Overview 
      if (route !== "documents") return;
      if (main.querySelector(".aaf-docs-workspace")) return;

      const reader = main.querySelector('section[aria-label="Document reader"]');
      const docSection = Array.from(main.querySelectorAll("section.card")).find(
        (s) => s !== reader && s.querySelector('input[type="search"]')
      );
      if (!docSection || !reader) return;

      enhancing = true;
      try {
        let refreshGraphFn = null;

        const renderMissingOrStaleSourceInReader = (targetPath, reasonMsg) => {
          reader.replaceChildren();
          const banner = el("div", "", "receipt aaf-provenance-banner", {
            "data-origin": "error",
            role: "alert",
          });
          banner.append(
            el("strong", t("Exact document source unavailable", "Không thể tải nguồn tài liệu chính xác")),
            el(
              "p",
              reasonMsg ||
                t(
                  `Source for "${targetPath}" could not be loaded from the workspace revision store. Synthetic templates are never substituted for live workspace documents.`,
                  `Không tìm thấy phiên bản nguồn của "${targetPath}" trong kho lưu trữ workspace. Hệ thống tuyệt đối không dùng mẫu giả lập để thay thế tài liệu thật.`
                )
            )
          );
          reader.append(banner);
        };

        const openV3NodeInReader = (nodeObj, originMode) => {
          if (!nodeObj) return;
          const mode =
            originMode ||
            (graphState.datasetMode === "v3-maximal"
              ? "synthetic"
              : window.__aafStandaloneCanvas === true
              ? "preview"
              : "live");
          if (mode === "live") {
            renderMissingOrStaleSourceInReader(nodeObj.path || nodeObj.id);
            return;
          }
          graphState.activeLeafPath = nodeObj.path;
          graphState.activeLeafNode = nodeObj;
          const mdText = synthesizeV3Markdown(nodeObj, mode);
          reader.replaceChildren();
          const provBanner = el("div", "", "receipt aaf-provenance-banner", {
            "data-origin": mode,
          });
          const h3El = el("h3", nodeObj.path);
          h3El.dataset.rawPath = nodeObj.path;
          reader.append(
            provBanner,
            h3El,
            el("p", `[${nodeObj.slot_code || "M"}] ${nodeObj.id} · ${nodeObj.kind} · ${nodeObj.owner}`),
            el("p", nodeObj.revision, "mono"),
            el("pre", mdText)
          );
          enhanceDocumentReader(reader, currentModel, (p, targetNode) => {
            if (targetNode) openV3NodeInReader(targetNode, mode);
          });
          if (refreshGraphFn) refreshGraphFn();
        };

        const triggerTreeDoc = (targetPath, nodeObj) => {
          if (graphState.datasetMode === "v3-maximal" && nodeObj) {
            openV3NodeInReader(nodeObj, "synthetic");
            return;
          }
          if (window.__aafStandaloneCanvas === true && nodeObj) {
            openV3NodeInReader(nodeObj, "preview");
            return;
          }
          const nativeTreeUl = Array.from(docSection.querySelectorAll(":scope > ul")).find(
            (u) => u.id !== "aaf-v3-tree-host"
          );
          const buttons = nativeTreeUl ? Array.from(nativeTreeUl.querySelectorAll("button")) : [];
          let btn = buttons.find(
            (b) =>
              (b.dataset.rawPath || b.textContent || "").trim() === targetPath ||
              (b.textContent || "").trim() === safeText(targetPath)
          );
          if (!btn && nativeTreeUl) {
            const searchInput = docSection.querySelector('input[type="search"]');
            if (searchInput && searchInput.value) {
              searchInput.value = "";
              searchInput.dispatchEvent(new Event("input", { bubbles: true }));
              const refreshedUl = Array.from(docSection.querySelectorAll(":scope > ul")).find(
                (u) => u.id !== "aaf-v3-tree-host"
              );
              btn = refreshedUl
                ? Array.from(refreshedUl.querySelectorAll("button")).find(
                    (b) => (b.dataset.rawPath || b.textContent || "").trim() === targetPath
                  )
                : null;
            }
          }
          if (btn) {
            btn.click();
            return;
          }
          const registeredArt = (currentModel.artifacts || []).find(
            (a) => a.path === targetPath || (nodeObj && a.id === nodeObj.id)
          );
          if (registeredArt && location.protocol.startsWith("http")) {
            const query = new URLSearchParams({
              id: registeredArt.id,
              revision: registeredArt.revision,
            });
            if (currentModel.change_id) query.set("change", currentModel.change_id);
            const artifactUrl = "/api/artifact?" + query.toString();
            fetch(artifactUrl)
              .then(async (res) => {
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
                reader.replaceChildren();
                reader.append(
                  el("h3", registeredArt.path),
                  el("p", `${registeredArt.id} · ${registeredArt.kind} · ${registeredArt.owner}`),
                  el("p", data.revision, "mono"),
                  el("pre", data.text)
                );
                if (data.has_more) {
                  reader.append(
                    el("p", "This display is truncated. Use the complete source before review.")
                  );
                }
                enhanceDocumentReader(reader, currentModel, (p, targetNode) =>
                  triggerTreeDoc(p, targetNode)
                );
              })
              .catch((err) => {
                renderMissingOrStaleSourceInReader(
                  targetPath,
                  err instanceof Error ? err.message : String(err)
                );
              });
          } else {
            renderMissingOrStaleSourceInReader(targetPath);
          }
        };

        const workspaceGrid = el("div", "", "aaf-docs-workspace");
        const leftCol = el("div", "", "aaf-docs-left-col");
        const centerCol = el("div", "", "aaf-docs-center-col");
        const rightCol = el("div", "", "aaf-docs-right-col");

        const { card: graphCard, refreshGraph } = buildDocumentGraphCard(
          currentModel,
          (targetPath, nodeObj) => {
            triggerTreeDoc(targetPath, nodeObj);
          },
          () => {
            enhanceLeftDocumentTree(docSection, currentModel, reader, openV3NodeInReader, refreshGraph, triggerTreeDoc);
            if (graphState.datasetMode === "v3-maximal") {
              const v3Nodes = getMaximalV3CatalogueModel().document_graph.nodes;
              const matched =
                (graphState.activeLeafPath &&
                  v3Nodes.find((n) => n.path === graphState.activeLeafPath)) ||
                (graphState.drillPath &&
                  v3Nodes.find((n) => n.path.startsWith(graphState.drillPath))) ||
                v3Nodes[0];
              if (matched) {
                graphState.activeLeafPath = matched.path;
                graphState.activeLeafNode = matched;
                openV3NodeInReader(matched);
              }
            }
          }
        );
        refreshGraphFn = refreshGraph;

        const browserDetails = el("details", "", "aaf-document-browser");
        browserDetails.open = window.matchMedia("(min-width: 1000px)").matches;
        browserDetails.append(el("summary", t("Browse documents", "Duyệt tài liệu")), docSection);
        leftCol.append(browserDetails);
        centerCol.append(graphCard);
        rightCol.append(reader);
        workspaceGrid.append(leftCol, centerCol, rightCol);
        main.append(workspaceGrid);

        enhanceLeftDocumentTree(docSection, currentModel, reader, openV3NodeInReader, refreshGraph, triggerTreeDoc);
        if (window.__aafStandaloneCanvas === true && !reader.querySelector("h3")) {
          const initGraph = extractGraphData(currentModel);
          const initDoc =
            (initGraph.nodes || []).find((n) => n.id === "API") || (initGraph.nodes || [])[0];
          if (initDoc) {
            openV3NodeInReader(initDoc);
          }
        }

        const searchInput = docSection.querySelector('input[type="search"]');
        if (searchInput) {
          searchInput.addEventListener("input", () => {
            window.setTimeout(() => {
              enhanceLeftDocumentTree(docSection, currentModel, reader, openV3NodeInReader, refreshGraph, triggerTreeDoc);
            }, 0);
          });
        }

        enhanceDocumentReader(reader, currentModel, (path, targetNode) => {
          triggerTreeDoc(path, targetNode);
        });

        if (reader.__aafObserver) {
          reader.__aafObserver.disconnect();
        }
        const readerObserver = new MutationObserver(() => {
          if (reader.querySelector(".aaf-reader-header") || reader.querySelector(".aaf-reader-empty")) {
            return;
          }
          const changed = enhanceDocumentReader(reader, currentModel, (path, targetNode) => {
            triggerTreeDoc(path, targetNode);
          });
          if (changed) {
            refreshGraph();
          }
        });
        readerObserver.observe(reader, { childList: true });
        reader.__aafObserver = readerObserver;

        if (graphState.pendingDocPath) {
          const pending = graphState.pendingDocPath;
          graphState.pendingDocPath = null;
          window.setTimeout(() => triggerTreeDoc(pending), 0);
        }
      } finally {
        enhancing = false;
      }
    }

    const mainObserver = new MutationObserver(() => {
      enhanceCurrentMain();
    });
    mainObserver.observe(main, { childList: true });
    enhanceCurrentMain();
  }

  function initReviewConsoleEnhancer() {
    const app = document.querySelector("[id=app]");
    if (!app || document.getElementById("main")) return;

    let enhancing = false;
    function enhanceReviewApp() {
      if (enhancing) return;
      if (typeof packet === "undefined" || !packet) return;
      if (app.querySelector(".doc-graph-card")) return;

      enhancing = true;
      try {
        const changesSection = Array.from(app.querySelectorAll("section")).find((s) => {
          const h2 = s.querySelector("h2");
          return (
            h2 &&
            (h2.textContent === "Changes from accepted baseline" ||
              h2.textContent === "Thay đổi so với bản đã duyệt")
          );
        });
        const { card: graphCard } = buildDocumentGraphCard(packet, (targetPath) => {
          if (!changesSection) return;
          const summary = Array.from(changesSection.querySelectorAll("details > summary")).find(
            (sum) => (sum.textContent || "").trim() === targetPath
          );
          if (summary && summary.parentElement) {
            summary.parentElement.open = true;
            summary.focus();
          }
        });
        if (changesSection) {
          changesSection.before(graphCard);
        } else {
          app.append(graphCard);
        }
      } finally {
        enhancing = false;
      }
    }

    const appObserver = new MutationObserver(() => {
      enhanceReviewApp();
    });
    appObserver.observe(app, { childList: true });
    enhanceReviewApp();
  }

  if (document.getElementById("main") && document.getElementById("core-model")) {
    initWorkbenchEnhancer();
  } else if (document.querySelector("[id=app]")) {
    initReviewConsoleEnhancer();
  }
})();
