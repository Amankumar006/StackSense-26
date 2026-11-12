"""Lightweight web dashboard and REST API for StackSense.

Enables judges and users to interactively test scenarios, tweak parameters,
and inspect visual recommendations per Section 2.1 (FR1) and Section 12 (FAQ).
"""

import json
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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
                    "category": "Edge Case",
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


@app.get("/", response_class=HTMLResponse)
def index_page() -> str:
    """Serves the interactive web UI dashboard."""
    return HTML_CONTENT


HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StackSense · Intelligent Tech Stack Recommendation Engine</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #0f172a; color: #f8fafc; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; }
    .layer-card { background: #1e293b; border-left: 4px solid #3b82f6; }
    pre { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  </style>
</head>
<body class="p-6">
  <div class="max-w-7xl mx-auto space-y-6">
    
    <!-- Header -->
    <header class="flex flex-col md:flex-row justify-between items-start md:items-center pb-4 border-b border-slate-700 gap-4">
      <div>
        <div class="flex items-center gap-3">
          <div class="p-2.5 bg-blue-600 rounded-lg text-white text-xl">
            <i class="fa-solid fa-layer-group"></i>
          </div>
          <div>
            <h1 class="text-2xl font-bold tracking-tight text-white">StackSense</h1>
            <p class="text-xs text-slate-400">Intelligent Tech Stack Recommendation Engine · Synergy '26 (IIIT Bangalore)</p>
          </div>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
          <i class="fa-solid fa-shield-halved mr-1.5"></i> Deterministic Engine (100% LLM-off)
        </span>
        <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-950 text-blue-400 border border-blue-800">
          <i class="fa-solid fa-database mr-1.5"></i> 37 Verified Technologies
        </span>
      </div>
    </header>

    <!-- Main Workspace -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      
      <!-- Left Column: Scenario Input -->
      <div class="lg:col-span-5 space-y-4">
        <div class="card p-5 space-y-4">
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-semibold text-white flex items-center gap-2">
              <i class="fa-solid fa-sliders text-blue-400 text-sm"></i> Scenario Input
            </h2>
            <select id="scenarioSelect" class="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:ring-blue-500 focus:border-blue-500">
              <option value="">-- Load Preset Scenario --</option>
            </select>
          </div>

          <p class="text-xs text-slate-400">
            Edit the Section 3.1 JSON payload below or select a benchmark scenario to run real-time constraint evaluation.
          </p>

          <div class="relative">
            <textarea id="jsonEditor" rows="18" class="w-full bg-slate-950 text-slate-200 font-mono text-xs p-3 rounded-lg border border-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed" spellcheck="false"></textarea>
          </div>

          <div class="flex items-center justify-between pt-2">
            <div class="text-xs text-slate-500" id="jsonValidationMsg">Valid Section 3.1 JSON</div>
            <button id="runBtn" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg flex items-center gap-2 shadow-lg shadow-blue-900/40 transition">
              <i class="fa-solid fa-bolt"></i> Generate Recommendation
            </button>
          </div>
        </div>
      </div>

      <!-- Right Column: Recommendation Output -->
      <div class="lg:col-span-7 space-y-4">
        
        <!-- Status & Summary Header -->
        <div id="outputContainer" class="space-y-4">
          <div class="card p-5 text-center text-slate-500 py-20">
            <i class="fa-solid fa-circle-nodes text-4xl mb-3 text-slate-700"></i>
            <p class="text-sm">Select a scenario on the left and click "Generate Recommendation".</p>
          </div>
        </div>

      </div>

    </div>

  </div>

  <script>
    const scenarioSelect = document.getElementById('scenarioSelect');
    const jsonEditor = document.getElementById('jsonEditor');
    const runBtn = document.getElementById('runBtn');
    const outputContainer = document.getElementById('outputContainer');
    const jsonValidationMsg = document.getElementById('jsonValidationMsg');

    // Fetch scenario list
    async function loadScenarioList() {
      try {
        const res = await fetch('/api/scenarios');
        const list = await res.json();
        
        const pubGroup = document.createElement('optgroup');
        pubGroup.label = "Public Benchmarks (P1 - P6)";
        const edgeGroup = document.createElement('optgroup');
        edgeGroup.label = "Section 6 Edge Cases (E1 - E11)";

        list.forEach(s => {
          const opt = document.createElement('option');
          opt.value = s.id;
          opt.textContent = `${s.id}: ${s.name} (${s.type})`;
          if (s.category === "Public Benchmark") pubGroup.appendChild(opt);
          else edgeGroup.appendChild(opt);
        });

        scenarioSelect.appendChild(pubGroup);
        scenarioSelect.appendChild(edgeGroup);

        // Load P2 as default
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
        jsonEditor.value = JSON.stringify(data, null, 2);
        validateJson();
        executeRecommendation();
      } catch (err) {
        console.error("Error loading scenario:", err);
      }
    }

    scenarioSelect.addEventListener('change', () => {
      loadScenario(scenarioSelect.value);
    });

    jsonEditor.addEventListener('input', validateJson);

    function validateJson() {
      try {
        JSON.parse(jsonEditor.value);
        jsonValidationMsg.textContent = "Valid JSON payload";
        jsonValidationMsg.className = "text-xs text-emerald-400";
        return true;
      } catch (e) {
        jsonValidationMsg.textContent = "Invalid JSON: " + e.message;
        jsonValidationMsg.className = "text-xs text-rose-400";
        return false;
      }
    }

    async function executeRecommendation() {
      if (!validateJson()) return;
      
      runBtn.disabled = true;
      runBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Evaluating...';

      try {
        const scenarioObj = JSON.parse(jsonEditor.value);
        const res = await fetch('/api/recommend', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario: scenarioObj, enable_llm: false })
        });
        const out = await res.json();
        renderOutput(out);
      } catch (err) {
        outputContainer.innerHTML = `<div class="card p-5 border-rose-800 text-rose-300">Execution Error: ${err.message}</div>`;
      } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Generate Recommendation';
      }
    }

    runBtn.addEventListener('click', executeRecommendation);

    function renderOutput(data) {
      let statusBadge = "";
      if (data.status === "ok") {
        statusBadge = '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800"><i class="fa-solid fa-circle-check mr-1"></i> STATUS: OK</span>';
      } else if (data.status === "ok_with_warnings") {
        statusBadge = '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-amber-950 text-amber-400 border border-amber-800"><i class="fa-solid fa-triangle-exclamation mr-1"></i> STATUS: OK WITH WARNINGS</span>';
      } else if (data.status === "infeasible") {
        statusBadge = '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-rose-950 text-rose-400 border border-rose-800"><i class="fa-solid fa-ban mr-1"></i> STATUS: INFEASIBLE</span>';
      } else {
        statusBadge = '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-rose-950 text-rose-400 border border-rose-800"><i class="fa-solid fa-circle-xmark mr-1"></i> STATUS: INVALID INPUT</span>';
      }

      let archBadge = data.architecture_style ? `<span class="px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">Arch: ${data.architecture_style.toUpperCase().replace('_', ' ')}</span>` : '';
      let costBadge = data.estimated_monthly_cost_usd ? `<span class="px-3 py-1 rounded-full text-xs font-bold bg-blue-950 text-blue-300 border border-blue-800">$${Math.round(data.estimated_monthly_cost_usd.min)} - $${Math.round(data.estimated_monthly_cost_usd.max)} / month</span>` : '';

      let html = `
        <div class="card p-5 space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div class="flex items-center gap-2">
              ${statusBadge}
              ${archBadge}
            </div>
            ${costBadge}
          </div>
          <p class="text-sm text-slate-200 leading-relaxed font-medium">${data.summary}</p>
        </div>
      `;

      // Validation Errors if any
      if (data.validation_errors && data.validation_errors.length > 0) {
        html += `
          <div class="card p-4 border-rose-800/80 bg-rose-950/20 space-y-2">
            <h3 class="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
              <i class="fa-solid fa-triangle-exclamation"></i> Validation Errors (${data.validation_errors.length})
            </h3>
            <ul class="text-xs text-rose-200 space-y-1">
              ${data.validation_errors.map(e => `<li><span class="font-mono text-rose-400 font-semibold">${e.field}:</span> ${e.message}</li>`).join('')}
            </ul>
          </div>
        `;
      }

      // Warnings if any
      if (data.warnings && data.warnings.length > 0) {
        html += `
          <div class="card p-4 border-amber-800/80 bg-amber-950/20 space-y-2">
            <h3 class="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
              <i class="fa-solid fa-bell"></i> Detected Constraints & Warnings (${data.warnings.length})
            </h3>
            <ul class="text-xs text-amber-200 space-y-1.5">
              ${data.warnings.map(w => `
                <li class="flex items-start gap-1.5">
                  <span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${w.severity === 'critical' ? 'bg-rose-900 text-rose-200' : 'bg-amber-900 text-amber-200'}">${w.severity.toUpperCase()}</span>
                  <span><strong>${w.code}:</strong> ${w.message}</span>
                </li>
              `).join('')}
            </ul>
          </div>
        `;
      }

      // Core Stack
      if (data.stack) {
        const layers = [
          { name: "Frontend", comp: data.stack.frontend, icon: "fa-desktop", color: "border-blue-500" },
          { name: "Backend", comp: data.stack.backend, icon: "fa-server", color: "border-indigo-500" },
          { name: "Database", comp: data.stack.database, icon: "fa-database", color: "border-purple-500" },
          { name: "Hosting", comp: data.stack.hosting, icon: "fa-cloud", color: "border-teal-500" },
        ];

        html += `<div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">`;
        layers.forEach(l => {
          const c = l.comp;
          if (!c) return;
          const alts = c.alternatives && c.alternatives.length > 0 
            ? c.alternatives.map(a => `<div class="text-[11px] text-slate-400 mt-1"><span class="text-slate-300 font-medium">${a.choice}:</span> ${a.why_not}</div>`).join('') 
            : '';
          const drivers = c.driven_by ? c.driven_by.map(d => `<span class="bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded text-[10px] font-mono">${d}</span>`).join(' ') : '';

          html += `
            <div class="card p-4 space-y-2 border-l-4 ${l.color}">
              <div class="flex justify-between items-start">
                <span class="text-[11px] uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1.5">
                  <i class="fa-solid ${l.icon}"></i> ${l.name}
                </span>
                <span class="text-sm font-bold text-white">${c.choice}</span>
              </div>
              <p class="text-xs text-slate-300 leading-relaxed">${c.justification}</p>
              ${drivers ? `<div class="pt-1 flex flex-wrap gap-1 items-center"><span class="text-[10px] text-slate-500 font-semibold mr-1">Driven By:</span> ${drivers}</div>` : ''}
              ${alts ? `<div class="pt-2 border-t border-slate-800/80"><span class="text-[10px] text-slate-500 uppercase font-bold">Rejected Alternatives</span>${alts}</div>` : ''}
            </div>
          `;
        });
        html += `</div>`;

        // Supporting Services
        if (data.stack.supporting && data.stack.supporting.length > 0) {
          html += `
            <div class="card p-4 space-y-3">
              <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <i class="fa-solid fa-puzzle-piece text-blue-400"></i> Supporting Services (${data.stack.supporting.length})
              </h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                ${data.stack.supporting.map(s => `
                  <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800 space-y-1">
                    <div class="flex justify-between items-center">
                      <span class="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-blue-950 text-blue-300 border border-blue-900">${s.layer}</span>
                      <span class="text-xs font-bold text-white">${s.choice}</span>
                    </div>
                    <p class="text-[11px] text-slate-300">${s.justification}</p>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }
      }

      // Assumptions
      if (data.assumptions && data.assumptions.length > 0) {
        html += `
          <div class="card p-4 space-y-2 border-slate-800 text-xs">
            <h3 class="font-bold text-slate-400 uppercase tracking-wider text-[11px]">Assumptions Applied (${data.assumptions.length})</h3>
            <ul class="list-disc pl-4 text-slate-400 space-y-0.5">
              ${data.assumptions.map(a => `<li>${a}</li>`).join('')}
            </ul>
          </div>
        `;
      }

      outputContainer.innerHTML = html;
    }

    // Initialize
    loadScenarioList();
  </script>
</body>
</html>
"""
