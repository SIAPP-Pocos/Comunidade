"""
Recebe um pacote enviado pelo SIAPP como pedido no GitHub (issue) e o prepara para virar um pull request.

Como o SIAPP envia (motor/envio.py, desde a 1.4):
  - a issue tem no texto a marca  <!-- siapp-pacote id=<uuid> partes=<n> sha256=<hex> -->
  - o pacote (JSON compactado com gzip, em base64) vai em <n> comentários do próprio autor da issue,
    cada um com a marca  <!-- siapp-parte i/n -->  e o trecho dentro de um bloco ```.

O que este script faz (chamado pelo workflow "receber pacote", que nunca executa nada do que vem na issue):
  1. junta as partes; se ainda faltar alguma, sai com código 2 (o workflow espera o próximo comentário);
  2. confere o SHA-256, descompacta (no máximo 20 MB) e lê o JSON;
  3. grava contribuicoes/AAAA-MM-DD_sobrenome_<id>.json e valida a pasta inteira (ferramentas/validar.py);
  4. escreve o resumo para o comentário e as saídas para o workflow.

Uso:  python ferramentas/receber_pacote.py issue.json comentarios.json saida/
Códigos de saída: 0 pronto para o pull request; 2 faltam partes; 1 recusado (motivo em saida/erro.md).
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import io
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validar  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RE_CABECALHO = re.compile(r"<!--\s*siapp-pacote\s+id=([0-9A-Za-z-]{8,64})\s+partes=(\d{1,3})\s+sha256=([0-9a-f]{64})\s*-->")
RE_PARTE = re.compile(r"<!--\s*siapp-parte\s+(\d{1,3})/(\d{1,3})\s*-->\s*```[a-z]*\s*([A-Za-z0-9+/=\s]+?)\s*```", re.S)
MAX_PARTES = 200
MAX_JSON = 20 * 1024 * 1024


class Recusado(Exception):
    pass


def cabecalho(corpo: str) -> dict | None:
    m = RE_CABECALHO.search(corpo or "")
    if not m:
        return None
    partes = int(m.group(2))
    if not 1 <= partes <= MAX_PARTES:
        raise Recusado(f"Número de partes fora do limite ({partes}).")
    return {"id": m.group(1), "partes": partes, "sha256": m.group(3)}


def juntar(cab: dict, comentarios: list[dict], autor: str) -> str | None:
    """O base64 completo, só com comentários do autor da issue. None se ainda falta parte."""
    pedacos: dict[int, str] = {}
    for c in comentarios:
        if (c.get("user") or {}).get("login") != autor:
            continue
        for m in RE_PARTE.finditer(c.get("body") or ""):
            i, n = int(m.group(1)), int(m.group(2))
            if n != cab["partes"] or not 1 <= i <= n:
                raise Recusado(f"Parte {i}/{n} não bate com o cabeçalho ({cab['partes']} partes).")
            pedacos.setdefault(i, re.sub(r"\s+", "", m.group(3)))
    if len(pedacos) < cab["partes"]:
        return None
    return "".join(pedacos[i] for i in range(1, cab["partes"] + 1))


def decodificar(b64: str, sha256: str) -> dict:
    try:
        comprimido = base64.b64decode(b64, validate=True)
    except ValueError as e:
        raise Recusado("O pacote não está em base64 válido.") from e
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(comprimido)) as g:
            dados = g.read(MAX_JSON + 1)
    except (OSError, EOFError) as e:
        raise Recusado("O pacote não está compactado como o SIAPP faz (gzip).") from e
    if len(dados) > MAX_JSON:
        raise Recusado("O pacote passa de 20 MB. Divida o envio (exporte em partes menores).")
    if hashlib.sha256(dados).hexdigest() != sha256:
        raise Recusado("O conteúdo não confere com o SHA-256 do cabeçalho (envio incompleto ou alterado).")
    try:
        pacote = json.loads(dados.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise Recusado(f"O pacote não é um JSON válido ({e}).") from e
    if not isinstance(pacote, dict):
        raise Recusado("O pacote não é um objeto JSON.")
    return pacote


def _slug(t: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFD", t or "") if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:30] or "autor"


def nome_arquivo(pacote: dict) -> str:
    data = str(pacote.get("criado_em") or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data):
        data = "0000-00-00"
    nome = (pacote.get("autor") or {}).get("nome") or ""
    sobrenome = _slug(nome.split()[-1] if nome.split() else "")
    return f"{data}_{sobrenome}_{_slug(str(pacote.get('id') or ''))[:8]}.json"


def contar(p: dict) -> dict:
    v = p.get("vocabulario") or {}
    pocos = sorted({x.get("poco") for x in (p.get("fatos") or []) + (p.get("interpretacoes") or []) if x.get("poco")})
    return {"correcoes": len(v.get("correcoes") or []), "palavras": len(v.get("palavras") or []),
            "fatos": len(p.get("fatos") or []), "interpretacoes": len(p.get("interpretacoes") or []),
            "pocos": pocos}


def receber(issue: dict, comentarios: list[dict], pasta_contrib: str) -> dict:
    """Grava o pacote em `pasta_contrib` e valida. Devolve {estado: pronto|incompleto, ...}; Recusado se não serve."""
    cab = cabecalho(issue.get("body") or "")
    if not cab:
        raise Recusado("A issue não tem a marca de pacote do SIAPP.")
    autor = (issue.get("user") or {}).get("login") or ""
    b64 = juntar(cab, comentarios, autor)
    if b64 is None:
        return {"estado": "incompleto"}
    pacote = decodificar(b64, cab["sha256"])
    if str(pacote.get("id")) != cab["id"]:
        raise Recusado("O id do pacote não bate com o do cabeçalho.")
    for existente in os.listdir(pasta_contrib):
        if existente.endswith(".json"):
            try:
                with open(os.path.join(pasta_contrib, existente), encoding="utf-8") as f:
                    if json.load(f).get("id") == cab["id"]:
                        raise Recusado(f"Este pacote já está na base ({existente}).")
            except (OSError, ValueError):
                pass
    nome = nome_arquivo(pacote)
    caminho = os.path.join(pasta_contrib, nome)
    n = 2
    while os.path.exists(caminho):
        caminho = os.path.join(pasta_contrib, nome.replace(".json", f"-{n}.json"))
        n += 1
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(pacote, f, ensure_ascii=False, indent=2)
        f.write("\n")
    erros = [e for e in validar.validar(pasta_contrib) if e.startswith(os.path.basename(caminho) + ":")]
    graves = [e for e in erros if "CONFLITO" not in e]
    if graves:
        os.remove(caminho)
        raise Recusado("O pacote não passou na validação:\n" + "\n".join(f"- {e}" for e in graves[:30]))
    return {"estado": "pronto", "arquivo": os.path.basename(caminho), "autor": pacote.get("autor") or {},
            "login": autor, "id": cab["id"], "itens": contar(pacote),
            "conflitos": [e for e in erros if "CONFLITO" in e]}


def texto_pr(r: dict, numero_issue: int) -> str:
    a, it = r["autor"], r["itens"]
    quem = a.get("nome", "?") + (f" ({a['instituicao']})" if a.get("instituicao") else "")
    linhas = [f"Pacote enviado pelo SIAPP por @{r['login']} — {quem}.", "",
              f"- Correções de OCR: {it['correcoes']}", f"- Palavras do vocabulário: {it['palavras']}",
              f"- Dados transcritos (fatos): {it['fatos']}", f"- Interpretações de perfil: {it['interpretacoes']}",
              f"- Poços: {', '.join(it['pocos'][:30]) or '—'}{' …' if len(it['pocos']) > 30 else ''}", "",
              f"Arquivo: `contribuicoes/{r['arquivo']}`. A validação passou."]
    if r["conflitos"]:
        linhas += ["", "**Conflitos com contribuições já aceitas (resolver na revisão):**"]
        linhas += [f"- {e}" for e in r["conflitos"][:30]]
    linhas += ["", "Revisão: confira uma amostra das correções e todos os fatos novos na imagem da página no REATE "
               "(documento, página e caixa estão no pacote). Aceitar publica a base nova sozinho.",
               "", f"Closes #{numero_issue}"]
    return "\n".join(linhas) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__)
        return 1
    with open(argv[1], encoding="utf-8") as f:
        issue = json.load(f)
    with open(argv[2], encoding="utf-8") as f:
        comentarios = json.load(f)
    saida = argv[3]
    os.makedirs(saida, exist_ok=True)
    try:
        r = receber(issue, comentarios, os.path.join(RAIZ, "contribuicoes"))
    except Recusado as e:
        with open(os.path.join(saida, "erro.md"), "w", encoding="utf-8") as f:
            f.write(str(e) + "\n")
        print("RECUSADO:", e)
        return 1
    if r["estado"] == "incompleto":
        print("Faltam partes; esperando o próximo comentário.")
        return 2
    with open(os.path.join(saida, "pr.md"), "w", encoding="utf-8") as f:
        f.write(texto_pr(r, issue["number"]))
    with open(os.path.join(saida, "resultado.json"), "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False)
    nome = re.sub(r"[<>\r\n\"]", "", (r["autor"].get("nome") or r["login"]))[:80].strip() or r["login"]
    it = r["itens"]
    with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a", encoding="utf-8") as f:
        f.write(f"arquivo={r['arquivo']}\nnome={nome}\n")
        f.write(f"titulo=Pacote de {nome}: {it['correcoes']} correções, {it['fatos']} fatos, "
                f"{it['interpretacoes']} interpretações\n")
    print("PRONTO:", r["arquivo"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
