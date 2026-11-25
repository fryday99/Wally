"""
BROKER WALLY — intermediador de controle de acesso sem custódia de dados pessoais.

  1. POST /acesso             -> Chamado pelo Wally / leitor na catraca.
                                 Consulta GET /validar no sistema legado e grava
                                 apenas {timestamp, token, recurso, autorizado, motivo}.
  2. POST /wallet/provisionar -> Chamado pelo UniGestão ao clicar em "Adicionar à Wallet"
                                 (ou ao clonar carteirinha física) para validar o token.
  3. GET /logs                -> Consumido em tempo real pelo painel UniGestão.
"""

from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI(title="Broker Wally (Intermediador de Acesso)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LEGACY_SYSTEM_URL = "https://legacy-system-cyc5.onrender.com"
LOGS: list[dict] = []


class PedidoAcesso(BaseModel):
    token: str
    recurso: str = "catraca_principal"


class PedidoProvisionamento(BaseModel):
    token: str
    origem: str = "portal_unigestao"  # "portal_unigestao" | "copia_carteirinha_fisica"


@app.post("/acesso")
def solicitar_acesso(pedido: PedidoAcesso):
    decisao = {"autorizado": False, "motivo": "erro_desconhecido", "campos_recebidos_da_instituicao": []}

    try:
        resposta = requests.get(
            f"{LEGACY_SYSTEM_URL}/validar",
            params={"id": pedido.token, "recurso": pedido.recurso},
            timeout=3,
        )
        resposta.raise_for_status()
        dados = resposta.json()

        decisao = {
            "autorizado": bool(dados.get("autorizado", False)),
            "motivo": dados.get("status_geral", "indisponivel"),
            "campos_recebidos_da_instituicao": list(dados.keys()),
        }
    except requests.exceptions.RequestException:
        decisao = {
            "autorizado": False,
            "motivo": "sistema_instituicao_indisponivel",
            "campos_recebidos_da_instituicao": [],
        }

    registro = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "token": pedido.token,
        "recurso": pedido.recurso,
        "autorizado": decisao["autorizado"],
        "motivo": decisao["motivo"],
        "campos_recebidos_da_instituicao": decisao["campos_recebidos_da_instituicao"],
    }
    LOGS.append(registro)
    return registro


@app.post("/wallet/provisionar")
def provisionar_wallet(pedido: PedidoProvisionamento):
    """
    Valida no sistema legado se o token (RA ou UID da carteirinha física) está ativo
    antes de emitir/clonar o passe na Wallet. Continua sem receber dados pessoais.
    """
    try:
        resposta = requests.get(
            f"{LEGACY_SYSTEM_URL}/validar",
            params={"id": pedido.token, "recurso": "catraca_principal"},
            timeout=3,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        autorizado = bool(dados.get("autorizado", False))
        motivo = dados.get("status_geral", "indisponivel")
    except requests.exceptions.RequestException:
        autorizado = False
        motivo = "sistema_instituicao_indisponivel"

    registro = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "token": pedido.token,
        "recurso": f"wallet:{pedido.origem}",
        "autorizado": autorizado,
        "motivo": motivo,
        "campos_recebidos_da_instituicao": ["autorizado", "status_geral"],
    }
    LOGS.append(registro)
    return registro


@app.get("/logs")
def listar_logs():
    return {"total": len(LOGS), "logs": list(reversed(LOGS))}


@app.get("/")
def health():
    return {"servico": "broker-wally", "status": "online"}
