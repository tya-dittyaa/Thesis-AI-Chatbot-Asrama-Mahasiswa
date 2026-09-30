"""
Interactive Dual-Architecture Chatbot Demo for Thesis Defense
Binus Square Boarder Virtual Receptionist: Single Agent (Baseline) vs Multi-Agent System (Proposed)

Features:
- Dual-Mode Architecture Toggle in Sidebar:
  1. 🔀 Multi-Agent System (Proposed Method - Bab 3):
     - Agen 1: Front Desk, RAG FAQ Router & Dialog Manager (Stateful Context)
     - Agen 2: Triage & Taxonomy Specialist (Stateless Focused Context with Function Calling)
     - Agen 3: Ticket Dispatcher & Official Card Formatter (Execution Specialist)
  2. 👤 Single Agent (Baseline Method - Bab 3):
     - Monolithic Gemini LLM call handling conversation, RAG, 5-dept taxonomy, and ticketing in 1 context window
- Live Multi-Agent Inspector: Real-time latency, token usage, per-agent status, and actionable JSON payload
- Strict Room Number Prerequisite & Anti-Hallucination Grounding for Electricity Billing (kWh)
"""

import os
import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

# Set page config
st.set_page_config(
    page_title="Binus Square AI Receptionist (Dual Architecture Demo)",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Root paths
base_dir = Path(__file__).resolve().parent
workspace_root = base_dir.parent
pipeline_dir = workspace_root / "pipeline"

# Load .env
env_path = workspace_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
model_name = os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite"

# Check GenAI
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Add workspace root to sys.path
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

key_manager = None
client = None
if GENAI_AVAILABLE:
    try:
        from pipeline.api_key_manager import ApiKeyManager
        key_manager = ApiKeyManager(env_path=str(env_path) if env_path.exists() else None)
        client = key_manager.get_client()
    except Exception as e:
        if api_key and api_key.strip() != "your_gemini_api_key_here":
            try:
                client = genai.Client(api_key=api_key)
            except Exception:
                client = None

# Official Binus Square Taxonomy (from docs/departemen_dan_taksonomi_keluhan.md)
OFFICIAL_TAXONOMY = {
    "Estate Department": {
        "code": "ED",
        "categories": [
            "AC Service",
            "Room Maintenance",
            "Cleaning Service",
            "Electricity Usage",
            "Building Facilities",
            "Gym",
            "Swimming Pool",
            "Parking",
            "Security",
            "Shuttle Bus",
            "Telephone Signal",
            "Others"
        ]
    },
    "Operations": {
        "code": "OP",
        "categories": [
            "Internet",
            "Mail and Package",
            "Room Change",
            "Visitor",
            "Tenants (Laundry, Cafeteria, Coffee Shop, Mini Market, Copy Center)",
            "Games",
            "Others"
        ]
    },
    "Finance": {
        "code": "FN",
        "categories": [
            "Room Payment and Due Date",
            "Electricity Bill",
            "Security Deposit",
            "Others"
        ]
    },
    "Marketing": {
        "code": "MR",
        "categories": [
            "Renewal",
            "Check Out",
            "Promotion Program",
            "Guest Room Reservation",
            "Others"
        ]
    },
    "Student Support Office": {
        "code": "SO",
        "categories": [
            "Boarder's Behavior",
            "Rules and Regulations",
            "Academic Consultation",
            "Boarder's Programs and Events",
            "Others"
        ]
    }
}

DEPT_CODE_TO_NAME = {v["code"]: k for k, v in OFFICIAL_TAXONOMY.items()}
DEPT_NAME_TO_CODE = {k.lower(): v["code"] for k, v in OFFICIAL_TAXONOMY.items()}


# Load Handbook Chunks, Prompts & Vectorizer
@st.cache_resource
def load_resources():
    chunks_path = pipeline_dir / "03_handbook_rag_prep" / "data" / "handbook_chunks.json"
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    from sklearn.feature_extraction.text import TfidfVectorizer
    docs = [c.get("section_title", "") + " " + c.get("text_content", "") for c in chunks]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
    doc_vectors = vectorizer.fit_transform(docs)

    # Load official pipeline prompts if available
    prompts_dir = pipeline_dir / "04_agent_schemas_and_prompts" / "prompts"
    prompts = {}
    for p_name in ["agent1_reception_rag", "agent2_triage_specialist", "agent3_response_generator", "single_agent_baseline"]:
        f_path = prompts_dir / f"{p_name}.txt"
        if f_path.exists():
            with open(f_path, "r", encoding="utf-8") as f:
                prompts[p_name] = f.read()
        else:
            prompts[p_name] = ""
    
    # Load triage tool schema
    schema_path = pipeline_dir / "04_agent_schemas_and_prompts" / "schemas" / "triage_tool_schema.json"
    triage_schema = {}
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            triage_schema = json.load(f)

    return chunks, vectorizer, doc_vectors, prompts, triage_schema

chunks, vectorizer, doc_vectors, pipeline_prompts, triage_tool_schema = load_resources()


# Bilingual Query Expansion for RAG Handbook Retrieval (Indonesian to English terms)
SYNONYM_EXPANSION = {
    "tamu": "visitor guest",
    "kunjung": "visiting hours",
    "kunjungan": "visiting hours",
    "kolam": "swimming pool",
    "renang": "swimming",
    "gym": "fitness center gym",
    "fitness": "fitness center gym",
    "denda": "fine penalty charge",
    "laundry": "laundry washing quota",
    "cuci": "laundry wash",
    "baju": "clothes laundry",
    "listrik": "electricity meter kwh",
    "kwh": "electricity meter kwh",
    "pindah": "room change move",
    "kunci": "key card replacement lost",
    "kartu": "access key card",
    "hilang": "lost replacement fine",
    "paket": "mail package",
    "kurir": "courier package",
    "parkir": "parking vehicle",
    "shuttle": "shuttle bus schedule",
    "wifi": "internet wifi connection",
    "deposit": "security deposit refund"
}


def search_handbook(query: str, top_k: int = 2, threshold: float = 0.08):
    """Semantic RAG retrieval with keyword expansion and similarity thresholding."""
    from sklearn.metrics.pairwise import cosine_similarity
    if not query.strip():
        return []

    # Semantic Keyword Expansion (bilingual bridge to English handbook)
    expanded_q = query.lower()
    for id_term, en_terms in SYNONYM_EXPANSION.items():
        if id_term in expanded_q:
            expanded_q += " " + en_terms

    q_vec = vectorizer.transform([expanded_q])
    sim = cosine_similarity(q_vec, doc_vectors)[0]
    top_indices = sim.argsort()[-top_k:][::-1]
    results = []
    for idx in top_indices:
        score = float(sim[idx])
        # Only inject chunk if similarity meets or exceeds semantic threshold
        if score >= threshold:
            c = chunks[idx].copy()
            c["score"] = score
            results.append(c)
    return results


# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Halo! Saya **Resepsionis Virtual Binus Square**. 👋\n\nAda yang bisa saya bantu hari ini? Anda dapat bertanya mengenai aturan dan fasilitas asrama, atau melaporkan kendala di kamar Anda."
        }
    ]

