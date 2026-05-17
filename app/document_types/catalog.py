from app.document_types.accessory import ACCESSORY_TYPES
from app.document_types.empresario_individual import EMPRESARIO_INDIVIDUAL_TYPES
from app.document_types.ltda import LTDA_TYPES
from app.document_types.sa import SA_TYPES
from app.document_types.schemas import CATALOG_REQUIRED_KEYS, get_form_blocks_for_type


DOCUMENT_TYPES = tuple(LTDA_TYPES + SA_TYPES + EMPRESARIO_INDIVIDUAL_TYPES + ACCESSORY_TYPES)
_BY_CODE = {item["code"]: item for item in DOCUMENT_TYPES}
USER_GROUP_ORDER = [
    "Contrato Social / LTDA",
    "Alteração Contratual",
    "Ata / Assembleia",
    "Estatuto Social",
    "Empresário Individual / SLU",
    "Documento acessório",
]


def get_all_document_types() -> list[dict]:
    return [dict(item) for item in DOCUMENT_TYPES]


def get_document_type(code: str) -> dict | None:
    item = _BY_CODE.get((code or "").upper())
    if not item:
        return None
    result = dict(item)
    result["form_blocks"] = get_form_blocks_for_type(result["code"], result)
    return result


def get_document_types_by_group(group: str) -> list[dict]:
    value = (group or "").upper()
    return [dict(item) for item in DOCUMENT_TYPES if item["group"].upper() == value]


def get_document_types_by_user_group(user_group: str) -> list[dict]:
    value = (user_group or "").casefold()
    return [dict(item) for item in DOCUMENT_TYPES if item["user_group"].casefold() == value]


def get_generation_ready_types() -> list[dict]:
    return [dict(item) for item in DOCUMENT_TYPES if item["generation_ready"]]


def get_review_ready_types() -> list[dict]:
    return [dict(item) for item in DOCUMENT_TYPES if item["review_ready"]]


def search_document_types(query: str) -> list[dict]:
    needle = " ".join((query or "").casefold().split())
    if not needle:
        return get_all_document_types()
    fields = ("code", "label", "user_label", "group", "user_group", "description", "purpose")
    return [
        dict(item)
        for item in DOCUMENT_TYPES
        if any(needle in str(item.get(field, "")).casefold() for field in fields)
    ]


def get_user_groups() -> list[str]:
    groups = {item["user_group"] for item in DOCUMENT_TYPES}
    ordered = [group for group in USER_GROUP_ORDER if group in groups]
    return ordered + sorted(groups - set(ordered))


def get_types_for_creation_menu() -> list[dict]:
    groups = []
    for user_group in get_user_groups():
        types = get_document_types_by_user_group(user_group)
        groups.append(
            {
                "user_group": user_group,
                "types": sorted(types, key=lambda item: item["user_label"]),
            }
        )
    return groups


def validate_catalog_shape() -> list[str]:
    errors = []
    codes = set()
    for item in DOCUMENT_TYPES:
        missing = CATALOG_REQUIRED_KEYS - set(item)
        if missing:
            errors.append(f"{item.get('code', '<sem codigo>')}: campos ausentes {sorted(missing)}")
        code = item.get("code")
        if code in codes:
            errors.append(f"{code}: código duplicado")
        codes.add(code)
    return errors
