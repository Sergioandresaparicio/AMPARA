<#
.SYNOPSIS
    Despliegue automatizado de AMPARA en Windows
.DESCRIPTION
    Crea venv, instala dependencias, indexa RAG, ejecuta demo y tests
#>

param(
    [switch]$SkipTests,
    [switch]$ForceReindex
)

Write-Host "Iniciando despliegue AMPARA en Windows..." -ForegroundColor Cyan

# Verificar Python
$pyVer = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "[ERROR] Python no encontrado. Instale Python 3.11+ desde python.org"
    exit 1
}
Write-Host "[OK] Python detectado: $pyVer" -ForegroundColor Green

# Directorio del script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

# Crear/activar venv
if (-not (Test-Path ".venv")) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Instalar dependencias
Write-Host "Instalando dependencias..." -ForegroundColor Yellow
python -m pip install --upgrade pip -q
$packages = @("pyyaml", "pypdf", "python-docx", "numpy")
if (-not $SkipTests) { $packages += "pytest" }
pip install $packages -q

# Indexar RAG
Write-Host "Indexando base vectorial..." -ForegroundColor Yellow
$reindexFlag = if ($ForceReindex) { "True" } else { "False" }
python -c "
from agent.tools.rag_search import get_rag_engine
engine = get_rag_engine()
if '$reindexFlag' -eq 'True':
    engine.load_and_index(force_reload=True)
print(f'Chunks indexados: {engine.vector_db.count_chunks()}')
"

# Ejecutar demo
Write-Host "Ejecutando demo integral..." -ForegroundColor Yellow
python main.py

# Verificar DOCX
if (Test-Path "tutelas_generadas") {
    $docxFiles = Get-ChildItem tutelas_generadas\*.docx
    Write-Host "DOCX generados: $($docxFiles.Count)" -ForegroundColor Green
    $docxFiles | ForEach-Object { Write-Host "   - $($_.Name)" }
}

# Tests
if (-not $SkipTests) {
    Write-Host "Ejecutando tests unitarios..." -ForegroundColor Yellow
    python -m pytest agent/tests/ -v
}

Write-Host "`n[OK] Despliegue completado exitosamente!" -ForegroundColor Cyan
Write-Host "Para usar en opencode: opencode --agent ampara" -ForegroundColor Gray