if "last_trace" not in st.session_state:
    st.session_state.last_trace = None

if "session_stats" not in st.session_state:
    st.session_state.session_stats = {
        "turns": 0,
        "total_latency": 0.0,
        "total_tokens": 0,
        "history": []
    }


def validate_and_extract_room(raw_room: str) -> str:
    """
    Deterministic Schema Guardrail for Binus Square Room Numbers.
    Standard Binus Square rooms: Tower A or B followed by 3-4 digits (e.g., A1249, B512, 512, 1204).
    Returns sanitized room string if valid, otherwise empty string ''.
    """
    if not raw_room:
        return ""
    match = re.search(r'\b(?:Tower\s*)?([ABab]?[- ]?\d{3,4})\b', str(raw_room).strip())
    if match:
        extracted = match.group(1).replace(" ", "").replace("-", "").upper()
        return extracted
    return ""


def format_ticket_card(ticket_data: dict) -> str:
    """Format clean digital ticket card for chat display adhering strictly to Binus Square standard."""
    urg = ticket_data.get("urgency_level", "Medium")
    urg_badge = {
        "Emergency": "🔴 **DARURAT (EMERGENCY)**",
        "High": "🟠 **TINGGI (HIGH PRIORITY)**",
        "Medium": "🔵 **SEDANG (MEDIUM)**",
        "Low": "🟢 **RENDAH (LOW)**"
    }.get(urg, f"🔵 **{urg}**")

    dept_name = ticket_data.get("target_department", "Estate Department")
    dept_code = ticket_data.get("department_code") or OFFICIAL_TAXONOMY.get(dept_name, {}).get("code", "ED")
    cat_name = ticket_data.get("subject_category", "Others")
    room_num = ticket_data.get("room_number", "Kamar Penghuni")
    title = ticket_data.get("problem_title", "Laporan Kendala Fasilitas")
    schedule = ticket_data.get("preferred_schedule", "Sesuai ketersediaan penghuni / jam kerja")
    complaint_detail = ticket_data.get("detailed_complaint", "Keluhan telah dicatat untuk ditindaklanjuti.")
    
    card = f"""
### 🎫 Bukti Tiket Layanan: `{ticket_data.get('ticket_id', 'TKT-BSQ')}`
**Status:** 🟢 **OPEN — TERKIRIM KE DEPARTEMEN** &nbsp;|&nbsp; **Prioritas:** {urg_badge}

---
#### 📋 Ringkasan Laporan: **{title}**

| Parameter Tiket | Rincian Resmi Binus Square |
| :--- | :--- |
| 📍 **Lokasi / Kamar** | **Kamar {room_num}** |
| 🏢 **Departemen Penangan** | **{dept_name}** (`{dept_code}`) |
| 🏷️ **Kategori Subjek Resmi** | **{cat_name}** |
| 🔧 **Komponen / Objek** | *{ticket_data.get('facility_item', 'Fasilitas Kamar')}* |
| 📅 **Jadwal Kunjungan Teknisi** | {schedule} |
| 📝 **Rincian Kendala** | {complaint_detail} |

---
*Tiket resmi ini dapat dipantau langsung perkembangannya melalui Boarder Portal Binus Square.*
"""
    return card


# Tool Declarations
def get_single_agent_tool_declaration():
    """Tool for Single Agent Baseline."""
    all_categories = []
    for dept, info in OFFICIAL_TAXONOMY.items():
        all_categories.extend(info["categories"])
    unique_categories = sorted(list(set(all_categories)))

    return types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="create_official_ticket",
            description="PANGGIL FUNGSI INI HANYA DAN HANYA JIKA: (1) Nomor kamar penghuni SUDAH DIKETAHUI secara jelas (misal: 512, A1249), DAN (2) Pesan TERAKHIR mahasiswa secara spesifik mengonfirmasi/menyetujui penerbitan tiket baru. DILARANG KERAS memanggil fungsi ini jika nomor kamar belum diinfokan!",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "target_department": {
                        "type": "STRING",
                        "enum": [
                            "Estate Department",
                            "Operations",
                            "Finance",
                            "Marketing",
                            "Student Support Office"
                        ],
                        "description": "Departemen penangan resmi Binus Square."
                    },
                    "subject_category": {
                        "type": "STRING",
                        "enum": unique_categories,
                        "description": "Kategori subjek resmi Binus Square yang paling tepat."
                    },
                    "room_number": {
                        "type": "STRING",
                        "description": "Nomor kamar penghuni yang valid (contoh: '512', 'A1249')."
                    },
                    "urgency_level": {
                        "type": "STRING",
                        "enum": ["Low", "Medium", "High", "Emergency"],
                        "description": "Tingkat urgensi penanganan."
                    },
                    "facility_item": {
                        "type": "STRING",
                        "description": "Objek fisik yang bermasalah (contoh: 'Unit AC Kamar', 'Keran Wastafel')."
                    },
                    "problem_title": {
                        "type": "STRING",
                        "description": "Judul masalah padat dan informatif."
                    },
                    "detailed_complaint": {
                        "type": "STRING",
                        "description": "Rangkuman lengkap keluhan penghuni."
                    },
                    "preferred_schedule": {
                        "type": "STRING",
                        "description": "Preferensi jadwal ketersediaan penghuni."
                    }
                },
                "required": [
                    "target_department",
                    "subject_category",
                    "room_number",
                    "urgency_level",
                    "facility_item",
                    "problem_title",
                    "detailed_complaint",
                    "preferred_schedule"
                ]
            }
        )
    ])


