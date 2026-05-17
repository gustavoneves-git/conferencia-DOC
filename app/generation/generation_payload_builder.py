from datetime import datetime

from app.generation.ltda_constituicao_schema import BOOLEAN_TRUE_VALUES, SENSITIVE_CLAUSE_FIELDS, STANDARD_DOCUMENT_TYPE


def build_ltda_constituicao_payload(form_data: dict) -> dict:
    empresa = {
        "razao_social": _get(form_data, "razao_social"),
        "nome_fantasia": _get(form_data, "nome_fantasia"),
        "endereco_sede": {
            "logradouro": _get(form_data, "sede_logradouro"),
            "numero": _get(form_data, "sede_numero"),
            "complemento": _get(form_data, "sede_complemento"),
            "bairro": _get(form_data, "sede_bairro"),
            "cidade": _get(form_data, "sede_cidade"),
            "uf": _get(form_data, "sede_uf").upper(),
            "cep": _get(form_data, "sede_cep"),
        },
        "objeto_social": _get(form_data, "objeto_social"),
        "foro": _get(form_data, "foro"),
        "data_instrumento": _get(form_data, "data_instrumento"),
        "cidade_assinatura": _get(form_data, "cidade_assinatura"),
        "uf_assinatura": _get(form_data, "uf_assinatura").upper(),
    }
    socios = _build_socios(form_data)
    payload = {
        "document_type": STANDARD_DOCUMENT_TYPE,
        "empresa": empresa,
        "socios": socios,
        "administracao": {
            "administrador_nome": _get(form_data, "administrador_nome"),
            "genero_textual": _get(form_data, "administrador_genero"),
            "tipo_administracao": _get(form_data, "tipo_administracao") or "isolada",
            "pro_labore": _get(form_data, "pro_labore") or "previsto_sem_valor",
            "poderes": _get(form_data, "poderes") or "poderes padrão de administração",
        },
        "capital": {
            "capital_social": _number(_get(form_data, "capital_social")),
            "quotas_totais": _int(_get(form_data, "quotas_totais")),
            "valor_unitario_quota": _number(_get(form_data, "valor_unitario_quota")),
            "forma_integralizacao": _get(form_data, "forma_integralizacao"),
            "prazo_integralizacao": _get(form_data, "prazo_integralizacao"),
        },
        "assinaturas": {
            "advogado": {
                "nome": _get(form_data, "advogado_nome"),
                "oab": _get(form_data, "advogado_oab"),
                "uf_oab": _get(form_data, "advogado_oab_uf").upper(),
            },
            "testemunhas": [
                {"nome": _get(form_data, "testemunha1_nome"), "documento": _get(form_data, "testemunha1_documento")},
                {"nome": _get(form_data, "testemunha2_nome"), "documento": _get(form_data, "testemunha2_documento")},
            ],
        },
        "clausulas_sensiveis": {field: _bool(form_data.get(field)) for field in SENSITIVE_CLAUSE_FIELDS},
        "metadata": {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "source": "formulario_manual",
            "ocr_used": False,
        },
    }
    return payload


def _build_socios(form_data: dict) -> list[dict]:
    socios = []
    for index in (1, 2):
        name = _get(form_data, f"socio{index}_nome")
        if not name:
            continue
        socios.append(
            {
                "tipo_pessoa": _get(form_data, f"socio{index}_tipo_pessoa") or "PF",
                "nome_completo": name,
                "nacionalidade": _get(form_data, f"socio{index}_nacionalidade"),
                "naturalidade": _get(form_data, f"socio{index}_naturalidade"),
                "data_nascimento": _get(form_data, f"socio{index}_data_nascimento"),
                "menor_idade": _bool(form_data.get(f"socio{index}_menor_idade")),
                "incapaz": _bool(form_data.get(f"socio{index}_incapaz")),
                "estrangeiro": _bool(form_data.get(f"socio{index}_estrangeiro")),
                "estado_civil": _get(form_data, f"socio{index}_estado_civil"),
                "regime_bens": _get(form_data, f"socio{index}_regime_bens"),
                "profissao": _get(form_data, f"socio{index}_profissao"),
                "rg": _get(form_data, f"socio{index}_rg"),
                "orgao_expedidor": _get(form_data, f"socio{index}_orgao_expedidor"),
                "cnh": _get(form_data, f"socio{index}_cnh"),
                "cpf": _get(form_data, f"socio{index}_cpf"),
                "endereco": _get(form_data, f"socio{index}_endereco"),
                "quotas": _int(_get(form_data, f"socio{index}_quotas")),
                "percentual": _number(_get(form_data, f"socio{index}_percentual")),
            }
        )
    return socios


def _get(data: dict, key: str) -> str:
    value = data.get(key, "")
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or "").strip()


def _bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in BOOLEAN_TRUE_VALUES


def _number(value: str) -> float:
    value = str(value or "").strip().replace(".", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return 0.0


def _int(value: str) -> int:
    try:
        return int(float(str(value or "0").replace(".", "").replace(",", ".")))
    except ValueError:
        return 0
