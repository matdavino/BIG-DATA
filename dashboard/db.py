"""
db.py — layer di accesso a MongoDB Atlas.
Tutte le query sono centralizzate qui, le pagine importano solo funzioni.
"""

import os
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# ── Connessione Singola al Cluster con cache Streamlit ───────────────────
@st.cache_resource
def get_mongo_client():
    """Inizializza il client verso il cluster una sola volta."""
    return MongoClient(os.getenv("MONGO_URI"))

def get_db(env_key="DB_NAME"):
    """Recupera la specifica istanza del database usando la chiave ambiente."""
    client = get_mongo_client()
    return client[os.getenv(env_key, "asr_dialects_db")]

def _db():
    """Riferimento di default per retrocompatibilità."""
    return get_db("DB_NAME")


# ════════════════════════════════════════════════════════════════════════
# OVERVIEW E AGGREGAZIONI
# ════════════════════════════════════════════════════════════════════════

def get_all_sessions(db_instance=None) -> list:
    """Restituisce tutte le sessioni completate."""
    db = db_instance if db_instance is not None else _db()
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$lookup": {"from": "participants", "localField": "participant_id", "foreignField": "_id", "as": "participant"}},
        {"$unwind": {"path": "$participant", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {"from": "Transcripts", "localField": "_id", "foreignField": "_id", "as": "transcript"}},
        {"$unwind": {"path": "$transcript", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {"from": "Translation_Metrics", "localField": "_id", "foreignField": "_id", "as": "metrics"}},
        {"$unwind": {"path": "$metrics", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id":                  1,
                "filename":             {"$ifNull": ["$filename", "—"]},
                "promptCategory":       {"$ifNull": ["$promptCategory", "—"]},
                "started_at":           {"$ifNull": ["$started_at", None]},
                "completed_at":         {"$ifNull": ["$completed_at", None]},
                "status":               1,
                "participant_id":       1,
                "gender":               {"$ifNull": ["$participant.gender", "—"]},
                "ageRange":             {"$ifNull": ["$participant.ageRange", "—"]},
                "dialect":              {"$ifNull": ["$participant.dialect", "—"]},
                "dialectFrequency":     {"$ifNull": ["$participant.dialectFrequency", "—"]},
                "education":            {"$ifNull": ["$participant.education", "—"]},
                "livingContext":        {"$ifNull": ["$participant.livingContext", "—"]},
                # ── NUOVO SCHEMA RISCHIO TOTALE ──
                "overall_risk_level":   {"$ifNull": ["$overall_risk.overall_risk_level", "green"]},
                "overall_reason":       {"$ifNull": ["$overall_risk.overall_reason", "—"]},
                "period_conf_mean":     {"$ifNull": ["$transcript.analysis_stage.period_conf_mean", None]},
                "cosine_similarity":    {"$ifNull": ["$metrics.cosine_similarity", None]},
                "wer":                  {"$ifNull": ["$metrics.wer", None]},
                "bleu":                 {"$ifNull": ["$metrics.bleu", None]},
                "rouge1":               {"$ifNull": ["$metrics.rouge1", None]},
            }
        },
        {"$sort": {"started_at": -1}},
    ]
    return list(db["Sessions"].aggregate(pipeline))

def get_aggregate_semantic_issues(session_ids: list, db_instance=None) -> list:
    """
    Estrae le parole problematiche dal nuovo Stage 5_ensemble_llm.
    """
    if not session_ids: return []
    db = db_instance if db_instance is not None else _db()
    issues = []
    
    for doc in db["Pipeline_Stages"].find({"_id": {"$in": session_ids}}):
        stages = doc.get("stages", {})
        ensemble_data = stages.get("5_ensemble_llm", {}).get("data", {})
        semantic_issues = ensemble_data.get("semantic_issues", [])
        
        if isinstance(semantic_issues, list):
            for issue in semantic_issues:
                words_list = issue.get("words", [])
                if isinstance(words_list, list):
                    word_str = " ".join(words_list)
                else:
                    word_str = str(words_list)
                
                if word_str.strip():
                    issues.append({
                        "word": word_str.strip().lower(),
                        "reason": issue.get("reason", ""),
                        "session_id": doc["_id"],
                    })
    return issues

def get_kpi_overview(sessions: list) -> dict:
    if not sessions:
        return {
            "total": 0, "green": 0, "yellow": 0, "red": 0,
            "green_pct": 0.0, "yellow_pct": 0.0, "red_pct": 0.0,
            "avg_conf": 0.0, "avg_dialectal_ratio": 0.0,
        }
    total  = len(sessions)
    green  = sum(1 for s in sessions if s.get("overall_risk_level") == "green")
    yellow = sum(1 for s in sessions if s.get("overall_risk_level") == "yellow")
    red    = sum(1 for s in sessions if s.get("overall_risk_level") == "red")
    confs = [s["period_conf_mean"] for s in sessions if s.get("period_conf_mean") is not None]
    avg_conf = round(sum(confs) / len(confs), 4) if confs else 0.0
    return {
        "total":      total,
        "green":      green,
        "yellow":     yellow,
        "red":        red,
        "green_pct":  round(green  / total * 100, 1),
        "yellow_pct": round(yellow / total * 100, 1),
        "red_pct":    round(red    / total * 100, 1),
        "avg_conf":   avg_conf,
    }


# ════════════════════════════════════════════════════════════════════════
# DETTAGLIO SESSIONE
# ════════════════════════════════════════════════════════════════════════

def get_session_detail(session_id: str) -> dict:
    db = _db()
    pipeline = [
        {"$match": {"_id": session_id}},
        {"$lookup": {"from": "participants", "localField": "participant_id", "foreignField": "_id", "as": "participant"}},
        {"$unwind": {"path": "$participant", "preserveNullAndEmptyArrays": True}},
    ]
    aggregated_results = list(db["Sessions"].aggregate(pipeline))
    if not aggregated_results:
        return {}
    
    session = aggregated_results[0]
    participant = session.get("participant", {})
    filename_key = session.get("filename", session_id)

    transcript  = db["Transcripts"].find_one({"_id": filename_key}) or db["Transcripts"].find_one({"_id": session_id}) or {}
    risk        = db["Risk_Logs"].find_one({"_id": filename_key}) or db["Risk_Logs"].find_one({"_id": session_id}) or {}
    stages_doc  = db["Pipeline_Stages"].find_one({"_id": filename_key}) or db["Pipeline_Stages"].find_one({"_id": session_id}) or {}
    recording   = db["recordings"].find_one({"filename": filename_key}) or db["recordings"].find_one({"_id": session_id}) or {}
    metrics     = db["Translation_Metrics"].find_one({"_id": filename_key}) or db["Translation_Metrics"].find_one({"_id": session_id}) or {}

    stages = stages_doc.get("stages", {})
    interaction = stages.get("5_ensemble_llm", {})

    return {
        "session":     session,
        "participant": participant,
        "transcript":  transcript,
        "risk":        risk,
        "stages":      stages,
        "recording":   recording,
        "interaction": interaction,
        "metrics":     metrics,
    }

def get_session_ids_with_labels() -> list[tuple]:
    sessions = get_all_sessions()
    result = []
    for s in sessions:
        gender   = s.get("gender", "?")
        age      = s.get("ageRange", "?")
        dialect  = s.get("dialect", "?")
        filename = s.get("filename", s["_id"])
        label    = f"{filename}  ·  {gender} · {age} · {dialect}"
        result.append((s["_id"], label))
    return result

def get_drive_file_id(session_id: str) -> str | None:
    db   = _db()
    doc  = db["recordings"].find_one({"_id": session_id}, {"drive_file_id": 1})
    return doc.get("drive_file_id") if doc else None


# ════════════════════════════════════════════════════════════════════════
# ANALISI AGGREGATA
# ════════════════════════════════════════════════════════════════════════

def get_filtered_sessions(
    age_ranges:        list | None = None,
    genders:           list | None = None,
    dialects:          list | None = None,
    educations:        list | None = None,
    dialect_freqs:     list | None = None,
    living_contexts:   list | None = None,
    db_instance=None
) -> list:
    all_sessions = get_all_sessions(db_instance)
    def _keep(s):
        if age_ranges      and s.get("ageRange")          not in age_ranges:      return False
        if genders         and s.get("gender")             not in genders:         return False
        if dialects        and s.get("dialect")            not in dialects:        return False
        if educations      and s.get("education")          not in educations:      return False
        if dialect_freqs   and s.get("dialectFrequency")   not in dialect_freqs:   return False
        if living_contexts and s.get("livingContext")      not in living_contexts: return False
        return True
    return [s for s in all_sessions if _keep(s)]

def get_aggregate_words_stats(session_ids: list, db_instance=None) -> list:
    if not session_ids: return []
    db = db_instance if db_instance is not None else _db()
    words = []
    for doc in db["Pipeline_Stages"].find({"_id": {"$in": session_ids}}):
        stages = doc.get("stages", {})
        llm_analysis_root = stages.get("4_llm_dialect_analysis", {})
        if not llm_analysis_root: continue
        
        if isinstance(llm_analysis_root, dict) and "data" in llm_analysis_root:
            llm_analysis = llm_analysis_root["data"]
        else:
            llm_analysis = llm_analysis_root

        if isinstance(llm_analysis, list):
            for w in llm_analysis:
                words.append({
                    "word":           w.get("word", ""),
                    "is_dialectal":   w.get("is_dialectal", False),
                    "dialectal_type": w.get("dialectal_type", "standard"),
                    "surprisal":      w.get("surprisal", 0.0),
                    "conf_mean":      w.get("conf_mean", 1.0),
                    "session_id":     doc["_id"],
                })
        elif isinstance(llm_analysis, dict):
            for _, w in llm_analysis.items():
                if isinstance(w, dict):
                    words.append({
                        "word":           w.get("word", ""),
                        "is_dialectal":   w.get("is_dialectal", False),
                        "dialectal_type": w.get("dialectal_type", "standard"),
                        "surprisal":      w.get("surprisal", 0.0),
                        "conf_mean":      w.get("conf_mean", 1.0),
                        "session_id":     doc["_id"],
                    })
    return words

def get_distinct_filter_values() -> dict:
    db = _db()
    col = db["participants"]
    return {
        "age_ranges":      sorted(col.distinct("ageRange")),
        "genders":         sorted(col.distinct("gender")),
        "dialects":        sorted(col.distinct("dialect")),
        "educations":      sorted(col.distinct("education")),
        "dialect_freqs":   sorted(col.distinct("dialectFrequency")),
        "living_contexts": sorted(col.distinct("livingContext")),
    }

def get_claims_for_heatmap(session_ids: list, db_instance=None) -> list:
    if not session_ids: return []
    db = db_instance if db_instance is not None else _db()
    claims = []
    for doc in db["Risk_Logs"].find({"_id": {"$in": session_ids}}):
        for claim in doc.get("scored_claims", []):
            claims.append({
                "claim_type": claim.get("claim_type", "sconosciuto"),
                "risk_level": claim.get("risk_level", "green"),
            })
    return claims