def get_agent1_delegate_tool():
    """Tool for Agen 1 to handoff confirmed complaint to Agen 2."""
    return types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="delegate_to_triage",
            description="Panggil hanya jika nomor kamar valid dan mahasiswa menyetujui pembuatan tiket perbaikan.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "room_number": {"type": "STRING", "description": "Nomor kamar valid (misal: A1249, 512)."},
                    "complaint_summary": {"type": "STRING", "description": "Ringkasan keluhan fasilitas."},
                    "preferred_schedule": {"type": "STRING", "description": "Jadwal ketersediaan penghuni."}
                },
                "required": ["room_number", "complaint_summary"]
            }
        )
    ])


def get_agent2_triage_tool():
    """Tool for Agen 2 to execute taxonomy triage."""
    if triage_tool_schema:
        return types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name=triage_tool_schema["name"],
                description=triage_tool_schema["description"],
                parameters=triage_tool_schema["parameters"]
            )
        ])
    
    # Fallback declaration
    return types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="route_and_classify_complaint",
            description="Fungsi otomatisasi triase keluhan fasilitas hunian mahasiswa Binus Square.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "target_department": {"type": "STRING", "enum": ["ED", "OP", "FN", "MR", "SO"]},
                    "target_department_name": {
                        "type": "STRING",
                        "enum": ["Estate Department", "Operations", "Finance", "Marketing", "Student Support Office"]
                    },
                    "problem_category": {"type": "STRING"},
                    "urgency_level": {"type": "STRING", "enum": ["Low", "Medium", "High", "Emergency"]},
                    "facility_item": {"type": "STRING"},
                    "location_context": {"type": "STRING"},
                    "reasoning_summary": {"type": "STRING"}
                },
                "required": ["target_department", "target_department_name", "problem_category", "urgency_level", "facility_item"]
            }
        )
    ])


def build_chat_contents(max_window: int = 6):
    """Build clean alternating conversation history for multi-turn chat with sliding window."""
    # Batasi hanya N pesan terakhir (sliding window) agar tidak terjadi memory inflation / boros token
    recent_msgs = st.session_state.messages[-max_window:] if len(st.session_state.messages) > max_window else st.session_state.messages
    contents = []
    for msg in recent_msgs:
        if msg["role"] == "assistant" and len(contents) == 0:
            continue
        role = "user" if msg["role"] == "user" else "model"
        txt = msg.get("content", "")
        if "### 🎫" in txt:
            card_split = txt.split("### 🎫")
            txt = card_split[0].strip() + "\n[Sistem: Tiket resmi telah dibuat]"
        txt = re.sub(r'```(?:action_trace|json|action_handoff)?\s*\{.*?\}\s*```', '', txt, flags=re.DOTALL).strip()
        if txt:
            if contents and contents[-1].role == role:
                contents[-1].parts[0].text += f"\n{txt}"
            else:
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=txt)]))
    return contents


def call_with_retry(model, contents, config, max_retries=3):
    """Auto-retry with backoff, multi-key rotation, and model fallback on temporary 503/429 spikes."""
    models_to_try = [model, "gemini-2.5-flash"]
    last_err = None
    for m in models_to_try:
        for attempt in range(max_retries):
            try:
                active_client = key_manager.get_random_client() if key_manager else client
                if not active_client:
                    raise ValueError("Client API Gemini belum terkonfigurasi di .env")
                resp = active_client.models.generate_content(
                    model=m,
                    contents=contents,
                    config=config
                )
                return resp
            except Exception as err:
                last_err = err
                err_str = str(err).lower()
                is_rate = any(k in err_str for k in ["503", "429", "unavailable", "resourceexhausted", "high demand", "quota"])
                if is_rate:
                    if key_manager and len(key_manager.keys) > 1 and ("429" in err_str or "quota" in err_str or "resourceexhausted" in err_str):
                        key_manager.rotate(wait_sec=1)
                    time.sleep(1.0)
                    continue
                else:
                    raise err
    raise last_err or Exception("Server AI sedang sibuk.")


