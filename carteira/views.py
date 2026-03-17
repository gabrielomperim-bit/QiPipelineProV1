from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from .forms import ClienteForm, ClienteQiBuscaForm, ContatoForm, FundoBuscaForm, FundoCatalogoBuscaForm, FundoReceitaForm, RegraReceitaForm, UploadCarteiraForm
from .services.cvm_sync import (
    discover_qi_client_candidates,
    get_sync_metadata,
    import_qi_client_candidate,
    search_funds,
    sync_cvm_data,
)
from .services.data_store import (
    add_client,
    add_contact,
    add_fund,
    build_dashboard_metrics,
    delete_client,
    delete_rule,
    ensure_storage,
    get_client,
    get_client_by_name,
    group_clients_by_category,
    list_all_linked_funds,
    list_known_product_types,
    list_rules,
    parse_decimal,
    refresh_client_revenue,
    set_fund_user_status,
    update_client_company_identity,
    upsert_company_profile,
    upsert_rule,
    update_fund_fee_rate,
)
from .services.importers import import_clients_from_file
from .services.public_company import enrich_company_profiles_for_client


def dashboard(request):
    ensure_storage()
    context = {
        "metrics": build_dashboard_metrics(),
        "groups": group_clients_by_category(),
        "cvm_metadata": get_sync_metadata(),
    }
    return render(request, "carteira/dashboard.html", context)


def importar_carteira(request):
    ensure_storage()
    summary = None

    if request.method == "POST":
        form = UploadCarteiraForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.cleaned_data["arquivo"]
            destination = Path(settings.UPLOAD_DIR) / upload.name
            with destination.open("wb+") as file_handle:
                for chunk in upload.chunks():
                    file_handle.write(chunk)
            summary = import_clients_from_file(destination)
    else:
        form = UploadCarteiraForm()

    return render(
        request,
        "carteira/importar.html",
        {
            "form": form,
            "summary": summary,
        },
    )


def novo_cliente(request):
    ensure_storage()
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            payload = {
                "name": form.cleaned_data["nome"],
                "category": form.cleaned_data["categoria"],
                "monthly_revenue": str(form.cleaned_data["receita_mensal"] or ""),
                "monthly_revenue_source": form.cleaned_data["fonte_receita"],
                "notes": form.cleaned_data["observacoes"],
            }
            client = add_client(payload)
            return redirect("detalhe_cliente", client_id=client["id"])
    else:
        form = ClienteForm()

    return render(request, "carteira/novo_cliente.html", {"form": form})


def detalhe_cliente(request, client_id: str):
    ensure_storage()
    client = get_client(client_id)
    if not client:
        raise Http404("Cliente nao encontrado.")
    return render(
        request,
        "carteira/detalhe_cliente.html",
        {
            "client": client,
            "cvm_metadata": get_sync_metadata(),
            "contact_form": ContatoForm(),
            "fund_type_options": list_known_product_types(),
        },
    )


def sincronizar_cvm(request):
    ensure_storage()
    sync_result = None
    error_message = None
    if request.method == "POST":
        try:
            sync_result = sync_cvm_data()
        except Exception as exc:
            error_message = str(exc)

    return render(
        request,
        "carteira/cvm_sync.html",
        {
            "sync_result": sync_result,
            "error_message": error_message,
            "metadata": get_sync_metadata(),
        },
    )


def buscar_fundos_cliente(request, client_id: str):
    ensure_storage()
    client = get_client(client_id)
    if not client:
        raise Http404("Cliente nao encontrado.")

    metadata = get_sync_metadata()
    results: list[dict[str, str]] = []
    if request.GET:
        form = FundoBuscaForm(request.GET)
        if form.is_valid() and metadata:
            results = search_funds(
                search_term=form.cleaned_data["consulta"] or client["name"],
                qitech_only=form.cleaned_data["somente_qi"],
            )
    else:
        form = FundoBuscaForm(initial={"consulta": client["name"], "somente_qi": True})
        if metadata:
            results = search_funds(search_term=client["name"], qitech_only=True)

    return render(
        request,
        "carteira/buscar_fundos.html",
        {
            "client": client,
            "form": form,
            "results": results,
            "metadata": metadata,
        },
    )


