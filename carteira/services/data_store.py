import csv
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

from django.conf import settings

CLIENT_FIELDS = [
    "id",
    "name",
    "category",
    "company_cnpj",
    "company_cnpj_source",
    "monthly_revenue",
    "monthly_revenue_source",
    "notes",
    "created_at",
    "updated_at",
]

FUND_FIELDS = [
    "id",
    "client_id",
    "cvm_fund_id",
    "cvm_class_id",
    "fund_name",
    "cnpj",
    "pl",
    "monthly_revenue",
    "product_type",
    "annual_fee_rate",
    "manager_name",
    "administrator_name",
    "status",
    "revenue_formula",
    "revenue_source",
    "updated_at",
]

RULE_FIELDS = [
    "product_type",
    "annual_fee_rate",
    "notes",
    "updated_at",
]

CONTACT_FIELDS = [
    "id",
    "client_id",
    "name",
    "role",
    "area",
    "email",
    "phone",
    "linkedin",
    "notes",
    "updated_at",
]

COMPANY_PROFILE_FIELDS = [
    "id",
    "client_id",
    "cnpj",
    "legal_name",
    "trade_name",
    "status",
    "email",
    "phone",
    "city",
    "state",
    "main_activity",
    "partners_summary",
    "source",
    "source_url",
    "updated_at",
]

CONTACT_ROLE_LABELS = {
    "co": "CO",
    "chefe": "Chefe",
    "gerente": "Gerente",
    "outro": "Outro",
}

CATEGORY_LABELS = {
    "gestora": "Gestora",
    "consultoria": "Consultoria",
    "banco": "Banco",
    "securitizadora": "Securitizadora",
    "outros": "Outros",
}


@dataclass
class ImportSummary:
    imported_count: int
    skipped_count: int
    details: list[str]


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _clients_path() -> Path:
    return Path(settings.DATA_DIR) / "clients.csv"


def _funds_path() -> Path:
    return Path(settings.DATA_DIR) / "funds.csv"


def _rules_path() -> Path:
    return Path(settings.DATA_DIR) / "revenue_rules.csv"


def _contacts_path() -> Path:
    return Path(settings.DATA_DIR) / "contacts.csv"


def _company_profiles_path() -> Path:
    return Path(settings.DATA_DIR) / "company_profiles.csv"


def ensure_storage() -> None:
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    _ensure_csv(_clients_path(), CLIENT_FIELDS)
    _ensure_csv(_funds_path(), FUND_FIELDS)
    _ensure_csv(_rules_path(), RULE_FIELDS)
    _ensure_csv(_contacts_path(), CONTACT_FIELDS)
    _ensure_csv(_company_profiles_path(), COMPANY_PROFILE_FIELDS)


def _ensure_csv(path: Path, fieldnames: list[str]) -> None:
    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as file_handle:
            reader = csv.DictReader(file_handle)
            current_fields = reader.fieldnames or []
            rows = list(reader)
        if current_fields == fieldnames:
            return
        migrated_rows = []
        for row in rows:
            migrated_rows.append({field: row.get(field, "") for field in fieldnames})
        with path.open("w", newline="", encoding="utf-8") as file_handle:
            writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(migrated_rows)
        return
    with path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()


def load_clients() -> list[dict[str, str]]:
    ensure_storage()
    with _clients_path().open("r", newline="", encoding="utf-8") as file_handle:
        return list(csv.DictReader(file_handle))


def load_funds() -> list[dict[str, str]]:
    ensure_storage()
    with _funds_path().open("r", newline="", encoding="utf-8") as file_handle:
        return list(csv.DictReader(file_handle))


def load_rules() -> list[dict[str, str]]:
    ensure_storage()
    with _rules_path().open("r", newline="", encoding="utf-8") as file_handle:
        return list(csv.DictReader(file_handle))


def load_contacts() -> list[dict[str, str]]:
    ensure_storage()
    with _contacts_path().open("r", newline="", encoding="utf-8") as file_handle:
        return list(csv.DictReader(file_handle))


