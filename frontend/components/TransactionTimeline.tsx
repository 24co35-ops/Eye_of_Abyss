"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ReferenceArea,
} from "recharts";

// Synthetic 30-day transaction flow data
const TIMELINE_DATA = Array.from({ length: 30 }, (_, i) => {
  const day = i + 1;
  const isComplaint = day === 22;
  const isDormant = day > 15 && day < 28;
  const inflow = day === 5 ? 1.8 : day === 12 ? 2.4 : day === 20 ? 0.53 : isDormant ? 0.02 : (Math.sin(day) * 0.3 + 0.4);
  const outflow = day === 6 ? 0.9 : day === 13 ? 1.2 : day === 29 ? 2.8 : isDormant ? 0.01 : (Math.cos(day) * 0.2 + 0.3);

  return {
    day: `Day ${day}`,
    dayNum: day,
    inflow: Math.max(0, parseFloat(inflow.toFixed(2))),
    outflow: Math.max(0, parseFloat(outflow.toFixed(2))),
    date: `Aug ${day}`,
  };
});

export function TransactionTimeline() {
  return (
    <div className="bg-void border border-mist rounded-[4px] p-3 space-y-2 select-none">
      {/* Timeline Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-text-primary tracking-tight">
            Transaction Timeline
          </span>
          <span className="text-[10px] font-mono text-text-muted">
            30-DAY INFLOW VS OUTFLOW DYNAMICS
          </span>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 text-[10px] font-mono">
          <span className="flex items-center gap-1.5 text-signal">
            <span className="w-2.5 h-2.5 bg-signal rounded-[1px]" /> Inflow (BTC)
          </span>
          <span className="flex items-center gap-1.5 text-gaze">
            <span className="w-2.5 h-2.5 bg-gaze rounded-[1px]" /> Outflow (BTC)
          </span>
          <span className="flex items-center gap-1.5 text-threat">
            <span className="w-2.5 h-0.5 bg-threat" /> Complaint Filed (D22)
          </span>
          <span className="flex items-center gap-1.5 text-gaze font-bold">
            <span className="w-2.5 h-0.5 bg-gaze" /> Predicted Window (D28)
          </span>
        </div>
      </div>

      {/* Recharts Bar Container */}
      <div className="w-full h-36">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={TIMELINE_DATA} margin={{ top: 12, right: 10, left: -25, bottom: 0 }}>
            <XAxis
              dataKey="date"
              stroke="#4A4768"
              fontSize={9}
              tickLine={false}
              interval={4}
              fontFamily="JetBrains Mono"
            />
            <YAxis
              stroke="#4A4768"
              fontSize={9}
              tickLine={false}
              axisLine={false}
              fontFamily="JetBrains Mono"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1C1929",
                borderColor: "#2A2640",
                borderRadius: "4px",
                fontSize: "10px",
                fontFamily: "JetBrains Mono",
                color: "#E8E6F2",
              }}
              cursor={{ fill: "rgba(42, 38, 64, 0.4)" }}
            />

            {/* Shaded amber band around predicted window (Day 27.5 to 28.5) */}
            <ReferenceArea
              x1="Aug 27"
              x2="Aug 29"
              fill="#F0A500"
              fillOpacity={0.12}
              stroke="#F0A500"
              strokeOpacity={0.4}
              strokeDasharray="2 2"
            />

            {/* Red Line: Complaint Filed (Day 22) */}
            <ReferenceLine
              x="Aug 22"
              stroke="#C92A2A"
              strokeWidth={1.5}
              label={{
                value: "Complaint Filed",
                position: "top",
                fill: "#C92A2A",
                fontSize: 9,
                fontFamily: "Space Grotesk",
                fontWeight: 600,
              }}
            />

            {/* Amber Line: Predicted Window (Day 28) */}
            <ReferenceLine
              x="Aug 28"
              stroke="#F0A500"
              strokeWidth={1.5}
              label={{
                value: "Predicted Window (±12h)",
                position: "top",
                fill: "#F0A500",
                fontSize: 9,
                fontFamily: "Space Grotesk",
                fontWeight: 600,
              }}
            />

            {/* Bars */}
            <Bar dataKey="inflow" fill="#6B4FFF" radius={[2, 2, 0, 0]} maxBarSize={8} />
            <Bar dataKey="outflow" fill="#F0A500" radius={[2, 2, 0, 0]} maxBarSize={8} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
