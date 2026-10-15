import json
import os
import shutil
import sqlite3
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import compilar  # noqa: E402
import validar   # noqa: E402

EXEMPLO = os.path.join(RAIZ, "contribuicoes", "exemplo.json")


def _pasta(tmp_path, *pacotes):
    for i, p in enumerate(pacotes):
        (tmp_path / f"c{i}.json").write_text(json.dumps(p), encoding="utf-8")
    return str(tmp_path)


def _base(**mudar):
    c = json.load(open(EXEMPLO, encoding="utf-8"))
    c.update(mudar)
    return c


def test_exemplo_do_repositorio_e_valido():
    assert validar.validar() == []


def test_correcao_de_numero_isolado_e_recusada(tmp_path):
    c = _base(vocabulario={"correcoes": [{"de": "87", "para": "83"}]})
    assert any("correcoes/0/de" in e for e in validar.validar(_pasta(tmp_path, c)))


def test_conflito_entre_autores_e_apontado(tmp_path):
    a = _base()
    b = _base(id="11111111-2222-4333-8444-555555555555", autor={"nome": "Outra Pessoa"},
              vocabulario={"correcoes": [{"de": "BARIGIRAS", "para": "BARRERAS"}]})
    erros = validar.validar(_pasta(tmp_path, a, b))
    assert len(erros) == 1 and "CONFLITO" in erros[0] and "Outra Pessoa" in erros[0]


def test_id_repetido_e_campo_desconhecido(tmp_path):
    erros = validar.validar(_pasta(tmp_path, _base(), _base(extra=1)))
    assert any("id repetido" in e for e in erros) and any("extra" in e for e in erros)


def test_compilar_preserva_autoria(tmp_path):
    shutil.copy(EXEMPLO, tmp_path / "exemplo.json")
    r = compilar.compilar(str(tmp_path), str(tmp_path / "dist"))
    assert r == {"contribuicoes": 1, "correcoes": 2, "palavras": 0}
    con = sqlite3.connect(tmp_path / "dist" / "siapp-dados.sqlite")
    linha = con.execute("SELECT c.de, k.autor FROM correcoes c JOIN contribuicoes k ON k.id = c.contribuicao "
                        "WHERE c.de = 'BARIGIRAS'").fetchone()
    assert linha == ("BARIGIRAS", "Ruan da Silva Nobre")
