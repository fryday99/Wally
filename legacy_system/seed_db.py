"""
Cria o banco de dados SQLite da "instituição" (instituicao.db) a partir da planilha
banco_dados_carteirinha.xlsx (aba 'Discentes'), usando o RA como token principal.

Rode uma vez (ou sempre que editar a planilha):
    python3 seed_db.py
"""

import os
import sqlite3
import openpyxl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "instituicao.db")
XLSX_CANDIDATES = [
    os.path.join(BASE_DIR, "banco_dados_carteirinha.xlsx"),
    os.path.join(BASE_DIR, "..", "banco_dados_carteirinha.xlsx"),
]

FALLBACK_ALUNOS = [
    ("11202320826", "ALISON VIANA DIAS", "CIÊNCIA E TECNOLOGIA/PROGRAD", "TDB2ESMA002-23SA", "ATIVO", "UID-0001"),
    ("11202421752", "CAIO CAMARGO VENANCIO", "CIÊNCIA E TECNOLOGIA/PROGRAD", "TDB2ESMA002-23SA", "ATIVO", "UID-0002"),
    ("11202421578", "CLARA DIAS FERRO", "CIÊNCIA E TECNOLOGIA/PROGRAD", "TDB2ESMA002-23SA", "ATIVO", "UID-0003"),
    ("11202320258", "GABRIEL GOMES SANTOS", "CIÊNCIA E TECNOLOGIA/PROGRAD", "TDB2ESMA002-23SA", "ATIVO", "UID-0004"),
    ("11202532639", "HAYDAR HUSSEIN MOHSEN", "CIÊNCIA E TECNOLOGIA/PROGRAD", "TDB2ESMA002-23SA", "ATIVO", "UID-0005"),
    ("11202021735", "MURILO POCARLI DE CARVALHO", "CIÊNCIA E TECNOLOGIA/PROGRAD", "TDB2ESMA002-23SA", "ATIVO", "UID-0006"),
]


def carregar_da_planilha():
    xlsx_path = next((p for p in XLSX_CANDIDATES if os.path.exists(p)), None)
    if not xlsx_path:
        print("Planilha não encontrada; usando dados internos dos 6 integrantes.")
        return FALLBACK_ALUNOS

    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Discentes"] if "Discentes" in wb.sheetnames else wb.active

    registros = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0 or not row or not row[0]:
            continue
        ra = str(row[0]).strip()
        nome = str(row[1]).strip()
        curso = str(row[2]).strip()
        turma = str(row[3]).strip() if row[3] else "TDB2ESMA002-23SA"
        status = str(row[4]).strip().upper()
        uid = str(row[5]).strip() if row[5] else f"UID-{i:04d}"
        registros.append((ra, nome, curso, turma, status, uid))

    print(f"Lidos {len(registros)} registros reais de: {xlsx_path}")
    return registros


def criar_banco():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE alunos (
            token TEXT PRIMARY KEY,
            uid_carteirinha TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL,
            email TEXT NOT NULL,
            turma TEXT NOT NULL,
            curso TEXT NOT NULL,
            status TEXT NOT NULL,
            recursos_autorizados TEXT NOT NULL
        )
    """)

    registros = carregar_da_planilha()
    alunos_db = []

    for idx, (ra, nome, curso, turma, status, uid) in enumerate(registros, start=1):
        primeiro_nome = nome.split()[0].lower()
        ultimo_nome = nome.split()[-1].lower()
        cpf_ficticio = f"{100 + idx:03d}.{200 + idx:03d}.{300 + idx:03d}-{10 + idx:02d}"
        email_ficticio = f"{primeiro_nome}.{ultimo_nome}@aluno.ufabc.edu.br"

        # Regra da planilha: apenas Status == ATIVO libera acesso
        recursos = "catraca_principal,biblioteca,refeitorio" if status == "ATIVO" else ""

        alunos_db.append((
            ra,
            uid,
            nome,
            cpf_ficticio,
            email_ficticio,
            turma,
            curso,
            status.lower(),
            recursos,
        ))

    cur.executemany(
        "INSERT INTO alunos VALUES (?,?,?,?,?,?,?,?,?)",
        alunos_db,
    )
    conn.commit()
    conn.close()
    print(f"Banco SQLite criado em {DB_PATH} com {len(alunos_db)} alunos (RA como token).")


if __name__ == "__main__":
    criar_banco()
