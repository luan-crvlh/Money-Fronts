# Money Fronts

Aplicação de gestão financeira pessoal **Local-First**, construída 100% a
partir da Especificação de Requisitos de Software (ERSW) e do Documento de
Arquitetura de Software (DAS) fornecidos.

## Arquitetura (Sidecar Pattern)

```
┌─────────────────────────┐      HTTP (127.0.0.1)      ┌──────────────────────────┐
│  Frontend (Vite/WebView) │ ──────────────────────────▶ │  Sidecar Python (FastAPI) │
│  HTML5 + CSS + JS        │                              │  + SQLAlchemy + SQLCipher │
└───────────┬──────────────┘                              └──────────────┬───────────┘
            │ invoke()                                                    │
            ▼                                                             ▼
┌─────────────────────────┐                                  ┌──────────────────────────┐
│  Orquestrador Tauri/Rust │ ── spawn/kill do sidecar ──────▶ │  money_fronts.db (SQLite  │
│  (ciclo de vida, janela) │                                  │  encriptado AES-256)      │
└───────────────────────────                                  └──────────────────────────┘
```

## Estrutura de diretórios

```
money-fronts/
├── frontend/          # Apresentação: Vite + HTML/CSS/JS puro
│   └── src/
│       ├── api.js             # Cliente HTTP do backend local
│       ├── main.js            # Bootstrap + roteamento + health check
│       ├── components/        # Dashboard, Transactions, Categories
│       └── styles/main.css
├── src-tauri/         # Orquestrador: Tauri v2 (Rust)
│   ├── tauri.conf.json        # externalBin, janela, CSP
│   ├── capabilities/default.json  # shell:allow-execute restrito ao sidecar
│   └── src/{main.rs,lib.rs}   # spawn/kill do sidecar, porta dinâmica
├── backend/           # Processo Auxiliar: Python + FastAPI (Sidecar)
│   └── app/
│       ├── main.py            # Entrypoint Uvicorn, CORS, /health
│       ├── config.py          # Paths, porta, CORS, regra 50/30/20
│       ├── security.py        # Keyring (chave AES-256)
│       ├── database.py        # Engine SQLAlchemy + PRAGMA key/foreign_keys
│       ├── models.py          # Category, Account, Transaction, Budget...
│       ├── schemas.py         # Pydantic
│       ├── crud.py
│       ├── seed.py            # Categorias padrão (RF02)
│       └── routers/           # categories, accounts, transactions, budgets, dashboard
│   ├── alembic/                # Migrações (RN3)
│   └── build_sidecar.py        # Empacotamento PyInstaller
├── .github/workflows/release.yml  # CI: PyInstaller + Tauri + SignPath + Sigstore
└── docs/BUILD.md
```

## Rastreabilidade Requisitos → Código

| Requisito | Onde está implementado |
|---|---|
| RF01 (Registo de fluxos monetários) | `backend/app/routers/transactions.py`, `Transactions.js` |
| RF02 (Categorias + seed inicial) | `backend/app/seed.py`, `routers/categories.py` |
| RF03 (Monitorização orçamental) | `routers/budgets.py` (`/progress`) |
| RF04 (Dashboard + Regra 50/30/20 + Safe-to-Spend) | `routers/dashboard.py`, `Dashboard.js` |
| RF05 (Recorrência) | `routers/recurring.py`, geração idempotente no arranque e tela `Recurring.js` |
| RNF01 (Criptografia AES-256 em repouso) | `database.py` (SQLCipher + PRAGMA key) |
| RNF02 (Offline-first) | Nenhuma chamada de rede externa em todo o backend |
| RNF03 (Keyring nativo) | `security.py` |
| RNF04 (Distribuição certificada) | `.github/workflows/release.yml`, `docs/BUILD.md` |
| RNF05 (Latência < 100ms) | Stack local (SQLite + loopback), sem chamadas remotas |
| RNF06 (Sidecar Pattern / desacoplamento) | Estrutura completa de 3 processos |
| RN1 (Ciclo de vida gracioso) | `src-tauri/src/lib.rs` (spawn/kill), `main.js` (health check) |
| RN2 (Foreign keys + cascade) | `database.py` (PRAGMA), `models.py` (`ondelete`) |
| RN3 (Migrações silenciosas) | `backend/alembic/` + `run_migrations()` no arranque do sidecar |

## Próximos passos sugeridos (não cobertos neste scaffold inicial)

As duas funcionalidades "inéditas" descritas no ERSW (IA local via SLMs
quantizados e cofre biométrico com Secure Enclave) exigem integrações
nativas mais profundas (ex.: `tauri-plugin-biometric`, `llama.cpp` bindings)
e foram deixadas como próxima fase para não inflar o escopo inicial — a
base de dados e a API já estão preparadas para recebê-las sem quebras de
compatibilidade.

Ver `docs/BUILD.md` para instruções de execução e empacotamento.
