#!/usr/bin/env bash
# =====================================================================
# Despliegue automatizado de AMPARA en Linux/macOS
# =====================================================================
# Uso: ./deploy.sh [--skip-tests] [--force-reindex]
# =====================================================================

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SKIP_TESTS=false
FORCE_REINDEX=false

for arg in "$@"; do
    case $arg in
        --skip-tests) SKIP_TESTS=true ;;
        --force-reindex) FORCE_REINDEX=true ;;
        *) echo "Uso: $0 [--skip-tests] [--force-reindex]"; exit 1 ;;
    esac
done

echo -e "${CYAN}Iniciando despliegue AMPARA en Linux/macOS...${NC}"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python3 no encontrado. Instale Python 3.11+${NC}"
    exit 1
fi

PY_VER=$(python3 --version)
echo -e "${GREEN}[OK] Python detectado: $PY_VER${NC}"

# Directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Crear/activar venv
if [[ ! -d ".venv" ]]; then
    echo -e "${YELLOW}Creando entorno virtual...${NC}"
    python3 -m venv .venv
fi

echo -e "${YELLOW}Activando entorno virtual...${NC}"
source .venv/bin/activate

# Instalar dependencias
echo -e "${YELLOW}Instalando dependencias Python...${NC}"
pip install --upgrade pip -q
PACKAGES=("pyyaml" "pypdf" "python-docx" "numpy")
[[ "$SKIP_TESTS" == "false" ]] && PACKAGES+=("pytest")
pip install "${PACKAGES[@]}" -q

# Indexar RAG
echo -e "${YELLOW}Indexando base vectorial...${NC}"
REINDEX_FLAG="False"
[[ "$FORCE_REINDEX" == "true" ]] && REINDEX_FLAG="True"

python3 -c "
from agent.tools.rag_search import get_rag_engine
engine = get_rag_engine()
if '$REINDEX_FLAG' == 'True':
    engine.load_and_index(force_reload=True)
print(f'Chunks indexados: {engine.vector_db.count_chunks()}')
"

# Ejecutar demo
echo -e "${YELLOW}Ejecutando demo integral...${NC}"
python main.py

# Verificar DOCX
if [[ -d "tutelas_generadas" ]]; then
    DOCX_COUNT=$(find tutelas_generadas -name "*.docx" | wc -l)
    echo -e "${GREEN}DOCX generados: $DOCX_COUNT${NC}"
    find tutelas_generadas -name "*.docx" -exec basename {} \;
fi

# Tests
if [[ "$SKIP_TESTS" == "false" ]]; then
    echo -e "${YELLOW}Ejecutando tests unitarios...${NC}"
    python -m pytest agent/tests/ -v
fi

echo -e "\n${CYAN}[OK] Despliegue completado exitosamente!${NC}"
echo -e "${CYAN}Para usar en opencode: opencode --agent ampara${NC}"
