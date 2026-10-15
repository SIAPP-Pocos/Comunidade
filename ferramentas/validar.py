"""
Valida todas as contribuições em contribuicoes/*.json.

Regras, além do esquema JSON (esquema/contribuicao-v1.schema.json):
  - cada pacote tem `id` único no repositório;
  - nenhuma correção troca um número isolado (o esquema já exige letra em "de");
  - CONFLITO: duas contribuições corrigindo a mesma palavra para formas diferentes
    precisam ser resolvidas na revisão — o validador falha e mostra os autores.

Uso:  python ferramentas/validar.py        (código de saída 1 se houver erro)
"""
from __future__ import annotations

import glob
import json
import os
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def normalizar(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn").upper()


def carregar_esquema():
    with open(os.path.join(RAIZ, "esquema", "contribuicao-v1.schema.json"), encoding="utf-8") as f:
        return json.load(f)


def validar(pasta: str | None = None) -> list[str]:
    import jsonschema

    pasta = pasta or os.path.join(RAIZ, "contribuicoes")
    validador = jsonschema.Draft202012Validator(carregar_esquema(),
                                                format_checker=jsonschema.FormatChecker())
    erros, ids, correcoes = [], {}, {}
    for caminho in sorted(glob.glob(os.path.join(pasta, "*.json"))):
        nome = os.path.basename(caminho)
        try:
            with open(caminho, encoding="utf-8") as f:
                c = json.load(f)
        except json.JSONDecodeError as e:
            erros.append(f"{nome}: JSON inválido ({e})")
            continue
        for e in validador.iter_errors(c):
            local = "/".join(str(p) for p in e.absolute_path) or "(raiz)"
            erros.append(f"{nome}: {local}: {e.message}")
        if "id" in c:
            if c["id"] in ids:
                erros.append(f"{nome}: id repetido (já usado em {ids[c['id']]})")
            ids[c["id"]] = nome
        autor = c.get("autor", {}).get("nome", "?")
        for corr in c.get("vocabulario", {}).get("correcoes", []):
            chave = normalizar(corr.get("de", ""))
            if chave in correcoes and normalizar(correcoes[chave][0]) != normalizar(corr.get("para", "")):
                para0, autor0, arq0 = correcoes[chave]
                erros.append(f"{nome}: CONFLITO em '{corr['de']}': '{corr['para']}' ({autor}) "
                             f"× '{para0}' ({autor0}, {arq0}) — resolva na revisão")
            correcoes.setdefault(chave, (corr.get("para", ""), autor, nome))
    return erros


if __name__ == "__main__":
    erros = validar()
    for e in erros:
        print("ERRO", e)
    n = len(glob.glob(os.path.join(RAIZ, "contribuicoes", "*.json")))
    print(f"{n} contribuição(ões) verificada(s), {len(erros)} erro(s).")
    sys.exit(1 if erros else 0)
