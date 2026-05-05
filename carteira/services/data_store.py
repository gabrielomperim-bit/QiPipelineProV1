import csv
import re
import unicodedata
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
    "is_user_client",
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
    "fund_type_raw",
    "annual_fee_rate",
    "manager_name",
    "administrator_name",
    "status",
    "is_user_fund",
    "regulation_url",
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

USER_DASHBOARD_COLORS = [
    "#2d7ff9",
    "#0d2b66",
    "#4c9aff",
    "#7aa8ff",
    "#14b8a6",
    "#06b6d4",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#10b981",
]


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


def reset_storage(clear_cvm_cache: bool = False, clear_uploads: bool = True) -> dict[str, object]:
    ensure_storage()

    _write_empty_csv(_clients_path(), CLIENT_FIELDS)
    _write_empty_csv(_funds_path(), FUND_FIELDS)
    _write_empty_csv(_rules_path(), RULE_FIELDS)
    _write_empty_csv(_contacts_path(), CONTACT_FIELDS)
    _write_empty_csv(_company_profiles_path(), COMPANY_PROFILE_FIELDS)

    removed_uploads = 0
    if clear_uploads:
        upload_dir = Path(settings.UPLOAD_DIR)
        for path in upload_dir.iterdir():
            if path.is_file():
                path.unlink()
                removed_uploads += 1

    removed_cvm_files = 0
    if clear_cvm_cache:
        cvm_dir = Path(settings.CVM_CACHE_DIR)
        if cvm_dir.exists():
            for path in cvm_dir.iterdir():
                if path.is_file():
                    path.unlink()
                    removed_cvm_files += 1

    return {
        "cleared_files": [
            str(_clients_path().name),
            str(_funds_path().name),
            str(_rules_path().name),
            str(_contacts_path().name),
            str(_company_profiles_path().name),
        ],
        "removed_uploads": removed_uploads,
        "removed_cvm_files": removed_cvm_files,
        "clear_cvm_cache": clear_cvm_cache,
    }


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
            migrated_rows.append(
                {
                    field: _default_field_value(field, row.get(field, ""))
                    for field in fieldnames
                }
            )
        with path.open("w", newline="", encoding="utf-8") as file_handle:
            writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(migrated_rows)
        return
    with path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()


def _write_empty_csv(path: Path, fieldnames: list[str]) -> None:
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


def refresh_linked_funds_from_catalog(catalog_rows: list[dict[str, str]]) -> None:
    funds = load_funds()
    index_by_class_id = {row.get("cvm_class_id", ""): row for row in catalog_rows if row.get("cvm_class_id", "")}
    index_by_cnpj = {row.get("cnpj", ""): row for row in catalog_rows if row.get("cnpj", "")}
    changed = False

    for fund in funds:
        catalog_row = index_by_class_id.get(fund.get("cvm_class_id", "")) or index_by_cnpj.get(fund.get("cnpj", ""))
        if not catalog_row:
            continue
        fund["product_type"] = normalize_fund_type(catalog_row.get("product_type", fund.get("product_type", "")))
        fund["fund_type_raw"] = _as_clean_string(catalog_row.get("product_type", fund.get("fund_type_raw", "")))
        fund["manager_name"] = _as_clean_string(catalog_row.get("manager_name", fund.get("manager_name", "")))
        fund["administrator_name"] = _as_clean_string(catalog_row.get("administrator_name", fund.get("administrator_name", "")))
        fund["status"] = _as_clean_string(catalog_row.get("status", fund.get("status", "")))
        fund["regulation_url"] = _regulation_url_or_default(catalog_row.get("regulation_url", fund.get("regulation_url", "")))
        changed = True

    if changed:
        save_funds(funds)


