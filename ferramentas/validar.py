"""
Valida todas as contribuições em contribuicoes/*.json.

Regras, além do esquema JSON (esquema/contribuicao-v<N>.schema.json, conforme
o campo versao_formato de cada pacote; as versões 1, 2 e 3 são aceitas):
  - cada pacote tem `id` único no repositório;
  - nenhuma correção troca um número isolado (o esquema exige letra em "de");
  - fato com base acima do topo é recusado;
  - CONFLITO: duas contribuições corrigindo a mesma palavra para formas diferentes,
    ou o mesmo fato (mesmo id) enviado por autores diferentes, precisam ser
    resolvidos na revisão — o validador falha e mostra os autores.
    O mesmo autor reenviando um fato com o mesmo id é uma atualização (vale o mais novo).
  - interpretação de perfil (v3) com intervalo de base acima do topo é recusada; a mesma
    interpretação (mesmo id) enviada por autores diferentes é CONFLITO, como os fatos.

Uso:  python ferramentas/validar.py        (código de saída 1 se houver erro)
"""
from __future__ import annotations

import glob
import json
import os
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSOES = (1, 2, 3)


def normalizar(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn").upper()


def carregar_esquema(versao: int):
    with open(os.path.join(RAIZ, "esquema", f"contribuicao-v{versao}.schema.json"), encoding="utf-8") as f:
        return json.load(f)


def validar(pasta: str | None = None) -> list[str]:
    import jsonschema

    pasta = pasta or os.path.join(RAIZ, "contribuicoes")
    validadores = {v: jsonschema.Draft202012Validator(carregar_esquema(v),
                                                      format_checker=jsonschema.FormatChecker())
                   for v in VERSOES}
    erros, ids, correcoes, fatos, interps = [], {}, {}, {}, {}
    for caminho in sorted(glob.glob(os.path.join(pasta, "*.json"))):
        nome = os.path.basename(caminho)
        try:
            with open(caminho, encoding="utf-8") as f:
                c = json.load(f)
        except json.JSONDecodeError as e:
            erros.append(f"{nome}: JSON inválido ({e})")
            continue
        versao = c.get("versao_formato")
        if versao not in validadores:
            erros.append(f"{nome}: versao_formato {versao!r} não suportada (aceitas: {VERSOES})")
            continue
        for e in validadores[versao].iter_errors(c):
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
        for f in c.get("fatos", []):
            topo, base = f.get("prof_topo"), f.get("prof_base")
            if isinstance(topo, (int, float)) and isinstance(base, (int, float)) and base < topo:
                erros.append(f"{nome}: fato {f.get('id')}: base ({base}) acima do topo ({topo})")
            anterior = fatos.get(f.get("id"))
            if anterior and anterior[0] != autor:
                erros.append(f"{nome}: CONFLITO no fato {f['id']} ({f.get('poco')}): enviado por "
                             f"{autor} e por {anterior[0]} ({anterior[1]}) — resolva na revisão")
            fatos.setdefault(f.get("id"), (autor, nome))
        for i in c.get("interpretacoes", []):
            for k, iv in enumerate(i.get("intervalos", [])):
                t, b = iv.get("topo"), iv.get("base")
                if isinstance(t, (int, float)) and isinstance(b, (int, float)) and b <= t:
                    erros.append(f"{nome}: interpretação {i.get('id')}: intervalo {k + 1} com base ({b}) "
                                 f"acima do topo ({t})")
            anterior = interps.get(i.get("id"))
            if anterior and anterior[0] != autor:
                erros.append(f"{nome}: CONFLITO na interpretação {i['id']} ({i.get('poco')}): enviada por "
                             f"{autor} e por {anterior[0]} ({anterior[1]}) — resolva na revisão")
            interps.setdefault(i.get("id"), (autor, nome))
    return erros


if __name__ == "__main__":
    erros = validar()
    for e in erros:
        print("ERRO", e)
    n = len(glob.glob(os.path.join(RAIZ, "contribuicoes", "*.json")))
    print(f"{n} contribuição(ões) verificada(s), {len(erros)} erro(s).")
    sys.exit(1 if erros else 0)
