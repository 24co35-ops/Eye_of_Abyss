"use client";

import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

// Compact 200px force-directed actor graph for ShadowTrace Prompt 4
export default function ActorNetworkGraph() {
  const containerRef = useRef<HTMLDivElement>(null);
  // ponytail: any matches WalletClusterGraph pattern; cytoscape types differ by version
  const cyRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const elements: any[] = [
      // Central node
      { data: { id: "central", label: "d4rk_exch4nger", type: "primary" } },
      // Co-actors
      { data: { id: "a1", label: "cryptolock99",   type: "secondary" } },
      { data: { id: "a2", label: "mixerbot_eu",    type: "secondary" } },
      { data: { id: "a3", label: "mule_acc_07",    type: "secondary" } },
      { data: { id: "a4", label: "referrer_dark",  type: "secondary" } },
      // Edges with relation labels
      { data: { id: "e1", source: "central", target: "a1", label: "co-posted"  } },
      { data: { id: "e2", source: "central", target: "a2", label: "transacted" } },
      { data: { id: "e3", source: "central", target: "a3", label: "referred"   } },
      { data: { id: "e4", source: "central", target: "a4", label: "co-posted"  } },
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: "node[type='primary']",
          style: {
            "background-color": "#F0A500",
            "label": "data(label)",
            "color": "#0D0B14",
            "font-size": "9px",
            "font-family": "JetBrains Mono, monospace",
            "font-weight": 600,
            "text-valign": "center",
            "text-halign": "center",
            "text-wrap": "wrap",
            "width": 60,
            "height": 60,
            "border-width": 0,
          },
        },
        {
          selector: "node[type='secondary']",
          style: {
            "background-color": "#1C1929",
            "border-color": "#6B4FFF",
            "border-width": 1,
            "label": "data(label)",
            "color": "#8884A8",
            "font-size": "8px",
            "font-family": "JetBrains Mono, monospace",
            "text-valign": "bottom",
            "text-margin-y": 4,
            "text-halign": "center",
            "width": 28,
            "height": 28,
          },
        },
        {
          selector: "edge",
          style: {
            "width": 1,
            "line-color": "#6B4FFF",
            "line-opacity": 0.6,
            "label": "data(label)",
            "color": "#4A4768",
            "font-size": "7px",
            "font-family": "Space Grotesk, sans-serif",
            "text-rotation": "autorotate",
            "text-margin-y": -6,
            "curve-style": "bezier",
            "target-arrow-color": "#6B4FFF",
            "target-arrow-shape": "triangle",
            "arrow-scale": 0.6,
          },
        },
      ],
      layout: {
        name: "cose",
        animate: false,
        nodeRepulsion: () => 4000,
        idealEdgeLength: () => 60,
        gravity: 0.4,
        padding: 16,
      },
      userZoomingEnabled: false,
      userPanningEnabled: false,
      boxSelectionEnabled: false,
    });

    cyRef.current = cy;
    return () => { cy.destroy(); cyRef.current = null; };
  }, []);

  return (
    <div
      ref={containerRef}
      className="w-full rounded bg-[#0D0B14] border border-[#2A2640]"
      style={{ height: "200px" }}
    />
  );
}
