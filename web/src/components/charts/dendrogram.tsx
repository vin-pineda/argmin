"use client";

import { Group } from "@visx/group";
import { hierarchy } from "@visx/hierarchy";
import { scaleLinear } from "@visx/scale";
import { useMemo } from "react";

import { ChartFrame, tickLabelProps } from "@/components/charts/frame";
import { num } from "@/lib/format";

/** Raw HRP linkage tree shape from the engine. Leaves carry a ticker name + vol;
 *  internal nodes carry the cluster linkage distance as `height`. */
export interface HrpNode {
  name: string;
  height?: number;
  vol?: number;
  children?: HrpNode[];
}

interface Positioned {
  x: number; // horizontal coordinate (leaf-order axis)
  y: number; // vertical coordinate from linkage height
  node: HrpNode;
  children?: Positioned[];
}

function Dendro({
  tree,
  width,
  height,
}: {
  tree: HrpNode;
  width: number;
  height: number;
}) {
  const margin = { top: 14, right: 14, bottom: 40, left: 36 };
  const innerW = Math.max(0, width - margin.left - margin.right);
  const innerH = Math.max(0, height - margin.top - margin.bottom);

  const { positioned, leaves, maxHeight } = useMemo(() => {
    const root = hierarchy<HrpNode>(tree, (d) => d.children);
    const leafNodes = root.leaves();
    const n = leafNodes.length;
    // Assign each leaf an index in traversal order (== HRP quasi-diagonal order).
    const leafIndex = new Map<HrpNode, number>();
    leafNodes.forEach((l, i) => leafIndex.set(l.data, i));

    let hMax = 0;
    root.each((d) => {
      if (d.data.height && d.data.height > hMax) hMax = d.data.height;
    });

    const xScale = scaleLinear<number>({
      domain: [0, Math.max(1, n - 1)],
      range: [0, innerW],
    });
    const yScale = scaleLinear<number>({
      // root (largest height) at the top, leaves (height 0) at the bottom.
      domain: [0, hMax || 1],
      range: [innerH, 0],
    });

    // Recursively position: leaf x from its index; internal x = mean of children x.
    function place(d: typeof root): Positioned {
      const data = d.data;
      if (!d.children || d.children.length === 0) {
        const idx = leafIndex.get(data) ?? 0;
        return { x: xScale(idx), y: innerH, node: data };
      }
      const kids = d.children.map(place);
      const x = kids.reduce((s, k) => s + k.x, 0) / kids.length;
      const y = yScale(data.height ?? 0);
      return { x, y, node: data, children: kids };
    }

    return {
      positioned: place(root),
      leaves: leafNodes.map((l) => ({
        x: xScale(leafIndex.get(l.data) ?? 0),
        ticker: l.data.name,
        vol: l.data.vol,
      })),
      maxHeight: hMax,
    };
  }, [tree, innerW, innerH]);

  // Draw bracket links (elbow): each internal node connects to children with a
  // horizontal bar at the parent height, then vertical drops to each child.
  const links: { d: string; key: string }[] = [];
  function walk(p: Positioned) {
    if (!p.children) return;
    const xs = p.children.map((c) => c.x);
    const xLeft = Math.min(...xs);
    const xRight = Math.max(...xs);
    links.push({ key: `bar-${p.x}-${p.y}`, d: `M ${xLeft} ${p.y} H ${xRight}` });
    for (const c of p.children) {
      links.push({ key: `drop-${c.x}-${c.y}`, d: `M ${c.x} ${p.y} V ${c.y}` });
      walk(c);
    }
  }
  walk(positioned);

  const yAxis = scaleLinear<number>({
    domain: [0, maxHeight || 1],
    range: [innerH, 0],
  });
  const yTicks = yAxis.ticks(4);

  return (
    <svg width={width} height={height} role="img" aria-label="HRP linkage dendrogram">
      <Group left={margin.left} top={margin.top}>
        {/* distance axis */}
        {yTicks.map((t) => (
          <g key={`yt-${t}`}>
            <line
              x1={-4}
              x2={innerW}
              y1={yAxis(t)}
              y2={yAxis(t)}
              stroke="var(--color-grid)"
              strokeWidth={1}
            />
            <text x={-8} y={yAxis(t)} textAnchor="end" dominantBaseline="middle" {...tickLabelProps()}>
              {num(t, 2)}
            </text>
          </g>
        ))}

        {/* linkage brackets */}
        {links.map((l) => (
          <path
            key={l.key}
            d={l.d}
            fill="none"
            stroke="var(--color-line-strong)"
            strokeWidth={1.25}
          />
        ))}

        {/* leaf ticks + labels */}
        {leaves.map((leaf) => (
          <g key={`leaf-${leaf.ticker}`}>
            <circle cx={leaf.x} cy={innerH} r={2.5} fill="var(--color-accent)" />
            <text
              x={leaf.x}
              y={innerH + 16}
              textAnchor="middle"
              fill="var(--color-fg-dim)"
              fontSize={10}
              fontFamily="var(--font-plex-mono)"
            >
              {leaf.ticker}
            </text>
            {leaf.vol != null ? (
              <text
                x={leaf.x}
                y={innerH + 28}
                textAnchor="middle"
                fill="var(--color-fg-faint)"
                fontSize={9}
                fontFamily="var(--font-plex-mono)"
              >
                {num(leaf.vol * 100, 0)}%
              </text>
            ) : null}
          </g>
        ))}
      </Group>

      {/* axis caption */}
      <text
        x={12}
        y={14}
        fill="var(--color-fg-faint)"
        fontSize={10.5}
        fontFamily="var(--font-plex-mono)"
      >
        linkage distance
      </text>
    </svg>
  );
}

export function Dendrogram({
  tree,
  order,
}: {
  tree: HrpNode;
  order?: string[];
}) {
  return (
    <div className="flex flex-col gap-3">
      <ChartFrame height={300} className="rounded-[var(--radius)] border border-line p-1">
        {({ width, height }) => <Dendro tree={tree} width={width} height={height} />}
      </ChartFrame>
      {order ? (
        <p className="text-[12px] leading-relaxed text-fg-faint">
          Leaves are ordered by recursive agglomeration so that adjacent assets are the most
          correlated, the <span className="text-fg-dim">quasi-diagonal</span> sequence{" "}
          <span className="tnum text-fg-dim">{order.join(" → ")}</span>. Each leaf is
          annotated with its annualized volatility; bracket height is the cluster linkage
          distance.
        </p>
      ) : null}
    </div>
  );
}