# ==============================================================================
# ARCHITECTURE 1: SINGLE AGENT BASELINE (MONOLITHIC CONTEXT)
# ==============================================================================
def process_single_agent(user_msg: str, top_chunks: list) -> str:
    rag_context = ""
    if top_chunks:
        rag_context = "\n\n".join([f"[{c['section_title']} (Halaman {c['page_start']})]\n{c['text_content']}" for c in top_chunks])

    taxonomy_text = "\n".join([f"- {dept} ({data['code']}): {', '.join(data['categories'])}" for dept, data in OFFICIAL_TAXONOMY.items()])

    system_instruction = f"""Asisten AI monolitik (Single-Agent Baseline) portal hunian Binus Square.
Tugas: Menjawab FAQ aturan, menyaring topik luar asrama, menentukan taksonomi 5 departemen, dan memanggil create_official_ticket.
ATURAN LISTRIK (kWh): Kuota gratis HANYA laundry (21 kg/bln). Listrik dihitung meteran kamar oleh Finance (FN). Dilarang mengarang angka kuota listrik.
SYARAT TIKET: Nomor kamar WAJIB ada dan valid. Panggil create_official_ticket hanya jika nomor kamar ada & disetujui.

TAKSONOMI 5 DEPARTEMEN:
{taxonomy_text}

{f"RAG CONTEXT:\n{rag_context}" if rag_context else ""}
"""
    contents = build_chat_contents()
    tool = get_single_agent_tool_declaration()
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.3,
        tools=[tool]
    )

    t0 = time.time()
    resp = call_with_retry(model_name, contents, config)
    lat = time.time() - t0
    usage = getattr(resp, "usage_metadata", None)
    in_tokens = getattr(usage, "prompt_token_count", 0) or 0
    out_tokens = getattr(usage, "candidates_token_count", 0) or 0
    tokens = in_tokens + out_tokens

    func_name = ""
    tool_args = {}
    if hasattr(resp, "function_calls") and resp.function_calls:
        fc = resp.function_calls[0]
        func_name = getattr(fc, "name", "")
        tool_args = dict(fc.args) if hasattr(fc, "args") and fc.args else {}
    elif resp.candidates and resp.candidates[0].content and resp.candidates[0].content.parts:
        for part in resp.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                func_name = part.function_call.name
                tool_args = dict(part.function_call.args) if part.function_call.args else {}
                break

    if func_name == "create_official_ticket" and tool_args:
        raw_room = str(tool_args.get("room_number", "")).strip()
        room_num = validate_and_extract_room(raw_room)
        if not room_num:
            st.session_state.last_trace = {
                "architecture": "SINGLE_AGENT_BASELINE",
                "type": "CLARIFICATION_AND_CONFIRMATION",
                "latency": round(lat, 3),
                "tokens": tokens,
                "reasoning": "Single Agent mendeteksi format nomor kamar belum valid sesuai standar Binus Square."
            }
            return (
                "Baik Kak, detail kendala dan jadwalnya sudah saya catat ya. 😊\n\n"
                "Namun mohon bantuannya untuk menginfokan **nomor kamar Kakak** (contoh: 512 atau A1249)? "
                "Rekan-rekan teknisi wajib mengetahui lokasi kamar yang tepat sebelum tiket perbaikan resmi bisa diterbitkan ke sistem. Ditunggu nomor kamarnya ya Kak! 🙏"
            )

        ticket_num = f"TKT-BSQ-{datetime.now().strftime('%Y%m')}-{int(time.time()) % 10000:04d}"
        tool_args["ticket_id"] = ticket_num
        tool_args["room_number"] = room_num
        tool_args["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dept = tool_args.get("target_department", "Estate Department")
        tool_args["department_code"] = OFFICIAL_TAXONOMY.get(dept, {}).get("code", "ED")
        
        card = format_ticket_card(tool_args)
        greeting = (
            f"Sip Kak! Tiket resminya sudah berhasil saya buatkan ya. 😊🙏\n\n"
            f"Laporan Kakak untuk Kamar **{room_num}** sudah langsung kami teruskan ke rekan-rekan di **{dept}** "
            f"agar dapat ditindaklanjuti sesuai jadwal ketersediaan yang Kakak tentukan.\n\n"
            f"Berikut bukti rincian tiket resminya ya Kak:\n\n{card}\n\n"
            f"Ada hal lain lagi yang bisa saya bantu, Kak?"
        )
        st.session_state.last_trace = {
            "architecture": "SINGLE_AGENT_BASELINE",
            "type": "OFFICIAL_TICKET_CREATED",
            "latency": round(lat, 3),
            "tokens": tokens,
            "in_tokens": in_tokens,
            "out_tokens": out_tokens,
            "ticket": tool_args,
            "reasoning": f"Single Agent Baseline mengeksekusi tool dalam 1 pemanggilan monolitik untuk {dept} ({tool_args.get('subject_category')})."
        }
        return greeting

    reply_text = resp.text or ""
    st.session_state.last_trace = {
        "architecture": "SINGLE_AGENT_BASELINE",
        "type": "HANDBOOK_RAG_ANSWER" if top_chunks else "GENERAL_CONVERSATION",
        "latency": round(lat, 3),
        "tokens": tokens,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "matched_section": top_chunks[0]["section_title"] if top_chunks else None,
        "page": top_chunks[0]["page_start"] if top_chunks else None,
        "reasoning": "Single Agent Baseline memproses percakapan/FAQ dalam 1 context window monolitik."
    }
    return reply_text if reply_text.strip() else "Halo Kak! Ada yang bisa saya bantu terkait hunian Binus Square? 😊"


# ==============================================================================
# ARCHITECTURE 2: MULTI-AGENT SYSTEM (PROPOSED 3-AGENT PIPELINE)
# ==============================================================================
def process_multi_agent(user_msg: str, top_chunks: list) -> str:
    rag_context = ""
    if top_chunks:
        rag_context = "\n\n".join([f"[{c['section_title']} (Halaman {c['page_start']})]\n{c['text_content']}" for c in top_chunks])

    # ---------------------------------------------------------
    # STEP 1: AGEN 1 (Front Desk & RAG Router - Stateful Memory)
    # ---------------------------------------------------------
    agent1_system_prompt = f"""Resepsionis Virtual Meja Depan Binus Square. Ramah & efisien ('Halo Kak', 'Baik Kak').
Tugas:
1. INFORMATIONAL_QUERY: Jawab pertanyaan aturan asrama secara faktual dari RAG CONTEXT. Listrik (kWh) dihitung meteran kamar oleh Finance (FN) via Boarder Portal; kuota gratis HANYALAH laundry 21 kg/bulan. Dilarang mengarang kuota listrik.
2. OUT_OF_SCOPE: Tolak sopan di luar urusan hunian asrama, arahkan kembali ke fasilitas hunian.
3. EMERGENCY: Darurat medis/kesehatan arahkan ke Security Lobby Ext 0 / RS Siloam.
4. COMPLAINT (Kendala Kamar):
   - Jika belum ada nomor kamar: Sambut ramah & tanyakan nomor kamar serta rincian kendalanya. JANGAN delegasikan!
   - Jika nomor kamar ada tapi belum minta tiket: Konfirmasi kesediaan tiket & jadwal. JANGAN delegasikan!
   - Jika nomor kamar valid & disetujui: PANGGIL delegate_to_triage.

{f"RAG CONTEXT (Handbook):\n{rag_context}" if rag_context else ""}
"""
    contents = build_chat_contents()
    agent1_tool = get_agent1_delegate_tool()
    config1 = types.GenerateContentConfig(
        system_instruction=agent1_system_prompt,
        temperature=0.2,
        tools=[agent1_tool]
    )

    t0_agent1 = time.time()
    resp1 = call_with_retry(model_name, contents, config1)
    lat_agent1 = time.time() - t0_agent1
    usage1 = getattr(resp1, "usage_metadata", None)
    in_tok1 = getattr(usage1, "prompt_token_count", 0) or 0
    out_tok1 = getattr(usage1, "candidates_token_count", 0) or 0
    tok_agent1 = in_tok1 + out_tok1

    # Check if Agen 1 triggered handoff to Agen 2
    handoff_args = {}
    if hasattr(resp1, "function_calls") and resp1.function_calls:
        fc = resp1.function_calls[0]
        if getattr(fc, "name", "") == "delegate_to_triage":
            handoff_args = dict(fc.args) if hasattr(fc, "args") and fc.args else {}
    elif resp1.candidates and resp1.candidates[0].content and resp1.candidates[0].content.parts:
        for part in resp1.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call and part.function_call.name == "delegate_to_triage":
                handoff_args = dict(part.function_call.args) if part.function_call.args else {}
                break

    # If Agen 1 did NOT trigger handoff, it resolved the query directly (FAQ / Clarification / Out-of-scope)
    if not handoff_args:
        reply_text = resp1.text or ""
        reply_text = re.sub(r'```(?:action_handoff|action_trace|json)?\s*\{.*?\}\s*```', '', reply_text, flags=re.DOTALL).strip()
        
        # Check intent for inspector based on whether semantic RAG was triggered
        is_rag = bool(top_chunks)
        intent_type = "HANDBOOK_RAG_ANSWER" if is_rag else "CONVERSATION_AND_CLARIFICATION"

        st.session_state.last_trace = {
            "architecture": "MULTI_AGENT_SYSTEM",
            "type": intent_type,
            "active_agents": ["Agen 1 (Front Desk)"],
            "agent1": {
                "role": "Receptionist & Dialog Router",
                "status": "Dijawab Langsung (FAQ / Percakapan)",
                "latency": round(lat_agent1, 3),
                "tokens": tok_agent1,
                "in_tokens": in_tok1,
                "out_tokens": out_tok1
            },
            "total_latency": round(lat_agent1, 3),
            "total_tokens": tok_agent1,
            "in_tokens": in_tok1,
            "out_tokens": out_tok1,
            "matched_section": top_chunks[0]["section_title"] if is_rag else None,
            "page": top_chunks[0]["page_start"] if is_rag else None,
            "reasoning": "Agen 1 menangani percakapan/RAG langsung tanpa membebani Agen 2 & Agen 3 (Context Window Bersih)."
        }
        return reply_text if reply_text.strip() else "Halo Kak! Ada yang bisa saya bantu terkait hunian Binus Square? 😊"

    # ---------------------------------------------------------
    # STEP 2: AGEN 2 (Triage & Taxonomy Specialist - Stateless)
    # ---------------------------------------------------------
    raw_room = str(handoff_args.get("room_number", "")).strip()
    room_number = validate_and_extract_room(raw_room)
    complaint_summary = str(handoff_args.get("complaint_summary", "Kerusakan fasilitas kamar")).strip()
    preferred_schedule = str(handoff_args.get("preferred_schedule", "Sesuai ketersediaan penghuni / jam operasional")).strip()

    # Backend Guardrail check
    if not room_number:
        st.session_state.last_trace = {
            "architecture": "MULTI_AGENT_SYSTEM",
            "type": "CLARIFICATION_AND_CONFIRMATION",
            "active_agents": ["Agen 1 (Front Desk)"],
            "agent1": {
                "role": "Receptionist & Dialog Router",
                "status": "Nomor Kamar Belum Valid (Ditahan)",
                "latency": round(lat_agent1, 3),
                "tokens": tok_agent1
            },
            "total_latency": round(lat_agent1, 3),
            "total_tokens": tok_agent1,
            "reasoning": "Agen 1 menahan handoff ke Agen 2 karena nomor kamar belum valid sesuai format Binus Square."
        }
        return (
            "Baik Kak, detail kendala dan jadwalnya sudah saya catat ya. 😊\n\n"
            "Namun mohon bantuannya untuk menginfokan **nomor kamar Kakak** terlebih dahulu (contoh: 512 atau A1249)? "
            "Rekan-rekan teknisi wajib mengetahui lokasi kamar yang tepat sebelum tiket perbaikan resmi bisa diterbitkan ke sistem. Ditunggu nomor kamarnya ya Kak! 🙏"
        )

    # Prepare Agen 2 system instruction & tool
    agent2_prompt = pipeline_prompts.get("agent2_triage_specialist") or """
Anda adalah Agen 2: Spesialis Triase & Klasifikasi Keluhan untuk fasilitas hunian Binus Square.
Anda menerima laporan keluhan yang telah divalidasi oleh Agen 1. Tugas Anda adalah menganalisis keluhan dan WAJIB memanggil fungsi tool `route_and_classify_complaint`.
Direktori 5 Departemen:
1. Estate Department (ED): Fasilitas fisik, AC, perabot kamar, kelistrikan fisik, pipa/air, kebersihan.
2. Operations (OP): Front Office, internet/WiFi, paket, pindah kamar, tenant komersial, izin tamu.
3. Finance (FN): Pembayaran sewa, tagihan listrik kWh, deposit.
4. Marketing (MR): Renewal kontrak sewa, checkout keluar asrama, promo.
5. Student Support Office (SO): Tata tertib, kebisingan, konflik teman sekamar, konseling.
"""
    agent2_tool = get_agent2_triage_tool()
    config2 = types.GenerateContentConfig(
        system_instruction=agent2_prompt,
        temperature=0.1,
        tools=[agent2_tool]
    )

    agent2_input = f"""LAPORAN KELUHAN TERVERIFIKASI DARI AGEN 1:
- Nomor Kamar: {room_number}
- Rincian Kendala: {complaint_summary}
- Preferensi Jadwal: {preferred_schedule}

Silakan analisis taksonomi dan panggil fungsi tool `route_and_classify_complaint`."""

    t0_agent2 = time.time()
    resp2 = call_with_retry(model_name, agent2_input, config2)
    lat_agent2 = time.time() - t0_agent2
    usage2 = getattr(resp2, "usage_metadata", None)
    in_tok2 = getattr(usage2, "prompt_token_count", 0) or 0
    out_tok2 = getattr(usage2, "candidates_token_count", 0) or 0
    tok_agent2 = in_tok2 + out_tok2

    triage_args = {}
    if hasattr(resp2, "function_calls") and resp2.function_calls:
        triage_args = dict(resp2.function_calls[0].args) if hasattr(resp2.function_calls[0], "args") else {}
    elif resp2.candidates and resp2.candidates[0].content and resp2.candidates[0].content.parts:
        for part in resp2.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                triage_args = dict(part.function_call.args) if part.function_call.args else {}
                break

    dept_code = triage_args.get("target_department", "ED")
    dept_name = triage_args.get("target_department_name") or DEPT_CODE_TO_NAME.get(dept_code, "Estate Department")
    # Clean taxonomy extraction: fallback to "Others" without biased heuristic keywords
    category = triage_args.get("problem_category") or "Others"
    urgency = triage_args.get("urgency_level", "Medium")
    facility_item = triage_args.get("facility_item", "Fasilitas Kamar")
    reasoning_summary = triage_args.get("reasoning_summary", f"Diarahkan ke {dept_name} sesuai taksonomi resmi.")

    # ---------------------------------------------------------
    # STEP 3: AGEN 3 (Ticket Dispatcher & Formatter)
    # ---------------------------------------------------------
    ticket_num = f"TKT-BSQ-{datetime.now().strftime('%Y%m')}-{int(time.time()) % 10000:04d}"
    lat_agent3 = 0.05
    tok_agent3 = 0

    ticket_data = {
        "ticket_id": ticket_num,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "OPEN",
        "target_department": dept_name,
        "department_code": dept_code,
        "subject_category": category,
        "room_number": room_number,
        "urgency_level": urgency,
        "facility_item": facility_item,
        "problem_title": f"{category} Kamar {room_number}",
        "detailed_complaint": complaint_summary,
        "preferred_schedule": preferred_schedule,
        "triage_reasoning": reasoning_summary
    }

    card = format_ticket_card(ticket_data)
    receptionist_greeting = (
        f"Sip Kak! Tiket resminya sudah berhasil saya buatkan ya. 😊🙏\n\n"
        f"Laporan Kakak untuk Kamar **{room_number}** sudah langsung kami teruskan ke rekan-rekan di **{dept_name}** "
        f"agar dapat ditindaklanjuti sesuai jadwal ketersediaan yang Kakak tentukan ({preferred_schedule}).\n\n"
        f"Berikut bukti rincian tiket resminya ya Kak:\n\n{card}\n\n"
        f"Ada hal lain lagi yang bisa saya bantu, Kak?"
    )

    tot_lat = round(lat_agent1 + lat_agent2 + lat_agent3, 3)
    tot_tok = tok_agent1 + tok_agent2 + tok_agent3
    tot_in = in_tok1 + in_tok2
    tot_out = out_tok1 + out_tok2

    st.session_state.last_trace = {
        "architecture": "MULTI_AGENT_SYSTEM",
        "type": "OFFICIAL_TICKET_CREATED",
        "active_agents": ["Agen 1 (Front Desk)", "Agen 2 (Triase)", "Agen 3 (Eksekutor Tiket)"],
        "agent1": {
            "role": "Receptionist & Dialog Router",
            "status": f"Handoff Sukses (Kamar {room_number} Terverifikasi)",
            "latency": round(lat_agent1, 3),
            "tokens": tok_agent1,
            "in_tokens": in_tok1,
            "out_tokens": out_tok1
        },
        "agent2": {
            "role": "Triage & Taxonomy Specialist",
            "status": "Function Calling `route_and_classify_complaint` Berhasil",
            "department": f"{dept_name} ({dept_code})",
            "category": category,
            "urgency": urgency,
            "latency": round(lat_agent2, 3),
            "tokens": tok_agent2,
            "in_tokens": in_tok2,
            "out_tokens": out_tok2
        },
        "agent3": {
            "role": "Ticket Dispatcher & Formatter",
            "status": "Tiket Resmi Diterbitkan & Terverifikasi",
            "ticket_id": ticket_num,
            "latency": round(lat_agent3, 3),
            "tokens": tok_agent3,
            "in_tokens": 0,
            "out_tokens": 0
        },
        "total_latency": tot_lat,
        "total_tokens": tot_tok,
        "in_tokens": tot_in,
        "out_tokens": tot_out,
        "ticket": ticket_data,
        "reasoning": f"Pipeline Multi-Agent sukses: Agen 1 memvalidasi keluhan -> Agen 2 melakukan triase ke {dept_name} ({category}) -> Agen 3 menerbitkan tiket resmi {ticket_num}."
    }

    return receptionist_greeting


def process_user_input(user_msg: str, arch_mode: str) -> str:
    # 1. Semantic RAG Search with Relevance Threshold (Only injects handbook if query is relevant)
    top_chunks = search_handbook(user_msg, top_k=2, threshold=0.08)

    active_client = key_manager.get_client() if key_manager else client
    if not active_client:
        st.session_state.last_trace = {
            "type": "API_KEY_MISSING",
            "reasoning": "GEMINI_API_KEY belum dikonfigurasi di file .env."
        }
        return "Halo Kak! Kunci API Gemini belum terkonfigurasi. Silakan isi `GEMINI_API_KEY` pada file `.env` untuk mengaktifkan AI Resepsionis."

    try:
        if "Single Agent" in arch_mode:
            return process_single_agent(user_msg, top_chunks)
        else:
            return process_multi_agent(user_msg, top_chunks)
    except Exception as e:
        st.session_state.last_trace = {
            "type": "SYSTEM_EXCEPTION",
            "reasoning": f"Koneksi LLM terputus: {str(e)}"
        }
        return "Aduh maaf banget ya Kak, server pusat AI kami sedang padat sesaat. 🥺 Boleh mohon bantu kirim ulang pesan Kakak sekali lagi? 🙏"


# ==============================================================================
# UI LAYOUT & SIDEBAR INSPECTOR
# ==============================================================================
# SIDEBAR: Multi-Agent Live Inspector & Presets
with st.sidebar:
    st.header("⚙️ Mode Arsitektur")
    arch_mode = st.radio(
        "Pilih Model Evaluasi:",
        options=[
            "🔀 Multi-Agent System (Proposed)",
            "👤 Single Agent (Baseline)"
        ],
        index=0,
        key="arch_mode_select",
        help="Bandingkan arsitektur Multi-Agent (Agen 1 -> Agen 2 -> Agen 3) dengan Single Agent Baseline monolitik."
    )

    st.divider()
    st.caption(f"🤖 Model: `{model_name}`")
    if key_manager:
        st.caption(f"🔑 API Keys: `{len(key_manager.keys)} keys aktif` (Multi-Key Balanced)")
    st.subheader("🔍 Live Inspector")

    # Status Monitor
    if st.session_state.last_trace:
        trace = st.session_state.last_trace
        arch = trace.get("architecture", "")
        t_type = trace.get("type", "")
        reasoning = trace.get("reasoning", "")

        # Multi-Agent Mode Inspector View
        if arch == "MULTI_AGENT_SYSTEM":
            st.info("Pipeline: **Multi-Agent System**")
            
            # Step 1: Agen 1
            ag1 = trace.get("agent1", {})
            st.markdown(f"**Agen 1 (Front Desk):** `{ag1.get('status', 'Standby')}`")
            st.caption(f"⏱️ {ag1.get('latency', 0)}s | 🪙 **{ag1.get('tokens', 0):,} tok** (In: {ag1.get('in_tokens', 0):,} | Out: {ag1.get('out_tokens', 0):,})")

            # Step 2: Agen 2 (if invoked)
            if "agent2" in trace:
                ag2 = trace.get("agent2", {})
                st.markdown(f"**Agen 2 (Triase):** `{ag2.get('department', '')}`")
                st.caption(f"🏷️ Kategori: {ag2.get('category')} ({ag2.get('urgency')})")
                st.caption(f"⏱️ {ag2.get('latency', 0)}s | 🪙 **{ag2.get('tokens', 0):,} tok** (In: {ag2.get('in_tokens', 0):,} | Out: {ag2.get('out_tokens', 0):,})")

            # Step 3: Agen 3 (if invoked)
            if "agent3" in trace:
                ag3 = trace.get("agent3", {})
                st.markdown(f"**Agen 3 (Tiket):** `{ag3.get('ticket_id', '')}`")
                st.caption(f"⏱️ {ag3.get('latency', 0)}s | 🪙 Formatter Lokal (0 tok)")

            st.caption(f"📊 **Total Turn:** {trace.get('total_latency', 0)}s | 🪙 **{trace.get('total_tokens', 0):,} tokens** (Prompt: {trace.get('in_tokens', 0):,} | Reply: {trace.get('out_tokens', 0):,})")

        # Single Agent Mode Inspector View
        elif arch == "SINGLE_AGENT_BASELINE":
            st.warning("Pipeline: **Single Agent Baseline**")
            st.markdown(f"**Status:** `{trace.get('type')}`")
            st.caption(f"⏱️ Latensi: {trace.get('latency', 0)}s | 🪙 **{trace.get('tokens', 0):,} tokens** (Prompt: {trace.get('in_tokens', 0):,} | Reply: {trace.get('out_tokens', 0):,})")

        # Ticket Card Payload Display if generated
        if t_type == "OFFICIAL_TICKET_CREATED":
            st.success("Tiket Resmi Diterbitkan!")
            t_data = trace.get("ticket", {})
            st.markdown(f"- **Nomor Tiket:** `{t_data.get('ticket_id')}`")
            st.markdown(f"- **Departemen:** **{t_data.get('target_department')}** (`{t_data.get('department_code')}`)")
            st.markdown(f"- **Kategori:** **{t_data.get('subject_category')}**")
            st.markdown(f"- **Kamar:** `{t_data.get('room_number')}`")
            st.markdown(f"- **Jadwal:** {t_data.get('preferred_schedule')}")
            if reasoning:
                st.caption(f"🧠 Reasoning: {reasoning}")
            st.markdown("**Payload JSON:**")
            st.json(t_data)

        elif t_type in ["CLARIFICATION_AND_CONFIRMATION"]:
            st.warning("Status: Klarifikasi Nomor Kamar & Jadwal")
            if reasoning:
                st.caption(f"🧠 Reasoning: {reasoning}")

        elif t_type in ["HANDBOOK_RAG_ANSWER"]:
            st.info("Status: FAQ / Pedoman Asrama (Handbook RAG)")
            if trace.get("matched_section"):
                st.caption(f"Pasal: {trace.get('matched_section')} (Halaman {trace.get('page')})")
            if reasoning:
                st.caption(f"🧠 Reasoning: {reasoning}")

        elif reasoning:
            st.caption(f"🧠 Reasoning: {reasoning}")

    else:
        st.info("Status: **Siaga (Menunggu Pesan Mahasiswa)**")

    st.divider()
    st.subheader("⚡ Skenario Pengujian")

    if st.button("1. Lapor AC Rusak (Tanpa Kamar)", use_container_width=True):
        st.session_state.preset_msg = "Kak AC kamar saya rusak nih."

    if st.button("2. Info Kamar A1249 & Kendala", use_container_width=True):
        st.session_state.preset_msg = "Kamar A1249 kak, mati total gak mau nyala sama sekali."

    if st.button("3. Konfirmasi Tiket & Jadwal", use_container_width=True):
        st.session_state.preset_msg = "Boleh tolong diproses tiketnya ya kak, jadwal besok jam 10 pagi pas saya kuliah."

    if st.button("4. Jatah Listrik kWh (Anti-Ngasal)", use_container_width=True):
        st.session_state.preset_msg = "Kak kalau listrik kwh perbulannya berapa jatahnya?"

    if st.button("5. Kuota Laundry Gratis (RAG)", use_container_width=True):
        st.session_state.preset_msg = "Kak kalau kuota laundry gratis per bulan berapa kg ya?"

    if st.button("6. Jam Tamu Asrama (RAG)", use_container_width=True):
        st.session_state.preset_msg = "Kak jam kunjung tamu di kamar sampai jam berapa ya?"

    st.divider()
    if st.button("🔄 Reset Percakapan Baru", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Halo! Saya **Resepsionis Virtual Binus Square**. 👋\n\nAda yang bisa saya bantu hari ini? Anda dapat bertanya mengenai aturan dan fasilitas asrama, atau melaporkan kendala di kamar Anda."
            }
        ]
        st.session_state.last_trace = None
        st.session_state.session_stats = {
            "turns": 0,
            "total_latency": 0.0,
            "total_tokens": 0,
            "history": []
        }
        st.rerun()


