"""Lightweight, enterprise-grade web dashboard and REST API for StackSense.

Implements the DevTools Modern (Linear / Vercel / Supabase) dark-mode aesthetic.
Provides:
1. Visual Form Studio with bi-directional synchronization and debounced JSON linter gate.
2. Canonical Section 4 evaluation endpoint (`POST /api/recommend`).
3. Dedicated architecture topology endpoint (`POST /api/topology`) generating Mermaid and pure-Python SVG.
4. In-memory memoized benchmark matrix endpoint (`GET /api/scenarios/matrix`).
5. Offline-first static asset serving via local vendor mounts (`src/stacksense/static/`).
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from stacksense.engine import RecommendationEngine
from stacksense.models.output import ScenarioOutput
from stacksense.topology import generate_topology_mermaid, generate_topology_svg

engine = RecommendationEngine()
SCENARIOS_DIR = Path("data/scenarios")
STATIC_DIR = Path(__file__).parent / "static"
REPORT_PATH = Path("Report_Aman_Kumar.pdf")

# Global in-memory cache for benchmark matrix
_BENCHMARK_MATRIX_CACHE: list[dict[str, Any]] = []


def _build_benchmark_matrix() -> list[dict[str, Any]]:
    """Pre-computes recommendations for all public benchmarks (P1-P6) at startup."""
    matrix: list[dict[str, Any]] = []
    for p in sorted(SCENARIOS_DIR.glob("P*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            out = engine.evaluate_scenario(data)
            proj = data.get("project", {})
            stack = out.stack

            fe = stack.frontend.choice if stack else "None"
            be = stack.backend.choice if stack else "None"
            db = stack.database.choice if stack else "None"
            ho = stack.hosting.choice if stack else "None"
            supp = [s.choice for s in stack.supporting] if stack else []

            c_min = f"${out.estimated_monthly_cost_usd.min:.0f}" if out.estimated_monthly_cost_usd else "$0"
            c_max = f"${out.estimated_monthly_cost_usd.max:.0f}" if out.estimated_monthly_cost_usd else "$0"
            cost_str = f"{c_min} – {c_max} / mo"

            top_alt = "None"
            if stack and stack.backend.alternatives:
                top_alt = f"{stack.backend.alternatives[0].choice}: {stack.backend.alternatives[0].why_not}"
            elif stack and stack.frontend.alternatives:
                top_alt = f"{stack.frontend.alternatives[0].choice}: {stack.frontend.alternatives[0].why_not}"

            matrix.append({
                "scenario_id": p.stem,
                "project_name": proj.get("name", p.stem),
                "archetype": proj.get("type", "other"),
                "architecture_style": out.architecture_style.value if out.architecture_style else "serverless",
                "recommended_stack": {
                    "frontend": fe,
                    "backend": be,
                    "database": db,
                    "hosting": ho,
                    "supporting": supp,
                },
                "cost_range": cost_str,
                "key_driver": out.summary,
                "top_rejected_alternative": top_alt,
            })
        except Exception:
            pass
    return matrix


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes in-memory caches and pre-computes benchmark matrix on startup."""
    global _BENCHMARK_MATRIX_CACHE
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "vendor").mkdir(parents=True, exist_ok=True)
    _BENCHMARK_MATRIX_CACHE = _build_benchmark_matrix()
    yield


