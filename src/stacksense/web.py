"""Lightweight, enterprise-grade web dashboard and REST API for StackSense.

Implements the DevTools Modern (Linear / Vercel / Supabase) dark-mode aesthetic.
Provides both a rich Visual Form Studio and a Section 3.1 JSON Code Editor,
with real-time constraint validation and interactive architectural breakdown cards.
"""

import json
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from stacksense.engine import RecommendationEngine
from stacksense.models.output import ScenarioOutput

app = FastAPI(
    title="StackSense Recommendation Engine",
    description="Explainable, deterministic technology-stack recommendation engine for Synergy '26",
    version="1.0.0",
)

engine = RecommendationEngine()
SCENARIOS_DIR = Path("data/scenarios")
REPORT_PATH = Path("Report_Aman_Kumar.pdf")


class RecommendRequest(BaseModel):
    scenario: dict[str, Any]
    enable_llm: bool = False


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
    """Evaluates raw scenario JSON and produces Section 4 compliant recommendation."""
    return engine.evaluate_scenario(req.scenario, enable_llm=req.enable_llm)


@app.get("/api/download-report")
def download_report():
    """Serves the generated official Project Report PDF."""
    if not REPORT_PATH.is_file():
        raise HTTPException(status_code=404, detail="Report PDF not generated yet.")
    return FileResponse(
        path=REPORT_PATH,
        filename="Report_Aman_Kumar.pdf",
        media_type="application/pdf",
    )


@app.get("/", response_class=HTMLResponse)
def index_page() -> str:
    """Serves the modern Linear/Vercel styled web UI dashboard."""
    return HTML_CONTENT


