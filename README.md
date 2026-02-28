# 🛸 Sovereign Computer

> A zero-cost, fully private, open-source local AI orchestration system.  
> Runs on your hardware alone. No APIs. No subscriptions. No data leaves your machine.

**Version 1.0 — February 28, 2026**  
Built by [Mellowambience](https://github.com/Mellowambience) · Part of the [Aetherhaven](https://aetherhaven.io) ecosystem

---

## Core Philosophy

High-level natural-language goal → automatic decomposition → parallel specialized agents → secure execution → persistent artifacts.

Every layer is MIT/Apache/AGPL licensed. Total cost: only electricity and your existing GPU/CPU.

---

## Hardware Minimum

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 8 cores | 16 cores |
| RAM | 16 GB | 32 GB |
| GPU VRAM | 8 GB | 16 GB+ |
| Storage | 50 GB | 100 GB |

CPU-only fallback supported (slower, but works).

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Mellowambience/sovereign-computer.git
cd sovereign-computer

# 2. Copy env
cp .env.example .env

# 3. Install Ollama + pull models
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull llama3.1:70b
ollama pull nomic-embed-text

# 4. Install Python deps
pip install -r requirements.txt

# 5. Start supporting services
docker compose up -d

# 6. Run
python sovereign_computer.py
```

---

## Architecture

```
User Goal (natural language)
        │
        ▼
  Conductor (LangGraph)
   decompose → route
        │
   ┌────┴────┐────────┐────────┐
   ▼         ▼        ▼        ▼
Researcher  Coder   Media  Integrator
(SearXNG)  (Docker) (local) (n8n)
   │         │        │        │
   └────┬────┘────────┘────────┘
        ▼
   ChromaDB Memory
        ▼
   ./output artifacts
```

---

## Agents

Defined in `agents/agents.yaml`. Add new agents with a single YAML block:

```yaml
- name: MyAgent
  role: "Custom Role"
  goal: "What this agent accomplishes"
  tools: [web_search, file_write]
```

---

## Services

| Service | Port | Purpose |
|---------|------|---------|
| Ollama | 11434 | Local LLM inference |
| SearXNG | 8080 | Private web search |
| Perplexica UI | 3000 | Dashboard |
| n8n | 5678 | Self-hosted connectors |
| ChromaDB | 8000 | Vector memory |

---

## First Flight

```bash
python sovereign_computer.py
# Goal: Create a 7-day local marketing campaign: research trends, write copy, compile PDF, save to ./output
```

---

## Maintenance

```bash
ollama pull llama3.1:70b          # weekly model refresh
git pull && pip install -r requirements.txt --upgrade
docker compose pull && docker compose up -d
```

---

## Roadmap

- [ ] Web UI for goal input + live task tree
- [ ] YAML-configurable agent marketplace
- [ ] AetherMind conductor integration
- [ ] Encrypted vault for connector tokens
- [ ] GPU-aware model routing

---

## License

MIT — fork it, own it, extend it.

---

*Part of the Aetherhaven stack. Execute. Extend. Own the horizon.*
