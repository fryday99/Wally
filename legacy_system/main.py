"""
SISTEMA LEGADO (UniGestão Backend) — representa o sistema de TI da instituição.

Expõe:
  1. GET /validar?id=X&recurso=Y  -> ÚNICA rota chamada pelo Broker.
                                     Devolve só autorizado (bool) e status_geral (str).
                                     NUNCA trafega nome, CPF, e-mail ou curso.

  2. Rotas /interno/*             -> Usadas apenas pelo portal da própria instituição
                                     (UniGestão) e pela tela de demonstração.
"""

import os
import sqlite3
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Sistema Legado da Instituição (UniGestão)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instituicao.db")


def get_conn():
    if not os.path.exists(DB_PATH):
        from seed_db import criar_banco
        criar_banco()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class StatusUpdate(BaseModel):
    status: str  # "ativo" | "trancado" | "inativo"


# ---------------------------------------------------------------------------
# ROTA 1 — Única rota exposta ao Broker (zero dados pessoais)
# ---------------------------------------------------------------------------
@app.get("/validar")
def validar(
    id: str = Query(..., description="Token do aluno (RA ou UID da carteirinha)"),
    recurso: str = Query(..., description="Recurso sendo acessado"),
):
    conn = get_conn()
    # Aceita tanto o RA (token principal) quanto o UID físico (ex: UID-0001)
    row = conn.execute(
        "SELECT status, recursos_autorizados FROM alunos WHERE token = ? OR uid_carteirinha = ?",
        (id.strip(), id.strip().upper()),
    ).fetchone()
    conn.close()

    if row is None:
        return {"autorizado": False, "status_geral": "credencial_nao_encontrada"}

    recursos = row["recursos_autorizados"].split(",") if row["recursos_autorizados"] else []
    autorizado = (row["status"].lower() == "ativo") and (recurso in recursos)

    return {"autorizado": autorizado, "status_geral": row["status"]}


# ---------------------------------------------------------------------------
# ROTAS INTERNAS DA INSTITUIÇÃO (Portal UniGestão + Clonagem inicial na Wallet)
# ---------------------------------------------------------------------------
@app.get("/interno/alunos")
def listar_alunos():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM alunos ORDER BY rowid ASC").fetchall()
    conn.close()
    return {"total": len(rows), "alunos": [dict(r) for r in rows]}


@app.get("/interno/aluno")
def visao_interna(id: str = Query(...)):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM alunos WHERE token = ? OR uid_carteirinha = ?",
        (id.strip(), id.strip().upper()),
    ).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    return dict(row)


@app.patch("/interno/aluno/{token}/status")
def atualizar_status(token: str, body: StatusUpdate):
    novo_status = body.status.strip().lower()
    recursos = "catraca_principal,biblioteca,refeitorio" if novo_status == "ativo" else ""

    conn = get_conn()
    cur = conn.execute(
        "UPDATE alunos SET status = ?, recursos_autorizados = ? WHERE token = ? OR uid_carteirinha = ?",
        (novo_status, recursos, token.strip(), token.strip().upper()),
    )
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    return {"token": token, "status": novo_status, "acesso_liberado": novo_status == "ativo"}


@app.get("/")
def health():
    return {"servico": "sistema-legado-unigestao", "status": "online", "banco": "sqlite"}
