# Build e Distribuição — Money Fronts

Este documento descreve como compilar e empacotar a aplicação, seguindo a
arquitetura Sidecar Pattern definida no DAS.

## 1. Pré-requisitos

- Node.js 20+ e um gestor de pacotes (`pnpm` ou `npm`)
- Rust stable + toolchain do Tauri v2 (`cargo install tauri-cli` opcional)
- Python 3.12, 3.13 ou 3.14 (o projeto usa `sqlcipher3-binary`, que publica
  wheels self-contained — **não é necessário instalar `libsqlcipher` no
  sistema**, ao contrário de versões antigas deste documento)

> **Nota sobre versão do Python:** o backend funciona em qualquer versão a
> partir da 3.12. Se você usa uma versão muito recente do Python (ex.: recém
> lançada) e uma instalação falhar por falta de wheel, normalmente é questão
> de dias/semanas até os mantenedores publicarem o build — nesse meio tempo,
> uma versão LTS-like como 3.12 ou 3.13 costuma ter cobertura mais ampla no
> ecossistema (PyInstaller, extensões C de terceiros etc.).

## 2. Desenvolvimento local

```bash
# Backend (modo dev, sem SQLCipher compilado -> usa sqlite puro)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-v2.txt --upgrade
export MONEY_FRONTS_DEV_PLAINTEXT_DB=1
python -m app.main --port 8756

# Frontend
cd frontend
npm install
npm run dev

# Tauri (orquestra os dois acima via tauri.conf.json)
cd src-tauri
cargo tauri dev
```

## 3. Build de produção

```bash
# 1) Empacotar o sidecar Python como binário standalone
cd backend
pip install -r requirements-v2.txt --upgrade
python build_sidecar.py
mkdir -p ../src-tauri/binaries
cp dist/app-backend-* ../src-tauri/binaries/

# 2) Build do frontend
cd ../frontend
npm install && npm run build

# 3) Build final do Tauri (gera MSI/DMG/AppImage conforme SO)
cd ../src-tauri
cargo tauri build
```

## 4. Migrações de schema (Alembic)

Ao adicionar campos/tabelas novas em `app/models.py`:

```bash
cd backend
alembic revision --autogenerate -m "descrição da mudança"
alembic upgrade head
```

O sidecar executa `alembic upgrade head` automaticamente no arranque (RN3),
antes de abrir qualquer sessão de dados. Para instalações antigas do scaffold,
a primeira migração preserva as tabelas já existentes e acrescenta os campos
necessários às contas.

## 5. Cadeia de confiança (Supply Chain Security)

Ver `.github/workflows/release.yml`. Resumo:

| Etapa | Ferramenta | Garantia |
|---|---|---|
| Assinatura Windows | SignPath Foundation | Remove o alerta do SmartScreen |
| Notarização macOS | Apple Developer ID | Gatekeeper aprova sem aviso |
| Proveniência | Sigstore / GitHub Attestations | SBOM + verificação SLSA L3 |

Para verificar a autenticidade de um binário publicado:

```bash
gh attestation verify <arquivo-baixado> --owner <org-do-repo>
```
