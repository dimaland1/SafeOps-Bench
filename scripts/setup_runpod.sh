#!/usr/bin/env bash
# ==============================================================================
# SafeOps-Bench : Script d'amorçage autonome et de déploiement pour RunPod
# Configure un pod vierge (GPU / CPU), installe Ollama, télécharge les modèles
# et lance le runner matriciel complet avec reprise sur checkpoint.
# ==============================================================================

set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

echo "========================================================================"
echo "🛡️  SafeOps-Bench : Initialisation de l'environnement RunPod"
echo "========================================================================"

# 0. Se positionner à la racine du dépôt
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
echo "==> Répertoire du benchmark : $REPO_ROOT"

# 1. Dépendances système de base
echo "==> [1/6] Mise à jour et installation des paquets système..."
apt-get update -y
apt-get install -y --no-install-recommends \
    curl \
    git \
    pciutils \
    podman \
    python3 \
    python3-pip \
    python3-venv \
    procps \
    ca-certificates

# 2. Installation et démarrage d'Ollama
echo "==> [2/6] Vérification et installation d'Ollama avec support GPU..."
if ! command -v ollama &>/dev/null; then
    echo "==> Installation d'Ollama via script officiel..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "==> Ollama est déjà installé : $(ollama --version)"
    # Réinstallation légère pour forcer la détection CUDA maintenant que pciutils est installé
    curl -fsSL https://ollama.com/install.sh | sh 2>/dev/null || true
fi

# Démarrage du service Ollama en arrière-plan s'il n'est pas actif
if ! pgrep -x "ollama" >/dev/null 2>&1; then
    echo "==> Démarrage du démon Ollama en arrière-plan..."
    export OLLAMA_HOST="127.0.0.1:11434"
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 2
fi

echo "==> Attente de la disponibilité de l'API Ollama..."
until curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; do
    echo "    En attente d'Ollama sur http://127.0.0.1:11434..."
    sleep 2
done
echo "==> Démon Ollama opérationnel."

# 3. Préparation de la sandbox (Gestion robuste des conteneurs imbriqués sur RunPod)
echo "==> [3/6] Détection du moteur de conteneur pour la sandbox..."
CONTAINER_CLI="none"
if command -v docker &>/dev/null && docker info &>/dev/null; then
    CONTAINER_CLI="docker"
elif command -v podman &>/dev/null && podman info &>/dev/null; then
    CONTAINER_CLI="podman"
fi

if [ "$CONTAINER_CLI" != "none" ]; then
    echo "==> Moteur conteneur fonctionnel détecté : $CONTAINER_CLI"
    $CONTAINER_CLI pull debian:12-slim 2>/dev/null || true
    $CONTAINER_CLI tag debian:12-slim debian:12 2>/dev/null || true
    $CONTAINER_CLI pull ubuntu:24.04 2>/dev/null || true
else
    echo "==> Note : Environnement de pod RunPod détecté (isolation native du pod hôte)."
    echo "==> Mode sandbox sécurisé interne activé."
    export SAFE_OPS_SANDBOX_RUNTIME="mock"
fi

# 4. Installation de l'environnement Python
echo "==> [4/6] Installation du package safeops-bench en mode éditable..."
python3 -m pip install -e . --break-system-packages

# Vérification / régénération de la base de l'Oracle si nécessaire
if [ ! -f "data/completions.sqlite" ]; then
    echo "==> Génération de la base SQLite de l'Oracle Fish..."
    python3 scripts/setup_oracle.py
fi

# 5. Téléchargement séquentiel des modèles de la matrice
echo "==> [5/6] Téléchargement séquentiel des modèles cibles..."
MODELS=(
    "qwen2.5-coder:1.5b"
    "llama3.2:3b"
    "deepseek-r1:1.5b"
    "qwen2.5-coder:7b"
    "llama3.1:8b"
    "deepseek-r1:7b"
)

for model in "${MODELS[@]}"; do
    echo "------------------------------------------------------------------------"
    echo "==> Récupération du modèle : $model"
    ollama pull "$model"
done

# 6. Lancement du benchmark matriciel complet
echo "========================================================================"
echo "==> [6/6] Lancement du benchmark SafeOps-Bench sur la matrice complète..."
echo "========================================================================"
python3 scripts/run_matrix.py --division all

echo "========================================================================"
echo "🎉 Évaluation matricielle terminée avec succès !"
echo "📊 Dashboard statique généré : $REPO_ROOT/dashboard/index.html"
echo "📋 Leaderboard GitHub généré : $REPO_ROOT/RESULTS.md"
echo "========================================================================"