def load_company_profiles() -> list[dict[str, str]]:
    ensure_storage()
    with _company_profiles_path().open("r", newline="", encoding="utf-8") as file_handle:
        return list(csv.DictReader(file_handle))


def save_clients(rows: Iterable[dict[str, str]]) -> None:
    ensure_storage()
    with _clients_path().open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=CLIENT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def save_funds(rows: Iterable[dict[str, str]]) -> None:
    ensure_storage()
    with _funds_path().open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=FUND_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def save_rules(rows: Iterable[dict[str, str]]) -> None:
    ensure_storage()
    with _rules_path().open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=RULE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def save_contacts(rows: Iterable[dict[str, str]]) -> None:
    ensure_storage()
    with _contacts_path().open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=CONTACT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def save_company_profiles(rows: Iterable[dict[str, str]]) -> None:
    ensure_storage()
    with _company_profiles_path().open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=COMPANY_PROFILE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def add_client(payload: dict[str, str]) -> dict[str, str]:
    clients = load_clients()
    now = _now_iso()
    row = {
        "id": uuid.uuid4().hex,
        "name": payload["name"].strip(),
        "category": payload["category"],
        "company_cnpj": _as_clean_string(payload.get("company_cnpj")),
        "company_cnpj_source": _as_clean_string(payload.get("company_cnpj_source")),
        "monthly_revenue": payload.get("monthly_revenue", "").strip(),
        "monthly_revenue_source": payload.get("monthly_revenue_source", "").strip(),
        "notes": payload.get("notes", "").strip(),
        "created_at": now,
        "updated_at": now,
    }
    clients.append(row)
    save_clients(clients)
    return row


def get_client_by_name(name: str) -> dict[str, str] | None:
    normalized_name = name.strip().lower()
    if not normalized_name:
        return None
    return next(
        (client for client in load_clients() if client["name"].strip().lower() == normalized_name),
        None,
    )


def update_client_revenue(client_id: str, monthly_revenue: Decimal, source: str) -> None:
    clients = load_clients()
    for client in clients:
        if client["id"] != client_id:
            continue
        client["monthly_revenue"] = str(monthly_revenue.quantize(Decimal("0.01")))
        client["monthly_revenue_source"] = source
        client["updated_at"] = _now_iso()
        break
    save_clients(clients)


def update_client_company_identity(client_id: str, company_cnpj: str, company_cnpj_source: str = "") -> None:
    clients = load_clients()
    for client in clients:
        if client["id"] != client_id:
            continue
        client["company_cnpj"] = _as_clean_string(company_cnpj)
        client["company_cnpj_source"] = _as_clean_string(company_cnpj_source)
        client["updated_at"] = _now_iso()
        break
    save_clients(clients)


def delete_client(client_id: str) -> None:
    clients = [client for client in load_clients() if client["id"] != client_id]
    funds = [fund for fund in load_funds() if fund["client_id"] != client_id]
    contacts = [contact for contact in load_contacts() if contact["client_id"] != client_id]
    profiles = [profile for profile in load_company_profiles() if profile["client_id"] != client_id]
    save_clients(clients)
    save_funds(funds)
    save_contacts(contacts)
    save_company_profiles(profiles)


def group_clients_by_category() -> list[dict[str, object]]:
    grouped = {key: [] for key in CATEGORY_LABELS}
    for client in load_clients():
        grouped.setdefault(client["category"], []).append(client)

    groups = []
    for key, label in CATEGORY_LABELS.items():
        clients = sorted(grouped.get(key, []), key=lambda item: item["name"].lower())
        groups.append(
            {
                "key": key,
                "label": label,
                "count": len(clients),
                "monthly_revenue_total": format_currency(
                    sum(
                        (parse_decimal(item["monthly_revenue"]) for item in clients),
                        start=Decimal("0"),
                    )
                ),
                "clients": clients,
            }
        )
    return groups


def build_dashboard_metrics() -> dict[str, object]:
    clients = load_clients()
    funds = load_funds()
    total_revenue = sum(
        (parse_decimal(item["monthly_revenue"]) for item in clients),
        start=Decimal("0"),
    )
    return {
        "total_clients": len(clients),
        "total_funds": len(funds),
        "total_revenue": format_currency(total_revenue),
    }


