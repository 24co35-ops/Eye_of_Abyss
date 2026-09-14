"use client";

import React, { useEffect, useRef } from "react";
import cytoscape from "cytoscape";
import { ZoomIn, ZoomOut, Maximize2, Download } from "lucide-react";

interface WalletClusterGraphProps {
  suspectAddress?: string;
  onSelectNode?: (nodeId: string) => void;
}

export function WalletClusterGraph({
  suspectAddress = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
  onSelectNode,
}: WalletClusterGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const elements = [
      // Central Suspect Node
      {
        data: {
          id: "suspect",
          label: "SUSPECT WALLET\n1BvBMSEYst...",
          fullAddress: suspectAddress,
          type: "suspect",
          bg: "#F0A500",
          color: "#0D0B14",
          shape: "ellipse",
          size: 64,
        },
      },
      // 2 Binance Exchange nodes (indigo, diamond/rectangle)
      {
        data: {
          id: "binance_1",
          label: "BINANCE (Hot 14)\n0x71C...498B",
          type: "exchange",
          bg: "#6B4FFF",
          color: "#E8E6F2",
          shape: "round-rectangle",
          size: 48,
        },
      },
      {
        data: {
          id: "binance_2",
          label: "BINANCE (Deposit)\n0x38a...991c",
          type: "exchange",
          bg: "#6B4FFF",
          color: "#E8E6F2",
          shape: "round-rectangle",
          size: 44,
        },
      },
      // 2 Mixer nodes (crimson)
      {
        data: {
          id: "mixer_1",
          label: "MIXER (Wasabi Pool)\nbc1q99...mix",
          type: "mixer",
          bg: "#C92A2A",
          color: "#E8E6F2",
          shape: "ellipse",
          size: 46,
        },
      },
      {
        data: {
          id: "mixer_2",
          label: "MIXER (CoinJoin)\nbc1q7a...hop",
          type: "mixer",
          bg: "#C92A2A",
          color: "#E8E6F2",
          shape: "ellipse",
          size: 44,
        },
      },
      // 1 Mule wallet (muted crimson)
      {
        data: {
          id: "mule_1",
          label: "MULE WALLET\n0x918...42a1",
          type: "mule",
          bg: "#8A2B2B",
          color: "#E8E6F2",
          shape: "ellipse",
          size: 40,
        },
      },
      // 1 Unknown wallet (muted grey)
      {
        data: {
          id: "unknown_1",
          label: "UNKNOWN\n1A1zP...839b",
          type: "unknown",
          bg: "#4A4768",
          color: "#E8E6F2",
          shape: "ellipse",
          size: 38,
        },
      },

      // Edges with BTC amount labels
      { data: { id: "e1", source: "suspect", target: "binance_1", label: "2.10 BTC" } },
      { data: { id: "e2", source: "suspect", target: "binance_2", label: "1.20 BTC" } },
      { data: { id: "e3", source: "suspect", target: "mixer_1", label: "0.85 BTC" } },
      { data: { id: "e4", source: "mixer_1", target: "mixer_2", label: "0.43 BTC" } },
      { data: { id: "e5", source: "suspect", target: "mule_1", label: "0.15 BTC" } },
      { data: { id: "e6", source: "mule_1", target: "unknown_1", label: "0.05 BTC" } },
    ];

    try {
      cyRef.current = cytoscape({
        container: containerRef.current,
        elements,
        style: [
          {
            selector: "node",
            style: {
              label: "data(label)",
              "background-color": "data(bg)",
              color: "data(color)",
              shape: "data(shape)",
              width: "data(size)",
              height: "data(size)",
              "font-family": "Space Grotesk, sans-serif",
              "font-size": "9px",
              "font-weight": 600,
              "text-valign": "center",
              "text-halign": "center",
              "text-wrap": "wrap",
              "text-max-width": "80px",
              "border-width": 1.5,
              "border-color": "#2A2640",
            },
          },
          {
            selector: "node[id = 'suspect']",
            style: {
              "border-color": "#F0A500",
              "border-width": 2.5,
              "font-size": "10px",
            },
          },
          {
            selector: "edge",
            style: {
              width: 1.5,
              "line-color": "#2A2640",
              "target-arrow-color": "#6B4FFF",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              label: "data(label)",
              "font-family": "JetBrains Mono, monospace",
              "font-size": "8px",
              color: "#8884A8",
              "text-background-color": "#13111E",
              "text-background-opacity": 0.85,
              "text-background-padding": "2px",
              "text-background-shape": "roundrectangle",
            },
          },
        ],
        layout: {
          name: "concentric",
          concentric: (node: any) => (node.id() === "suspect" ? 2 : 1),
          levelWidth: () => 1,
          padding: 30,
          minNodeSpacing: 50,
        },
        userZoomingEnabled: true,
        userPanningEnabled: true,
        boxSelectionEnabled: false,
      });

      cyRef.current.on("tap", "node", (evt: any) => {
        const node = evt.target;
        if (onSelectNode) onSelectNode(node.id());
      });
    } catch {
      // Fallback
    }

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [suspectAddress, onSelectNode]);

  const [minAmount, setMinAmount] = React.useState<number>(0);
  const [highlightMixers, setHighlightMixers] = React.useState<boolean>(false);

  useEffect(() => {
    if (!cyRef.current) return;
    // Apply highlight mixers style dynamically
    cyRef.current.nodes().forEach((n: any) => {
      if (n.data("type") === "mixer") {
        if (highlightMixers) {
          n.style({
            "border-color": "#FF4444",
            "border-width": 3.5,
            "shadow-blur": 15,
            "shadow-color": "#FF4444",
            "shadow-opacity": 0.8,
          });
        } else {
          n.style({
            "border-color": "#2A2640",
            "border-width": 1.5,
            "shadow-blur": 0,
            "shadow-opacity": 0,
          });
        }
      }
    });
  }, [highlightMixers]);

  const handleZoomIn = () => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current && cyRef.current.fit(undefined, 30);
  
  const handleExportPNG = () => {
    if (!cyRef.current) return;
    const png = cyRef.current.png({ full: true });
    const a = document.createElement("a");
    a.href = png;
    a.download = `wallet_graph_${suspectAddress.slice(0, 8)}.png`;
    a.click();
  };

  const handleExportJSON = () => {
    if (!cyRef.current) return;
    const jsonStr = JSON.stringify(cyRef.current.json(), null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `wallet_graph_${suspectAddress.slice(0, 8)}.json`;
    a.click();
  };

  const handleExportGraphML = () => {
    if (!cyRef.current) return;
    const nodes = cyRef.current.nodes();
    const edges = cyRef.current.edges();
    let graphml = `<?xml version="1.0" encoding="UTF-8"?>\n<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n  <graph id="ChainEyeGraph" edgedefault="directed">\n`;
    nodes.forEach((n: any) => {
      graphml += `    <node id="${n.id()}"/>\n`;
    });
    edges.forEach((e: any) => {
      graphml += `    <edge id="${e.id()}" source="${e.source().id()}" target="${e.target().id()}"/>\n`;
    });
    graphml += `  </graph>\n</graphml>`;
    const blob = new Blob([graphml], { type: "application/xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `wallet_graph_${suspectAddress.slice(0, 8)}.graphml`;
    a.click();
  };

  return (
    <div className="relative w-full h-[380px] bg-void border border-mist rounded-[4px] overflow-hidden select-none">
      {/* Top bar over graph */}
      <div className="absolute top-2.5 left-3 right-3 flex items-center justify-between z-10 pointer-events-none">
        <div className="bg-shadow/80 border border-mist px-2.5 py-1 rounded-[4px] text-[11px] font-mono text-text-secondary flex items-center gap-2 pointer-events-auto">
          <span className="w-1.5 h-1.5 rounded-full bg-gaze" />
          <span>CENTRAL SUSPECT:</span>
          <span className="text-text-primary font-medium">{suspectAddress}</span>
        </div>

        {/* Graph Controls & Filters */}
        <div className="flex items-center gap-1.5 pointer-events-auto bg-shadow border border-mist rounded-[4px] p-1">
          {/* Highlight Mixers toggle */}
          <button
            onClick={() => setHighlightMixers(!highlightMixers)}
            className={`px-2 py-0.5 text-[10px] font-mono rounded transition-colors flex items-center gap-1 ${
              highlightMixers ? "bg-[#C92A2A] text-white" : "text-[#8884A8] hover:text-[#E8E6F2] hover:bg-[#2A2640]"
            }`}
            title="Highlight Wasabi / Tornado mixers"
          >
            🔥 Mixers
          </button>

          {/* Amount Filter */}
          <div className="flex items-center gap-1 px-1.5 py-0.5 border-l border-r border-[#2A2640] text-[10px] font-mono text-[#8884A8]">
            <span>&gt;=</span>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={minAmount}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                setMinAmount(val);
                if (cyRef.current) {
                  cyRef.current.edges().forEach((edge: any) => {
                    const label = edge.data("label") || "0";
                    const btc = parseFloat(label.replace(" BTC", "")) || 0;
                    edge.style("display", btc >= val ? "element" : "none");
                  });
                }
              }}
              className="w-14 h-1 accent-[#F0A500]"
            />
            <span className="text-[#F0A500]">{minAmount} BTC</span>
          </div>

          <button
            onClick={handleZoomIn}
            className="w-6 h-6 flex items-center justify-center text-text-secondary hover:text-text-primary rounded-[2px] transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleZoomOut}
            className="w-6 h-6 flex items-center justify-center text-text-secondary hover:text-text-primary rounded-[2px] transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleFit}
            className="w-6 h-6 flex items-center justify-center text-text-secondary hover:text-text-primary rounded-[2px] transition-colors"
            title="Fit to Screen"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>

          {/* Export Dropdown / Buttons */}
          <div className="flex items-center gap-0.5 border-l border-[#2A2640] pl-1">
            <button
              onClick={handleExportPNG}
              className="px-1.5 py-0.5 text-[9px] font-mono text-[#8884A8] hover:text-[#E8E6F2] hover:bg-[#2A2640] rounded transition-colors"
              title="Export PNG"
            >
              PNG
            </button>
            <button
              onClick={handleExportJSON}
              className="px-1.5 py-0.5 text-[9px] font-mono text-[#8884A8] hover:text-[#E8E6F2] hover:bg-[#2A2640] rounded transition-colors"
              title="Export JSON"
            >
              JSON
            </button>
            <button
              onClick={handleExportGraphML}
              className="px-1.5 py-0.5 text-[9px] font-mono text-[#8884A8] hover:text-[#E8E6F2] hover:bg-[#2A2640] rounded transition-colors"
              title="Export GraphML"
            >
              GraphML
            </button>
          </div>
        </div>
      </div>

      {/* Cytoscape Canvas */}
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Graph Legend */}
      <div className="absolute bottom-2 left-3 flex items-center gap-3 bg-shadow/80 border border-mist px-2 py-1 rounded-[4px] text-[9px] font-mono text-text-secondary">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-gaze" /> Suspect
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-[2px] bg-signal" /> Binance (Exchange)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-threat" /> Mixer / Wasabi
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-[#8A2B2B]" /> Mule
        </span>
      </div>
    </div>
  );
}
