import React, { useMemo, useRef, useEffect } from "react";
import { Box, Typography, Paper, Chip, useTheme } from "@mui/material";

/* -------------------- Tree utils -------------------- */
function buildTree(elements) {
    const nodes = {};
    elements.forEach((el) => (nodes[el.id] = { ...el, children: [] }));
    const roots = [];
    elements.forEach((el) => {
        if (el.parent && nodes[el.parent]) nodes[el.parent].children.push(nodes[el.id]);
        else roots.push(nodes[el.id]);
    });
    return roots;
}

/* -------------------- Animated vertical connector -------------------- */
function ArrowDown({ height = 40, color = "#D0D5DD" }) {
    const id = Math.random().toString(36).slice(2);
    return (
        <svg width="18" height={height} viewBox={`0 0 18 ${height}`} style={{ display: "block" }}>
            <defs>
                <style>{`
          @keyframes dash-${id} { to { stroke-dashoffset: -12; } }
        `}</style>
            </defs>
            <line
                x1="9"
                y1="0"
                x2="9"
                y2={height - 10}
                stroke={color}
                strokeWidth="2.5"
                strokeDasharray="6 6"
                style={{ animation: `dash-${id} 1.6s linear infinite` }}
            />
            <polygon points={`5,${height - 10} 9,${height} 13,${height - 10}`} fill={color} />
        </svg>
    );
}

/* -------------------- Node card -------------------- */
function NodeCard({ node }) {
    const theme = useTheme();
    const border = theme.palette.divider;
    const text = theme.palette.text.primary;
    const bg = theme.palette.background.paper;

    const base = {
        p: 2,
        minWidth: { xs: 200, sm: 240 },
        maxWidth: { xs: 300, sm: 350 },
        width: "auto",
        textAlign: "center",
        position: "relative",
        border: `1px solid ${border}`,
        bgcolor: bg,
        boxShadow: "0 6px 22px rgba(0,0,0,0.06)",
        transition: "transform .15s ease, box-shadow .15s ease",
        "&:hover": {
            transform: "translateY(-2px)",
            boxShadow: "0 12px 28px rgba(0,0,0,0.10)",
        },
    };

    const color = {
        start: theme.palette.success.main,
        end: theme.palette.error.main,
        decision: theme.palette.warning.main,
        process: theme.palette.primary.main,
    }[node.type] || theme.palette.grey[700];

    const shape = {
        start: { borderRadius: 999 },
        end: { borderRadius: 999 },
        process: { borderRadius: 14 },
        decision: { 
            borderRadius: 8,
            border: `2px dashed ${color}`,
        },
    }[node.type] || { borderRadius: 12 };

    return (
        <Paper elevation={0} sx={{ ...base, ...shape }}>
            <Typography 
                variant="subtitle1" 
                sx={{ 
                    fontWeight: 700, 
                    color: text, 
                    mb: 1,
                    wordBreak: "break-word",
                    overflowWrap: "break-word",
                    hyphens: "auto",
                    lineHeight: 1.4,
                    fontSize: { xs: "1rem", sm: "1.1rem" },
                    whiteSpace: "normal",
                    overflow: "visible",
                    textOverflow: "clip",
                    display: "block",
                    width: "100%"
                }}
            >
                {node.label}
            </Typography>
            <Chip
                size="small"
                label={node.type}
                sx={{ fontWeight: 700, color: "#fff", bgcolor: color, textTransform: "none" }}
            />
        </Paper>
    );
}

