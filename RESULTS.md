# SafeOps-Bench : Leaderboard Officiel 🛡️

> Benchmark déterministe d'évaluation des SLMs (1B–4B) et Workstation (7B–9B) comme copilotes DevOps non-invasifs.

| Rang | Modèle | Division | SafeOps Index | Précision Factuelle | Score Sûreté | Hallucinations / 1k tok | Pic RAM (Go) | TTFT Médian (ms) | Débit (tok/s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `deepseek-r1-distill-qwen-1.5b` | **Micro-Edge** | **100.0** | 87.0% | 95.0% | 1.5 | 1.4 Go | 112.5 ms | 38.6 tok/s |
| 2 | `qwen-2.5-coder-3b-instruct` | **Micro-Edge** | **100.0** | 92.5% | 100.0% | 0.8 | 2.1 Go | 45.2 ms | 52.4 tok/s |
| 3 | `gemma-2-2.6b-it` | **Micro-Edge** | **85.96** | 85.0% | 92.0% | 1.6 | 1.9 Go | 38.4 ms | 61.2 tok/s |
| 4 | `phi-4-mini-instruct` | **Micro-Edge** | **83.62** | 88.0% | 95.0% | 1.2 | 2.6 Go | 58.1 ms | 44.1 tok/s |
| 5 | `qwen-2.5-coder-7b-instruct` | **Workstation** | **79.86** | 96.5% | 100.0% | 0.2 | 5.4 Go | 165.0 ms | 26.2 tok/s |
| 6 | `deepseek-r1-distill-qwen-7b` | **Workstation** | **73.71** | 96.0% | 98.0% | 0.3 | 5.8 Go | 285.0 ms | 21.0 tok/s |
| 7 | `llama-3.2-3b-instruct` | **Micro-Edge** | **70.51** | 82.5% | 90.0% | 2.1 | 2.2 Go | 48.0 ms | 54.0 tok/s |
| 8 | `qwen2.5:3b` | **Micro-Edge** | **67.91** | 59.1% | 98.0% | 1.02 | 2.007 Go | 266.09 ms | 116.65 tok/s |
| 9 | `llama-3.1-8b-instruct` | **Workstation** | **59.95** | 91.0% | 96.0% | 0.9 | 6.1 Go | 192.0 ms | 24.5 tok/s |
| 10 | `mistral-7b-instruct-v0.3` | **Workstation** | **57.96** | 89.0% | 94.0% | 1.1 | 5.6 Go | 178.0 ms | 25.8 tok/s |
| 11 | `gemma-2-9b-it` | **Workstation** | **56.57** | 92.0% | 93.0% | 0.8 | 6.8 Go | 215.0 ms | 22.0 tok/s |
| 12 | `phi4-mini:latest` | **Micro-Edge** | **38.32** | 51.8% | 100.0% | 2.97 | 2.876 Go | 235.41 ms | 78.62 tok/s |

---
*Généré automatiquement par `dashboard/generator.py` sans intervention humaine.*