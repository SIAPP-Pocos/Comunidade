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
# Pacote exportado de verdade pelo SIAPP 0.10 (contrato entre os dois repositórios):
# se o aplicativo mudar o formato sem mudar o esquema daqui, este teste quebra.
DO_APP = os.path.join(RAIZ, "tests", "dados", "pacote-siapp-0.10.json")
# Formato v3, exportado pelo SIAPP 0.35 (perfil sintético): fatos com trecho e interpretação de perfil.
DO_APP_V3 = os.path.join(RAIZ, "tests", "dados", "pacote-siapp-0.35.json")


def _pasta(tmp_path, *pacotes):
    for i, p in enumerate(pacotes):
        (tmp_path / f"c{i}.json").write_text(json.dumps(p), encoding="utf-8")
    return str(tmp_path)


def _ler(caminho, **mudar):
    with open(caminho, encoding="utf-8") as f:
        c = json.load(f)
    c.update(mudar)
    return c


def test_exemplo_do_repositorio_e_valido():
    assert validar.validar() == []


def test_pacote_exportado_pelo_siapp_e_valido(tmp_path):
    assert validar.validar(_pasta(tmp_path, _ler(DO_APP))) == []


def test_versao_1_continua_aceita(tmp_path):
    assert _ler(EXEMPLO)["versao_formato"] == 1
    assert validar.validar(_pasta(tmp_path, _ler(EXEMPLO))) == []


def test_correcao_de_numero_isolado_e_recusada(tmp_path):
    c = _ler(EXEMPLO, vocabulario={"correcoes": [{"de": "87", "para": "83"}]})
    assert any("correcoes/0/de" in e for e in validar.validar(_pasta(tmp_path, c)))


def test_conflito_entre_autores_e_apontado(tmp_path):
    a = _ler(EXEMPLO)
    b = _ler(EXEMPLO, id="11111111-2222-4333-8444-555555555555", autor={"nome": "Outra Pessoa"},
             vocabulario={"correcoes": [{"de": "BARIGIRAS", "para": "BARRERAS"}]})
    erros = validar.validar(_pasta(tmp_path, a, b))
    assert len(erros) == 1 and "CONFLITO" in erros[0] and "Outra Pessoa" in erros[0]


def test_fato_de_outro_autor_com_mesmo_id_e_conflito(tmp_path):
    a = _ler(DO_APP)
    b = _ler(DO_APP, id="11111111-2222-4333-8444-555555555555", autor={"nome": "Outra Pessoa"})
    erros = validar.validar(_pasta(tmp_path, a, b))
    assert any("CONFLITO no fato" in e for e in erros)


def test_fato_com_base_acima_do_topo(tmp_path):
    c = _ler(DO_APP)
    c["fatos"][0]["prof_base"] = 10.0
    assert any("acima do topo" in e for e in validar.validar(_pasta(tmp_path, c)))


def test_fato_de_tipo_desconhecido(tmp_path):
    c = _ler(DO_APP)
    c["fatos"][0]["tipo"] = "palpite"
    assert any("fatos/0/tipo" in e for e in validar.validar(_pasta(tmp_path, c)))


def test_id_repetido_e_campo_desconhecido(tmp_path):
    erros = validar.validar(_pasta(tmp_path, _ler(EXEMPLO), _ler(EXEMPLO, extra=1)))
    assert any("id repetido" in e for e in erros) and any("extra" in e for e in erros)


def test_compilar_preserva_autoria_e_fonte(tmp_path):
    shutil.copy(EXEMPLO, tmp_path / "exemplo.json")
    shutil.copy(DO_APP, tmp_path / "app.json")
    r = compilar.compilar(str(tmp_path), str(tmp_path / "dist"), versao="v2026.10.0")
    assert r["contribuicoes"] == 2 and r["fatos"] == 1 and r["versao"] == "v2026.10.0"
    con = sqlite3.connect(tmp_path / "dist" / "siapp-dados.sqlite")
    meta = dict(con.execute("SELECT chave, valor FROM meta"))
    assert meta["formato"] == "siapp-dados-base" and meta["versao_formato_base"] == "1"
    linha = con.execute("SELECT v.de, k.autor FROM vocab v JOIN contribuicoes k ON k.id = v.contribuicao "
                        "WHERE v.de = 'BARIGIRAS' ORDER BY k.criado_em").fetchone()
    assert linha == ("BARIGIRAS", "Ruan da Silva Nobre")
    f = con.execute("SELECT poco, pagina, caixa, fonte_sha256 FROM fatos").fetchone()
    assert f[0] == "7-GMR-13-RN" and f[1] == 28 and json.loads(f[2])[0] == 0.7642 and len(f[3]) == 64


def test_pacote_v3_exportado_pelo_siapp_e_valido(tmp_path):
    c = _ler(DO_APP_V3)
    assert c["versao_formato"] == 3 and c["interpretacoes"] and any(f["tipo"] == "trecho" for f in c["fatos"])
    assert validar.validar(_pasta(tmp_path, c)) == []


def test_interpretacao_invalida(tmp_path):
    c = _ler(DO_APP_V3)
    i = c["interpretacoes"][0]
    i["intervalos"][0]["base"] = i["intervalos"][0]["topo"] - 1
    i["metodos"]["sw"] = "magia"
    i["parametros"]["chute"] = 1
    erros = " ".join(validar.validar(_pasta(tmp_path, c)))
    assert "acima do topo" in erros and "metodos/sw" in erros and "chute" in erros


def test_interpretacao_em_pacote_v2_e_recusada(tmp_path):
    c = _ler(DO_APP_V3, versao_formato=2)
    assert any("interpretacoes" in e for e in validar.validar(_pasta(tmp_path, c)))


def test_mesma_interpretacao_de_outro_autor_e_conflito(tmp_path):
    a = _ler(DO_APP_V3)
    b = _ler(DO_APP_V3, id="11111111-2222-4333-8444-555555555555", autor={"nome": "Outra Pessoa"}, fatos=[])
    assert any("CONFLITO na interpretação" in e for e in validar.validar(_pasta(tmp_path, a, b)))


def test_compilar_leva_as_interpretacoes(tmp_path):
    shutil.copy(DO_APP_V3, tmp_path / "v3.json")
    r = compilar.compilar(str(tmp_path), str(tmp_path / "dist"), versao="v2026.11.0")
    assert r["interpretacoes"] == 1 and r["fatos"] == 2
    con = sqlite3.connect(tmp_path / "dist" / "siapp-dados.sqlite")
    poco, autor, dados = con.execute("SELECT poco, autor, dados FROM interpretacoes").fetchone()
    d = json.loads(dados)
    assert poco == "7-TST-1-RN" and autor == "Ruan da Silva Nobre" and d["parametros"]["rw"] == 0.05
