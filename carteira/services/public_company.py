import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


def enrich_company_profiles_for_client(client: dict[str, object]) -> list[dict[str, str]]:
    company_cnpj = _digits_only(str(client.get("company_cnpj", "")))
    profiles: list[dict[str, str]] = []
    if len(company_cnpj) != 14:
        return profiles

    profile = fetch_company_profile(company_cnpj)
    if not profile:
        return profiles

    profiles.append(
        {
            "client_id": str(client["id"]),
            "cnpj": _format_cnpj(company_cnpj),
            "legal_name": profile.get("razao_social", ""),
            "trade_name": profile.get("nome_fantasia", ""),
            "status": profile.get("descricao_situacao_cadastral", ""),
            "email": profile.get("email", ""),
            "phone": _format_phone(profile.get("ddd_telefone_1", ""), profile.get("ddd_telefone_2", "")),
            "city": profile.get("municipio", ""),
            "state": profile.get("uf", ""),
            "main_activity": _extract_main_activity(profile),
            "partners_summary": _extract_partners(profile),
            "source": "BrasilAPI CNPJ",
            "source_url": settings.PUBLIC_COMPANY_ENRICHMENT_URL.format(cnpj=company_cnpj),
        }
    )
    return profiles


def fetch_company_profile(cnpj: str) -> dict[str, object] | None:
    url = settings.PUBLIC_COMPANY_ENRICHMENT_URL.format(cnpj=cnpj)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None


def _extract_main_activity(profile: dict[str, object]) -> str:
    activity = profile.get("cnae_fiscal_descricao") or ""
    code = str(profile.get("cnae_fiscal", "") or "").strip()
    if code and activity:
        return f"{code} - {activity}"
    return activity or code


def _extract_partners(profile: dict[str, object]) -> str:
    qsa = profile.get("qsa") or []
    snippets = []
    for partner in qsa[:5]:
        name = str(partner.get("nome_socio") or "").strip()
        role = str(partner.get("qualificacao_socio") or "").strip()
        if name and role:
            snippets.append(f"{name} ({role})")
        elif name:
            snippets.append(name)
    return "; ".join(snippets)


def _digits_only(value: str) -> str:
    return "".join(char for char in str(value) if char.isdigit())


def _format_cnpj(value: str) -> str:
    digits = _digits_only(value)
    if len(digits) != 14:
        return value
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def _format_phone(phone_1: str, phone_2: str) -> str:
    numbers = [str(item).strip() for item in [phone_1, phone_2] if str(item).strip()]
    return " / ".join(numbers)
