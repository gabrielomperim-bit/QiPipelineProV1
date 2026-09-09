import csv
import io
import json
import zipfile
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.request import urlopen

from django.conf import settings
from django.utils import timezone

from .data_store import (
    add_client,
    add_fund,
    format_cnpj,
    format_currency,
    load_clients,
    load_funds,
    get_client_by_name,
    normalize_fund_type,
    parse_decimal,
    refresh_linked_funds_from_catalog,
    update_client_company_identity,
)


CADASTRO_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip"
INF_DIARIO_URL_TEMPLATE = "https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/inf_diario_fi_{year_month}.zip"
EVENTUAL_URL_TEMPLATE = "https://dados.cvm.gov.br/dados/FI/DOC/EVENTUAL/DADOS/eventual_fi_{year}.csv"


@dataclass
class CVMSyncResult:
    downloaded_files: list[str]
    imported_at: str
    details: list[str]


def ensure_cvm_cache() -> Path:
    path = Path(settings.CVM_CACHE_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def sync_cvm_data() -> CVMSyncResult:
    cache_dir = ensure_cvm_cache()
    downloaded_files: list[str] = []
    details: list[str] = []

    cadastro_zip = _download_bytes(CADASTRO_URL)
    cadastro_archive = zipfile.ZipFile(io.BytesIO(cadastro_zip))
    for member in ["registro_fundo.csv", "registro_classe.csv"]:
        target = cache_dir / member
        with cadastro_archive.open(member) as source, target.open("wb") as destination:
            destination.write(source.read())
        downloaded_files.append(member)

    inf_member_name, inf_content = _download_latest_inf_diario()
    with (cache_dir / inf_member_name).open("wb") as destination:
        destination.write(inf_content)
    downloaded_files.append(inf_member_name)

    latest_pl = _build_latest_pl_index_from_file(cache_dir / inf_member_name)
    _write_semicolon_csv(
        cache_dir / "latest_pl.csv",
        ["cnpj", "DT_COMPTC", "VL_PATRIM_LIQ"],
        [
            {
                "cnpj": cnpj,
                "DT_COMPTC": row.get("DT_COMPTC", ""),
                "VL_PATRIM_LIQ": row.get("VL_PATRIM_LIQ", ""),
            }
            for cnpj, row in latest_pl.items()
        ],
    )
    downloaded_files.append("latest_pl.csv")

    regulation_index = _build_regulation_index(cache_dir)

    catalog_rows = _build_catalog_rows(
        _load_semicolon_csv(cache_dir / "registro_fundo.csv"),
        _load_semicolon_csv(cache_dir / "registro_classe.csv"),
        latest_pl,
        regulation_index,
    )
    _write_semicolon_csv(
        cache_dir / "catalog.csv",
        [
            "cvm_fund_id",
            "cvm_class_id",
            "fund_name",
            "cnpj",
            "raw_cnpj",
            "pl",
            "pl_date",
            "product_type",
            "status",
            "manager_name",
            "manager_document",
            "administrator_name",
            "administrator_document",
            "custodian_name",
            "custodian_document",
            "controller_name",
            "controller_document",
            "fund_legal_name",
            "regulation_url",
            "qi_relationship_role",
        ],
        catalog_rows,
    )
    downloaded_files.append("catalog.csv")
    refresh_linked_funds_from_catalog(catalog_rows)

    metadata = {
        "imported_at": timezone.now().isoformat(timespec="seconds"),
        "cadastro_url": CADASTRO_URL,
        "inf_diario_file": inf_member_name,
        "downloaded_files": downloaded_files,
    }
    with (cache_dir / "metadata.json").open("w", encoding="utf-8") as file_handle:
        json.dump(metadata, file_handle, indent=2, ensure_ascii=False)

    details.append("Cadastro de fundos e classes atualizado a partir dos dados abertos oficiais da CVM.")
    details.append(f"Arquivo diario utilizado: {inf_member_name}.")
    return CVMSyncResult(
        downloaded_files=downloaded_files,
        imported_at=metadata["imported_at"],
        details=details,
    )


def get_sync_metadata() -> dict[str, str] | None:
    metadata_path = ensure_cvm_cache() / "metadata.json"
    if not metadata_path.exists():
        return None
    with metadata_path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def search_funds(search_term: str = "", qitech_only: bool = True, limit: int = 100) -> list[dict[str, str]]:
    cache_dir = ensure_cvm_cache()
    catalog_rows = _load_semicolon_csv(cache_dir / "catalog.csv")
    normalized_search = search_term.strip().lower()
    results: list[dict[str, str]] = []

    for record in catalog_rows:
        if normalized_search and not _record_matches(record, normalized_search):
            continue
        if qitech_only and not _is_qi_related(record):
            continue
        results.append(record)

    results.sort(key=lambda item: item["fund_name"])
    return results[:limit]


def list_catalog_funds(search_term: str = "", qitech_only: bool = False) -> list[dict[str, object]]:
    cache_dir = ensure_cvm_cache()
    catalog_path = cache_dir / "catalog.csv"
    if not catalog_path.exists():
        return []

    catalog_rows = _load_semicolon_csv(catalog_path)
    local_funds = load_funds()
    clients_by_id = {client["id"]: client for client in load_clients()}

    local_by_class_id = {
        fund.get("cvm_class_id", ""): fund
        for fund in local_funds
        if fund.get("cvm_class_id", "")
    }
    local_by_cnpj = {
        "".join(char for char in str(fund.get("cnpj", "")) if char.isdigit()): fund
        for fund in local_funds
        if fund.get("cnpj", "")
    }

    normalized_search = search_term.strip().lower()
    results: list[dict[str, object]] = []

    for record in catalog_rows:
        if normalized_search and not _record_matches(record, normalized_search):
            continue
        if qitech_only and not _is_qi_related(record):
            continue

        local_fund = (
            local_by_class_id.get(record.get("cvm_class_id", ""))
            or local_by_cnpj.get(_digits_only(record.get("cnpj", "")))
        )
        client = clients_by_id.get(local_fund.get("client_id", ""), {}) if local_fund else {}

        results.append(
            {
                **record,
                "client_id": local_fund.get("client_id", "") if local_fund else "",
                "local_fund_id": local_fund.get("id", "") if local_fund else "",
                "client_name": client.get("name", "") or "Nao cadastrado",
                "has_client": bool(client),
                "monthly_revenue": local_fund.get("monthly_revenue", "") if local_fund else "",
                "formatted_revenue": format_currency(parse_decimal(local_fund.get("monthly_revenue", ""))) if local_fund else "-",
                "formatted_pl": format_currency(parse_decimal(record.get("pl", ""))) if record.get("pl") else "-",
                "product_type": normalize_fund_type(record.get("product_type", "")),
                "is_user_fund_bool": str(local_fund.get("is_user_fund", "0")).strip().lower() in {"1", "true", "sim", "yes", "y", "on"} if local_fund else False,
                "regulation_url": record.get("regulation_url", "") or "https://cvmweb.cvm.gov.br/SWB/default.asp?sg_sistema=fundosreg",
            }
        )

    results.sort(key=lambda item: str(item.get("fund_name", "")).lower())
    return results


def discover_qi_client_candidates(limit: int = 300) -> list[dict[str, object]]:
    cache_dir = ensure_cvm_cache()
    catalog_rows = _load_semicolon_csv(cache_dir / "catalog.csv")
    grouped: dict[str, dict[str, object]] = {}

    for record in catalog_rows:
        if not _is_qi_related(record):
            continue
        candidate = _extract_client_candidate(record)
        if not candidate:
            continue

        key = candidate["name"].strip().lower()
        bucket = grouped.setdefault(
            key,
            {
                "name": candidate["name"],
                "category": candidate["category"],
                "company_cnpj": candidate["company_cnpj"],
                "company_cnpj_source": candidate["company_cnpj_source"],
                "relationship_roles": set(),
                "fund_count": 0,
                "pl_total": "0",
                "funds": [],
                "already_exists": False,
            },
        )
        bucket["relationship_roles"].add(record.get("qi_relationship_role", "") or "Relacionamento QITech")
        bucket["fund_count"] += 1
        bucket["pl_total"] = str(_sum_decimal_strings(bucket["pl_total"], record.get("pl", "")))
        bucket["funds"].append(record)

    results: list[dict[str, object]] = []
    for item in grouped.values():
        existing = get_client_by_name(str(item["name"]))
        item["already_exists"] = existing is not None
        item["existing_client_id"] = existing["id"] if existing else ""
        if existing:
            item["company_cnpj"] = existing.get("company_cnpj", "") or item.get("company_cnpj", "")
        item["funds"] = sorted(
            [
                {
                    **fund,
                    "cnpj": format_cnpj(fund.get("cnpj", "")),
                    "formatted_pl": format_currency(parse_decimal(fund.get("pl", ""))),
                    "product_type": normalize_fund_type(fund.get("product_type", "")),
                    "regulation_url": fund.get("regulation_url", "") or "https://cvmweb.cvm.gov.br/SWB/default.asp?sg_sistema=fundosreg",
                }
                for fund in item["funds"]
            ],
            key=lambda fund: str(fund.get("fund_name", "")).lower(),
        )
        item["relationship_roles"] = ", ".join(
            sorted(role for role in item["relationship_roles"] if str(role).strip())
        )
        results.append(item)

    results.sort(key=lambda item: (item["already_exists"], -int(item["fund_count"]), str(item["name"])))
    return results[:limit]


def import_qi_client_candidate(client_name: str) -> dict[str, object] | None:
    candidate = next(
        (item for item in discover_qi_client_candidates(limit=1000) if item["name"] == client_name),
        None,
    )
    if not candidate:
        return None

    client = get_client_by_name(candidate["name"])
    if client is None:
        client = add_client(
            {
                "name": candidate["name"],
                "category": candidate["category"],
                "company_cnpj": candidate.get("company_cnpj", ""),
                "company_cnpj_source": candidate.get("company_cnpj_source", ""),
                "monthly_revenue": "",
                "monthly_revenue_source": "",
                "notes": f"Cliente descoberto automaticamente via base CVM. Relacao com QITech: {candidate['relationship_roles']}.",
            }
        )
    elif candidate.get("company_cnpj") and not client.get("company_cnpj"):
        update_client_company_identity(
            client["id"],
            str(candidate.get("company_cnpj", "")),
            str(candidate.get("company_cnpj_source", "")),
        )

    for fund in candidate["funds"]:
        add_fund(
            {
                "client_id": client["id"],
                "cvm_fund_id": fund.get("cvm_fund_id", ""),
                "cvm_class_id": fund.get("cvm_class_id", ""),
                "fund_name": fund.get("fund_name", ""),
                "cnpj": fund.get("cnpj", ""),
                "pl": fund.get("pl", ""),
                "product_type": fund.get("product_type", ""),
                "manager_name": fund.get("manager_name", ""),
                "administrator_name": fund.get("administrator_name", ""),
                "status": fund.get("status", ""),
                "revenue_source": "CVM Dados Abertos",
                "regulation_url": fund.get("regulation_url", ""),
                "is_user_fund": "0",
            }
        )

    return {
        "client": client,
        "fund_count": len(candidate["funds"]),
    }


def import_all_qi_client_candidates() -> dict[str, int]:
    imported_clients = 0
    linked_funds = 0
    for candidate in discover_qi_client_candidates(limit=1000):
        if candidate["already_exists"]:
            continue
        result = import_qi_client_candidate(str(candidate["name"]))
        if not result:
            continue
        imported_clients += 1
        linked_funds += int(result["fund_count"])
    return {
        "imported_clients": imported_clients,
        "linked_funds": linked_funds,
    }


def _download_latest_inf_diario() -> tuple[str, bytes]:
    today = date.today().replace(day=1)
    candidates = [
        today.strftime("%Y%m"),
        _previous_month(today).strftime("%Y%m"),
    ]
    for candidate in candidates:
        url = INF_DIARIO_URL_TEMPLATE.format(year_month=candidate)
        try:
            raw = _download_bytes(url)
        except Exception:
            continue
        archive = zipfile.ZipFile(io.BytesIO(raw))
        member = archive.namelist()[0]
        with archive.open(member) as source:
            return member, source.read()
    raise RuntimeError("Nao foi possivel baixar o informe diario mais recente da CVM.")


def _download_bytes(url: str) -> bytes:
    with urlopen(url, timeout=180) as response:
        return response.read()


def _previous_month(value: date) -> date:
    if value.month == 1:
        return value.replace(year=value.year - 1, month=12)
    return value.replace(month=value.month - 1)


def _load_semicolon_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    for encoding in ["utf-8", "latin1"]:
        try:
            with path.open("r", encoding=encoding, newline="") as file_handle:
                reader = csv.DictReader(file_handle, delimiter=";")
                return [{key: value.strip() for key, value in row.items()} for row in reader]
        except UnicodeDecodeError:
            continue
    return []


def _load_latest_pl_index(cache_dir: Path) -> dict[str, dict[str, str]]:
    indexed_path = cache_dir / "latest_pl.csv"
    if indexed_path.exists():
        rows = _load_semicolon_csv(indexed_path)
        return {
            row["cnpj"]: {
                "DT_COMPTC": row.get("DT_COMPTC", ""),
                "VL_PATRIM_LIQ": row.get("VL_PATRIM_LIQ", ""),
            }
            for row in rows
        }

    metadata = get_sync_metadata()
    if not metadata:
        return {}
    inf_path = cache_dir / metadata["inf_diario_file"]
    if not inf_path.exists():
        return {}
    return _build_latest_pl_index_from_file(inf_path)


def _build_latest_pl_index_from_file(inf_path: Path) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    with inf_path.open("r", encoding="latin1", newline="") as file_handle:
        reader = csv.DictReader(file_handle, delimiter=";")
        for row in reader:
            cnpj = _digits_only(row.get("CNPJ_FUNDO_CLASSE", ""))
            current_date = row.get("DT_COMPTC", "")
            previous = latest.get(cnpj)
            if previous is None or current_date >= previous.get("DT_COMPTC", ""):
                latest[cnpj] = row
    return latest


def _build_catalog_rows(
    fund_rows: list[dict[str, str]],
    class_rows: list[dict[str, str]],
    latest_pl: dict[str, dict[str, str]],
    regulation_index: dict[str, str],
) -> list[dict[str, str]]:
    fund_index = {row["ID_Registro_Fundo"]: row for row in fund_rows}
    return [
        _build_catalog_record(
            fund_index.get(class_row["ID_Registro_Fundo"], {}),
            class_row,
            latest_pl,
            regulation_index,
        )
        for class_row in class_rows
    ]


def _write_semicolon_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=headers, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def _build_catalog_record(
    fund_row: dict[str, str],
    class_row: dict[str, str],
    latest_pl: dict[str, dict[str, str]],
    regulation_index: dict[str, str],
) -> dict[str, str]:
    cnpj = _digits_only(class_row.get("CNPJ_Classe", ""))
    daily_row = latest_pl.get(cnpj, {})
    pl = daily_row.get("VL_PATRIM_LIQ") or class_row.get("Patrimonio_Liquido", "")
    manager_document = _digits_only(fund_row.get("CPF_CNPJ_Gestor", ""))
    administrator_document = _digits_only(fund_row.get("CNPJ_Administrador", ""))
    custodian_document = _digits_only(class_row.get("CNPJ_Custodiante", ""))
    controller_document = _digits_only(class_row.get("CNPJ_Controlador", ""))
    return {
        "cvm_fund_id": fund_row.get("ID_Registro_Fundo", ""),
        "cvm_class_id": class_row.get("ID_Registro_Classe", ""),
        "fund_name": class_row.get("Denominacao_Social", ""),
        "cnpj": _format_cnpj(cnpj),
        "raw_cnpj": cnpj,
        "pl": pl,
        "pl_date": daily_row.get("DT_COMPTC") or class_row.get("Data_Patrimonio_Liquido", ""),
        "product_type": normalize_fund_type(class_row.get("Tipo_Classe", "")),
        "status": class_row.get("Situacao", ""),
        "manager_name": fund_row.get("Gestor", ""),
        "manager_document": _format_cnpj(manager_document),
        "administrator_name": fund_row.get("Administrador", ""),
        "administrator_document": _format_cnpj(administrator_document),
        "custodian_name": class_row.get("Custodiante", ""),
        "custodian_document": _format_cnpj(custodian_document),
        "controller_name": class_row.get("Controlador", ""),
        "controller_document": _format_cnpj(controller_document),
        "fund_legal_name": fund_row.get("Denominacao_Social", ""),
        "regulation_url": regulation_index.get(cnpj, "https://cvmweb.cvm.gov.br/SWB/default.asp?sg_sistema=fundosreg"),
        "qi_relationship_role": _detect_qi_relationship_role(
            manager_document,
            administrator_document,
            custodian_document,
            controller_document,
            fund_row.get("Gestor", ""),
            fund_row.get("Administrador", ""),
            class_row.get("Custodiante", ""),
            class_row.get("Controlador", ""),
        ),
    }


def _record_matches(record: dict[str, str], search_term: str) -> bool:
    haystack = " ".join(
        [
            record["fund_name"],
            record["fund_legal_name"],
            record["manager_name"],
            record["administrator_name"],
            record["custodian_name"],
            record["controller_name"],
        ]
    ).lower()
    return search_term in haystack


def _is_qi_related(record: dict[str, str]) -> bool:
    if record.get("qi_relationship_role", "").strip():
        return True

    qi_documents = set(settings.QITECH_ENTITY_CNPJS)
    record_documents = {
        _digits_only(record.get("manager_document", "")),
        _digits_only(record.get("administrator_document", "")),
        _digits_only(record.get("custodian_document", "")),
        _digits_only(record.get("controller_document", "")),
    }
    if qi_documents & record_documents:
        return True

    haystack = " ".join(
        [
            record["manager_name"],
            record["administrator_name"],
            record["custodian_name"],
            record["controller_name"],
        ]
    ).upper()
    return any(keyword.upper() in haystack for keyword in settings.QITECH_MATCH_KEYWORDS)


def _detect_qi_relationship_role(
    manager_document: str,
    administrator_document: str,
    custodian_document: str,
    controller_document: str,
    manager_name: str,
    administrator_name: str,
    custodian_name: str,
    controller_name: str,
) -> str:
    qi_documents = set(settings.QITECH_ENTITY_CNPJS)
    candidates = [
        ("Consultoria", manager_document, manager_name),
        ("Administrador", administrator_document, administrator_name),
        ("Custodiante", custodian_document, custodian_name),
        ("Controlador", controller_document, controller_name),
    ]
    for role, document, name in candidates:
        if _digits_only(document) in qi_documents:
            return role
        upper_name = str(name).upper()
        if any(keyword.upper() in upper_name for keyword in settings.QITECH_MATCH_KEYWORDS):
            return role
    return ""


def _extract_client_candidate(record: dict[str, str]) -> dict[str, str] | None:
    candidates = [
        ("gestora", record.get("manager_name", ""), record.get("manager_document", ""), "Consultoria"),
        ("outros", record.get("administrator_name", ""), record.get("administrator_document", ""), "Administrador"),
        ("outros", record.get("controller_name", ""), record.get("controller_document", ""), "Controlador"),
        ("outros", record.get("custodian_name", ""), record.get("custodian_document", ""), "Custodiante"),
    ]
    qi_documents = set(settings.QITECH_ENTITY_CNPJS)
    for suggested_category, name, document, source_role in candidates:
        normalized_name = str(name).strip()
        normalized_document = _digits_only(document)
        if not normalized_name:
            continue
        if normalized_document in qi_documents:
            continue
        if any(keyword.upper() in normalized_name.upper() for keyword in settings.QITECH_MATCH_KEYWORDS):
            continue
        return {
            "name": normalized_name,
            "category": _guess_client_category(normalized_name, suggested_category),
            "company_cnpj": normalized_document,
            "company_cnpj_source": f"CVM {source_role}",
        }
    return None


def _guess_client_category(name: str, fallback: str) -> str:
    upper_name = name.upper()
    if "CONSULT" in upper_name:
        return "consultoria"
    if "BANCO" in upper_name:
        return "banco"
    if "SECURIT" in upper_name:
        return "securitizadora"
    if any(token in upper_name for token in ["ASSET", "GEST", "CAPITAL", "MANAGEMENT"]):
        return "gestora"
    return fallback


def _build_regulation_index(cache_dir: Path) -> dict[str, str]:
    years = [date.today().year, date.today().year - 1]
    latest_by_cnpj: dict[str, tuple[str, str]] = {}
    for year in years:
        try:
            raw = _download_bytes(EVENTUAL_URL_TEMPLATE.format(year=year))
        except Exception:
            continue
        target = cache_dir / f"eventual_fi_{year}.csv"
        target.write_bytes(raw)
        rows = _load_semicolon_csv(target)
        for row in rows:
            if row.get("TP_DOC", "") != "REGUL FDO":
                continue
            cnpj = _digits_only(row.get("CNPJ_FUNDO_CLASSE", ""))
            link = row.get("LINK_ARQ", "")
            if not cnpj or not link:
                continue
            received_at = row.get("DT_RECEB", "") or row.get("DT_COMPTC", "")
            previous = latest_by_cnpj.get(cnpj)
            if previous is None or received_at >= previous[0]:
                latest_by_cnpj[cnpj] = (received_at, link)
    return {cnpj: link for cnpj, (_, link) in latest_by_cnpj.items()}


def _sum_decimal_strings(left: str, right: str) -> Decimal:
    return _to_decimal(left) + _to_decimal(right)


def _to_decimal(value: str) -> Decimal:
    sanitized = str(value or "").strip()
    if "," in sanitized and "." in sanitized:
        sanitized = sanitized.replace(".", "").replace(",", ".")
    elif "," in sanitized:
        sanitized = sanitized.replace(",", ".")
    try:
        return Decimal(sanitized)
    except InvalidOperation:
        return Decimal("0")


def _digits_only(value: str) -> str:
    return "".join(char for char in str(value) if char.isdigit())


def _format_cnpj(value: str) -> str:
    digits = _digits_only(value)
    if len(digits) != 14:
        return value
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
