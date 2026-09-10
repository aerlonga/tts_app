from app.core.pronunciation import apply_pronunciation, resolve_language_code


def test_sigla_go_e_soletrada():
    assert apply_pronunciation("selecione a GO correspondente") == "selecione a gê-ó correspondente"


def test_goinfra_nao_e_soletrada():
    assert apply_pronunciation("Aplicativo da GOINFRA") == "Aplicativo da Goinfra"


def test_rodovia_com_numero():
    assert apply_pronunciation("a GO-060") == "a gê-ó zero seis zero"
    assert apply_pronunciation("a BR 101") == "a bê-erre um zero um"


def test_email_e_falado_por_partes():
    assert (
        apply_pronunciation("email getin@goinfra.go.gov.br agora")
        == "email getin arroba Goinfra ponto gê-ó ponto gov ponto bê-erre agora"
    )


def test_palavras_com_go_nao_sao_afetadas():
    texto = "Ele vai jogar go go e Goiás agora"
    assert apply_pronunciation(texto) == texto


def test_outros_idiomas_passam_direto():
    texto = "select the GO option"
    assert apply_pronunciation(texto, language="en") == texto


def test_resolve_language_code():
    assert resolve_language_code("pt") == "pt-BR"
    assert resolve_language_code("en") == "en-US"
    assert resolve_language_code("pt-PT") == "pt-PT"
