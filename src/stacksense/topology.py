"""Architecture topology diagram generator for StackSense.

Generates deterministic systems architecture diagrams in two formats:
1. Mermaid.js flowchart syntax (`graph TD`) for interactive browser rendering and export.
2. Self-contained vector SVG using pure Python with a fixed 5-tier vertical layout,
   enabling zero-dependency offline rendering and headless PDF report embedding.
"""

import html
from typing import Any, Optional

from stacksense.models.enums import EngineStatus
from stacksense.models.output import ScenarioOutput


def sanitize_node_label(label: str) -> str:
    """Strips quotes, brackets, and escapes HTML characters for Mermaid and SVG compatibility."""
    if not label:
        return ""
    cleaned = (
        label.replace('"', "'")
        .replace("[", "(")
        .replace("]", ")")
        .replace("{", "(")
        .replace("}", ")")
        .replace("`", "")
    )
    return html.escape(cleaned.strip())


def generate_topology_mermaid(
    output: ScenarioOutput,
    scenario_input: Optional[dict[str, Any]] = None,
) -> str:
    """Generates a deterministic 5-tier Mermaid flowchart string from ScenarioOutput."""
    # Defensive null-safety guard
    if output.stack is None or output.status in (EngineStatus.INFEASIBLE, EngineStatus.INVALID_INPUT):
        reason = sanitize_node_label(output.summary or "Infeasible requirements detected")
        return (
            "graph TD\n"
            f'    Infeasible["⚠️ Infeasible Architecture - {reason}"]\n'
            "    style Infeasible fill:#1c1917,stroke:#dc2626,stroke-width:2px,color:#f87171"
        )

    lines = ["graph TD"]
    stack = output.stack
    project_input = (scenario_input or {}).get("project", {})
    platforms = project_input.get("platforms", [])

    # Tier 1: Client Layer
    client_nodes: list[str] = []
    lines.append('    subgraph Clients["Client Tier"]')
    if not platforms or "web" in platforms:
        fe_choice = sanitize_node_label(stack.frontend.choice) if stack.frontend.choice != "None" else "Web Browser"
        lines.append(f'        C_Web["Web Client ({fe_choice})"]')
        client_nodes.append("C_Web")
    if "android" in platforms:
        lines.append('        C_Android["Android Mobile App"]')
        client_nodes.append("C_Android")
    if "ios" in platforms:
        lines.append('        C_IOS["iOS Mobile App"]')
        client_nodes.append("C_IOS")
    if "desktop" in platforms:
        lines.append('        C_Desktop["Desktop App"]')
        client_nodes.append("C_Desktop")
    if not client_nodes:
        fe_choice = sanitize_node_label(stack.frontend.choice)
        lines.append(f'        C_Client["Client ({fe_choice})"]')
        client_nodes.append("C_Client")
    lines.append("    end")

    # Tier 2: Edge & Ingress Tier
    edge_node = "Edge_Ingress"
    hosting_choice = sanitize_node_label(stack.hosting.choice)
    cdn_choice = None
    for sup in stack.supporting:
        if sup.layer in ("cdn", "edge"):
            cdn_choice = sanitize_node_label(sup.choice)
            break

    edge_label = cdn_choice or f"Edge CDN & Ingress ({hosting_choice})"
    lines.append('    subgraph Edge["Edge & Security Tier"]')
    lines.append(f'        {edge_node}["{edge_label}"]')
    lines.append("    end")

    # Tier 3: Compute & Application Tier
    has_compute = stack.backend.choice != "None"
    compute_node = "App_Compute"
    if has_compute:
        be_choice = sanitize_node_label(stack.backend.choice)
        lines.append('    subgraph Compute["Application & Compute Tier"]')
        lines.append(f'        {compute_node}["{be_choice} on {hosting_choice}"]')
        lines.append("    end")

    # Tier 4: Persistence Tier
    has_db = stack.database.choice != "None"
    db_node = "Primary_DB"
    cache_node = "Cache_DB"
    has_cache = any(s.layer == "cache" for s in stack.supporting)
    cache_choice = next((sanitize_node_label(s.choice) for s in stack.supporting if s.layer == "cache"), "In-Memory Cache")

    if has_db or has_cache:
        lines.append('    subgraph Persistence["Persistence & Cache Tier"]')
        if has_db:
            db_choice = sanitize_node_label(stack.database.choice)
            lines.append(f'        {db_node}[("Primary DB: {db_choice}")]')
        if has_cache:
            lines.append(f'        {cache_node}[("Cache: {cache_choice}")]')
        lines.append("    end")

    # Tier 5: Asynchronous & Supporting Services Tier
    async_nodes: list[tuple[str, str, str]] = []
    for idx, sup in enumerate(stack.supporting):
        if sup.layer in ("queue", "worker"):
            async_nodes.append((f"Async_Queue_{idx}", sanitize_node_label(sup.choice), "Job Queue"))
        elif sup.layer in ("search",):
            async_nodes.append((f"Async_Search_{idx}", sanitize_node_label(sup.choice), "Search Engine"))
        elif sup.layer in ("payments",):
            async_nodes.append((f"Async_Pay_{idx}", sanitize_node_label(sup.choice), "Payment Gateway"))
        elif sup.layer in ("auth",) and "Entra" in sup.choice:
            async_nodes.append((f"Async_Auth_{idx}", sanitize_node_label(sup.choice), "Identity Provider"))

    if async_nodes:
        lines.append('    subgraph Async["Asynchronous & External Tier"]')
        for node_id, choice, label in async_nodes:
            lines.append(f'        {node_id}["{label}: {choice}"]')
        lines.append("    end")

    # Connections and Protocols
    for c in client_nodes:
        lines.append(f"    {c} -->|HTTPS / TLS 1.3| {edge_node}")

    target_app = compute_node if has_compute else (db_node if has_db else None)
    if target_app:
        protocol = "HTTP/2 REST / GraphQL"
        if any(s.layer == "realtime" for s in stack.supporting):
            protocol = "HTTPS / WSS - WebSocket"
        lines.append(f"    {edge_node} -->|{protocol}| {target_app}")

    if has_compute and has_db:
        lines.append(f"    {compute_node} -->|TCP / SSL| {db_node}")

    if has_compute and has_cache:
        lines.append(f"    {compute_node} -->|In-Memory Buffer| {cache_node}")

    if has_compute:
        for node_id, _, label in async_nodes:
            if "Queue" in label:
                lines.append(f"    {compute_node} -->|AMQP / Async Dispatch| {node_id}")
            elif "Search" in label:
                lines.append(f"    {compute_node} -->|Search Index / Query| {node_id}")
            else:
                lines.append(f"    {compute_node} -->|Outbound Webhook| {node_id}")

    return "\n".join(lines)