HTML_CONTENT = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StackSense · Intelligent Tech Stack Recommendation Engine</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: ['Geist', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
          },
          colors: {
            brand: {
              50: '#eef2ff',
              400: '#818cf8',
              500: '#6366f1',
              600: '#4f46e5',
              700: '#4338ca',
            },
            surface: {
              base: '#090d16',
              card: '#111625',
              elevated: '#181f33',
              border: '#1f2942',
              hover: '#242e4a',
            }
          }
        }
      }
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
      background: rgba(17, 22, 37, 0.75);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.07);
      box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
    }

    .glass-card:hover {
      border-color: rgba(255, 255, 255, 0.12);
    }

    .badge-glow-emerald {
      box-shadow: 0 0 15px -2px rgba(16, 185, 129, 0.25);
    }

    .badge-glow-amber {
      box-shadow: 0 0 15px -2px rgba(245, 158, 11, 0.25);
    }

    .badge-glow-rose {
      box-shadow: 0 0 15px -2px rgba(244, 63, 94, 0.25);
    }

    /* Custom Scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #090d16; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #334155; }
  </style>
</head>
<body class="min-h-screen antialiased flex flex-col">

  <!-- Top Navigation Bar -->
  <header class="border-b border-white/[0.08] bg-surface-card/60 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5">
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
          <p class="text-[11px] text-slate-400">Intelligent Tech Stack Recommendation Engine · IIIT Bangalore</p>
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

    <!-- ========================================================================= -->
    <!-- LEFT PANEL: Scenario Inputs & Preset Controller (5 Cols)                  -->
    <!-- ========================================================================= -->
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
                    <option value="realtime_collab">Real-time Collaboration</option>
                    <option value="internal_tool">Internal Enterprise Tool</option>
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

          <!-- Section 3: Infrastructure, Compliance & Security -->
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
                  <option value="aws">Amazon Web Services</option>
                  <option value="gcp">Google Cloud Platform</option>
                  <option value="azure">Microsoft Azure</option>
                  <option value="none">None / On-Premise</option>
                </select>
              </div>
              <div>
                <label class="text-[11px] text-slate-400 block mb-1">Target Availability</label>
                <select id="vf_availability" class="w-full bg-surface-elevated text-xs text-slate-200 px-2 py-1.5 rounded-lg border border-white/10">
                  <option value="99">99.0%</option>
                  <option value="99.9">99.9% (Standard)</option>
                  <option value="99.95">99.95% (High Availability)</option>
                  <option value="99.99">99.99% (Mission Critical)</option>
                </select>
              </div>
            </div>

            <!-- Compliance standards chips -->
            <div>
              <label class="text-[11px] text-slate-400 block mb-1.5">Compliance Requirements</label>
              <div class="flex flex-wrap gap-1.5" id="complianceBadges">
                <button type="button" data-val="rbi_localisation" class="comp-chip px-2 py-0.5 rounded text-[11px] font-mono border border-white/10 bg-surface-elevated text-slate-400">RBI Localisation</button>
                <button type="button" data-val="dpdp" class="comp-chip px-2 py-0.5 rounded text-[11px] font-mono border border-white/10 bg-surface-elevated text-slate-400">DPDP (India)</button>
                <button type="button" data-val="pci_dss" class="comp-chip px-2 py-0.5 rounded text-[11px] font-mono border border-white/10 bg-surface-elevated text-slate-400">PCI-DSS</button>
                <button type="button" data-val="gdpr" class="comp-chip px-2 py-0.5 rounded text-[11px] font-mono border border-white/10 bg-surface-elevated text-slate-400">GDPR</button>
                <button type="button" data-val="iso27001" class="comp-chip px-2 py-0.5 rounded text-[11px] font-mono border border-white/10 bg-surface-elevated text-slate-400">ISO 27001</button>
              </div>
            </div>
          </div>

          <!-- Section 4: Supporting Feature Toggles -->
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
            <span>Raw Section 3.1 JSON Payload</span>
            <span id="jsonValidationMsg" class="text-emerald-400 font-mono">Valid JSON</span>
          </div>
          <textarea id="jsonEditor" class="w-full flex-1 bg-surface-elevated font-mono text-xs text-slate-200 p-3.5 rounded-xl border border-white/10 focus:ring-1 focus:ring-brand-500 focus:outline-none leading-relaxed resize-none min-h-[500px]" spellcheck="false"></textarea>
        </div>

        <!-- Execute Action Footer -->
        <div class="pt-2 border-t border-white/[0.08] flex items-center justify-between gap-3">
          <button id="formatBtn" type="button" class="px-3 py-2 text-xs font-medium text-slate-400 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] rounded-lg border border-white/10 transition">
            <i class="fa-solid fa-align-left mr-1"></i> Format
          </button>
          
          <button id="runBtn" type="button" class="flex-1 py-2.5 px-4 rounded-xl font-semibold text-xs text-white bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 shadow-lg shadow-brand-500/25 flex items-center justify-center gap-2 transition active:scale-[0.99]">
            <i class="fa-solid fa-bolt text-amber-300"></i> Evaluate & Recommend Stack
          </button>
        </div>

      </div>

    </div>

    <!-- ========================================================================= -->
    <!-- RIGHT PANEL: Executive Architecture & Result Breakdown (7 Cols)           -->
    <!-- ========================================================================= -->
    <div class="lg:col-span-7 space-y-4">
      
      <div id="outputContainer" class="space-y-4">
        <!-- Placeholder Empty State -->
        <div class="glass-card rounded-2xl p-12 text-center text-slate-500 space-y-3">
          <div class="h-14 w-14 rounded-2xl bg-white/[0.03] border border-white/[0.08] flex items-center justify-center mx-auto text-slate-600 text-2xl">
            <i class="fa-solid fa-layer-group"></i>
          </div>
          <h3 class="text-sm font-semibold text-slate-300">Awaiting Scenario Evaluation</h3>
          <p class="text-xs text-slate-500 max-w-sm mx-auto">Select a preset scenario on the left or customize your parameters, then click Evaluate to generate explainable recommendations.</p>
        </div>
      </div>

    </div>

  </main>

  <script>
    // State
    let currentScenario = {};

    // Elements
    const scenarioSelect = document.getElementById('scenarioSelect');
    const tabFormBtn = document.getElementById('tabFormBtn');
    const tabJsonBtn = document.getElementById('tabJsonBtn');
    const visualFormView = document.getElementById('visualFormView');
    const jsonCodeView = document.getElementById('jsonCodeView');
    const jsonEditor = document.getElementById('jsonEditor');
    const jsonValidationMsg = document.getElementById('jsonValidationMsg');
    const runBtn = document.getElementById('runBtn');
    const formatBtn = document.getElementById('formatBtn');
    const outputContainer = document.getElementById('outputContainer');

    // Visual Form Elements
    const vf_name = document.getElementById('vf_name');
    const vf_type = document.getElementById('vf_type');
    const vf_workload = document.getElementById('vf_workload');
    const vf_users12m = document.getElementById('vf_users12m');
    const vf_budget = document.getElementById('vf_budget');
    const vf_team_size = document.getElementById('vf_team_size');
    const vf_team_exp = document.getElementById('vf_team_exp');
    const vf_languages = document.getElementById('vf_languages');
    const vf_deploy_model = document.getElementById('vf_deploy_model');
    const vf_residency = document.getElementById('vf_residency');
    const vf_cloud_pref = document.getElementById('vf_cloud_pref');
    const vf_availability = document.getElementById('vf_availability');
    const vf_realtime = document.getElementById('vf_realtime');
    const vf_offline = document.getElementById('vf_offline');
    const vf_search = document.getElementById('vf_search');
    const vf_storage = document.getElementById('vf_storage');
    const vf_payments = document.getElementById('vf_payments');
    const vf_devops = document.getElementById('vf_devops');

    // Tab Switching
    tabFormBtn.addEventListener('click', () => {
      tabFormBtn.className = "flex-1 py-1.5 rounded-lg bg-brand-600 text-white shadow-sm flex items-center justify-center gap-1.5 transition";
      tabJsonBtn.className = "flex-1 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 flex items-center justify-center gap-1.5 transition";
      visualFormView.classList.remove('hidden');
      jsonCodeView.classList.add('hidden');
      syncJsonToForm();
    });

    tabJsonBtn.addEventListener('click', () => {
      tabJsonBtn.className = "flex-1 py-1.5 rounded-lg bg-brand-600 text-white shadow-sm flex items-center justify-center gap-1.5 transition";
      tabFormBtn.className = "flex-1 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 flex items-center justify-center gap-1.5 transition";
      jsonCodeView.classList.remove('hidden');
      visualFormView.classList.add('hidden');
      syncFormToJson();
    });

    // Preset Scenarios Loader
    async function initScenarios() {
      try {
        const res = await fetch('/api/scenarios');
        const list = await res.json();
        
        const g1 = document.createElement('optgroup');
        g1.label = "Public Benchmarks (P1 - P6)";
        const g2 = document.createElement('optgroup');
        g2.label = "Section 6 Edge Cases (E1 - E11)";

        list.forEach(s => {
          const opt = document.createElement('option');
          opt.value = s.id;
          opt.textContent = `${s.id}: ${s.name}`;
          if (s.category === "Public Benchmark") g1.appendChild(opt);
          else g2.appendChild(opt);
        });

        scenarioSelect.appendChild(g1);
        scenarioSelect.appendChild(g2);

        // Load P2 as initial demonstration
        scenarioSelect.value = "P2";
        await loadScenario("P2");
      } catch (err) {
        console.error("Failed to load scenario list:", err);
      }
    }

    async function loadScenario(id) {
      if (!id) return;
      try {
        const res = await fetch(`/api/scenarios/${id}`);
        currentScenario = await res.json();
        jsonEditor.value = JSON.stringify(currentScenario, null, 2);
        syncJsonToForm();
        await evaluateStack();
      } catch (err) {
        console.error("Error loading scenario:", err);
      }
    }

    scenarioSelect.addEventListener('change', () => loadScenario(scenarioSelect.value));

    // Two-way synchronization: JSON -> Form
    function syncJsonToForm() {
      try {
        const s = JSON.parse(jsonEditor.value);
        currentScenario = s;
        vf_name.value = s.project?.name || "";
        vf_type.value = s.project?.type || "web_app";
        vf_workload.value = s.scale?.workload || "balanced";
        vf_users12m.value = s.scale?.users_12_months ?? 10000;
        vf_budget.value = s.budget?.monthly_infra_usd ?? 150;
        vf_team_size.value = s.team?.size ?? 3;
        vf_team_exp.value = s.team?.experience || "intermediate";
        vf_languages.value = (s.team?.languages || []).join(', ');
        vf_deploy_model.value = s.infrastructure?.deployment_model || "managed_cloud";
        vf_residency.value = s.infrastructure?.data_residency || "none";
        vf_cloud_pref.value = s.infrastructure?.cloud_preference || "any";
        vf_availability.value = s.requirements?.availability || "99.9";

        vf_realtime.checked = !!s.requirements?.realtime;
        vf_offline.checked = !!s.requirements?.offline_support;
        vf_search.checked = !!s.requirements?.full_text_search;
        vf_storage.checked = !!s.requirements?.file_media_storage;
        vf_payments.checked = !!s.requirements?.payments;
        vf_devops.checked = !!s.team?.has_devops;

        // Platform chips
        const plats = s.project?.platforms || [];
        document.querySelectorAll('.plat-chip').forEach(btn => {
          const val = btn.getAttribute('data-val');
          if (plats.includes(val)) {
            btn.className = "plat-chip px-2.5 py-1 rounded-md text-xs font-semibold bg-brand-600 text-white border border-brand-500";
          } else {
            btn.className = "plat-chip px-2.5 py-1 rounded-md text-xs font-medium border border-white/10 bg-surface-elevated text-slate-400";
          }
        });

        // Compliance chips
        const comps = s.compliance || [];
        document.querySelectorAll('.comp-chip').forEach(btn => {
          const val = btn.getAttribute('data-val');
          if (comps.includes(val)) {
            btn.className = "comp-chip px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-emerald-600 text-white border border-emerald-500";
          } else {
            btn.className = "comp-chip px-2 py-0.5 rounded text-[11px] font-mono border border-white/10 bg-surface-elevated text-slate-400";
          }
        });

        jsonValidationMsg.textContent = "Valid Section 3.1 JSON";
        jsonValidationMsg.className = "text-emerald-400 font-mono";
      } catch (e) {
        jsonValidationMsg.textContent = "JSON Syntax Error: " + e.message;
        jsonValidationMsg.className = "text-rose-400 font-mono";
      }
    }

    // Two-way synchronization: Form -> JSON
    function syncFormToJson() {
      const activePlatforms = [];
      document.querySelectorAll('.plat-chip').forEach(btn => {
        if (btn.classList.contains('bg-brand-600')) activePlatforms.push(btn.getAttribute('data-val'));
      });

      const activeCompliance = [];
      document.querySelectorAll('.comp-chip').forEach(btn => {
        if (btn.classList.contains('bg-emerald-600')) activeCompliance.push(btn.getAttribute('data-val'));
      });

      const langs = vf_languages.value.split(',').map(l => l.trim().toLowerCase()).filter(Boolean);

      currentScenario = {
        schema_version: "1.0",
        scenario_id: currentScenario.scenario_id || "CUSTOM",
        project: {
          name: vf_name.value || "Custom Project",
          type: vf_type.value,
          description: currentScenario.project?.description || "Interactive custom scenario.",
          platforms: activePlatforms.length > 0 ? activePlatforms : ["web"]
        },
        scale: {
          traffic_pattern: currentScenario.scale?.traffic_pattern || "steady",
          workload: vf_workload.value,
          users_at_launch: currentScenario.scale?.users_at_launch || 500,
          users_12_months: parseInt(vf_users12m.value) || 10000,
          peak_concurrent_users: currentScenario.scale?.peak_concurrent_users || 100,
          data_volume_gb_12_months: currentScenario.scale?.data_volume_gb_12_months || 20
        },
        team: {
          has_devops: vf_devops.checked,
          size: parseInt(vf_team_size.value) || 3,
          experience: vf_team_exp.value,
          languages: langs.length > 0 ? langs : ["typescript"]
        },
        budget: {
          monthly_infra_usd: parseFloat(vf_budget.value) || 100
        },
        timeline: {
          mvp_weeks: currentScenario.timeline?.mvp_weeks || 12
        },
        infrastructure: {
          cloud_preference: vf_cloud_pref.value,
          deployment_model: vf_deploy_model.value,
          data_residency: vf_residency.value,
          existing_systems: currentScenario.infrastructure?.existing_systems || []
        },
        compliance: activeCompliance,
        requirements: {
          realtime: vf_realtime.checked,
          offline_support: vf_offline.checked,
          full_text_search: vf_search.checked,
          file_media_storage: vf_storage.checked,
          payments: vf_payments.checked,
          auth: currentScenario.requirements?.auth || "email_password",
          multi_tenant: currentScenario.requirements?.multi_tenant || false,
          ml_features: currentScenario.requirements?.ml_features || "none",
          seo_critical: currentScenario.requirements?.seo_critical || false,
          availability: vf_availability.value,
          p95_latency_ms: currentScenario.requirements?.p95_latency_ms || null
        },
        priorities: currentScenario.priorities || {
          cost: 3, time_to_market: 3, scalability: 3, performance: 3, maintainability: 3, security: 3
        }
      };

      jsonEditor.value = JSON.stringify(currentScenario, null, 2);
    }

    // Platform chip toggle
    document.querySelectorAll('.plat-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        if (btn.classList.contains('bg-brand-600')) {
          btn.className = "plat-chip px-2.5 py-1 rounded-md text-xs font-medium border border-white/10 bg-surface-elevated text-slate-400";
        } else {
          btn.className = "plat-chip px-2.5 py-1 rounded-md text-xs font-semibold bg-brand-600 text-white border border-brand-500";
        }
        syncFormToJson();
      });
    });

    // Compliance chip toggle
    document.querySelectorAll('.comp-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        if (btn.classList.contains('bg-emerald-600')) {
          btn.className = "comp-chip px-2 py-0.5 rounded text-[11px] font-mono border border-white/10 bg-surface-elevated text-slate-400";
        } else {
          btn.className = "comp-chip px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-emerald-600 text-white border border-emerald-500";
        }
        syncFormToJson();
      });
    });

    // Real-time Form inputs change listener
    [vf_name, vf_type, vf_workload, vf_users12m, vf_budget, vf_team_size, vf_team_exp, vf_languages, 
     vf_deploy_model, vf_residency, vf_cloud_pref, vf_availability, vf_realtime, vf_offline, 
     vf_search, vf_storage, vf_payments, vf_devops].forEach(el => {
      el.addEventListener('change', syncFormToJson);
    });

    // Format JSON Button
    formatBtn.addEventListener('click', () => {
      try {
        const parsed = JSON.parse(jsonEditor.value);
        jsonEditor.value = JSON.stringify(parsed, null, 2);
        syncJsonToForm();
      } catch (err) {}
    });

    jsonEditor.addEventListener('input', () => {
      syncJsonToForm();
    });

    // Evaluate Stack Action
    async function evaluateStack() {
      try {
        runBtn.disabled = true;
        runBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Solving Constraints...';

        const payload = JSON.parse(jsonEditor.value);
        const res = await fetch('/api/recommend', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario: payload, enable_llm: false })
        });
        const output = await res.json();
        renderOutput(output);
      } catch (err) {
        outputContainer.innerHTML = `
          <div class="glass-card rounded-2xl p-5 border-rose-500/40 text-rose-300 space-y-2">
            <h4 class="font-bold flex items-center gap-2"><i class="fa-solid fa-circle-exclamation"></i> Evaluation Error</h4>
            <p class="text-xs text-rose-200/80">${err.message}</p>
          </div>
        `;
      } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = '<i class="fa-solid fa-bolt text-amber-300"></i> Evaluate & Recommend Stack';
      }
    }

    runBtn.addEventListener('click', evaluateStack);

    // Render Section 4 Recommendation Cards
    function renderOutput(data) {
      let statusBadge = "";
      if (data.status === "ok") {
        statusBadge = '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 badge-glow-emerald flex items-center gap-1.5"><i class="fa-solid fa-circle-check text-[11px]"></i> STATUS: OK</span>';
      } else if (data.status === "ok_with_warnings") {
        statusBadge = '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30 badge-glow-amber flex items-center gap-1.5"><i class="fa-solid fa-triangle-exclamation text-[11px]"></i> STATUS: OK WITH WARNINGS</span>';
      } else if (data.status === "infeasible") {
        statusBadge = '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30 badge-glow-rose flex items-center gap-1.5"><i class="fa-solid fa-ban text-[11px]"></i> STATUS: INFEASIBLE</span>';
      } else {
        statusBadge = '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30 badge-glow-rose flex items-center gap-1.5"><i class="fa-solid fa-circle-xmark text-[11px]"></i> STATUS: INVALID INPUT</span>';
      }

      let archBadge = data.architecture_style 
        ? `<span class="px-3 py-1 rounded-full text-xs font-medium bg-brand-500/15 text-brand-300 border border-brand-500/25 flex items-center gap-1.5"><i class="fa-solid fa-network-wired text-[11px]"></i> ${data.architecture_style.toUpperCase().replace('_', ' ')}</span>` 
        : '';
      
      let costMin = data.estimated_monthly_cost_usd ? Math.round(data.estimated_monthly_cost_usd.min) : 0;
      let costMax = data.estimated_monthly_cost_usd ? Math.round(data.estimated_monthly_cost_usd.max) : 0;

      let html = `
        <!-- Header Banner Card -->
        <div class="glass-card rounded-2xl p-5 space-y-4 border-l-4 border-l-brand-500">
          <div class="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] pb-3.5">
            <div class="flex items-center gap-2.5">
              ${statusBadge}
              ${archBadge}
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-slate-400 font-medium">Estimated Monthly Infra:</span>
              <span class="px-3 py-1 rounded-full text-xs font-bold font-mono bg-cyan-500/15 text-cyan-300 border border-cyan-500/25">
                $${costMin} – $${costMax} / mo
              </span>
            </div>
          </div>
          
          <div class="space-y-1">
            <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <i class="fa-regular fa-compass text-brand-400"></i> Architectural Strategy
            </span>
            <p class="text-sm text-slate-200 leading-relaxed font-normal">${data.summary}</p>
          </div>
        </div>
      `;

      // Validation Errors Notice
      if (data.validation_errors && data.validation_errors.length > 0) {
        html += `
          <div class="glass-card rounded-2xl p-4.5 border-rose-500/40 bg-rose-500/[0.04] space-y-2.5">
            <div class="flex items-center gap-2 text-rose-400 font-bold text-xs uppercase tracking-wider">
              <i class="fa-solid fa-triangle-exclamation"></i>
              <span>Schema Validation Errors (${data.validation_errors.length})</span>
            </div>
            <ul class="text-xs text-rose-200 space-y-1 pl-4 list-disc">
              ${data.validation_errors.map(e => `<li><span class="font-mono font-semibold text-rose-300">${e.field}:</span> ${e.message}</li>`).join('')}
            </ul>
          </div>
        `;
      }

      // Warnings Notice
      if (data.warnings && data.warnings.length > 0) {
        html += `
          <div class="glass-card rounded-2xl p-4.5 border-amber-500/30 bg-amber-500/[0.03] space-y-2.5">
            <div class="flex items-center gap-2 text-amber-400 font-bold text-xs uppercase tracking-wider">
              <i class="fa-solid fa-shield-virus"></i>
              <span>Detected Trade-Offs & Warnings (${data.warnings.length})</span>
            </div>
            <div class="space-y-2">
              ${data.warnings.map(w => `
                <div class="p-2.5 rounded-lg bg-surface-elevated/60 border border-white/[0.06] text-xs flex items-start gap-2.5">
                  <span class="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider font-mono uppercase ${w.severity === 'critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'}">${w.severity}</span>
                  <div class="flex-1 space-y-0.5">
                    <span class="font-semibold text-slate-200 font-mono text-[11px]">${w.code}</span>
                    <p class="text-slate-300 text-xs">${w.message}</p>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }

      // 4 Core Layers
      if (data.stack) {
        const coreLayers = [
          { key: "frontend", name: "Frontend", comp: data.stack.frontend, icon: "fa-desktop", accent: "from-blue-500/20 to-transparent", textAccent: "text-blue-400", borderAccent: "border-blue-500/40" },
          { key: "backend", name: "Backend", comp: data.stack.backend, icon: "fa-server", accent: "from-indigo-500/20 to-transparent", textAccent: "text-indigo-400", borderAccent: "border-indigo-500/40" },
          { key: "database", name: "Database", comp: data.stack.database, icon: "fa-database", accent: "from-purple-500/20 to-transparent", textAccent: "text-purple-400", borderAccent: "border-purple-500/40" },
          { key: "hosting", name: "Hosting & Runtime", comp: data.stack.hosting, icon: "fa-cloud", accent: "from-teal-500/20 to-transparent", textAccent: "text-teal-400", borderAccent: "border-teal-500/40" },
        ];

        html += `<div class="grid grid-cols-1 md:grid-cols-2 gap-4">`;

        coreLayers.forEach(l => {
          const c = l.comp;
          if (!c) return;

          const driversHtml = (c.driven_by || []).map(d => 
            `<span class="bg-white/[0.05] border border-white/[0.08] text-slate-300 px-2 py-0.5 rounded text-[10px] font-mono">${d}</span>`
          ).join('');

          const altsHtml = (c.alternatives || []).map(a => `
            <div class="p-2.5 rounded-lg bg-surface-elevated/70 border border-white/[0.05] text-[11px] space-y-1">
              <div class="flex items-center justify-between">
                <span class="font-semibold text-slate-200">${a.choice}</span>
                <span class="text-[9px] font-bold uppercase tracking-wider text-slate-400 px-1.5 py-0.5 rounded bg-white/[0.06]">Rejected</span>
              </div>
              <p class="text-slate-400 leading-snug">${a.why_not}</p>
            </div>
          `).join('');

          const tradeoffsHtml = (c.tradeoffs || []).map(t => 
            `<li class="text-[11px] text-slate-400 leading-snug">${t}</li>`
          ).join('');

          html += `
            <div class="glass-card rounded-2xl p-5 flex flex-col justify-between space-y-4 border-t-2 ${l.borderAccent}">
              <div class="space-y-3">
                
                <!-- Card Header (Fixes Spacing Bug) -->
                <div class="flex items-center justify-between border-b border-white/[0.06] pb-2.5">
                  <div class="flex items-center gap-2">
                    <span class="text-xs uppercase tracking-wider font-bold ${l.textAccent} flex items-center gap-1.5">
                      <i class="fa-solid ${l.icon}"></i> ${l.name}
                    </span>
                  </div>
                  <span class="text-xs font-semibold px-2 py-0.5 rounded bg-white/[0.04] text-slate-400 font-mono">Core Layer</span>
                </div>

                <!-- Choice Title -->
                <div>
                  <h4 class="text-base font-bold text-white tracking-tight">${c.choice}</h4>
                  <p class="text-xs text-slate-300 leading-relaxed mt-1.5">${c.justification}</p>
                </div>

                <!-- Input Drivers -->
                ${c.driven_by && c.driven_by.length > 0 ? `
                  <div class="space-y-1.5 pt-1">
                    <span class="text-[10px] uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1">
                      <i class="fa-solid fa-arrows-to-dot text-brand-400"></i> Driven By Input Constraints:
                    </span>
                    <div class="flex flex-wrap gap-1.5">${driversHtml}</div>
                  </div>
                ` : ''}

                <!-- Rejected Alternatives -->
                ${c.alternatives && c.alternatives.length > 0 ? `
                  <div class="space-y-2 pt-2 border-t border-white/[0.06]">
                    <span class="text-[10px] uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1">
                      <i class="fa-solid fa-scale-balanced text-amber-400"></i> Evaluated Alternatives:
                    </span>
                    <div class="space-y-1.5">${altsHtml}</div>
                  </div>
                ` : ''}

                <!-- Operational Trade-offs -->
                ${c.tradeoffs && c.tradeoffs.length > 0 ? `
                  <div class="space-y-1 pt-1 border-t border-white/[0.06]">
                    <span class="text-[10px] uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1">
                      <i class="fa-solid fa-circle-info text-cyan-400"></i> Operational Trade-offs:
                    </span>
                    <ul class="list-disc pl-4 space-y-0.5">${tradeoffsHtml}</ul>
                  </div>
                ` : ''}

              </div>
            </div>
          `;
        });

        html += `</div>`;

        // Supporting Services Grid
        if (data.stack.supporting && data.stack.supporting.length > 0) {
          const suppIcons = {
            cache: "fa-bolt text-amber-400",
            queue: "fa-inbox text-indigo-400",
            search: "fa-magnifying-glass text-cyan-400",
            auth: "fa-key text-emerald-400",
            storage: "fa-box-archive text-blue-400",
            payments: "fa-credit-card text-emerald-400",
            realtime: "fa-tower-broadcast text-rose-400",
            ml: "fa-brain text-purple-400",
            observability: "fa-chart-line text-cyan-400",
            forms: "fa-file-lines text-slate-300",
            other: "fa-puzzle-piece text-slate-400"
          };

          html += `
            <div class="glass-card rounded-2xl p-5 space-y-3.5">
              <div class="flex items-center justify-between border-b border-white/[0.06] pb-3">
                <span class="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <i class="fa-solid fa-puzzle-piece text-brand-400"></i>
                  <span>Activated Supporting Services (${data.stack.supporting.length})</span>
                </span>
                <span class="text-[11px] text-slate-400">Conditioned dynamically on project requirements</span>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                ${data.stack.supporting.map(s => `
                  <div class="p-3.5 rounded-xl bg-surface-elevated/50 border border-white/[0.06] space-y-1.5 hover:border-white/[0.12] transition">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <i class="fa-solid ${suppIcons[s.layer] || 'fa-cubes'} text-xs"></i>
                        <span class="text-[10px] font-bold uppercase tracking-wider font-mono text-slate-400">${s.layer}</span>
                      </div>
                      <span class="text-xs font-bold text-white tracking-tight">${s.choice}</span>
                    </div>
                    <p class="text-[11px] text-slate-300 leading-snug">${s.justification}</p>
                    ${s.alternatives && s.alternatives.length > 0 ? `
                      <div class="text-[10px] text-slate-400 pt-1 border-t border-white/[0.04]">
                        <span class="text-slate-400 font-medium">Alternative:</span> ${s.alternatives[0].choice} (${s.alternatives[0].why_not})
                      </div>
                    ` : ''}
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }
      }

      // Documented Assumptions Applied
      if (data.assumptions && data.assumptions.length > 0) {
        html += `
          <div class="glass-card rounded-2xl p-4.5 space-y-2 border-white/[0.05]">
            <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <i class="fa-solid fa-list-check text-brand-400"></i> Documented Defaults & Assumptions Applied (${data.assumptions.length})
            </span>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-xs text-slate-300">
              ${data.assumptions.map(a => `
                <div class="flex items-center gap-2 bg-surface-elevated/40 px-2.5 py-1.5 rounded-lg border border-white/[0.04]">
                  <i class="fa-solid fa-check text-[9px] text-emerald-400"></i>
                  <span class="font-mono text-[11px] text-slate-300">${a}</span>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }

      // JSON Copy & Export Action Bar
      html += `
        <div class="glass-card rounded-2xl p-4 flex items-center justify-between gap-4">
          <div class="flex items-center gap-2">
            <span class="h-2 w-2 rounded-full bg-emerald-400"></span>
            <span class="text-xs text-slate-300 font-medium">Section 4 Output Ready</span>
          </div>
          
          <button id="copyJsonBtn" class="px-4 py-2 rounded-xl text-xs font-semibold bg-white/[0.06] hover:bg-white/[0.12] text-white border border-white/10 transition flex items-center gap-2">
            <i class="fa-regular fa-copy"></i>
            <span>Copy Section 4 JSON</span>
          </button>
        </div>
      `;

      outputContainer.innerHTML = html;

      // Bind copy button
      const copyBtn = document.getElementById('copyJsonBtn');
      if (copyBtn) {
        copyBtn.addEventListener('click', () => {
          navigator.clipboard.writeText(JSON.stringify(data, null, 2));
          copyBtn.innerHTML = '<i class="fa-solid fa-check text-emerald-400"></i> Copied to Clipboard!';
          setTimeout(() => {
            copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy Section 4 JSON';
          }, 2500);
        });
      }
    }

    // Run initialization
    initScenarios();
  </script>
</body>
</html>
"""