app = FastAPI(
    title="StackSense Recommendation Engine",
    description="Explainable, deterministic technology-stack recommendation engine for Synergy '26",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount local vendor assets for offline resilience
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class RecommendRequest(BaseModel):
    scenario: dict[str, Any]
    enable_llm: bool = False


class TopologyRequest(BaseModel):
    output: Optional[ScenarioOutput] = None
    scenario: Optional[dict[str, Any]] = None


@app.get("/api/scenarios")
def list_scenarios() -> list[dict[str, str]]:
    """Lists all available preset scenarios (P1–P6 and Edge Cases)."""
    scenarios = []

    # Public benchmarks
    for p in sorted(SCENARIOS_DIR.glob("P*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            scenarios.append({
                "id": p.stem,
                "name": data.get("project", {}).get("name", p.stem),
                "type": data.get("project", {}).get("type", "other"),
                "category": "Public Benchmark",
                "path": str(p),
            })
        except Exception:
            pass

    # Edge cases
    edge_dir = SCENARIOS_DIR / "edge_cases"
    if edge_dir.is_dir():
        for e in sorted(edge_dir.glob("*.json")):
            try:
                with open(e, "r", encoding="utf-8") as f:
                    data = json.load(f)
                scenarios.append({
                    "id": e.stem,
                    "name": data.get("project", {}).get("name", e.stem),
                    "type": data.get("project", {}).get("type", "edge_case"),
                    "category": "Section 6 Edge Case",
                    "path": str(e),
                })
            except Exception:
                pass

    return scenarios


@app.get("/api/scenarios/matrix")
def get_benchmark_matrix() -> list[dict[str, Any]]:
    """Serves the pre-computed P1-P6 benchmark comparative matrix from RAM in <2ms."""
    global _BENCHMARK_MATRIX_CACHE
    if not _BENCHMARK_MATRIX_CACHE:
        _BENCHMARK_MATRIX_CACHE = _build_benchmark_matrix()
    return _BENCHMARK_MATRIX_CACHE


@app.get("/api/scenarios/{scenario_id}")
def get_scenario(scenario_id: str) -> dict[str, Any]:
    """Retrieves the full scenario input JSON for a given scenario ID."""
    target = SCENARIOS_DIR / f"{scenario_id}.json"
    if not target.is_file():
        target = SCENARIOS_DIR / "edge_cases" / f"{scenario_id}.json"
    if not target.is_file():
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")

    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/recommend", response_model=ScenarioOutput)
def recommend_stack(req: RecommendRequest) -> ScenarioOutput:
    """Evaluates raw scenario JSON and produces canonical Section 4 compliant recommendation."""
    return engine.evaluate_scenario(req.scenario, enable_llm=req.enable_llm)


@app.post("/api/topology")
def get_topology(req: TopologyRequest) -> dict[str, str]:
    """Auxiliary endpoint returning deterministic Mermaid flowchart syntax and pure-Python SVG."""
    out = req.output
    if out is None:
        if not req.scenario:
            raise HTTPException(status_code=400, detail="Either 'output' or 'scenario' must be provided.")
        out = engine.evaluate_scenario(req.scenario)

    mermaid_str = generate_topology_mermaid(out, req.scenario)
    svg_str = generate_topology_svg(out, req.scenario)
    return {"mermaid": mermaid_str, "svg": svg_str}


@app.get("/api/download-report")
def download_report():
    """Serves the generated official Project Report PDF."""
    report = REPORT_PATH if REPORT_PATH.is_file() else Path("..") / REPORT_PATH
    if not report.is_file():
        raise HTTPException(status_code=404, detail="Report PDF not generated yet.")
    return FileResponse(
        path=report,
        filename="Report_Aman_Kumar.pdf",
        media_type="application/pdf",
    )


@app.get("/", response_class=HTMLResponse)
def index_page() -> str:
    """Serves the modernized Linear/Vercel styled web UI studio."""
    return HTML_CONTENT


HTML_CONTENT = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StackSense · Systems-Design Recommendation Engine</title>
  <!-- Production-grade Offline Vendored Tailwind CSS (Zero external CDN dependency) -->
  <link rel="stylesheet" href="/static/vendor/tailwind.min.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  
  <!-- Offline-First Mermaid.js: local vendor asset with CDN fallback -->
  <script src="/static/vendor/mermaid.min.js"></script>
  <script>
    if (typeof mermaid === 'undefined') {
      document.write('<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"><\\/script>');
    }
  </script>

  <style>
    body {
      background-color: #090d16;
      background-image: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(14, 165, 233, 0.05) 0px, transparent 50%);
      color: #f1f5f9;
      font-feature-settings: "cv02", "cv03", "cv04", "cv11";
    }
    
    .glass-card {
      background: rgba(17, 22, 37, 0.85);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
    }

    .glass-card:hover {
      border-color: rgba(255, 255, 255, 0.14);
    }

    /* Custom Scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #090d16; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }

    /* Suppress any stray Mermaid error elements appended to body */
    svg[id^="dtopo_"], div[id^="dtopo_"], [id^="dtopo_"], .error-icon, [aria-roledescription="error"] {
      display: none !important;
    }
    ::-webkit-scrollbar-thumb:hover { background: #334155; }
  </style>
</head>
<body class="min-h-screen antialiased flex flex-col">

  <!-- Top Navigation Bar -->
  <header class="border-b border-white/[0.08] bg-surface-card/70 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5">
    <div class="max-w-7xl mx-auto flex items-center justify-between">
      
      <!-- Brand Logo & Title -->
      <div class="flex items-center gap-3.5">
        <div class="h-9 w-9 rounded-xl bg-gradient-to-tr from-brand-600 to-cyan-500 p-[1px] shadow-lg shadow-brand-500/20">
          <div class="h-full w-full bg-surface-card rounded-[11px] flex items-center justify-center text-brand-400">
            <i class="fa-solid fa-cubes-stacked text-base"></i>
          </div>
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="text-base font-bold tracking-tight text-white">StackSense</span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-brand-500/10 text-brand-400 border border-brand-500/20">Synergy '26</span>
          </div>
          <p class="text-[11px] text-slate-400">Systems-Design Recommendation Engine · IIIT Bangalore</p>
        </div>
      </div>

      <!-- Header Meta Badges & Actions -->
      <div class="flex items-center gap-3">
        <div class="hidden md:flex items-center gap-2">
          <span class="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 mr-2 animate-pulse"></span>
            Deterministic (100% LLM-off)
          </span>
          <span class="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <i class="fa-solid fa-server mr-1.5 text-[10px]"></i>
            37 Verified Technologies
          </span>
        </div>

        <a href="/api/download-report" target="_blank" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/[0.05] hover:bg-white/[0.1] text-slate-200 border border-white/[0.1] transition flex items-center gap-1.5">
          <i class="fa-regular fa-file-pdf text-rose-400"></i>
          <span>Official Report (PDF)</span>
        </a>
      </div>

    </div>
  </header>

  <!-- Main Content Layout -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">

    <!-- LEFT PANEL: Scenario Inputs & Mode Controller (5 Cols) -->
    <div class="lg:col-span-5 space-y-4 flex flex-col">
      <div class="glass-card rounded-2xl p-5 space-y-4 flex-1 flex flex-col">
        
        <!-- Scenario Selector Header -->
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <i class="fa-solid fa-sliders text-brand-400 text-sm"></i>
            <h2 class="text-sm font-semibold text-white tracking-tight">Scenario Configuration</h2>
          </div>
          
          <select id="scenarioSelect" class="bg-surface-elevated text-slate-200 text-xs rounded-lg px-3 py-1.5 border border-white/10 focus:outline-none focus:ring-1 focus:ring-brand-500 font-medium">
            <option value="">-- Load Scenario Preset --</option>
          </select>
        </div>

        <!-- Mode Tabs: Visual Form vs. JSON Code Editor -->
        <div class="flex items-center p-1 bg-surface-elevated/70 rounded-xl border border-white/[0.06] text-xs font-medium">
          <button id="tabFormBtn" class="flex-1 py-1.5 rounded-lg bg-brand-600 text-white shadow-sm flex items-center justify-center gap-1.5 transition">
            <i class="fa-solid fa-wand-magic-sparkles text-[10px]"></i> Visual Studio
          </button>
          <button id="tabJsonBtn" class="flex-1 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 flex items-center justify-center gap-1.5 transition">
            <i class="fa-solid fa-code text-[10px]"></i> JSON Code
          </button>
        </div>

        <!-- TAB 1: Visual Form Studio -->
        <div id="visualFormView" class="space-y-4 flex-1 overflow-y-auto max-h-[620px] pr-1">
          <!-- Section 1: Project Details -->
          <div class="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-3">
            <span class="text-[11px] uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1.5">
              <i class="fa-regular fa-folder text-brand-400"></i> Project & Target Platforms
            </span>
            <div class="space-y-2.5">
              <div>
                <label class="text-[11px] text-slate-400 block mb-1">Project Name</label>
                <input id="vf_name" type="text" class="w-full bg-surface-elevated text-xs text-slate-200 px-3 py-1.5 rounded-lg border border-white/10 focus:ring-1 focus:ring-brand-500 focus:outline-none">
              </div>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="text-[11px] text-slate-400 block mb-1">Project Archetype</label>
                  <select id="vf_type" class="w-full bg-surface-elevated text-xs text-slate-200 px-2.5 py-1.5 rounded-lg border border-white/10 focus:outline-none">
                    <option value="content_site">Content Site / Blog</option>
                    <option value="web_app">General Web App</option>
                    <option value="saas_b2b">B2B SaaS</option>
                    <option value="marketplace">Marketplace</option>
                    <option value="fintech">Fintech / Payments</option>
                    <option value="healthtech">Healthtech</option>
                    <option value="realtime_collab">Real-time Collab</option>
                    <option value="internal_tool">Internal Tool</option>
                    <option value="ecommerce">E-Commerce</option>
                    <option value="social">Social Network</option>
                    <option value="other">Other / Offline-first</option>
                  </select>
                </div>
                <div>
                  <label class="text-[11px] text-slate-400 block mb-1">Workload Profile</label>
                  <select id="vf_workload" class="w-full bg-surface-elevated text-xs text-slate-200 px-2.5 py-1.5 rounded-lg border border-white/10 focus:outline-none">
                    <option value="read_heavy">Read-Heavy</option>
                    <option value="balanced">Balanced</option>
                    <option value="write_heavy">Write-Heavy</option>
                  </select>
                </div>
              </div>

              <div>
                <label class="text-[11px] text-slate-400 block mb-1.5">Target Platforms</label>
                <div class="flex flex-wrap gap-1.5" id="platformBadges">
                  <button type="button" data-val="web" class="plat-chip px-2.5 py-1 rounded-md text-xs font-medium border border-white/10 bg-surface-elevated text-slate-300">Web</button>
                  <button type="button" data-val="android" class="plat-chip px-2.5 py-1 rounded-md text-xs font-medium border border-white/10 bg-surface-elevated text-slate-300">Android</button>
                  <button type="button" data-val="ios" class="plat-chip px-2.5 py-1 rounded-md text-xs font-medium border border-white/10 bg-surface-elevated text-slate-300">iOS</button>
                  <button type="button" data-val="desktop" class="plat-chip px-2.5 py-1 rounded-md text-xs font-medium border border-white/10 bg-surface-elevated text-slate-300">Desktop</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Section 2: Scale & Budget -->
          <div class="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-3">
            <span class="text-[11px] uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1.5">
              <i class="fa-solid fa-chart-line text-cyan-400"></i> Scale, Budget & Timeline
            </span>
            <div class="grid grid-cols-2 gap-2.5">
              <div>
                <label class="text-[11px] text-slate-400 block mb-1">12-Mo Users</label>
                <input id="vf_users12m" type="number" class="w-full bg-surface-elevated text-xs text-slate-200 px-3 py-1.5 rounded-lg border border-white/10">
              </div>
              <div>
                <label class="text-[11px] text-slate-400 block mb-1">Monthly Budget ($ USD)</label>
                <input id="vf_budget" type="number" class="w-full bg-surface-elevated text-xs text-slate-200 px-3 py-1.5 rounded-lg border border-white/10">
              </div>
              <div>
                <label class="text-[11px] text-slate-400 block mb-1">Team Size</label>
                <input id="vf_team_size" type="number" class="w-full bg-surface-elevated text-xs text-slate-200 px-3 py-1.5 rounded-lg border border-white/10">
              </div>
              <div>
                <label class="text-[11px] text-slate-400 block mb-1">Team Experience</label>
                <select id="vf_team_exp" class="w-full bg-surface-elevated text-xs text-slate-200 px-2.5 py-1.5 rounded-lg border border-white/10">
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="senior">Senior</option>
                  <option value="mixed">Mixed</option>
                </select>
              </div>
            </div>
            <div>
              <label class="text-[11px] text-slate-400 block mb-1">Team Languages (comma-separated)</label>
              <input id="vf_languages" type="text" placeholder="e.g. python, typescript, java" class="w-full bg-surface-elevated text-xs text-slate-200 px-3 py-1.5 rounded-lg border border-white/10">
            </div>
          </div>

          <!-- Section 3: Infrastructure & Compliance -->
          <div class="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-3">
            <span class="text-[11px] uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1.5">
              <i class="fa-solid fa-shield-halved text-emerald-400"></i> Infrastructure & Compliance
            </span>
            <div class="grid grid-cols-2 gap-2.5">
              <div>
                <label class="text-[11px] text-slate-400 block mb-1">Deployment Model</label>
                <select id="vf_deploy_model" class="w-full bg-surface-elevated text-xs text-slate-200 px-2 py-1.5 rounded-lg border border-white/10">
                  <option value="managed_cloud">Managed Cloud</option>
                  <option value="self_hosted_cloud_vm">Self-Hosted VM</option>
                  <option value="on_premise">On-Premise Server</option>
                  <option value="air_gapped">Air-Gapped Isolated</option>
                </select>
              </div>
              <div>
                <label class="text-[11px] text-slate-400 block mb-1">Data Residency</label>
                <select id="vf_residency" class="w-full bg-surface-elevated text-xs text-slate-200 px-2 py-1.5 rounded-lg border border-white/10">
                  <option value="none">None (Global)</option>
                  <option value="india">India (DPDP / RBI)</option>
                  <option value="eu">European Union (GDPR)</option>
                  <option value="us">United States</option>
                </select>
              </div>
              <div>
                <label class="text-[11px] text-slate-400 block mb-1">Cloud Preference</label>
                <select id="vf_cloud_pref" class="w-full bg-surface-elevated text-xs text-slate-200 px-2 py-1.5 rounded-lg border border-white/10">
                  <option value="any">Any Cloud</option>
                  <option value="aws">AWS</option>
                  <option value="gcp">GCP</option>
                  <option value="azure">Azure</option>
                  <option value="none">None / On-Premise</option>
                </select>
              </div>
              <div>
                <label class="text-[11px] text-slate-400 block mb-1">Availability</label>
                <select id="vf_availability" class="w-full bg-surface-elevated text-xs text-slate-200 px-2 py-1.5 rounded-lg border border-white/10">
                  <option value="99">99.0%</option>
                  <option value="99.9">99.9% (Standard)</option>
                  <option value="99.95">99.95% (High)</option>
                  <option value="99.99">99.99% (Critical)</option>
                </select>
              </div>
            </div>

            <div>
              <label class="text-[11px] text-slate-400 block mb-1.5">Compliance Requirements</label>
              <div class="flex flex-wrap gap-1.5" id="complianceBadges">
                <button type="button" data-val="rbi_localisation" class="comp-chip px-2 py-0.5 rounded text-[11px] font-mono border border-white/10 bg-surface-elevated text-slate-400">RBI Localisation</button>
                <button type="button" data-val="dpdp" class="comp-chip px-2 py-0.5 rounded text-[11px] font-mono border border-white/10 bg-surface-elevated text-slate-400">DPDP (India)</button>
                <button type="button" data-val="pci_dss" class="comp-chip px-2 py-0.5 rounded text-[11px] font-mono border border-white/10 bg-surface-elevated text-slate-400">PCI-DSS</button>
                <button type="button" data-val="gdpr" class="comp-chip px-2 py-0.5 rounded text-[11px] font-mono border border-white/10 bg-surface-elevated text-slate-400">GDPR</button>
              </div>
            </div>
          </div>

          <!-- Section 4: Features -->
          <div class="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-2.5">
            <span class="text-[11px] uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1.5">
              <i class="fa-solid fa-puzzle-piece text-amber-400"></i> Functional Requirements
            </span>
            <div class="grid grid-cols-2 gap-2 text-xs text-slate-300">
              <label class="flex items-center gap-2 cursor-pointer">
                <input id="vf_realtime" type="checkbox" class="rounded bg-surface-elevated border-white/10 text-brand-500"> Real-time Sync
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input id="vf_offline" type="checkbox" class="rounded bg-surface-elevated border-white/10 text-brand-500"> Offline Support
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input id="vf_search" type="checkbox" class="rounded bg-surface-elevated border-white/10 text-brand-500"> Full-Text Search
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input id="vf_storage" type="checkbox" class="rounded bg-surface-elevated border-white/10 text-brand-500"> Media / S3 Storage
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input id="vf_payments" type="checkbox" class="rounded bg-surface-elevated border-white/10 text-brand-500"> Payments Gateway
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input id="vf_devops" type="checkbox" class="rounded bg-surface-elevated border-white/10 text-brand-500"> Dedicated DevOps
              </label>
            </div>
          </div>
        </div>

        <!-- TAB 2: Section 3.1 JSON Code Editor -->
        <div id="jsonCodeView" class="hidden space-y-2 flex-1 flex flex-col">
          <div class="flex justify-between items-center text-[11px] text-slate-400">
            <span>Section 3.1 JSON Spec</span>
            <span id="jsonValidationMsg" class="text-emerald-400 font-mono font-medium">Valid JSON</span>
          </div>
          <textarea id="jsonEditor" class="w-full flex-1 bg-surface-elevated font-mono text-xs text-slate-200 p-3.5 rounded-xl border border-white/10 focus:ring-1 focus:ring-brand-500 focus:outline-none leading-relaxed resize-none min-h-[500px]" spellcheck="false"></textarea>
        </div>

        <!-- Action Button -->
        <div class="pt-2 border-t border-white/[0.08]">
          <button id="evaluateBtn" class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-semibold text-xs tracking-wide shadow-lg shadow-brand-500/25 transition flex items-center justify-center gap-2">
            <i class="fa-solid fa-bolt"></i>
            <span>Evaluate Stack Recommendation</span>
          </button>
        </div>

      </div>
    </div>

    <!-- RIGHT PANEL: 6-Tab Studio Workspace (7 Cols) -->
    <div class="lg:col-span-7 space-y-4 flex flex-col">
      
      <!-- Top Metrics Ribbon -->
      <div id="metricsRibbon" class="glass-card rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 border-l-4 border-l-brand-500">
        <div class="flex items-center gap-2.5" id="statusBadges">
          <span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span> STATUS: OK
          </span>
          <span class="px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            Arch: SERVERLESS
          </span>
        </div>
        <div class="flex items-center gap-2 font-mono text-xs" id="costBadge">
          <span class="text-slate-400 font-sans text-xs">Estimated Monthly TCO:</span>
          <span class="px-3 py-1 rounded-full font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/25">
            $45 – $200 / mo
          </span>
        </div>
      </div>

      <!-- Studio Workspace Tabs -->
      <div class="glass-card rounded-2xl p-2 flex items-center gap-1 border border-white/[0.08] overflow-x-auto text-xs font-medium">
        <button id="wsTabBlueprint" class="ws-tab px-3.5 py-1.5 rounded-lg bg-brand-600 text-white flex items-center gap-1.5 transition">
          <i class="fa-solid fa-layer-group text-[11px]"></i> Blueprint
        </button>
        <button id="wsTabTopology" class="ws-tab px-3.5 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition">
          <i class="fa-solid fa-diagram-project text-[11px]"></i> System Topology
        </button>
        <button id="wsTabTradeoffs" class="ws-tab px-3.5 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition">
          <i class="fa-solid fa-scale-balanced text-[11px]"></i> Trade-Off Matrix
        </button>
        <button id="wsTabRelaxation" class="ws-tab px-3.5 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition">
          <i class="fa-solid fa-triangle-exclamation text-[11px]"></i> Conflicts & Repairs
        </button>
        <button id="wsTabMatrix" class="ws-tab px-3.5 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition">
          <i class="fa-solid fa-table-cells text-[11px]"></i> Benchmark Matrix
        </button>
        <button id="wsTabJson" class="ws-tab px-3.5 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition">
          <i class="fa-solid fa-code text-[11px]"></i> Section 4 JSON
        </button>
      </div>

      <!-- Workspace Tab Contents -->
      <div id="wsContainer" class="flex-1 space-y-4">
        
        <!-- View 1: Architecture Blueprint -->
        <div id="viewBlueprint" class="space-y-4">
          <!-- Summary card -->
          <div class="glass-card rounded-2xl p-4.5 space-y-1.5">
            <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <i class="fa-regular fa-compass text-brand-400"></i> Recommendation Architecture Summary
            </span>
            <p id="bpSummary" class="text-xs text-slate-200 leading-relaxed font-normal"></p>
          </div>

          <!-- 4 Core Layers Grid (Fixes Header Overlap Bug) -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="bpCoreLayers"></div>

          <!-- Supporting Services Grid -->
          <div class="glass-card rounded-2xl p-5 space-y-3.5" id="bpSupporting"></div>
        </div>

        <!-- View 2: System Topology Visualizer -->
        <div id="viewTopology" class="hidden space-y-3">
          <div class="glass-card rounded-2xl p-4 flex items-center justify-between border-b border-white/[0.08]">
            <div class="flex items-center gap-2">
              <i class="fa-solid fa-diagram-project text-cyan-400 text-xs"></i>
              <span class="text-xs font-semibold text-white tracking-tight">System Architecture Topology (5-Tier)</span>
            </div>
            <div class="flex items-center gap-2">
              <button id="copyMermaidBtn" class="px-2.5 py-1 rounded-md text-[11px] font-medium bg-white/[0.05] hover:bg-white/[0.1] text-slate-300 border border-white/10 transition flex items-center gap-1">
                <i class="fa-regular fa-copy text-brand-400"></i> Copy Mermaid
              </button>
              <button id="downloadSvgBtn" class="px-2.5 py-1 rounded-md text-[11px] font-medium bg-white/[0.05] hover:bg-white/[0.1] text-slate-300 border border-white/10 transition flex items-center gap-1">
                <i class="fa-solid fa-download text-emerald-400"></i> Download SVG
              </button>
            </div>
          </div>
          <div class="glass-card rounded-2xl p-5 overflow-auto max-h-[650px] flex items-center justify-center min-h-[400px]">
            <div id="topologyRenderArea" class="w-full flex justify-center text-center"></div>
          </div>
        </div>

        <!-- View 3: Architectural Trade-Off Matrix -->
        <div id="viewTradeoffs" class="hidden space-y-4">
          <div class="glass-card rounded-2xl p-5 space-y-3">
            <div class="flex items-center justify-between border-b border-white/[0.06] pb-3">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <i class="fa-solid fa-scale-balanced text-amber-400"></i>
                <span>Architectural Trade-Off Analysis</span>
              </span>
              <span class="text-[11px] text-slate-400 font-mono">Input-grounded decision ledger</span>
            </div>
            <div id="tradeoffTableContainer" class="overflow-x-auto"></div>
          </div>
        </div>

        <!-- View 4: Conflict Relaxation & Remediation Guide -->
        <div id="viewRelaxation" class="hidden space-y-4">
          <div class="glass-card rounded-2xl p-5 space-y-3.5">
            <div class="flex items-center justify-between border-b border-white/[0.06] pb-3">
              <span class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2">
                <i class="fa-solid fa-shield-virus"></i>
                <span>Detected Conflicts & Actionable Repair Advice</span>
              </span>
              <span class="text-[11px] text-slate-400">Deterministic relaxation heuristics</span>
            </div>
            <div id="relaxationCardContainer" class="space-y-3"></div>
          </div>
        </div>

        <!-- View 5: Benchmark Matrix (P1-P6) -->
        <div id="viewMatrix" class="hidden space-y-4">
          <div class="glass-card rounded-2xl p-5 space-y-3.5">
            <div class="flex items-center justify-between border-b border-white/[0.06] pb-3">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <i class="fa-solid fa-table-cells text-cyan-400"></i>
                <span>Cross-Scenario Benchmark Comparative Matrix</span>
              </span>
              <span class="text-[11px] text-slate-400 font-mono">P1 through P6 live benchmarks</span>
            </div>
            <div id="matrixTableContainer" class="overflow-x-auto"></div>
          </div>
        </div>

        <!-- View 6: Section 4 JSON Spec -->
        <div id="viewJson" class="hidden space-y-3">
          <div class="glass-card rounded-2xl p-4 flex items-center justify-between">
            <span class="text-xs font-medium text-slate-300 flex items-center gap-2">
              <span class="h-2 w-2 rounded-full bg-emerald-400"></span>
              <span>Canonical Section 4 JSON Spec</span>
            </span>
            <button id="copyRawJsonBtn" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white/[0.08] hover:bg-white/[0.14] text-white border border-white/10 transition flex items-center gap-1.5">
              <i class="fa-regular fa-copy"></i> Copy JSON
            </button>
          </div>
          <pre id="rawJsonSpec" class="glass-card rounded-2xl p-4.5 font-mono text-xs text-slate-300 overflow-auto max-h-[600px] leading-relaxed"></pre>
        </div>

      </div>

    </div>

  </main>

  <script>
    // State
    let currentScenario = null;
    let currentOutput = null;
    let currentTopology = { mermaid: "", svg: "" };
    let jsonDebounceTimer = null;

    // DOM Elements
    const scenarioSelect = document.getElementById('scenarioSelect');
    const tabFormBtn = document.getElementById('tabFormBtn');
    const tabJsonBtn = document.getElementById('tabJsonBtn');
    const visualFormView = document.getElementById('visualFormView');
    const jsonCodeView = document.getElementById('jsonCodeView');
    const jsonEditor = document.getElementById('jsonEditor');
    const jsonValidationMsg = document.getElementById('jsonValidationMsg');
    const evaluateBtn = document.getElementById('evaluateBtn');

    // Workspace Tabs
    const wsTabs = [
      { btn: document.getElementById('wsTabBlueprint'), view: document.getElementById('viewBlueprint') },
      { btn: document.getElementById('wsTabTopology'), view: document.getElementById('viewTopology') },
      { btn: document.getElementById('wsTabTradeoffs'), view: document.getElementById('viewTradeoffs') },
      { btn: document.getElementById('wsTabRelaxation'), view: document.getElementById('viewRelaxation') },
      { btn: document.getElementById('wsTabMatrix'), view: document.getElementById('viewMatrix') },
      { btn: document.getElementById('wsTabJson'), view: document.getElementById('viewJson') },
    ];

    function activateWsTab(targetIndex) {
      wsTabs.forEach((tab, idx) => {
        if (idx === targetIndex) {
          tab.btn.className = "ws-tab px-3.5 py-1.5 rounded-lg bg-brand-600 text-white flex items-center gap-1.5 transition font-semibold";
          tab.view.classList.remove('hidden');
        } else {
          tab.btn.className = "ws-tab px-3.5 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition font-medium";
          tab.view.classList.add('hidden');
        }
      });
      if (targetIndex === 1) renderTopology();
      if (targetIndex === 4) loadBenchmarkMatrix();
    }

    wsTabs.forEach((tab, index) => {
      tab.btn.addEventListener('click', () => activateWsTab(index));
    });

    // Toggle Form vs JSON Editor
    tabFormBtn.addEventListener('click', () => {
      tabFormBtn.className = "flex-1 py-1.5 rounded-lg bg-brand-600 text-white shadow-sm flex items-center justify-center gap-1.5 transition font-semibold";
      tabJsonBtn.className = "flex-1 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 flex items-center justify-center gap-1.5 transition";
      visualFormView.classList.remove('hidden');
      jsonCodeView.classList.add('hidden');
    });

    tabJsonBtn.addEventListener('click', () => {
      tabJsonBtn.className = "flex-1 py-1.5 rounded-lg bg-brand-600 text-white shadow-sm flex items-center justify-center gap-1.5 transition font-semibold";
      tabFormBtn.className = "flex-1 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 flex items-center justify-center gap-1.5 transition";
      jsonCodeView.classList.remove('hidden');
      visualFormView.classList.add('hidden');
    });

    // Load Scenarios List
    async function initScenarios() {
      try {
        const res = await fetch('/api/scenarios');
        const scenarios = await res.json();
        
        scenarioSelect.innerHTML = '<option value="">-- Load Scenario Preset --</option>';
        
        const pubGroup = document.createElement('optgroup');
        pubGroup.label = "Public Benchmarks (P1–P6)";
        const edgeGroup = document.createElement('optgroup');
        edgeGroup.label = "Section 6 Edge Cases";

        scenarios.forEach(sc => {
          const opt = document.createElement('option');
          opt.value = sc.id;
          opt.textContent = `${sc.id}: ${sc.name} (${sc.type})`;
          if (sc.category === "Public Benchmark") {
            pubGroup.appendChild(opt);
          } else {
            edgeGroup.appendChild(opt);
          }
        });

        scenarioSelect.appendChild(pubGroup);
        scenarioSelect.appendChild(edgeGroup);

        // Auto load P2
        scenarioSelect.value = "P2";
        loadScenario("P2");
      } catch (err) {
        console.error("Failed to load scenarios:", err);
      }
    }

    async function loadScenario(id) {
      if (!id) return;
      try {
        const res = await fetch(`/api/scenarios/${id}`);
        const data = await res.json();
        currentScenario = data;
        syncModelToForm(data);
        jsonEditor.value = JSON.stringify(data, null, 2);
        evaluateCurrentScenario();
      } catch (err) {
        console.error(`Failed to fetch scenario ${id}:`, err);
      }
    }

    scenarioSelect.addEventListener('change', (e) => {
      loadScenario(e.target.value);
    });

    // Unidirectional State Machine & Debounced Gate
    function syncModelToForm(sc) {
      if (!sc) return;
      document.getElementById('vf_name').value = sc.project?.name || "";
      document.getElementById('vf_type').value = sc.project?.type || "web_app";
      document.getElementById('vf_workload').value = sc.scale?.workload || "balanced";
      document.getElementById('vf_users12m').value = sc.scale?.users_12_months || 0;
      document.getElementById('vf_budget').value = sc.budget?.monthly_infra_usd || 0;
      document.getElementById('vf_team_size').value = sc.team?.size || 1;
      document.getElementById('vf_team_exp').value = sc.team?.experience || "intermediate";
      document.getElementById('vf_languages').value = (sc.team?.languages || []).join(', ');
      document.getElementById('vf_deploy_model').value = sc.infrastructure?.deployment_model || "managed_cloud";
      document.getElementById('vf_residency').value = sc.infrastructure?.data_residency || "none";
      document.getElementById('vf_cloud_pref').value = sc.infrastructure?.cloud_preference || "any";
      document.getElementById('vf_availability').value = sc.requirements?.availability || "99.9";

      // Platforms
      const plats = sc.project?.platforms || [];
      document.querySelectorAll('.plat-chip').forEach(btn => {
        const val = btn.dataset.val;
        if (plats.includes(val)) {
          btn.classList.add('bg-brand-600', 'text-white', 'border-brand-500');
          btn.classList.remove('bg-surface-elevated', 'text-slate-300');
        } else {
          btn.classList.remove('bg-brand-600', 'text-white', 'border-brand-500');
          btn.classList.add('bg-surface-elevated', 'text-slate-300');
        }
      });

      // Compliance
      const comps = sc.infrastructure?.compliance || [];
      document.querySelectorAll('.comp-chip').forEach(btn => {
        const val = btn.dataset.val;
        if (comps.includes(val)) {
          btn.classList.add('bg-emerald-600/30', 'text-emerald-300', 'border-emerald-500/40');
          btn.classList.remove('bg-surface-elevated', 'text-slate-400');
        } else {
          btn.classList.remove('bg-emerald-600/30', 'text-emerald-300', 'border-emerald-500/40');
          btn.classList.add('bg-surface-elevated', 'text-slate-400');
        }
      });

      // Toggles
      document.getElementById('vf_realtime').checked = !!sc.requirements?.real_time;
      document.getElementById('vf_offline').checked = !!sc.requirements?.offline_support;
      document.getElementById('vf_search').checked = (sc.supporting_services || []).includes('search');
      document.getElementById('vf_storage').checked = (sc.supporting_services || []).includes('storage');
      document.getElementById('vf_payments').checked = (sc.supporting_services || []).includes('payments');
      document.getElementById('vf_devops').checked = !!sc.team?.has_devops;
    }

    function syncFormToModel() {
      if (!currentScenario) currentScenario = {};
      currentScenario.project = currentScenario.project || {};
      currentScenario.project.name = document.getElementById('vf_name').value;
      currentScenario.project.type = document.getElementById('vf_type').value;
      
      currentScenario.scale = currentScenario.scale || {};
      currentScenario.scale.workload = document.getElementById('vf_workload').value;
      currentScenario.scale.users_12_months = parseInt(document.getElementById('vf_users12m').value) || 0;

      currentScenario.budget = currentScenario.budget || {};
      currentScenario.budget.monthly_infra_usd = parseFloat(document.getElementById('vf_budget').value) || 0;

      currentScenario.team = currentScenario.team || {};
      currentScenario.team.size = parseInt(document.getElementById('vf_team_size').value) || 1;
      currentScenario.team.experience = document.getElementById('vf_team_exp').value;
      const langs = document.getElementById('vf_languages').value.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
      currentScenario.team.languages = langs;
      currentScenario.team.has_devops = document.getElementById('vf_devops').checked;

      currentScenario.infrastructure = currentScenario.infrastructure || {};
      currentScenario.infrastructure.deployment_model = document.getElementById('vf_deploy_model').value;
      currentScenario.infrastructure.data_residency = document.getElementById('vf_residency').value;
      currentScenario.infrastructure.cloud_preference = document.getElementById('vf_cloud_pref').value;

      currentScenario.requirements = currentScenario.requirements || {};
      currentScenario.requirements.availability = document.getElementById('vf_availability').value;
      currentScenario.requirements.real_time = document.getElementById('vf_realtime').checked;
      currentScenario.requirements.offline_support = document.getElementById('vf_offline').checked;

      // Platform selection
      const activePlats = [];
      document.querySelectorAll('.plat-chip.bg-brand-600').forEach(btn => activePlats.push(btn.dataset.val));
      currentScenario.project.platforms = activePlats.length ? activePlats : ["web"];

      // Compliance selection
      const activeComps = [];
      document.querySelectorAll('.comp-chip.bg-emerald-600\\/30').forEach(btn => activeComps.push(btn.dataset.val));
      currentScenario.infrastructure.compliance = activeComps;

      // Re-serialize into JSON textarea
      jsonEditor.value = JSON.stringify(currentScenario, null, 2);
    }

    // Bind form controls
    visualFormView.addEventListener('input', () => {
      syncFormToModel();
    });

    document.querySelectorAll('.plat-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        btn.classList.toggle('bg-brand-600');
        btn.classList.toggle('text-white');
        btn.classList.toggle('bg-surface-elevated');
        btn.classList.toggle('text-slate-300');
        syncFormToModel();
      });
    });

    document.querySelectorAll('.comp-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        btn.classList.toggle('bg-emerald-600/30');
        btn.classList.toggle('text-emerald-300');
        btn.classList.toggle('border-emerald-500/40');
        syncFormToModel();
      });
    });

    // 250ms Debounced Gate on JSON editor
    jsonEditor.addEventListener('input', () => {
      clearTimeout(jsonDebounceTimer);
      jsonDebounceTimer = setTimeout(() => {
        try {
          const parsed = JSON.parse(jsonEditor.value);
          jsonValidationMsg.textContent = "Valid JSON";
          jsonValidationMsg.className = "text-emerald-400 font-mono font-medium";
          currentScenario = parsed;
          syncModelToForm(parsed);
        } catch (err) {
          jsonValidationMsg.textContent = "Syntax Error: " + err.message;
          jsonValidationMsg.className = "text-rose-400 font-mono font-medium text-[10px]";
        }
      }, 250);
    });

    // Evaluation Controller
    evaluateBtn.addEventListener('click', evaluateCurrentScenario);

    async function evaluateCurrentScenario() {
      try {
        let payload = currentScenario;
        try {
          payload = JSON.parse(jsonEditor.value);
        } catch (e) {
          // fallback to memory
        }

        evaluateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i><span>Evaluating Architecture...</span>';

        const res = await fetch('/api/recommend', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario: payload })
        });
        const out = await res.json();
        currentOutput = out;

        // Render UI
        renderBlueprint(out);
        renderMetrics(out);
        renderTradeoffs(out);
        renderRelaxation(out);
        document.getElementById('rawJsonSpec').textContent = JSON.stringify(out, null, 2);

        // Fetch topology in background
        fetchTopology(out, payload);

      } catch (err) {
        console.error("Evaluation error:", err);
      } finally {
        evaluateBtn.innerHTML = '<i class="fa-solid fa-bolt"></i><span>Evaluate Stack Recommendation</span>';
      }
    }

    function renderMetrics(out) {
      const isOk = out.status === "ok";
      const isWarn = out.status === "ok_with_warnings";
      const statusColor = isOk ? "emerald" : (isWarn ? "amber" : "rose");

      document.getElementById('statusBadges').innerHTML = `
        <span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-${statusColor}-500/10 text-${statusColor}-400 border border-${statusColor}-500/20 flex items-center gap-1.5">
          <span class="h-1.5 w-1.5 rounded-full bg-${statusColor}-400 ${isOk ? 'animate-pulse' : ''}"></span>
          STATUS: ${out.status.toUpperCase()}
        </span>
        <span class="px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
          Arch: ${(out.architecture_style || 'serverless').toUpperCase()}
        </span>
      `;

      const cMin = out.estimated_monthly_cost_usd ? Math.round(out.estimated_monthly_cost_usd.min) : 0;
      const cMax = out.estimated_monthly_cost_usd ? Math.round(out.estimated_monthly_cost_usd.max) : 0;
      document.getElementById('costBadge').innerHTML = `
        <span class="text-slate-400 font-sans text-xs">Estimated Monthly TCO:</span>
        <span class="px-3 py-1 rounded-full font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/25">
          $${cMin} – $${cMax} / mo
        </span>
      `;
    }

    function renderBlueprint(out) {
      document.getElementById('bpSummary').textContent = out.summary;

      // 4 Core Layers with Fixed Header Spacing
      const bpGrid = document.getElementById('bpCoreLayers');
      if (!out.stack) {
        bpGrid.innerHTML = `
          <div class="col-span-2 p-5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
            <h4 class="font-bold uppercase tracking-wider mb-1">Architecture Infeasible</h4>
            <p>${out.summary}</p>
          </div>
        `;
        document.getElementById('bpSupporting').classList.add('hidden');
        return;
      }

      document.getElementById('bpSupporting').classList.remove('hidden');

      const layers = [
        { key: "frontend", name: "FRONTEND", comp: out.stack.frontend, icon: "fa-desktop", color: "blue" },
        { key: "backend", name: "BACKEND", comp: out.stack.backend, icon: "fa-server", color: "indigo" },
        { key: "database", name: "DATABASE", comp: out.stack.database, icon: "fa-database", color: "purple" },
        { key: "hosting", name: "HOSTING", comp: out.stack.hosting, icon: "fa-cloud", color: "cyan" },
      ];

      bpGrid.innerHTML = layers.map(l => {
        const c = l.comp;
        if (!c) return '';

        const driversHtml = (c.driven_by || []).map(d => 
          `<span class="bg-white/[0.05] border border-white/[0.08] text-slate-300 px-2 py-0.5 rounded text-[10px] font-mono">${d}</span>`
        ).join('');

        const altsHtml = (c.alternatives || []).map(a => `
          <div class="p-2 rounded-lg bg-surface-elevated/80 border border-white/[0.05] text-[11px] space-y-0.5">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-slate-200">${a.choice}</span>
              <span class="text-[9px] font-bold uppercase tracking-wider text-slate-400 px-1 rounded bg-white/[0.06]">Rejected</span>
            </div>
            <p class="text-slate-400 leading-snug">${a.why_not}</p>
          </div>
        `).join('');

        return `
          <div class="glass-card rounded-2xl p-5 flex flex-col justify-between space-y-3.5 border-t-2 border-t-${l.color}-500/40">
            <div class="space-y-2.5">
              
              <!-- Card Header with Clear Separation (Bug Fix) -->
              <div class="flex items-center justify-between border-b border-white/[0.06] pb-2">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase font-mono bg-${l.color}-500/10 text-${l.color}-400 border border-${l.color}-500/20 flex items-center gap-1.5">
                  <i class="fa-solid ${l.icon}"></i> ${l.name}
                </span>
                <span class="text-[10px] font-mono text-slate-400">Core Layer</span>
              </div>

              <!-- Title -->
              <div>
                <h4 class="text-sm font-bold text-white tracking-tight">${c.choice}</h4>
                <p class="text-xs text-slate-300 leading-relaxed mt-1">${c.justification}</p>
              </div>

              <!-- Drivers -->
              ${c.driven_by && c.driven_by.length ? `
                <div class="space-y-1 pt-1">
                  <span class="text-[9px] uppercase tracking-wider font-bold text-slate-400">Driven By:</span>
                  <div class="flex flex-wrap gap-1">${driversHtml}</div>
                </div>
              ` : ''}

              <!-- Alternatives -->
              ${c.alternatives && c.alternatives.length ? `
                <div class="space-y-1.5 pt-1.5 border-t border-white/[0.06]">
                  <span class="text-[9px] uppercase tracking-wider font-bold text-slate-400">Rejected Alternatives:</span>
                  <div class="space-y-1">${altsHtml}</div>
                </div>
              ` : ''}

            </div>
          </div>
        `;
      }).join('');

      // Supporting Services Grid
      const suppContainer = document.getElementById('bpSupporting');
      const supps = out.stack.supporting || [];
      if (!supps.length) {
        suppContainer.innerHTML = '<span class="text-xs text-slate-400">No supporting services required for this stack.</span>';
        return;
      }

      suppContainer.innerHTML = `
        <div class="flex items-center justify-between border-b border-white/[0.06] pb-2.5">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <i class="fa-solid fa-puzzle-piece text-brand-400"></i>
            <span>Supporting Services (${supps.length})</span>
          </span>
          <span class="text-[10px] text-slate-400">Conditioned dynamically on requirements</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5 pt-1">
          ${supps.map(s => `
            <div class="p-3 rounded-xl bg-surface-elevated/60 border border-white/[0.05] space-y-1">
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-mono uppercase text-brand-400 font-semibold">${s.layer}</span>
                <span class="text-xs font-bold text-white">${s.choice}</span>
              </div>
              <p class="text-[11px] text-slate-300 leading-snug">${s.justification}</p>
            </div>
          `).join('')}
        </div>
      `;
    }

    // Trade-Off Matrix View
    function renderTradeoffs(out) {
      const container = document.getElementById('tradeoffTableContainer');
      if (!out.stack) {
        container.innerHTML = '<p class="text-xs text-slate-400">No architecture stack available to compare.</p>';
        return;
      }

      const layers = [
        { name: "Frontend", comp: out.stack.frontend },
        { name: "Backend", comp: out.stack.backend },
        { name: "Database", comp: out.stack.database },
        { name: "Hosting", comp: out.stack.hosting },
      ];

      container.innerHTML = `
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="border-b border-white/10 text-slate-400 text-[11px] uppercase tracking-wider font-mono">
              <th class="py-2.5 px-3">Layer</th>
              <th class="py-2.5 px-3">Selected Architecture</th>
              <th class="py-2.5 px-3">Rejected Alternatives & Rationale</th>
              <th class="py-2.5 px-3">Operational Trade-offs</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/[0.05] text-slate-200">
            ${layers.map(l => {
              const c = l.comp;
              if (!c) return '';
              const alts = (c.alternatives || []).map(a => `<div class="mb-1"><span class="font-semibold text-slate-200 font-mono">${a.choice}:</span> <span class="text-slate-400">${a.why_not}</span></div>`).join('') || 'None';
              const trades = (c.tradeoffs || []).map(t => `<li>${t}</li>`).join('') || 'Standard operational profile';

              return `
                <tr class="hover:bg-white/[0.02]">
                  <td class="py-3 px-3 font-bold font-mono text-brand-400 align-top">${l.name}</td>
                  <td class="py-3 px-3 align-top">
                    <div class="font-bold text-white">${c.choice}</div>
                    <div class="text-[11px] text-slate-300 mt-1">${c.justification}</div>
                  </td>
                  <td class="py-3 px-3 text-[11px] align-top">${alts}</td>
                  <td class="py-3 px-3 text-[11px] text-slate-400 align-top"><ul class="list-disc pl-4 space-y-0.5">${trades}</ul></td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      `;
    }

    // Relaxation & Repair Guide View
    function renderRelaxation(out) {
      const container = document.getElementById('relaxationCardContainer');
      const warnings = out.warnings || [];

      if (!warnings.length) {
        container.innerHTML = `
          <div class="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2.5">
            <i class="fa-solid fa-circle-check text-emerald-400 text-sm"></i>
            <span>All declared requirements satisfied cleanly. Zero constraint contradictions detected.</span>
          </div>
        `;
        return;
      }

      container.innerHTML = warnings.map(w => {
        const isCrit = w.severity === "critical";
        const badgeClass = isCrit ? "bg-rose-500/20 text-rose-400 border-rose-500/30" : "bg-amber-500/20 text-amber-400 border-amber-500/30";
        return `
          <div class="p-4 rounded-xl bg-surface-elevated/70 border border-white/[0.06] space-y-2">
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase border ${badgeClass}">${w.severity}</span>
              <span class="text-[11px] font-mono text-slate-400">${w.code}</span>
            </div>
            <p class="text-xs text-slate-200 leading-relaxed">${w.message}</p>
            ${w.fields && w.fields.length ? `
              <div class="text-[10px] text-slate-400 font-mono pt-1">
                <span class="text-slate-400">Affected Parameters:</span> ${w.fields.join(', ')}
              </div>
            ` : ''}
          </div>
        `;
      }).join('');
    }

    // Fetch & Render Topology
    async function fetchTopology(out, scenario) {
      try {
        const res = await fetch('/api/topology', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ output: out, scenario: scenario })
        });
        currentTopology = await res.json();
      } catch (err) {
        console.error("Topology fetch failed:", err);
      }
    }

    async function renderTopology() {
      const area = document.getElementById('topologyRenderArea');
      if (!currentTopology.mermaid && !currentTopology.svg) {
        area.innerHTML = '<span class="text-xs text-slate-400">Generating system topology...</span>';
        return;
      }

      const id = "topo_" + Date.now();

      // Try client-side Mermaid first
      try {
        if (typeof mermaid !== 'undefined' && currentTopology.mermaid) {
          mermaid.initialize({
            startOnLoad: false,
            theme: 'dark',
            securityLevel: 'loose',
            suppressErrorRendering: true
          });
          // Defensive sanitization: strip any illegal parentheses inside pipe delimiters |...|
          const safeMermaid = currentTopology.mermaid.replace(/\\|([^|]+)\\|/g, (match, text) => {
            return '|' + text.replace(/[()]/g, ' ') + '|';
          });
          const { svg } = await mermaid.render(id, safeMermaid);
          area.innerHTML = `<div class="w-full flex justify-center">${svg}</div>`;
          return;
        }
      } catch (err) {
        console.warn("Mermaid client render fallback to pure SVG:", err);
        document.querySelectorAll('[id^="dtopo_"], [id^="topo_"]').forEach(el => el.remove());
      }

      // Fallback: Pure-Python SVG
      if (currentTopology.svg) {
        area.innerHTML = `<div class="w-full flex justify-center">${currentTopology.svg}</div>`;
      }
    }

    // Benchmark Matrix (P1-P6) View
    async function loadBenchmarkMatrix() {
      const container = document.getElementById('matrixTableContainer');
      container.innerHTML = '<p class="text-xs text-slate-400">Loading benchmark comparison matrix...</p>';
      try {
        const res = await fetch('/api/scenarios/matrix');
        const rows = await res.json();
        
        container.innerHTML = `
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-white/10 text-slate-400 text-[11px] uppercase tracking-wider font-mono">
                <th class="py-2.5 px-3">Scenario</th>
                <th class="py-2.5 px-3">Archetype</th>
                <th class="py-2.5 px-3">Recommended Stack</th>
                <th class="py-2.5 px-3">Est. Cost</th>
                <th class="py-2.5 px-3">Pattern</th>
                <th class="py-2.5 px-3">Top Rejected Alternative</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/[0.05] text-slate-200">
              ${rows.map(r => `
                <tr class="hover:bg-white/[0.03] transition cursor-pointer" onclick="loadScenario('${r.scenario_id}')">
                  <td class="py-3 px-3 font-bold font-mono text-cyan-400 align-top">${r.scenario_id} (${r.project_name})</td>
                  <td class="py-3 px-3 font-mono text-slate-400 align-top">${r.archetype}</td>
                  <td class="py-3 px-3 align-top font-mono text-[11px] text-slate-300">
                    <div>FE: <span class="text-white">${r.recommended_stack.frontend}</span></div>
                    <div>BE: <span class="text-white">${r.recommended_stack.backend}</span></div>
                    <div>DB: <span class="text-white">${r.recommended_stack.database}</span></div>
                    <div>Host: <span class="text-white">${r.recommended_stack.hosting}</span></div>
                  </td>
                  <td class="py-3 px-3 font-mono text-emerald-400 align-top font-semibold">${r.cost_range}</td>
                  <td class="py-3 px-3 font-mono uppercase text-indigo-400 align-top">${r.architecture_style}</td>
                  <td class="py-3 px-3 text-[11px] text-slate-400 align-top max-w-xs">${r.top_rejected_alternative}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      } catch (err) {
        container.innerHTML = '<p class="text-xs text-rose-400">Failed to load benchmark matrix.</p>';
      }
    }

    // Action Buttons
    document.getElementById('copyRawJsonBtn').addEventListener('click', () => {
      if (currentOutput) {
        navigator.clipboard.writeText(JSON.stringify(currentOutput, null, 2));
      }
    });

    document.getElementById('copyMermaidBtn').addEventListener('click', () => {
      if (currentTopology.mermaid) {
        navigator.clipboard.writeText(currentTopology.mermaid);
      }
    });

    document.getElementById('downloadSvgBtn').addEventListener('click', () => {
      if (currentTopology.svg) {
        const blob = new Blob([currentTopology.svg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `architecture_topology_${Date.now()}.svg`;
        a.click();
        URL.revokeObjectURL(url);
      }
    });

    // Run initialization
    initScenarios();
  </script>
</body>
</html>
"""
