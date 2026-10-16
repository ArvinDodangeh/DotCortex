"use client";

/**
 * 3D overview of pinned mastery paths (Zehnium-style spheres).
 * Falls back to a simple node grid if WebGL / force-graph fails to load.
 */

import { Component, useEffect, useMemo, useRef, type ReactNode } from "react";
import dynamic from "next/dynamic";

const ForceGraph3D = dynamic(() => import("react-force-graph-3d"), {
  ssr: false,
  loading: () => (
    <p className="flex h-full items-center justify-center text-[13px] text-[var(--muted-foreground)]">
      Loading map…
    </p>
  ),
});

const BG = "#0b0b0b";
const ACCENT = "#ff6b00";
const MUTED = "#666666";

export type MasteryGraphNode = {
  id: string;
  name: string;
  emoji?: string;
  progress: number | null;
  active?: boolean;
  x?: number;
  y?: number;
  z?: number;
  fx?: number;
  fy?: number;
  fz?: number;
};

export type MasteryGraphLink = {
  source: string;
  target: string;
  score?: number;
};

type GraphRef = {
  zoomToFit: (ms?: number, padding?: number) => void;
};

function nodeColor(node: MasteryGraphNode): string {
  if (node.active) return ACCENT;
  if (node.progress == null) return MUTED;
  if (node.progress >= 0.9) return "#39ff14";
  if (node.progress > 0) return ACCENT;
  return MUTED;
}

function placeNodes(nodes: MasteryGraphNode[]): MasteryGraphNode[] {
  const n = nodes.length;
  return nodes.map((node, index) => {
    if (
      typeof node.x === "number" &&
      typeof node.y === "number" &&
      typeof node.z === "number"
    ) {
      return { ...node, fx: node.x, fy: node.y, fz: node.z };
    }
    const angle = (index / Math.max(n, 1)) * Math.PI * 2 - Math.PI / 2;
    const radius = n <= 1 ? 0 : 40;
    const x = Math.cos(angle) * radius;
    const y = Math.sin(angle) * radius * 0.6;
    const z = Math.sin(angle * 1.3) * 18;
    return { ...node, x, y, z, fx: x, fy: y, fz: z };
  });
}

function FlatFallback({
  nodes,
  height,
  onNodeClick,
}: {
  nodes: MasteryGraphNode[];
  height: number | string;
  onNodeClick?: (pathId: string) => void;
}) {
  return (
    <div
      className="flex flex-wrap content-center items-center justify-center gap-3 p-6"
      style={{ height }}
    >
      {nodes.length === 0 ? (
        <p className="text-center text-[13px] text-[var(--muted-foreground)]">
          No paths pinned yet. Pin one on the right, or let the coach pin when you aim at a topic.
        </p>
      ) : (
        nodes.map((node) => (
          <button
            key={node.id}
            type="button"
            onClick={() => onNodeClick?.(node.id)}
            className="rounded-full border px-3 py-1.5 text-[12px]"
            style={{
              borderColor: node.active ? "var(--primary)" : "var(--border)",
              color: nodeColor(node),
              background: "var(--card)",
            }}
          >
            {node.emoji ? `${node.emoji} ` : ""}
            {node.name}
          </button>
        ))
      )}
    </div>
  );
}

class GraphErrorBoundary extends Component<
  { fallback: ReactNode; children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) return this.props.fallback;
    return this.props.children;
  }
}

function ForceGraphView({
  nodes,
  links,
  height,
  onNodeClick,
}: {
  nodes: MasteryGraphNode[];
  links: MasteryGraphLink[];
  height: number | string;
  onNodeClick?: (pathId: string) => void;
}) {
  const fgRef = useRef<GraphRef | undefined>(undefined);
  const data = useMemo(
    () => ({ nodes: placeNodes(nodes), links }),
    [nodes, links],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      fgRef.current?.zoomToFit?.(400, 80);
    }, 80);
    return () => window.clearTimeout(timer);
  }, [data.nodes.length]);

  return (
    <div className="relative h-full w-full overflow-hidden rounded-xl" style={{ height }}>
      <ForceGraph3D
        ref={fgRef}
        graphData={data}
        backgroundColor={BG}
        nodeId="id"
        nodeLabel={(node: MasteryGraphNode) =>
          `${node.emoji ? `${node.emoji} ` : ""}${node.name}`
        }
        nodeColor={nodeColor}
        nodeVal={(node: MasteryGraphNode) => (node.active ? 8 : 5)}
        nodeOpacity={0.95}
        linkColor={() => "#444444"}
        linkWidth={(link: MasteryGraphLink) =>
          0.6 + (typeof link.score === "number" ? link.score * 2 : 0)
        }
        linkOpacity={0.55}
        cooldownTicks={0}
        warmupTicks={0}
        enableNodeDrag={false}
        onNodeClick={(node: MasteryGraphNode) => onNodeClick?.(node.id)}
      />
    </div>
  );
}

export function MasteryForceMap({
  nodes,
  links = [],
  height = "100%",
  onNodeClick,
}: {
  nodes: MasteryGraphNode[];
  links?: MasteryGraphLink[];
  height?: number | string;
  onNodeClick?: (pathId: string) => void;
}) {
  if (nodes.length === 0) {
    return <FlatFallback nodes={nodes} height={height} onNodeClick={onNodeClick} />;
  }

  return (
    <GraphErrorBoundary
      fallback={<FlatFallback nodes={nodes} height={height} onNodeClick={onNodeClick} />}
    >
      <ForceGraphView
        nodes={nodes}
        links={links}
        height={height}
        onNodeClick={onNodeClick}
      />
    </GraphErrorBoundary>
  );
}
