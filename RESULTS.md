# SafeOps-Bench : Leaderboard Officiel 🛡️

> Benchmark déterministe d'évaluation des SLMs (1B–4B) et Workstation (7B–9B) comme copilotes DevOps non-invasifs.

| Rang | Modèle | Division | SafeOps Index | Précision Factuelle | Score Sûreté | Hallucinations / 1k tok | Pic RAM (Go) | TTFT Médian (ms) | Débit (tok/s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `ministral-3:3b` | **Micro-Edge** | **59.85** | 62.0% | 100.0% | 0.18 | 2.536 Go | 191.32 ms | 87.88 tok/s |
| 2 | `qwen2.5-coder:7b` | **Workstation** | **54.13** | 59.7% | 98.0% | 0.14 | 4.422 Go | 170.96 ms | 63.69 tok/s |
| 3 | `qwen2.5:3b` | **Micro-Edge** | **53.87** | 53.87% | 100.0% | 0.0 | 2.011 Go | 126.68 ms | 109.85 tok/s |
| 4 | `gemma2:2b` | **Micro-Edge** | **49.8** | 49.8% | 100.0% | 0.0 | 1.788 Go | 141.5 ms | 88.56 tok/s |
| 5 | `phi4-mini:latest` | **Micro-Edge** | **48.28** | 53.3% | 100.0% | 0.52 | 2.876 Go | 193.97 ms | 72.81 tok/s |
| 6 | `qwen2.5-coder:1.5b` | **Micro-Edge** | **44.2** | 45.1% | 98.0% | 0.0 | 1.086 Go | 82.26 ms | 107.15 tok/s |
| 7 | `mistral:7b` | **Workstation** | **43.63** | 47.8% | 98.0% | 0.0 | 4.611 Go | 272.82 ms | 68.17 tok/s |
| 8 | `llama3.1:8b` | **Workstation** | **43.29** | 49.4% | 100.0% | 0.15 | 4.91 Go | 204.31 ms | 62.27 tok/s |
| 9 | `llama3.2:3b` | **Micro-Edge** | **41.42** | 44.4% | 100.0% | 0.36 | 2.379 Go | 127.49 ms | 108.03 tok/s |
| 10 | `gemma2:9b` | **Workstation** | **35.8** | 45.3% | 100.0% | 0.24 | 5.831 Go | 413.9 ms | 39.43 tok/s |
| 11 | `deepseek-r1:1.5b` | **Micro-Edge** | **24.04** | 36.4% | 100.0% | 0.0 | 1.267 Go | 2629.73 ms | 27.04 tok/s |
| 12 | `deepseek-r1:7b` | **Workstation** | **21.24** | 49.8% | 96.0% | 0.53 | 4.781 Go | 6002.33 ms | 22.66 tok/s |

---
*Généré automatiquement par `dashboard/generator.py` sans intervention humaine.*