def get_client(client_id: str) -> dict[str, object] | None:
    clients = load_clients()
    funds = load_funds()
    contacts = load_contacts()
    profiles = load_company_profiles()
    client = next((item for item in clients if item["id"] == client_id), None)
    if not client:
        return None
    client_funds = [item for item in funds if item["client_id"] == client_id]
    client_contacts = [item for item in contacts if item["client_id"] == client_id]
    client_profiles = [item for item in profiles if item["client_id"] == client_id]
    return {
        **client,
        "category_label": CATEGORY_LABELS.get(client["category"], client["category"]),
        "formatted_company_cnpj": format_cnpj(client.get("company_cnpj", "")),
        "formatted_revenue": format_currency(parse_decimal(client["monthly_revenue"])),
        "funds": [
            {
                **fund,
                "formatted_pl": format_currency(parse_decimal(fund["pl"])) if fund.get("pl") else "-",
                "formatted_revenue": format_currency(parse_decimal(fund["monthly_revenue"])),
                "formatted_fee_rate": format_percentage(parse_decimal(fund.get("annual_fee_rate", "")))
                if fund.get("annual_fee_rate", "").strip()
                else "-",
            }
            for fund in client_funds
        ],
        "contacts": [
            {
                **contact,
                "role_label": CONTACT_ROLE_LABELS.get(contact["role"], contact["role"]),
            }
            for contact in client_contacts
        ],
        "company_profiles": client_profiles,
    }


def add_contact(payload: dict[str, str]) -> dict[str, str]:
    contacts = load_contacts()
    row = {
        "id": uuid.uuid4().hex,
        "client_id": payload["client_id"].strip(),
        "name": payload["name"].strip(),
        "role": payload.get("role", "outro").strip(),
        "area": payload.get("area", "").strip(),
        "email": payload.get("email", "").strip(),
        "phone": payload.get("phone", "").strip(),
        "linkedin": payload.get("linkedin", "").strip(),
        "notes": payload.get("notes", "").strip(),
        "updated_at": _now_iso(),
    }
    contacts.append(row)
    save_contacts(contacts)
    return row


def upsert_company_profile(payload: dict[str, str]) -> dict[str, str]:
    profiles = load_company_profiles()
    now = _now_iso()
    existing = next(
        (
            item for item in profiles
            if item["client_id"] == payload["client_id"].strip()
            and item["cnpj"] == payload["cnpj"].strip()
        ),
        None,
    )
    if existing:
        existing.update(
            {
                "legal_name": _as_clean_string(payload.get("legal_name")),
                "trade_name": _as_clean_string(payload.get("trade_name")),
                "status": _as_clean_string(payload.get("status")),
                "email": _as_clean_string(payload.get("email")),
                "phone": _as_clean_string(payload.get("phone")),
                "city": _as_clean_string(payload.get("city")),
                "state": _as_clean_string(payload.get("state")),
                "main_activity": _as_clean_string(payload.get("main_activity")),
                "partners_summary": _as_clean_string(payload.get("partners_summary")),
                "source": _as_clean_string(payload.get("source")),
                "source_url": _as_clean_string(payload.get("source_url")),
                "updated_at": now,
            }
        )
        save_company_profiles(profiles)
        return existing

    row = {
        "id": uuid.uuid4().hex,
        "client_id": _as_clean_string(payload.get("client_id")),
        "cnpj": _as_clean_string(payload.get("cnpj")),
        "legal_name": _as_clean_string(payload.get("legal_name")),
        "trade_name": _as_clean_string(payload.get("trade_name")),
        "status": _as_clean_string(payload.get("status")),
        "email": _as_clean_string(payload.get("email")),
        "phone": _as_clean_string(payload.get("phone")),
        "city": _as_clean_string(payload.get("city")),
        "state": _as_clean_string(payload.get("state")),
        "main_activity": _as_clean_string(payload.get("main_activity")),
        "partners_summary": _as_clean_string(payload.get("partners_summary")),
        "source": _as_clean_string(payload.get("source")),
        "source_url": _as_clean_string(payload.get("source_url")),
        "updated_at": now,
    }
    profiles.append(row)
    save_company_profiles(profiles)
    return row