def vincular_fundo_cliente(request, client_id: str):
    ensure_storage()
    client = get_client(client_id)
    if not client:
        raise Http404("Cliente nao encontrado.")
    if request.method != "POST":
        return redirect("buscar_fundos_cliente", client_id=client_id)

    payload = {
        "client_id": client_id,
        "cvm_fund_id": request.POST.get("cvm_fund_id", ""),
        "cvm_class_id": request.POST.get("cvm_class_id", ""),
        "fund_name": request.POST.get("fund_name", ""),
        "cnpj": request.POST.get("cnpj", ""),
        "pl": request.POST.get("pl", ""),
        "monthly_revenue": request.POST.get("monthly_revenue", ""),
        "product_type": request.POST.get("product_type", ""),
        "manager_name": request.POST.get("manager_name", ""),
        "administrator_name": request.POST.get("administrator_name", ""),
        "status": request.POST.get("status", ""),
        "regulation_url": request.POST.get("regulation_url", ""),
        "revenue_source": "CVM Dados Abertos",
    }
    if payload["fund_name"] and payload["cnpj"]:
        add_fund(payload)
    return redirect("detalhe_cliente", client_id=client_id)


def regras_receita(request):
    ensure_storage()
    if request.method == "POST":
        form = RegraReceitaForm(request.POST)
        if form.is_valid():
            upsert_rule(
                product_type=form.cleaned_data["product_type"],
                annual_fee_rate=str(form.cleaned_data["annual_fee_rate"]),
                notes=form.cleaned_data["notes"],
            )
            return redirect("regras_receita")
    else:
        form = RegraReceitaForm()

    return render(
        request,
        "carteira/regras_receita.html",
        {
            "form": form,
            "rules": list_rules(),
            "known_product_types": list_known_product_types(),
        },
    )


def remover_regra_receita(request, product_type: str):
    ensure_storage()
    if request.method == "POST":
        delete_rule(product_type)
    return redirect("regras_receita")


def atualizar_receita_fundo(request, client_id: str):
    ensure_storage()
    client = get_client(client_id)
    if not client:
        raise Http404("Cliente nao encontrado.")
    if request.method != "POST":
        return redirect("detalhe_cliente", client_id=client_id)

    form = FundoReceitaForm(request.POST)
    if form.is_valid():
        update_fund_fee_rate(
            fund_id=form.cleaned_data["fund_id"],
            annual_fee_rate=str(form.cleaned_data["annual_fee_rate"]),
        )
        refresh_client_revenue(client_id)
    return redirect("detalhe_cliente", client_id=client_id)


def adicionar_contato_cliente(request, client_id: str):
    ensure_storage()
    client = get_client(client_id)
    if not client:
        raise Http404("Cliente nao encontrado.")
    if request.method != "POST":
        return redirect("detalhe_cliente", client_id=client_id)

    form = ContatoForm(request.POST)
    if form.is_valid():
        add_contact(
            {
                "client_id": client_id,
                "name": form.cleaned_data["nome"],
                "role": form.cleaned_data["cargo"],
                "area": form.cleaned_data["area"],
                "email": form.cleaned_data["email"],
                "phone": form.cleaned_data["telefone"],
                "linkedin": form.cleaned_data["linkedin"],
                "notes": form.cleaned_data["observacoes"],
            }
        )
    return redirect("detalhe_cliente", client_id=client_id)


def enriquecer_cliente(request, client_id: str):
    ensure_storage()
    client = get_client(client_id)
    if not client:
        raise Http404("Cliente nao encontrado.")
    if request.method != "POST":
        return redirect("detalhe_cliente", client_id=client_id)

    if not str(client.get("company_cnpj", "")).strip():
        candidate = next(
            (
                item
                for item in discover_qi_client_candidates(limit=1000)
                if str(item.get("name", "")).strip().lower() == str(client.get("name", "")).strip().lower()
            ),
            None,
        )
        if candidate and candidate.get("company_cnpj"):
            update_client_company_identity(
                client_id,
                str(candidate.get("company_cnpj", "")),
                str(candidate.get("company_cnpj_source", "")),
            )
            client = get_client(client_id)

    profiles = enrich_company_profiles_for_client(client)
    for profile in profiles:
        upsert_company_profile(profile)
    return redirect("detalhe_cliente", client_id=client_id)


