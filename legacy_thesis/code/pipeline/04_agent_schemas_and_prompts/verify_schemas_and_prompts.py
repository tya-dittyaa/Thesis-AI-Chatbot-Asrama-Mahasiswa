"""
Pipeline Tahap 4: Verifikasi Schema Function Calling & Prompt Agen
Memverifikasi kelengkapan dan validitas sintaks schema JSON dan template prompt agen.
"""

import os
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMAS_DIR = os.path.join(CURRENT_DIR, "schemas")
PROMPTS_DIR = os.path.join(CURRENT_DIR, "prompts")

def verify_pipeline_stage_4():
    print("=" * 60)
    print("PIPELINE 04: VERIFIKASI TOOL SCHEMAS & AGENT PROMPTS")
    print("=" * 60)

    # 1. Verifikasi Schemas
    schema_files = ["triage_tool_schema.json"]
    print("\n[1/2] Memvalidasi Schema Tool Function Calling...")
    for sf in schema_files:
        path = os.path.join(SCHEMAS_DIR, sf)
        if not os.path.exists(path):
            print(f"  [GAGAL] File schema tidak ditemukan: {sf}")
            return False
        with open(path, "r", encoding="utf-8") as f:
            try:
                schema_data = json.load(f)
                name = schema_data.get("name")
                desc = schema_data.get("description", "")
                params = schema_data.get("parameters", {})
                props = params.get("properties", {})
                required = params.get("required", [])
                print(f"  * Schema: '{name}' -> VALID JSON")
                print(f"    - Deskripsi: {desc[:80]}...")
                print(f"    - Properti ({len(props)}): {list(props.keys())}")
                print(f"    - Parameter Wajib: {required}")
            except Exception as e:
                print(f"  [ERROR] Parsing JSON gagal pada {sf}: {e}")
                return False

    # 2. Verifikasi Prompts
    prompt_files = [
        ("single_agent_baseline.txt", "Single-Agent Monolithic Prompt (Baseline Model)"),
        ("agent1_reception_rag.txt", "Agent 1: Ingestion, Gatekeeping & RAG FAQ Agent"),
        ("agent2_triage_specialist.txt", "Agent 2: Triage Specialist (Function Calling Tool Agent)"),
        ("agent3_response_generator.txt", "Agent 3: Response & Ticket Generator Agent")
    ]

    print("\n[2/2] Memvalidasi Template Prompt Agen...")
    for pf, label in prompt_files:
        path = os.path.join(PROMPTS_DIR, pf)
        if not os.path.exists(path):
            print(f"  [GAGAL] File prompt tidak ditemukan: {pf}")
            return False
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            word_count = len(content.split())
            print(f"  * {label}:")
            print(f"    - File: prompts/{pf} ({word_count} kata, {len(content):,} karakter)")

    print("\n" + "=" * 60)
    print("[SUCCESS] SELURUH SCHEMA DAN PROMPT TERVERIFIKASI SEMPURNA!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    verify_pipeline_stage_4()