def add_client(payload: dict[str, str]) -> dict[str, str]:
    clients = load_clients()
    now = _now_iso()
    row = {
        "id": uuid.uuid4().hex,
        "name": payload["name"].strip(),
        "category": payload["category"],
        "is_user_client": _default_field_value("is_user_client", payload.get("is_user_client", "0")),
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


def update_client_category(client_id: str, category: str) -> None:
    normalized_category = _as_clean_string(category).lower()
    if normalized_category not in CATEGORY_LABELS:
        return
    clients = load_clients()
    for client in clients:
        if client["id"] != client_id:
            continue
        client["category"] = normalized_category
        client["updated_at"] = _now_iso()
        break
    save_clients(clients)


def set_client_user_status(client_id: str, is_user_client: bool) -> None:
    clients = load_clients()
    for client in clients:
        if client["id"] != client_id:
            continue
        client["is_user_client"] = "1" if is_user_client else "0"
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


def delete_rule(product_type: str) -> None:
    normalized_type = normalize_fund_type(product_type)
    rules = [rule for rule in load_rules() if normalize_fund_type(rule["product_type"]) != normalized_type]
    save_rules(rules)


def set_fund_user_status(fund_id: str, is_user_fund: bool) -> None:
    funds = load_funds()
    target_client_id = ""
    for fund in funds:
        if fund["id"] != fund_id:
            continue
        fund["is_user_fund"] = "1" if is_user_fund else "0"
        fund["updated_at"] = _now_iso()
        target_client_id = fund["client_id"]
        break
    save_funds(funds)
    if target_client_id:
        refresh_client_revenue(target_client_id)


def list_client_choices() -> list[tuple[str, str]]:
    return [(client["id"], client["name"]) for client in sorted(load_clients(), key=lambda item: item["name"].lower())]


def list_category_choices() -> list[tuple[str, str]]:
    return list(CATEGORY_LABELS.items())


def list_clients_overview(search_term: str = "") -> list[dict[str, str]]:
    clients = load_clients()
    funds = load_funds()
    fund_count_by_client: dict[str, int] = {}
    for fund in funds:
        client_id = fund.get("client_id", "")
        if not client_id:
            continue
        fund_count_by_client[client_id] = fund_count_by_client.get(client_id, 0) + 1

    query = _normalize_search_text(search_term)
    results = []
    for client in clients:
        row = {
            **client,
            "category_label": CATEGORY_LABELS.get(client.get("category", ""), client.get("category", "")),
            "formatted_company_cnpj": format_cnpj(client.get("company_cnpj", "")),
            "formatted_revenue": format_currency(parse_decimal(client.get("monthly_revenue", ""))),
            "fund_count": fund_count_by_client.get(client.get("id", ""), 0),
            "is_user_client_bool": _is_truthy(client.get("is_user_client", "0")),
        }
        haystack = _normalize_search_text(
            " ".join(
                [
                    row.get("name", ""),
                    row.get("category_label", ""),
                    row.get("company_cnpj", ""),
                    row.get("formatted_company_cnpj", ""),
                ]
            )
        )
        if query and query not in haystack:
            continue
        results.append(row)
    return sorted(results, key=lambda item: item.get("name", "").lower())


def list_all_linked_funds(search_term: str = "") -> list[dict[str, str]]:
    clients_by_id = {client["id"]: client for client in load_clients()}
    catalog_by_class_id, catalog_by_cnpj = _load_cvm_catalog_indexes()
    query = _normalize_search_text(search_term)
    results = []
    for fund in load_funds():
        catalog_row = _catalog_match_for_fund(fund, catalog_by_class_id, catalog_by_cnpj)
        client_name = clients_by_id.get(fund["client_id"], {}).get("name", "")
        client_name = client_name or "Cliente nao identificado"
        row = {
            **fund,
            "client_name": client_name,
            "has_client": fund["client_id"] in clients_by_id,
            "product_type": normalize_fund_type(fund.get("product_type", "")),
            "formatted_pl": format_currency(parse_decimal(fund["pl"])) if fund.get("pl") else "-",
            "formatted_revenue": format_currency(parse_decimal(fund["monthly_revenue"])),
            "is_user_fund_bool": _is_truthy(fund.get("is_user_fund", "0")),
            "regulation_url": _regulation_url_or_default(fund.get("regulation_url", "")),
            "manager_name": _as_clean_string(fund.get("manager_name")) or (_as_clean_string(catalog_row.get("manager_name")) if catalog_row else ""),
            "administrator_name": _as_clean_string(fund.get("administrator_name")) or (_as_clean_string(catalog_row.get("administrator_name")) if catalog_row else ""),
        }
        haystack = _normalize_search_text(
            " ".join(
                [
                    row.get("fund_name", ""),
                    row.get("client_name", ""),
                    row.get("cnpj", ""),
                    format_cnpj(row.get("cnpj", "")),
                    row.get("product_type", ""),
                ]
            )
        )
        if query and query not in haystack:
            continue
        results.append(row)
    return sorted(results, key=lambda item: (item["client_name"].lower(), item["fund_name"].lower()))


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


def build_user_dashboard(filters: dict[str, str] | None = None) -> dict[str, object]:
    selected_filters = filters or {}
    selected_fund_type = normalize_fund_type(selected_filters.get("fund_type", ""))
    selected_manager = _as_clean_string(selected_filters.get("manager_name"))
    selected_administrator = _as_clean_string(selected_filters.get("administrator_name"))
    selected_category = _as_clean_string(selected_filters.get("category")).lower()

    clients_by_id = {client["id"]: client for client in load_clients()}
    catalog_by_class_id, catalog_by_cnpj = _load_cvm_catalog_indexes()

    all_user_funds: list[dict[str, object]] = []
    for fund in load_funds():
        if not _is_truthy(fund.get("is_user_fund", "0")):
            continue
        catalog_row = _catalog_match_for_fund(fund, catalog_by_class_id, catalog_by_cnpj)
        client = clients_by_id.get(fund.get("client_id", ""), {})
        client_category = _as_clean_string(client.get("category")).lower()
        product_type = normalize_fund_type(fund.get("product_type", "")) or (
            normalize_fund_type(catalog_row.get("product_type", "")) if catalog_row else ""
        )
        manager_name = _as_clean_string(fund.get("manager_name")) or (
            _as_clean_string(catalog_row.get("manager_name")) if catalog_row else ""
        )
        administrator_name = _as_clean_string(fund.get("administrator_name")) or (
            _as_clean_string(catalog_row.get("administrator_name")) if catalog_row else ""
        )
        pl_value = parse_decimal(fund.get("pl", ""))
        revenue_value = parse_decimal(fund.get("monthly_revenue", ""))
        all_user_funds.append(
            {
                "id": fund.get("id", ""),
                "client_id": fund.get("client_id", ""),
                "client_name": _as_clean_string(client.get("name")) or "Cliente nao identificado",
                "client_category": client_category,
                "client_category_label": CATEGORY_LABELS.get(client_category, client_category or "Sem categoria"),
                "fund_name": _as_clean_string(fund.get("fund_name")),
                "cnpj": format_cnpj(fund.get("cnpj", "")),
                "product_type": product_type or "Sem tipo",
                "manager_name": manager_name or "Sem consultoria",
                "administrator_name": administrator_name or "Sem administrador",
                "pl_value": pl_value,
                "revenue_value": revenue_value,
                "formatted_pl": format_currency(pl_value),
                "formatted_revenue": format_currency(revenue_value),
                "regulation_url": _regulation_url_or_default(fund.get("regulation_url", "")),
            }
        )

    filtered_funds = []
    for fund in all_user_funds:
        if selected_fund_type and fund["product_type"] != selected_fund_type:
            continue
        if selected_manager and fund["manager_name"] != selected_manager:
            continue
        if selected_administrator and fund["administrator_name"] != selected_administrator:
            continue
        if selected_category and fund["client_category"] != selected_category:
            continue
        filtered_funds.append(fund)

    total_pl = sum((item["pl_value"] for item in filtered_funds), start=Decimal("0"))
    total_revenue = sum((item["revenue_value"] for item in filtered_funds), start=Decimal("0"))
    unique_clients = {item["client_id"]: item["client_name"] for item in filtered_funds if item["client_id"]}
    average_pl = (total_pl / Decimal(str(len(filtered_funds)))).quantize(Decimal("0.01")) if filtered_funds else Decimal("0")

    product_type_options = sorted({str(item["product_type"]) for item in all_user_funds if str(item["product_type"]).strip()})
    manager_options = sorted({str(item["manager_name"]) for item in all_user_funds if str(item["manager_name"]).strip()})
    administrator_options = sorted(
        {str(item["administrator_name"]) for item in all_user_funds if str(item["administrator_name"]).strip()}
    )
    category_options = [
        (value, label)
        for value, label in CATEGORY_LABELS.items()
        if any(item["client_category"] == value for item in all_user_funds)
    ]

    return {
        "metrics": {
            "total_user_funds": len(filtered_funds),
            "total_user_clients": len(unique_clients),
            "total_user_pl": format_currency(total_pl),
            "total_user_revenue": format_currency(total_revenue),
            "average_user_pl": format_currency(average_pl),
        },
        "filters": {
            "fund_type": selected_fund_type,
            "manager_name": selected_manager,
            "administrator_name": selected_administrator,
            "category": selected_category,
            "fund_type_options": product_type_options,
            "manager_options": manager_options,
            "administrator_options": administrator_options,
            "category_options": category_options,
        },
        "charts": {
            "product_types": _build_donut_chart(
                filtered_funds,
                key="product_type",
                title="Distribuicao por tipo de fundo",
                total_label=format_currency(total_pl),
            ),
            "categories": _build_donut_chart(
                filtered_funds,
                key="client_category_label",
                title="Distribuicao por categoria de cliente",
                total_label=format_currency(total_pl),
            ),
            "clients": _build_bar_chart(filtered_funds, key="client_name", title="Top clientes por PL"),
            "managers": _build_bar_chart(filtered_funds, key="manager_name", title="Top consultorias por PL"),
            "administrators": _build_bar_chart(filtered_funds, key="administrator_name", title="Top administradores por PL"),
        },
        "top_funds": sorted(filtered_funds, key=lambda item: (item["pl_value"], item["fund_name"]), reverse=True)[:12],
        "has_user_funds": bool(all_user_funds),
        "has_filtered_funds": bool(filtered_funds),
    }


def get_client(client_id: str) -> dict[str, object] | None:
    clients = load_clients()
    funds = load_funds()
    contacts = load_contacts()
    profiles = load_company_profiles()
    catalog_by_class_id, catalog_by_cnpj = _load_cvm_catalog_indexes()
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
        "user_fund_count": len([fund for fund in client_funds if _is_truthy(fund.get("is_user_fund", "0"))]),
        "funds": [
            (
                lambda catalog_row: {
                **fund,
                "product_type": normalize_fund_type(fund.get("product_type", "")),
                "formatted_pl": format_currency(parse_decimal(fund["pl"])) if fund.get("pl") else "-",
                "formatted_revenue": format_currency(parse_decimal(fund["monthly_revenue"])),
                "formatted_fee_rate": format_percentage(parse_decimal(fund.get("annual_fee_rate", "")))
                if fund.get("annual_fee_rate", "").strip()
                else "-",
                "is_user_fund_bool": _is_truthy(fund.get("is_user_fund", "0")),
                "regulation_url": _regulation_url_or_default(fund.get("regulation_url", "")),
                "manager_name": _as_clean_string(fund.get("manager_name")) or (_as_clean_string(catalog_row.get("manager_name")) if catalog_row else ""),
                "administrator_name": _as_clean_string(fund.get("administrator_name")) or (_as_clean_string(catalog_row.get("administrator_name")) if catalog_row else ""),
            }
            )(_catalog_match_for_fund(fund, catalog_by_class_id, catalog_by_cnpj))
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
    normalized_fund_type = normalize_fund_type(payload.get("product_type", ""))
    rule = get_rule_for_product_type(normalized_fund_type)
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
                "product_type": normalized_fund_type,
                "fund_type_raw": _as_clean_string(payload.get("product_type")),
                "annual_fee_rate": annual_fee_rate,
                "manager_name": payload.get("manager_name", "").strip(),
                "administrator_name": payload.get("administrator_name", "").strip(),
                "status": payload.get("status", "").strip(),
                "is_user_fund": _default_field_value("is_user_fund", payload.get("is_user_fund", existing.get("is_user_fund", "0"))),
                "regulation_url": _regulation_url_or_default(payload.get("regulation_url", existing.get("regulation_url", ""))),
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
        "product_type": normalized_fund_type,
        "fund_type_raw": _as_clean_string(payload.get("product_type")),
        "annual_fee_rate": annual_fee_rate,
        "manager_name": payload.get("manager_name", "").strip(),
        "administrator_name": payload.get("administrator_name", "").strip(),
        "status": payload.get("status", "").strip(),
        "is_user_fund": _default_field_value("is_user_fund", payload.get("is_user_fund", "0")),
        "regulation_url": _regulation_url_or_default(payload.get("regulation_url")),
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
    normalized_type = normalize_fund_type(product_type)
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
    normalized_type = normalize_fund_type(product_type).lower()
    if not normalized_type:
        return None
    return next((rule for rule in load_rules() if rule["product_type"].strip().lower() == normalized_type), None)


def list_rules() -> list[dict[str, str]]:
    return sorted(load_rules(), key=lambda item: item["product_type"].lower())


def list_known_product_types() -> list[str]:
    product_types = {
        normalize_fund_type(fund["product_type"])
        for fund in load_funds()
        if fund.get("product_type", "").strip()
    }
    for rule in load_rules():
        if rule["product_type"].strip():
            product_types.add(normalize_fund_type(rule["product_type"]))
    return sorted(product_types)


def recalculate_funds_for_product_type(product_type: str) -> None:
    normalized_type = normalize_fund_type(product_type)
    rule = get_rule_for_product_type(normalized_type)
    if not rule:
        return
    funds = load_funds()
    impacted_clients: set[str] = set()
    for fund in funds:
        if normalize_fund_type(fund.get("product_type", "")).lower() != normalized_type.lower():
            continue
        fund["product_type"] = normalized_type
        fund["annual_fee_rate"] = rule["annual_fee_rate"]
        fund["monthly_revenue"] = format_decimal_value(calculate_monthly_revenue(fund.get("pl", ""), rule["annual_fee_rate"]))
        fund["revenue_formula"] = "PL x taxa anual / 12"
        fund["revenue_source"] = f"Calculado por regra do tipo {normalized_type}"
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
        update_client_revenue(client_id, Decimal("0"), "Nenhum fundo vinculado")
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
    digits = _digits_only(value)
    if len(digits) != 14:
        return str(value or "").strip()
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def normalize_fund_type(value: str) -> str:
    normalized = _as_clean_string(value)
    if not normalized:
        return ""
    match = re.search(r"\b(FII|FIDC|FIP|FIA|FIF|ETF|FIM|FIC|FIRF|FICFIM|FICFIA)\b$", normalized.upper())
    if match:
        return match.group(1)
    tokens = re.findall(r"[A-Z]{2,}", normalized.upper())
    return tokens[-1] if tokens else normalized.upper()


def _default_field_value(field: str, value: object) -> str:
    if field in {"is_user_fund", "is_user_client"}:
        cleaned = _as_clean_string(value)
        return cleaned if cleaned else "0"
    return _as_clean_string(value)


def _is_truthy(value: object) -> bool:
    return _as_clean_string(value).lower() in {"1", "true", "sim", "yes", "y", "on"}


def _regulation_url_or_default(value: object) -> str:
    cleaned = _as_clean_string(value)
    if cleaned:
        return cleaned
    return "https://cvmweb.cvm.gov.br/SWB/default.asp?sg_sistema=fundosreg"


def _load_cvm_catalog_indexes() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    catalog_path = Path(settings.CVM_CACHE_DIR) / "catalog.csv"
    if not catalog_path.exists():
        return {}, {}
    with catalog_path.open("r", newline="", encoding="utf-8") as file_handle:
        rows = list(csv.DictReader(file_handle, delimiter=";"))
    by_class_id = {row.get("cvm_class_id", ""): row for row in rows if row.get("cvm_class_id", "")}
    by_cnpj = {_digits_only(row.get("cnpj", "")): row for row in rows if row.get("cnpj", "")}
    return by_class_id, by_cnpj


def _catalog_match_for_fund(
    fund: dict[str, str],
    catalog_by_class_id: dict[str, dict[str, str]],
    catalog_by_cnpj: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    return (
        catalog_by_class_id.get(_as_clean_string(fund.get("cvm_class_id")))
        or catalog_by_cnpj.get(_digits_only(fund.get("cnpj", "")))
    )


def _normalize_search_text(value: object) -> str:
    cleaned = _as_clean_string(value).lower()
    if not cleaned:
        return ""
    normalized = unicodedata.normalize("NFKD", cleaned)
    ascii_only = "".join(char for char in normalized if not unicodedata.combining(char))
    collapsed = re.sub(r"\s+", " ", ascii_only)
    return collapsed.strip()


def _aggregate_chart_rows(funds: list[dict[str, object]], key: str) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    for fund in funds:
        label = _as_clean_string(fund.get(key)) or "Nao informado"
        current = grouped.setdefault(
            label,
            {
                "label": label,
                "value": Decimal("0"),
                "count": 0,
            },
        )
        current["value"] = Decimal(current["value"]) + Decimal(fund.get("pl_value", Decimal("0")))
        current["count"] = int(current["count"]) + 1
    return sorted(grouped.values(), key=lambda item: (Decimal(item["value"]), item["label"]), reverse=True)


def _build_donut_chart(
    funds: list[dict[str, object]],
    key: str,
    title: str,
    total_label: str,
    top_n: int = 6,
) -> dict[str, object]:
    rows = _aggregate_chart_rows(funds, key)
    visible_rows = rows[:top_n]
    if len(rows) > top_n:
        other_total = sum((Decimal(row["value"]) for row in rows[top_n:]), start=Decimal("0"))
        other_count = sum((int(row["count"]) for row in rows[top_n:]), start=0)
        visible_rows.append({"label": "Outros", "value": other_total, "count": other_count})

    total_value = sum((Decimal(row["value"]) for row in visible_rows), start=Decimal("0"))
    segments = []
    legend = []
    current_angle = Decimal("0")

    for index, row in enumerate(visible_rows):
        color = USER_DASHBOARD_COLORS[index % len(USER_DASHBOARD_COLORS)]
        value = Decimal(row["value"])
        percent = (value / total_value * Decimal("100")) if total_value > 0 else Decimal("0")
        next_angle = current_angle + percent
        segments.append(
            f"{color} {current_angle.quantize(Decimal('0.01'))}% {next_angle.quantize(Decimal('0.01'))}%"
        )
        legend.append(
            {
                "label": row["label"],
                "count": row["count"],
                "formatted_value": format_currency(value),
                "share_percent": f"{percent.quantize(Decimal('0.1'))}%",
                "color": color,
            }
        )
        current_angle = next_angle

    return {
        "title": title,
        "total_label": total_label,
        "legend": legend,
        "conic_gradient": f"conic-gradient({', '.join(segments)})" if segments else "conic-gradient(#dbe9ff 0 100%)",
        "empty": not legend,
    }


def _build_bar_chart(
    funds: list[dict[str, object]],
    key: str,
    title: str,
    top_n: int = 8,
) -> dict[str, object]:
    rows = _aggregate_chart_rows(funds, key)[:top_n]
    max_value = max((Decimal(row["value"]) for row in rows), default=Decimal("0"))
    items = []
    for index, row in enumerate(rows):
        value = Decimal(row["value"])
        width_percent = (value / max_value * Decimal("100")) if max_value > 0 else Decimal("0")
        items.append(
            {
                "label": row["label"],
                "count": row["count"],
                "formatted_value": format_currency(value),
                "width_percent": f"{width_percent.quantize(Decimal('0.1'))}%",
                "color": USER_DASHBOARD_COLORS[index % len(USER_DASHBOARD_COLORS)],
            }
        )
    return {
        "title": title,
        "items": items,
        "empty": not items,
    }


def _digits_only(value: object) -> str:
    return "".join(char for char in _as_clean_string(value) if char.isdigit())