# ==============================================================================
# MAIN PANEL: STANDARD STREAMLIT LAYOUT
# ==============================================================================
st.title("🏢 Binus Square AI Virtual Receptionist")
st.caption("Sistem Percakapan Cerdas Multi-Agent Berbasis LLM Function Calling & Taksonomi Resmi Kampus (Demo Sidang Tesis)")

# Compute Real-time Session Benchmark Metrics
stats = st.session_state.session_stats
turns = stats.get("turns", 0)
tot_lat = stats.get("total_latency", 0.0)
avg_lat = (tot_lat / turns) if turns > 0 else 0.0
tot_tok = stats.get("total_tokens", 0)
avg_tok = (tot_tok / turns) if turns > 0 else 0
throughput = (tot_tok / tot_lat) if tot_lat > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("💬 Putaran Sesi", f"{turns} Pesan")
col2.metric("⏱️ Rata-rata Latensi", f"{avg_lat:.2f} s")
col3.metric("🪙 Total Token", f"{tot_tok:,}")
col4.metric("⚡ Throughput", f"{throughput:.1f} tok/s")

st.divider()


# MAIN CHAT AREA
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user", avatar="👤").write(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🏢"):
            st.markdown(msg["content"])
            if msg.get("meta"):
                m = msg["meta"]
                lat_val = m.get("latency", 0)
                tok_val = m.get("tokens", 0)
                in_val = m.get("in_tokens", 0)
                out_val = m.get("out_tokens", 0)
                arch_tag = "🔀 Multi-Agent" if "MULTI" in m.get("architecture", "").upper() else "👤 Single Agent"
                tok_str = f"🪙 **{tok_val:,} tokens** (Prompt: {in_val:,} | Reply: {out_val:,})" if in_val > 0 else f"🪙 **{tok_val:,} tokens**"
                st.caption(f"⚡ **{lat_val:.2f}s** &nbsp;|&nbsp; {tok_str} &nbsp;|&nbsp; {arch_tag}")