def alternar_fundo_usuario(request, client_id: str, fund_id: str):
    ensure_storage()
    client = get_client(client_id)
    if not client:
        raise Http404("Cliente nao encontrado.")
    next_url = request.POST.get("next") or request.GET.get("next")
    if request.method == "POST":
        set_fund_user_status(fund_id, request.POST.get("is_user_fund", "0") == "1")
    if next_url:
        return redirect(next_url)
    return redirect("detalhe_cliente", client_id=client_id)


def remover_cliente(request, client_id: str):
    ensure_storage()
    client = get_client(client_id)
    if not client:
        raise Http404("Cliente nao encontrado.")
    if request.method == "POST":
        delete_client(client_id)
        return redirect("dashboard")
    return redirect("detalhe_cliente", client_id=client_id)


def clientes_qi_descobertos(request):
    ensure_storage()
    metadata = get_sync_metadata()
    import_summary = None

    if request.method == "POST" and metadata:
        action = request.POST.get("action", "")
        if action == "import_one":
            client_name = request.POST.get("client_name", "")
            exists_before = get_client_by_name(client_name) is not None
            result = import_qi_client_candidate(client_name)
            if result:
                import_summary = {
                    "imported_clients": 0 if exists_before else 1,
                    "linked_funds": int(result["fund_count"]),
                    "single_client": client_name,
                }

    search_form = ClienteQiBuscaForm(request.GET or None)
    candidates = discover_qi_client_candidates() if metadata else []
    if metadata and search_form.is_valid():
        query = (search_form.cleaned_data.get("consulta") or "").strip().lower()
        if query:
            candidates = [
                candidate
                for candidate in candidates
                if query in str(candidate.get("name", "")).lower()
                or query in str(candidate.get("company_cnpj", "")).lower()
                or query in str(candidate.get("category", "")).lower()
            ]

    return render(
        request,
        "carteira/clientes_qi_descobertos.html",
        {
            "metadata": metadata,
            "candidates": candidates,
            "import_summary": import_summary,
            "search_form": search_form,
        },
    )


def catalogo_fundos(request):
    ensure_storage()
    search_form = FundoCatalogoBuscaForm(request.GET or None)
    search_term = ""
    if search_form.is_valid():
        search_term = search_form.cleaned_data.get("consulta") or ""
    funds = list_all_linked_funds(search_term)
    fund_type_filter = (request.GET.get("fund_type") or "").strip()
    user_filter = (request.GET.get("user_filter") or "").strip()
    sort = (request.GET.get("sort") or "").strip()
    per_page = request.GET.get("per_page") or "20"

    if fund_type_filter:
        funds = [fund for fund in funds if fund.get("product_type", "") == fund_type_filter]
    if user_filter == "true":
        funds = [fund for fund in funds if fund.get("is_user_fund_bool")]
    elif user_filter == "false":
        funds = [fund for fund in funds if not fund.get("is_user_fund_bool")]

    if sort == "pl_asc":
        funds = sorted(funds, key=lambda item: parse_decimal(item.get("pl", "0")))
    elif sort == "pl_desc":
        funds = sorted(funds, key=lambda item: parse_decimal(item.get("pl", "0")), reverse=True)
    elif sort == "revenue_asc":
        funds = sorted(funds, key=lambda item: parse_decimal(item.get("monthly_revenue", "0")))
    elif sort == "revenue_desc":
        funds = sorted(funds, key=lambda item: parse_decimal(item.get("monthly_revenue", "0")), reverse=True)

    per_page_value = int(per_page) if per_page in {"20", "50", "100"} else 20
    paginator = Paginator(funds, per_page_value)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {
        "search_form": search_form,
        "page_obj": page_obj,
        "funds": page_obj.object_list,
        "fund_type_options": list_known_product_types(),
        "fund_type_filter": fund_type_filter,
        "user_filter": user_filter,
        "sort": sort,
        "per_page": str(per_page_value),
    }
    return render(request, "carteira/catalogo_fundos.html", context)
