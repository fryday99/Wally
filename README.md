# Wally — Integração Completa (UniGestão + Broker + Wallet)

## Estrutura de Pastas
- `legacy_system/`
  - `banco_dados_carteirinha.xlsx`: Planilha com os 6 integrantes do grupo.
  - `seed_db.py`: Lê `banco_dados_carteirinha.xlsx` e cria `instituicao.db` usando o **RA como token**.
  - `main.py`: API do sistema legado (`GET /validar` sem dados pessoais + rotas `/interno/*` para o UniGestão).
- `broker/`
  - `main.py`: Intermediador (`POST /acesso`, `POST /wallet/provisionar`, `GET /logs`) sem custódia de PII.
- `frontend/`
  - `unigestao.html`: Portal do discente com seleção dos 6 alunos, botão **Adicionar à Wallet** integrado e tabela **Últimos acessos** consumindo `GET /logs` em tempo real.
  - `wally.html`: Carteirinha digital com clonagem de carteirinha física (NFC real, simulação por RA/UID ou importação direta via `?import=` do UniGestão) e validação real via `POST /acesso`.
  - `demo_broker.html`: Tela de comparação lado a lado (Banco da Instituição vs. Payload recebido pelo Broker).

## Como rodar (3 terminais)

```bash
# Terminal 1 — Banco e Sistema Legado (porta 8001)
cd legacy_system
python3 seed_db.py
uvicorn main:app --port 8001

# Terminal 2 — Broker Wally (porta 8000)
cd broker
uvicorn main:app --port 8000

# Terminal 3 — Front-ends (porta 8080)
cd frontend
python3 -m http.server 8080
```

Acesse:
- Portal UniGestão: `http://localhost:8080/unigestao.html`
- Carteirinha Wally: `http://localhost:8080/wally.html`
- Comparativo Zero-PII: `http://localhost:8080/demo_broker.html`