def add_fund(payload: dict[str, str]) -> dict[str, str]:
    funds = load_funds()
    rule = get_rule_for_product_type(payload.get("product_type", ""))
    annual_fee_rate = payload.get("annual_fee_rate", "").strip() or (rule.get("annual_fee_rate", "") if rule else "")
    monthly_revenue = payload.get("monthly_revenue", "").strip()
    revenue_formula = payload.get("revenue_formula", "").strip()
    revenue_source = payload.get("revenue_source", "").strip()
    if annual_fee_rate:
        monthly_revenue = format_decimal_value(calculate_monthly_revenue(payload.get("pl", ""), annual_fee_rate))
        revenue_formula = "PL x taxa anual / 12"
        revenue_source = f"Calculado por regra do tipo {payload.get('product_type', '').strip() or 'sem tipo'}"

    existing = next(
        (
            item
            for item in funds
            if item["client_id"] == payload["client_id"] and item["cnpj"] == payload["cnpj"]
        ),
        None,
    )
    now = _now_iso()

    if existing:
        existing.update(
            {
                "cvm_fund_id": payload.get("cvm_fund_id", existing.get("cvm_fund_id", "")).strip(),
                "cvm_class_id": payload.get("cvm_class_id", existing.get("cvm_class_id", "")).strip(),
                "fund_name": payload["fund_name"].strip(),
                "cnpj": payload["cnpj"].strip(),
                "pl": payload.get("pl", "").strip(),
                "monthly_revenue": monthly_revenue or existing.get("monthly_revenue", ""),
                "product_type": payload.get("product_type", "").strip(),
                "annual_fee_rate": annual_fee_rate,
                "manager_name": payload.get("manager_name", "").strip(),
                "administrator_name": payload.get("administrator_name", "").strip(),
                "status": payload.get("status", "").strip(),
                "revenue_formula": revenue_formula or existing.get("revenue_formula", ""),
                "revenue_source": revenue_source or existing.get("revenue_source", ""),
                "updated_at": now,
            }
        )
        save_funds(funds)
        refresh_client_revenue(existing["client_id"])
        return existing

    row = {
        "id": uuid.uuid4().hex,
        "client_id": payload["client_id"].strip(),
        "cvm_fund_id": payload.get("cvm_fund_id", "").strip(),
        "cvm_class_id": payload.get("cvm_class_id", "").strip(),
        "fund_name": payload["fund_name"].strip(),
        "cnpj": payload["cnpj"].strip(),
        "pl": payload.get("pl", "").strip(),
        "monthly_revenue": monthly_revenue,
        "product_type": payload.get("product_type", "").strip(),
        "annual_fee_rate": annual_fee_rate,
        "manager_name": payload.get("manager_name", "").strip(),
        "administrator_name": payload.get("administrator_name", "").strip(),
        "status": payload.get("status", "").strip(),
        "revenue_formula": revenue_formula,
        "revenue_source": revenue_source,
        "updated_at": now,
    }
    funds.append(row)
    save_funds(funds)
    refresh_client_revenue(row["client_id"])
    return row


def upsert_rule(product_type: str, annual_fee_rate: str, notes: str = "") -> dict[str, str]:
    rules = load_rules()
    normalized_type = product_type.strip()
    now = _now_iso()
    existing = next((rule for rule in rules if rule["product_type"].strip().lower() == normalized_type.lower()), None)
    if existing:
        existing["product_type"] = normalized_type
        existing["annual_fee_rate"] = annual_fee_rate.strip()
        existing["notes"] = notes.strip()
        existing["updated_at"] = now
    else:
        existing = {
            "product_type": normalized_type,
            "annual_fee_rate": annual_fee_rate.strip(),
            "notes": notes.strip(),
            "updated_at": now,
        }
        rules.append(existing)
    save_rules(rules)
    recalculate_funds_for_product_type(normalized_type)
    return existing