/* -------------------- Recursive renderer -------------------- */
function NodeTree({ node }) {
    const theme = useTheme();
    const divider = theme.palette.divider;
    const kids = node.children || [];
    const isBranch = kids.length > 1;

    return (
        <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", mb: 1.5 }}>
            <NodeCard node={node} />

            {kids.length > 0 && (
                <Box sx={{ height: 12, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <ArrowDown height={18} color={divider} />
                </Box>
            )}

            {/* Straight chain */}
            {kids.length === 1 && <NodeTree node={kids[0]} />}

            {/* Branching row */}
            {isBranch && (
                <Box sx={{ width: "100%", maxWidth: "100%" }}>
                    {/* spine line */}
                    <Box sx={{ position: "relative", height: 12, mb: 0.125 }}>
                        <Box sx={{ position: "absolute", inset: 0, top: 12, borderTop: `2px solid ${divider}` }} />
                    </Box>

                    <Box
                        sx={{
                            display: "grid",
                            gridTemplateColumns: `repeat(${kids.length}, 1fr)`,
                            columnGap: { xs: 1, sm: 2, md: 3 },
                            alignItems: "start",
                            px: { xs: 1, sm: 2 }
                        }}
                    >
                        {kids.map((child, idx) => (
                            <Box key={child.id} sx={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                                {/* drop line */}
                                <ArrowDown height={16} color={divider} />

                                {/* auto Yes/No labels for a 2-way decision */}
                                {node.type === "decision" && kids.length === 2 && (
                                    <Chip
                                        size="small"
                                        label={idx === 0 ? "No" : "Yes"}
                                        sx={{
                                            mb: 1,
                                            fontWeight: 700,
                                            bgcolor: idx === 0 ? theme.palette.error.light : theme.palette.success.light,
                                        }}
                                    />
                                )}

                                <NodeTree node={child} />
                            </Box>
                        ))}
                    </Box>
                </Box>
            )}
        </Box>
    );
}

/* -------------------- Top-level component -------------------- */
const VisualFlowchart = ({ data }) => {
    const theme = useTheme();
    const roots = useMemo(() => (data?.elements?.length ? buildTree(data.elements) : []), [data]);
    const scrollContainerRef = useRef(null);
    const firstNodeRef = useRef(null);

    // Auto-scroll to center the first node on load and when sidebar changes
    useEffect(() => {
        const centerFirstNode = () => {
            if (scrollContainerRef.current && firstNodeRef.current) {
                const container = scrollContainerRef.current;
                const firstNode = firstNodeRef.current.firstElementChild;

                if (firstNode) {
                    // Get the bounding rectangles
                    const containerRect = container.getBoundingClientRect();
                    const nodeRect = firstNode.getBoundingClientRect();

                    // Calculate scroll position to center the node
                    const scrollPosition = container.scrollLeft + nodeRect.left - containerRect.left - (containerRect.width / 2) + (nodeRect.width / 2);

                    container.scrollLeft = scrollPosition;
                }
            }
        };

        // Initial centering with delay for rendering
        const timer = setTimeout(centerFirstNode, 150);

        // Re-center on window resize (includes sidebar open/close)
        window.addEventListener('resize', centerFirstNode);

        // Re-center after transitions complete
        const transitionTimer = setTimeout(centerFirstNode, 400);

        return () => {
            clearTimeout(timer);
            clearTimeout(transitionTimer);
            window.removeEventListener('resize', centerFirstNode);
        };
    }, [data]);

    if (!data?.elements?.length) {
        return (
            <Box sx={{ p: 3, textAlign: "center" }}>
                <Typography variant="body1" color="text.secondary">
                    No visual data available.
                </Typography>
            </Box>
        );
    }

    return (
        <Box
            sx={{
                width: "100%",
                p: { xs: 1, md: 2 },
            }}
        >
            {/* Header */}
            <Paper
                variant="outlined"
                sx={{
                    mb: 1,
                    p: 1.5,
                    textAlign: "center",
                    borderColor: theme.palette.divider,
                    background:
                        theme.palette.mode === "dark"
                            ? "linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03))"
                            : "linear-gradient(180deg,#ffffff,#f7f7f7)",
                }}
            >
                <Typography variant="h4" sx={{ fontWeight: 900, mb: 1 }}>
                    📊 {data.title || "Flowchart"}
                </Typography>
                {data.description && (
                    <Typography variant="body1" color="text.secondary">
                        {data.description}
                    </Typography>
                )}
                <Chip
                    size="small"
                    label={data.visual_type || "flowchart"}
                    sx={{ mt: 2, fontWeight: 800, color: "#fff", bgcolor: theme.palette.primary.main }}
                />
            </Paper>

            {/* Body */}
            <Box
                ref={scrollContainerRef}
                sx={{
                    width: "100%",
                    overflowX: "auto",
                    overflowY: "visible",
                }}
            >
                <Box sx={{
                    display: "inline-flex",
                    flexDirection: "column",
                    alignItems: "center",
                    px: { xs: 1, sm: 2 },
                    minWidth: "100%",
                }}>
                    <Box ref={firstNodeRef}>
                        {roots.map((root) => (
                            <NodeTree key={root.id} node={root} />
                        ))}
                    </Box>
                </Box>
            </Box>
        </Box>
    );
};

export default VisualFlowchart;