def generate_topology_svg(
    output: ScenarioOutput,
    scenario_input: Optional[dict[str, Any]] = None,
) -> str:
    """Generates a deterministic, self-contained SVG diagram using pure Python."""
    # Defensive null-safety guard
    if output.stack is None or output.status in (EngineStatus.INFEASIBLE, EngineStatus.INVALID_INPUT):
        reason = sanitize_node_label(output.summary or "Infeasible requirements detected")
        return f"""<svg viewBox="0 0 800 240" xmlns="http://www.w3.org/2000/svg" font-family="Geist, -apple-system, sans-serif">
  <rect width="100%" height="100%" fill="#090d16" rx="12"/>
  <rect x="50" y="50" width="700" height="140" fill="#18181b" stroke="#dc2626" stroke-width="2" rx="8"/>
  <text x="400" y="105" text-anchor="middle" fill="#f87171" font-size="16" font-weight="600">⚠️ Infeasible Architecture Specification</text>
  <text x="400" y="145" text-anchor="middle" fill="#a1a1aa" font-size="13">{reason}</text>
</svg>"""

    stack = output.stack
    project_input = (scenario_input or {}).get("project", {})
    platforms = project_input.get("platforms", [])
    if not platforms:
        platforms = ["web"]

    # Tier specifications
    tiers: list[dict[str, Any]] = []

    # 1. Clients
    client_boxes = []
    for p in platforms:
        client_boxes.append(f"{p.capitalize()} Client")
    tiers.append({"title": "CLIENT TIER", "y": 40, "boxes": client_boxes, "color": "#818cf8"})

    # 2. Edge
    edge_label = "Edge CDN & Ingress"
    for s in stack.supporting:
        if s.layer in ("cdn", "edge"):
            edge_label = s.choice
            break
    tiers.append({"title": "EDGE & INGRESS TIER", "y": 150, "boxes": [edge_label], "color": "#06b6d4"})

    # 3. Compute
    compute_boxes = []
    if stack.backend.choice != "None":
        compute_boxes.append(f"{stack.backend.choice} ({stack.hosting.choice})")
    tiers.append({"title": "COMPUTE & APPLICATION TIER", "y": 260, "boxes": compute_boxes or ["Static Edge Serving"], "color": "#10b981"})

    # 4. Persistence
    persistence_boxes = []
    if stack.database.choice != "None":
        persistence_boxes.append(f"DB: {stack.database.choice}")
    for s in stack.supporting:
        if s.layer == "cache":
            persistence_boxes.append(f"Cache: {s.choice}")
    tiers.append({"title": "PERSISTENCE & CACHE TIER", "y": 370, "boxes": persistence_boxes or ["Stateless (No Database)"], "color": "#f59e0b"})

    # 5. Async / Supporting
    async_boxes = []
    for s in stack.supporting:
        if s.layer in ("queue", "search", "payments", "auth"):
            async_boxes.append(f"{s.layer.capitalize()}: {s.choice}")
    if async_boxes:
        tiers.append({"title": "ASYNC & EXTERNAL SERVICES", "y": 480, "boxes": async_boxes[:3], "color": "#a855f7"})

    total_height = 580 if len(tiers) > 4 else 480
    svg_parts = [
        f'<svg viewBox="0 0 800 {total_height}" xmlns="http://www.w3.org/2000/svg" font-family="Geist, -apple-system, sans-serif">',
        '  <defs>',
        '    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1"/>',
        '    </marker>',
        '  </defs>',
        f'  <rect width="100%" height="100%" fill="#090d16" rx="12"/>',
    ]

    tier_centers: list[int] = []

    for tier in tiers:
        y = tier["y"]
        tier_centers.append(y + 25)
        title = tier["title"]
        boxes = tier["boxes"]
        color = tier["color"]

        # Tier section label
        svg_parts.append(f'  <text x="50" y="{y - 10}" fill="{color}" font-size="11" font-weight="700" letter-spacing="1">{title}</text>')

        box_count = len(boxes)
        box_width = min(220, int(680 / max(1, box_count) - 20))
        total_width = box_count * box_width + (box_count - 1) * 15
        start_x = int((800 - total_width) / 2)

        for i, box_text in enumerate(boxes):
            bx = start_x + i * (box_width + 15)
            clean_text = sanitize_node_label(box_text)
            if len(clean_text) > 28:
                clean_text = clean_text[:25] + "..."
            svg_parts.append(f'  <rect x="{bx}" y="{y}" width="{box_width}" height="50" fill="#111625" stroke="#1f2942" stroke-width="1.5" rx="8"/>')
            svg_parts.append(f'  <text x="{bx + box_width // 2}" y="{y + 30}" text-anchor="middle" fill="#f1f5f9" font-size="12" font-weight="500">{clean_text}</text>')

    # Connect tiers with arrows
    for idx in range(len(tier_centers) - 1):
        y1 = tier_centers[idx] + 25
        y2 = tier_centers[idx + 1] - 25
        svg_parts.append(f'  <line x1="400" y1="{y1}" x2="400" y2="{y2}" stroke="#6366f1" stroke-width="2" stroke-dasharray="4,4" marker-end="url(#arrow)"/>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)
