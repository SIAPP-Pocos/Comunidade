"""
Escreve as notas da versão da base (Markdown) a partir de dist/resumo.json e, se houver,
do resumo da versão anterior: o que tem na base e quais pacotes entraram desde a última.

Uso:  python ferramentas/notas.py dist/resumo.json [resumo-anterior.json]
"""
from __future__ import annotations

import json
import os
import sys


def _ler(caminho: str | None) -> dict | None:
    if not caminho or not os.path.isfile(caminho):
        return None
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _plural(n: int, um: str, varios: str) -> str:
    return f"{n} {um if n == 1 else varios}"


def notas(resumo: dict, anterior: dict | None = None) -> str:
    c = resumo["contagens"]
    linhas = [f"Base consolidada de todas as contribuições aceitas até {resumo['gerado_em'][:10]}. Licença CC-BY 4.0.",
              "",
              "| Na base | Quantidade |", "|---|---|",
              f"| Pacotes de contribuição | {c['contribuicoes']} |",
              f"| Correções de OCR | {c['correcoes']} |",
              f"| Palavras do vocabulário | {c['palavras']} |",
              f"| Dados transcritos (fatos) | {c['fatos']} |",
              f"| Interpretações de perfil | {c['interpretacoes']} |",
              f"| Poços com dados | {c['pocos']} |", ""]
    vistos = {p["id"] for p in anterior["pacotes"]} if anterior else set()
    novos = [p for p in resumo["pacotes"] if p["id"] not in vistos]
    if anterior:
        linhas.append(f"**Desde a {anterior['versao_base']}:** " + (_plural(len(novos), "pacote novo", "pacotes novos")
                                                                  if novos else "nenhum pacote novo") + ".")
    else:
        linhas.append("**Primeira versão publicada da base.**")
    for p in novos:
        partes = [_plural(p["correcoes"], "correção", "correções"), _plural(p["fatos"], "fato", "fatos")]
        if p["interpretacoes"]:
            partes.append(_plural(p["interpretacoes"], "interpretação", "interpretações"))
        poc = f" — {', '.join(p['pocos'][:8])}{'…' if len(p['pocos']) > 8 else ''}" if p["pocos"] else ""
        quem = p["autor"] + (f" ({p['instituicao']})" if p.get("instituicao") else "")
        linhas.append(f"- {quem}: {', '.join(partes)}{poc}")
    linhas += ["", "O SIAPP baixa esta base sozinho (aba Comunidade). Para usar sem o SIAPP: "
               "`siapp-dados.sqlite` (SQLite) e `vocabulario.json`."]
    return "\n".join(linhas) + "\n"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print(notas(_ler(sys.argv[1]), _ler(sys.argv[2] if len(sys.argv) > 2 else None)), end="")