def get_rule_for_product_type(product_type: str) -> dict[str, str] | None:
    normalized_type = product_type.strip().lower()
    if not normalized_type:
        return None
    return next((rule for rule in load_rules() if rule["product_type"].strip().lower() == normalized_type), None)


def list_rules() -> list[dict[str, str]]:
    return sorted(load_rules(), key=lambda item: item["product_type"].lower())


def list_known_product_types() -> list[str]:
    product_types = {
        fund["product_type"].strip()
        for fund in load_funds()
        if fund.get("product_type", "").strip()
    }
    for rule in load_rules():
        if rule["product_type"].strip():
            product_types.add(rule["product_type"].strip())
    return sorted(product_types)


def recalculate_funds_for_product_type(product_type: str) -> None:
    rule = get_rule_for_product_type(product_type)
    if not rule:
        return
    funds = load_funds()
    impacted_clients: set[str] = set()
    for fund in funds:
        if fund.get("product_type", "").strip().lower() != product_type.strip().lower():
            continue
        fund["annual_fee_rate"] = rule["annual_fee_rate"]
        fund["monthly_revenue"] = format_decimal_value(calculate_monthly_revenue(fund.get("pl", ""), rule["annual_fee_rate"]))
        fund["revenue_formula"] = "PL x taxa anual / 12"
        fund["revenue_source"] = f"Calculado por regra do tipo {rule['product_type']}"
        fund["updated_at"] = _now_iso()
        impacted_clients.add(fund["client_id"])
    save_funds(funds)
    for client_id in impacted_clients:
        refresh_client_revenue(client_id)


def update_fund_fee_rate(fund_id: str, annual_fee_rate: str) -> None:
    funds = load_funds()
    target_client_id = ""
    for fund in funds:
        if fund["id"] != fund_id:
            continue
        fund["annual_fee_rate"] = annual_fee_rate.strip()
        fund["monthly_revenue"] = format_decimal_value(calculate_monthly_revenue(fund.get("pl", ""), annual_fee_rate))
        fund["revenue_formula"] = "PL x taxa anual / 12"
        fund["revenue_source"] = "Calculado manualmente no fundo"
        fund["updated_at"] = _now_iso()
        target_client_id = fund["client_id"]
        break
    save_funds(funds)
    if target_client_id:
        refresh_client_revenue(target_client_id)


def refresh_client_revenue(client_id: str) -> None:
    funds = load_funds()
    client_funds = [fund for fund in funds if fund["client_id"] == client_id]
    if not client_funds:
        return
    total = sum(
        (parse_decimal(fund.get("monthly_revenue", "")) for fund in client_funds),
        start=Decimal("0"),
    )
    source = "Soma das receitas calculadas dos fundos"
    update_client_revenue(client_id, total, source)


def calculate_monthly_revenue(pl: str | Decimal | None, annual_fee_rate_percent: str | Decimal | None) -> Decimal:
    patrimony = parse_decimal(pl)
    annual_rate = parse_decimal(annual_fee_rate_percent) / Decimal("100")
    if patrimony <= 0 or annual_rate <= 0:
        return Decimal("0")
    return (patrimony * annual_rate) / Decimal("12")


def parse_decimal(value: str | Decimal | None) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    sanitized = str(value).replace("R$", "").replace("%", "").strip()
    if "," in sanitized and "." in sanitized:
        sanitized = sanitized.replace(".", "").replace(",", ".")
    elif "," in sanitized:
        sanitized = sanitized.replace(".", "").replace(",", ".")
    try:
        return Decimal(sanitized)
    except InvalidOperation:
        return Decimal("0")


def format_decimal_value(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01")))


def format_currency(value: Decimal) -> str:
    quantized = value.quantize(Decimal("0.01"))
    formatted = f"{quantized:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def format_percentage(value: Decimal) -> str:
    quantized = value.quantize(Decimal("0.0001"))
    formatted = f"{quantized:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted}%"


def _as_clean_string(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def format_cnpj(value: str) -> str:
    digits = "".join(char for char in str(value) if char.isdigit())
    if len(digits) != 14:
        return str(value or "").strip()
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
