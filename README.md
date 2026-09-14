# DAWS: Dialect-Aware Warning System

This repository contains the complete implementation and documentation for **DAWS (Dialect-Aware Warning System)**, a Master's degree project developed for the *Network & Cloud Infrastructure / Big Data* courses at the Università degli Studi di Napoli Federico II.

DAWS is an adaptable framework designed to process and analyze regional speech and code-switching (specifically focusing on Neapolitan and Italian) in critical environments (such as medical consultations). It mitigates the risk of automated transcription errors by integrating phonetic analysis, Retrieval-Augmented Generation (RAG) for Whisper, LLM-based semantic analysis, claim segmentation, and an advanced risk-scoring pipeline.

---

## Architecture Overview

The processing pipeline consists of several integrated stages:
1. **S2T (Speech-to-Text):** Retrieves audio from Google Drive, performs phonetic transcription via *PhoneticXeus* (IPA), and utilizes a custom *Whisper-RAG* technique with vector-based semantic retrieval and fuzzy string matching to generate robust transcriptions and token-level confidence scores.
2. **Transcription Analysis:** Uses *Mistral-large* to cross-reference standard Whisper, Whisper-RAG, and IPA outputs to produce a coherent standard Italian translation, identify semantic issues, and compute Pseudo-Perplexity (PPPL) using *bert-base-italian-cased*.
3. **Claim Segmentation & Validation:** Parses the text into logical semantic units ("claims") using *spaCy*, classifies their intent/category, maps them back to source words, and calculates claim-specific risk metrics.
4. **Risk Score Calculation:** Computes local and global risk scores using weighted multi-signal combinations (confidence metrics, translation perplexity, claim weights) mapped to visual severity levels (Green, Yellow, Red).
5. **Storage & Dashboard:** Centralizes all session metadata, intermediate stages, and final results in **MongoDB Atlas**, featuring an interactive multi-page **Streamlit** dashboard for inspection and real-time Kaggle-backed inference.

---

## Tech Stack & Requirements

* **Python** (Primary programming language)
* **Whisper (OpenAI) & PhoneticXeus** (Speech recognition & phonetic analysis)
* **Mistral-Large** (Semantic analysis & validation via LLM)
* **spaCy & Hugging Face Transformers** (NLP parsing & PPPL evaluation with *bert-base-italian-cased*)
* **MongoDB Atlas** (Document store and vector search database)
* **Streamlit & Plotly** (Interactive web dashboard & data visualization)
* **FastAPI & Ngrok** (Real-time transcription and remote Kaggle GPU execution tunnel)

---

## Repository Structure

```text
dashboard/
├── app.py                  # Home page
├── db.py                   # MongoDB centralized query layer
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration
├── .streamlit/
│   └── config.toml         # Streamlit styling and config
├── pages/
│   ├── 1_overview.py       # Global KPIs and session overview
│   ├── 2_dettaglio.py      # Deep-dive inspection per session
│   ├── 3_aggregata.py      # Cross-session and dialect analytics
│   ├── 4_upload.py         # Remote Kaggle inference & audio upload
│   └── 5_confronto_metriche.py # RAG vs Non-RAG performance comparison
└── utils/
    ├── style.py            # Custom CSS styling
    └── audio.py            # Google Drive audio downloader
