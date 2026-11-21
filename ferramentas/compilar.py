"""
Compila todas as contribuições numa base única, para o SIAPP baixar.

Saída em dist/:
  siapp-dados.sqlite   a base que o SIAPP aplica (aba Comunidade → Atualizar)
  vocabulario.json     vocabulário consolidado, para quem quiser usar sem o SIAPP
  resumo.json          o que tem na base (contagens e a lista de pacotes, com os poços de cada um):
                       pequeno, para o SIAPP saber o que mudou antes de baixar a base inteira

contribuicoes/exemplo.json mostra o formato e não entra na base.

Esquema da base (versao_formato_base 1 — o SIAPP confere antes de aplicar):
  meta           formato, versao_formato_base, versao_base, gerado_em
  contribuicoes  id, autor, instituicao, orcid, criado_em, arquivo
  vocab          tipo (palavra | correcao | manter_original), de, para, autor, contribuicao
  fatos          id, poco, tipo, nome, valor, unidade, prof_topo, prof_base, observacao,
                 criado_em, fonte_sha256, fonte_caminho, fonte_bacia, pagina, caixa (JSON),
                 autor, contribuicao
  apelidos       apelido, poco, contribuicao
  interpretacoes id, poco, titulo, autor, criado_em, dados (JSON: o item do pacote inteiro),
                 contribuicao — interpretações de perfil (formato v3; o SIAPP 0.35+ aplica,
                 os anteriores ignoram a tabela)

Cada linha guarda o pacote de origem: a autoria nunca se perde. Um fato ou uma
interpretação reenviada pelo mesmo autor (mesmo id) entra uma vez, na versão mais nova.

Uso:  python ferramentas/compilar.py [--versao v2026.10.0]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sqlite3
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORA_DA_BASE = {"exemplo.json"}
FORMATO_BASE = "siapp-dados-base"
VERSAO_FORMATO_BASE = 1

ESQUEMA = """
CREATE TABLE meta (chave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE contribuicoes (id TEXT PRIMARY KEY, autor TEXT, instituicao TEXT, orcid TEXT,
                            criado_em TEXT, arquivo TEXT);
CREATE TABLE vocab (tipo TEXT, de TEXT, para TEXT, autor TEXT,
                    contribuicao TEXT REFERENCES contribuicoes(id));
CREATE TABLE fatos (id TEXT PRIMARY KEY, poco TEXT, tipo TEXT, nome TEXT, valor TEXT, unidade TEXT,
                    prof_topo REAL, prof_base REAL, observacao TEXT, criado_em TEXT,
                    fonte_sha256 TEXT, fonte_caminho TEXT, fonte_bacia TEXT, pagina INTEGER,
                    caixa TEXT, autor TEXT, contribuicao TEXT REFERENCES contribuicoes(id));
CREATE TABLE apelidos (apelido TEXT, poco TEXT, contribuicao TEXT REFERENCES contribuicoes(id));
CREATE TABLE interpretacoes (id TEXT PRIMARY KEY, poco TEXT, titulo TEXT, autor TEXT, criado_em TEXT,
                             dados TEXT, contribuicao TEXT REFERENCES contribuicoes(id));
CREATE INDEX fatos_poco ON fatos(poco);
CREATE INDEX interpretacoes_poco ON interpretacoes(poco);
"""


def compilar(pasta_contrib: str | None = None, saida: str | None = None, versao: str = "dev") -> dict:
    pasta_contrib = pasta_contrib or os.path.join(RAIZ, "contribuicoes")
    saida = saida or os.path.join(RAIZ, "dist")
    os.makedirs(saida, exist_ok=True)
    banco = os.path.join(saida, "siapp-dados.sqlite")
    if os.path.exists(banco):
        os.remove(banco)
    con = sqlite3.connect(banco)
    con.executescript(ESQUEMA)
    gerado = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con.executemany("INSERT INTO meta VALUES (?, ?)", [
        ("formato", FORMATO_BASE), ("versao_formato_base", str(VERSAO_FORMATO_BASE)),
        ("versao_base", versao), ("gerado_em", gerado)])
    vocab = {"palavras": [], "correcoes": {}, "ignorar": []}
    pacotes = []
    for caminho in sorted(glob.glob(os.path.join(pasta_contrib, "*.json"))):
        if os.path.basename(caminho) in FORA_DA_BASE:
            continue
        with open(caminho, encoding="utf-8") as f:
            pacotes.append((os.path.basename(caminho), json.load(f)))
    pacotes.sort(key=lambda x: x[1].get("criado_em", ""))     # o mais novo sobrescreve fatos repetidos
    n_fatos = 0
    for arquivo, c in pacotes:
        a = c["autor"]
        con.execute("INSERT INTO contribuicoes VALUES (?,?,?,?,?,?)",
                    (c["id"], a["nome"], a.get("instituicao"), a.get("orcid"), c["criado_em"], arquivo))
        v = c.get("vocabulario", {})
        for x in v.get("correcoes", []):
            con.execute("INSERT INTO vocab VALUES ('correcao', ?, ?, ?, ?)", (x["de"], x["para"], a["nome"], c["id"]))
            vocab["correcoes"].setdefault(x["de"], x["para"])
        for t in v.get("palavras", []):
            con.execute("INSERT INTO vocab VALUES ('palavra', ?, NULL, ?, ?)", (t, a["nome"], c["id"]))
            if t not in vocab["palavras"]:
                vocab["palavras"].append(t)
        for t in v.get("manter_original", []):
            con.execute("INSERT INTO vocab VALUES ('manter_original', ?, NULL, ?, ?)", (t, a["nome"], c["id"]))
            if t not in vocab["ignorar"]:
                vocab["ignorar"].append(t)
        for f in c.get("fatos", []):
            fo = f.get("fonte", {})
            con.execute("INSERT OR REPLACE INTO fatos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (f["id"], f["poco"], f["tipo"], f.get("nome"), f.get("valor"), f.get("unidade"),
                         f.get("prof_topo"), f.get("prof_base"), f.get("observacao"), f.get("criado_em"),
                         fo.get("sha256"), fo.get("caminho_remoto"), fo.get("bacia"), fo.get("pagina"),
                         json.dumps(fo["caixa"]) if fo.get("caixa") else None, a["nome"], c["id"]))
        for ap in c.get("apelidos", []):
            con.execute("INSERT INTO apelidos VALUES (?,?,?)", (ap["apelido"], ap["poco"], c["id"]))
        for i in c.get("interpretacoes", []):
            con.execute("INSERT OR REPLACE INTO interpretacoes VALUES (?,?,?,?,?,?,?)",
                        (i["id"], i["poco"], i.get("titulo"), a["nome"], i.get("criado_em"),
                         json.dumps(i, ensure_ascii=False), c["id"]))
    n_fatos = con.execute("SELECT count(*) FROM fatos").fetchone()[0]
    n_interp = con.execute("SELECT count(*) FROM interpretacoes").fetchone()[0]
    pocos = {p for (p,) in con.execute("SELECT poco FROM fatos UNION SELECT poco FROM interpretacoes")}
    con.commit()
    con.close()
    with open(os.path.join(saida, "vocabulario.json"), "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)
    r = {"contribuicoes": len(pacotes), "correcoes": len(vocab["correcoes"]),
         "palavras": len(vocab["palavras"]), "fatos": n_fatos, "interpretacoes": n_interp,
         "pocos": len(pocos), "versao": versao}
    resumo = {"formato": "siapp-dados-resumo", "versao_base": versao, "gerado_em": gerado,
              "contagens": {k: v for k, v in r.items() if k != "versao"},
              "pacotes": [_resumo_do_pacote(arq, c) for arq, c in pacotes]}
    with open(os.path.join(saida, "resumo.json"), "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    return r


def _resumo_do_pacote(arquivo: str, c: dict) -> dict:
    v = c.get("vocabulario", {})
    pocos = sorted({x["poco"] for x in c.get("fatos", []) + c.get("interpretacoes", [])})
    return {"id": c["id"], "arquivo": arquivo, "autor": c["autor"]["nome"],
            "instituicao": c["autor"].get("instituicao"), "criado_em": c["criado_em"],
            "correcoes": len(v.get("correcoes", [])), "palavras": len(v.get("palavras", [])),
            "fatos": len(c.get("fatos", [])), "interpretacoes": len(c.get("interpretacoes", [])),
            "pocos": pocos}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--versao", default=os.environ.get("GITHUB_REF_NAME", "dev"))
    print(compilar(versao=ap.parse_args().versao))
