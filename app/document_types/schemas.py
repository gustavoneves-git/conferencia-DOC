from copy import deepcopy


CATALOG_REQUIRED_KEYS = {
    "code",
    "label",
    "user_label",
    "group",
    "user_group",
    "description",
    "purpose",
    "required_fields",
    "optional_fields",
    "supporting_documents",
    "output_documents",
    "validation_rules",
    "risk_points",
    "implemented",
    "generation_ready",
    "review_ready",
    "notes",
}


BASE_OUTPUT_DOCUMENTS = [
    "docx_minuta",
    "pdf_minuta",
    "checklist_conferencia",
    "docx_final",
    "pdf_final",
]


FIELD_LABELS = {
    "razao_social": "Razão social",
    "nome_fantasia": "Nome fantasia",
    "endereco_sede": "Endereço da sede",
    "objeto_social": "Objeto social",
    "capital_social": "Capital social",
    "socios": "Sócios",
    "administradores": "Administradores",
    "foro": "Foro",
    "pro_labore": "Pró-labore",
    "clausulas_especiais": "Cláusulas especiais",
    "testemunhas": "Testemunhas",
    "advogado": "Advogado",
    "local_data": "Local e data",
    "dados_empresa": "Dados da empresa",
    "deliberacoes": "Deliberações",
    "acionistas": "Acionistas",
    "diretores": "Diretores",
    "documentos_socios": "Documentos dos sócios",
    "comprovante_endereco": "Comprovante de endereço",
    "viabilidade": "Viabilidade",
    "dbe": "DBE",
}


DEFAULT_FORM_BLOCKS = [
    {
        "title": "Dados do ato",
        "fields": ["razao_social", "endereco_sede", "local_data"],
    },
    {
        "title": "Partes e responsáveis",
        "fields": ["socios", "administradores", "acionistas", "diretores"],
    },
    {
        "title": "Conteúdo",
        "fields": ["objeto_social", "capital_social", "deliberacoes", "clausulas_especiais"],
    },
    {
        "title": "Assinaturas",
        "fields": ["advogado", "testemunhas"],
    },
]


FORM_BLOCKS_BY_CODE = {
    "CONSTITUICAO_LTDA": [
        {
            "title": "Dados da empresa",
            "fields": ["razao_social", "nome_fantasia", "endereco_sede", "objeto_social", "capital_social", "foro"],
        },
        {
            "title": "Sócios",
            "fields": [
                "nome_completo",
                "nacionalidade",
                "estado_civil",
                "regime_bens",
                "profissao",
                "rg_cnh",
                "cpf",
                "endereco",
                "quotas",
                "percentual",
            ],
        },
        {
            "title": "Administração",
            "fields": ["administrador", "pro_labore", "poderes", "prazo"],
        },
        {
            "title": "Assinaturas",
            "fields": ["advogado", "testemunhas", "local_data"],
        },
    ],
}


def document_type(
    code: str,
    label: str,
    user_label: str,
    group: str,
    user_group: str,
    description: str,
    purpose: str,
    required_fields: list[str],
    optional_fields: list[str] | None = None,
    supporting_documents: list[str] | None = None,
    validation_rules: list[str] | None = None,
    risk_points: list[str] | None = None,
    notes: str = "",
    implemented: bool = False,
    generation_ready: bool = False,
    review_ready: bool = True,
    output_documents: list[str] | None = None,
) -> dict:
    return {
        "code": code,
        "label": label,
        "user_label": user_label,
        "group": group,
        "user_group": user_group,
        "description": description,
        "purpose": purpose,
        "required_fields": required_fields,
        "optional_fields": optional_fields or [],
        "supporting_documents": supporting_documents or [],
        "output_documents": output_documents or deepcopy(BASE_OUTPUT_DOCUMENTS),
        "validation_rules": validation_rules or [],
        "risk_points": risk_points or [],
        "implemented": implemented,
        "generation_ready": generation_ready,
        "review_ready": review_ready,
        "notes": notes,
    }


def get_form_blocks_for_type(code: str, doc_type: dict) -> list[dict]:
    blocks = deepcopy(FORM_BLOCKS_BY_CODE.get(code, DEFAULT_FORM_BLOCKS))
    available = set(doc_type.get("required_fields", [])) | set(doc_type.get("optional_fields", []))
    for block in blocks:
        block["fields"] = [
            {
                "name": field,
                "label": FIELD_LABELS.get(field, field.replace("_", " ").capitalize()),
                "required": field in doc_type.get("required_fields", []),
                "available": field in available or code == "CONSTITUICAO_LTDA",
            }
            for field in block["fields"]
        ]
    return blocks