# Handle preset input if button clicked
user_query = None
if "preset_msg" in st.session_state and st.session_state.preset_msg:
    user_query = st.session_state.preset_msg
    st.session_state.preset_msg = None

# Chat input widget
chat_input = st.chat_input("Ketik pesan Anda di sini...")
if chat_input:
    user_query = chat_input

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user", avatar="👤").write(user_query)

    with st.chat_message("assistant", avatar="🏢"):
        with st.spinner("AI Resepsionis sedang berpikir..."):
            reply = process_user_input(user_query, arch_mode)
            
            # Extract metadata from last_trace
            meta = {}
            if st.session_state.last_trace:
                t = st.session_state.last_trace
                lat = t.get("total_latency") or t.get("latency", 0.0)
                tok = t.get("total_tokens") or t.get("tokens", 0)
                in_tok = t.get("in_tokens", 0)
                out_tok = t.get("out_tokens", 0)
                arch_tag = t.get("architecture", arch_mode)
                meta = {
                    "latency": lat,
                    "tokens": tok,
                    "in_tokens": in_tok,
                    "out_tokens": out_tok,
                    "architecture": arch_tag,
                    "type": t.get("type", "GENERAL")
                }
                # Update session stats
                st.session_state.session_stats["turns"] += 1
                st.session_state.session_stats["total_latency"] += lat
                st.session_state.session_stats["total_tokens"] += tok
                st.session_state.session_stats["history"].append({
                    "turn": st.session_state.session_stats["turns"],
                    "latency": lat,
                    "tokens": tok,
                    "in_tokens": in_tok,
                    "out_tokens": out_tok,
                    "arch": arch_tag,
                    "type": t.get("type")
                })

            st.markdown(reply)
            if meta:
                lat_val = meta.get("latency", 0)
                tok_val = meta.get("tokens", 0)
                in_val = meta.get("in_tokens", 0)
                out_val = meta.get("out_tokens", 0)
                arch_tag = "🔀 Multi-Agent" if "MULTI" in meta.get("architecture", "").upper() else "👤 Single Agent"
                tok_str = f"🪙 **{tok_val:,} tokens** (Prompt: {in_val:,} | Reply: {out_val:,})" if in_val > 0 else f"🪙 **{tok_val:,} tokens**"
                st.caption(f"⚡ **{lat_val:.2f}s** &nbsp;|&nbsp; {tok_str} &nbsp;|&nbsp; {arch_tag}")

            st.session_state.messages.append({"role": "assistant", "content": reply, "meta": meta})
            st.rerun()
