"""
Compila todas as contribuições numa base única, para o SIAPP baixar.

Saída em dist/:
  siapp-dados.sqlite   tabelas: contribuicoes, correcoes, palavras, manter_original, documentos
  vocabulario.json     vocabulário consolidado (formato lido pelo SIAPP)

Cada linha guarda o pacote de origem: a autoria nunca se perde.
Uso:  python ferramentas/compilar.py
"""
from __future__ import annotations

import glob
import json
import os
import sqlite3

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def compilar(pasta_contrib: str | None = None, saida: str | None = None) -> dict:
    pasta_contrib = pasta_contrib or os.path.join(RAIZ, "contribuicoes")
    saida = saida or os.path.join(RAIZ, "dist")
    os.makedirs(saida, exist_ok=True)
    banco = os.path.join(saida, "siapp-dados.sqlite")
    if os.path.exists(banco):
        os.remove(banco)
    con = sqlite3.connect(banco)
    con.executescript("""
        CREATE TABLE contribuicoes (id TEXT PRIMARY KEY, arquivo TEXT, autor TEXT,
                                    instituicao TEXT, criado_em TEXT, siapp_versao TEXT);
        CREATE TABLE correcoes (de TEXT, para TEXT, contribuicao TEXT REFERENCES contribuicoes(id));
        CREATE TABLE palavras (termo TEXT, contribuicao TEXT REFERENCES contribuicoes(id));
        CREATE TABLE manter_original (termo TEXT, contribuicao TEXT REFERENCES contribuicoes(id));
        CREATE TABLE documentos (sha256 TEXT, bacia TEXT, poco TEXT, caminho_remoto TEXT, bytes INTEGER,
                                 texto_arquivo TEXT, texto_metodo TEXT, n_paginas INTEGER,
                                 contribuicao TEXT REFERENCES contribuicoes(id));
    """)
    vocab = {"palavras": [], "correcoes": {}, "ignorar": []}
    n = 0
    for caminho in sorted(glob.glob(os.path.join(pasta_contrib, "*.json"))):
        with open(caminho, encoding="utf-8") as f:
            c = json.load(f)
        n += 1
        a = c["autor"]
        con.execute("INSERT INTO contribuicoes VALUES (?,?,?,?,?,?)",
                    (c["id"], os.path.basename(caminho), a["nome"], a.get("instituicao"),
                     c["criado_em"], c.get("siapp_versao")))
        v = c.get("vocabulario", {})
        for x in v.get("correcoes", []):
            con.execute("INSERT INTO correcoes VALUES (?,?,?)", (x["de"], x["para"], c["id"]))
            vocab["correcoes"].setdefault(x["de"], x["para"])
        for t in v.get("palavras", []):
            con.execute("INSERT INTO palavras VALUES (?,?)", (t, c["id"]))
            if t not in vocab["palavras"]:
                vocab["palavras"].append(t)
        for t in v.get("manter_original", []):
            con.execute("INSERT INTO manter_original VALUES (?,?)", (t, c["id"]))
            if t not in vocab["ignorar"]:
                vocab["ignorar"].append(t)
        for d in c.get("documentos", []):
            tx = d.get("texto", {})
            con.execute("INSERT INTO documentos VALUES (?,?,?,?,?,?,?,?,?)",
                        (d["sha256"], d["bacia"], d["poco"], d["caminho_remoto"], d["bytes"],
                         tx.get("arquivo"), tx.get("metodo"), tx.get("n_paginas"), c["id"]))
    con.commit()
    con.close()
    with open(os.path.join(saida, "vocabulario.json"), "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)
    return {"contribuicoes": n, "correcoes": len(vocab["correcoes"]), "palavras": len(vocab["palavras"])}


if __name__ == "__main__":
    print(compilar())
