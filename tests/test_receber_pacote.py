"""O pacote que o SIAPP envia como issue vira um arquivo em contribuicoes/ (ferramentas/receber_pacote.py)."""
import base64
import gzip
import hashlib
import json
import os
import shutil
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import receber_pacote as rp  # noqa: E402

DO_APP_V3 = os.path.join(RAIZ, "tests", "dados", "pacote-siapp-0.35.json")


def _issue(pacote, tamanho=40, autor="maria", mexer=None):
    """Como o SIAPP monta (motor/envio.py): cabeçalho na issue, base64 do gzip em comentários do autor."""
    dados = json.dumps(pacote, ensure_ascii=False).encode()
    b64 = base64.b64encode(gzip.compress(dados)).decode()
    pedacos = [b64[i:i + tamanho] for i in range(0, len(b64), tamanho)]
    sha = hashlib.sha256(dados).hexdigest()
    issue = {"number": 7, "user": {"login": autor, "id": 1},
             "body": f"Pacote do SIAPP\n\n<!-- siapp-pacote id={pacote['id']} partes={len(pedacos)} sha256={sha} -->"}
    comentarios = [{"user": {"login": autor},
                    "body": f"<!-- siapp-parte {i}/{len(pedacos)} -->\n```\n{p}\n```"} for i, p in enumerate(pedacos, 1)]
    if mexer:
        mexer(issue, comentarios)
    return issue, comentarios


@pytest.fixture
def pacote():
    with open(DO_APP_V3, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def pasta(tmp_path):
    p = tmp_path / "contribuicoes"
    p.mkdir()
    return str(p)


def test_recebe_pacote_completo(pacote, pasta):
    issue, comentarios = _issue(pacote)
    assert len(comentarios) > 3
    r = rp.receber(issue, list(reversed(comentarios)), pasta)       # a ordem dos comentários não importa
    assert r["estado"] == "pronto" and r["login"] == "maria" and r["conflitos"] == []
    with open(os.path.join(pasta, r["arquivo"]), encoding="utf-8") as f:
        assert json.load(f) == pacote
    assert r["arquivo"].startswith(pacote["criado_em"][:10] + "_") and r["arquivo"].endswith(".json")
    assert r["itens"]["fatos"] == len(pacote["fatos"])
    texto = rp.texto_pr(r, 7)
    assert "@maria" in texto and "Closes #7" in texto


def test_espera_as_partes_que_faltam(pacote, pasta):
    issue, comentarios = _issue(pacote)
    assert rp.receber(issue, comentarios[:-1], pasta) == {"estado": "incompleto"}
    assert os.listdir(pasta) == []


def test_comentario_de_outra_pessoa_nao_conta(pacote, pasta):
    issue, comentarios = _issue(pacote)
    comentarios[0]["user"]["login"] = "intruso"
    assert rp.receber(issue, comentarios, pasta) == {"estado": "incompleto"}


def test_conteudo_alterado_e_recusado(pacote, pasta):
    def mexer(issue, comentarios):
        import re
        issue["body"] = re.sub(r"sha256=[0-9a-f]{64}", "sha256=" + "0" * 64, issue["body"])
    issue, comentarios = _issue(pacote, mexer=mexer)
    with pytest.raises(rp.Recusado, match="SHA-256"):
        rp.receber(issue, comentarios, pasta)


def test_pacote_invalido_e_recusado_e_nao_fica_na_pasta(pacote, pasta):
    pacote["versao_formato"] = 99
    issue, comentarios = _issue(pacote)
    with pytest.raises(rp.Recusado, match="validação"):
        rp.receber(issue, comentarios, pasta)
    assert os.listdir(pasta) == []


def test_pacote_repetido_e_recusado(pacote, pasta):
    issue, comentarios = _issue(pacote)
    rp.receber(issue, comentarios, pasta)
    with pytest.raises(rp.Recusado, match="já está na base"):
        rp.receber(issue, comentarios, pasta)


def test_main_escreve_as_saidas(pacote, tmp_path, monkeypatch):
    issue, comentarios = _issue(pacote)
    raiz = tmp_path / "repo"
    shutil.copytree(os.path.join(RAIZ, "esquema"), raiz / "esquema")
    (raiz / "contribuicoes").mkdir()
    monkeypatch.setattr(rp, "RAIZ", str(raiz))
    monkeypatch.setattr(rp.validar, "RAIZ", str(raiz))
    (tmp_path / "i.json").write_text(json.dumps(issue))
    (tmp_path / "c.json").write_text(json.dumps(comentarios))
    saida_gh = tmp_path / "gh_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(saida_gh))
    assert rp.main(["x", str(tmp_path / "i.json"), str(tmp_path / "c.json"), str(tmp_path / "s")]) == 0
    linhas = saida_gh.read_text(encoding="utf-8")
    assert "arquivo=" in linhas and "titulo=Pacote de " in linhas
    assert (tmp_path / "s" / "pr.md").exists()
    (tmp_path / "c.json").write_text("[]")
    assert rp.main(["x", str(tmp_path / "i.json"), str(tmp_path / "c.json"), str(tmp_path / "s")]) == 2
