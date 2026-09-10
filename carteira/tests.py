import csv
import io
import json
import tempfile
from datetime import datetime
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from openpyxl import Workbook, load_workbook

from .services.data_store import add_client, add_fund, ensure_storage


class WorkspaceSmokeTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_root = tempfile.TemporaryDirectory()
        base_path = Path(cls.temp_root.name)
        data_dir = base_path / "data"
        upload_dir = base_path / "uploads"
        cvm_cache_dir = data_dir / "cvm"
        cls.settings_override = override_settings(
            DATA_DIR=data_dir,
            UPLOAD_DIR=upload_dir,
            CVM_CACHE_DIR=cvm_cache_dir,
            ALLOWED_HOSTS=["127.0.0.1", "localhost", "testserver"],
        )
        cls.settings_override.enable()
        ensure_storage()
        cvm_cache_dir.mkdir(parents=True, exist_ok=True)
        cls._write_cvm_cache(cvm_cache_dir)
        cls.sample_client = add_client(
            {
                "name": "Solis Capital",
                "category": "gestora",
                "company_cnpj": "12345678000190",
                "company_cnpj_source": "CVM Consultoria",
                "monthly_revenue": "",
                "monthly_revenue_source": "",
                "notes": "Cliente de teste",
            }
        )
        cls.user_fund = add_fund(
            {
                "client_id": cls.sample_client["id"],
                "cvm_fund_id": "F001",
                "cvm_class_id": "C001",
                "fund_name": "Fundo Solis Alpha",
                "cnpj": "11.111.111/0001-11",
                "pl": "1200000.00",
                "monthly_revenue": "3000.00",
                "product_type": "FIDC",
                "manager_name": "Consultoria Solis",
                "administrator_name": "QITech Administracao",
                "status": "Em funcionamento",
                "regulation_url": "https://example.com/regulamento-alpha.pdf",
                "is_user_fund": "1",
            }
        )
        cls.other_fund = add_fund(
            {
                "client_id": cls.sample_client["id"],
                "cvm_fund_id": "F002",
                "cvm_class_id": "C002",
                "fund_name": "Fundo Solis Beta",
                "cnpj": "22.222.222/0001-22",
                "pl": "800000.00",
                "monthly_revenue": "1500.00",
                "product_type": "FIF",
                "manager_name": "Consultoria Solis",
                "administrator_name": "Outro Administrador",
                "status": "Em funcionamento",
                "regulation_url": "https://example.com/regulamento-beta.pdf",
                "is_user_fund": "0",
            }
        )

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        cls.temp_root.cleanup()
        super().tearDownClass()

    @classmethod
    def _write_cvm_cache(cls, cvm_cache_dir: Path) -> None:
        metadata = {
            "imported_at": "2026-05-05T10:00:00",
            "cadastro_url": "https://dados.cvm.gov.br/",
            "inf_diario_file": "inf_diario_fi_202605.csv",
            "downloaded_files": ["catalog.csv", "latest_pl.csv"],
        }
        with (cvm_cache_dir / "metadata.json").open("w", encoding="utf-8") as file_handle:
            json.dump(metadata, file_handle, ensure_ascii=False, indent=2)

        headers = [
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
        ]
        rows = [
            {
                "cvm_fund_id": "F001",
                "cvm_class_id": "C001",
                "fund_name": "Fundo Solis Alpha",
                "cnpj": "11.111.111/0001-11",
                "raw_cnpj": "11111111000111",
                "pl": "1200000.00",
                "pl_date": "2026-05-01",
                "product_type": "FIDC",
                "status": "Em funcionamento",
                "manager_name": "Consultoria Solis",
                "manager_document": "12.345.678/0001-90",
                "administrator_name": "QITech Administracao",
                "administrator_document": "30.620.610/0001-59",
                "custodian_name": "",
                "custodian_document": "",
                "controller_name": "",
                "controller_document": "",
                "fund_legal_name": "Fundo Solis Alpha",
                "regulation_url": "https://example.com/regulamento-alpha.pdf",
                "qi_relationship_role": "Administrador",
            },
            {
                "cvm_fund_id": "F002",
                "cvm_class_id": "C002",
                "fund_name": "Fundo Solis Beta",
                "cnpj": "22.222.222/0001-22",
                "raw_cnpj": "22222222000122",
                "pl": "800000.00",
                "pl_date": "2026-05-01",
                "product_type": "FIF",
                "status": "Em funcionamento",
                "manager_name": "Consultoria Solis",
                "manager_document": "12.345.678/0001-90",
                "administrator_name": "Outro Administrador",
                "administrator_document": "44.444.444/0001-44",
                "custodian_name": "",
                "custodian_document": "",
                "controller_name": "",
                "controller_document": "",
                "fund_legal_name": "Fundo Solis Beta",
                "regulation_url": "https://example.com/regulamento-beta.pdf",
                "qi_relationship_role": "Consultoria",
            },
        ]
        with (cvm_cache_dir / "catalog.csv").open("w", encoding="utf-8", newline="") as file_handle:
            writer = csv.DictWriter(file_handle, fieldnames=headers, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)

    def test_core_pages_render(self):
        paths = [
            "/",
            "/dashboard/usuario/",
            "/dashboard/comercial/",
            "/clientes/",
            "/fundos/",
            "/importar/",
            "/cvm/",
            "/cvm/clientes-qi/",
            "/receita/regras/",
            "/clientes/novo/",
            f"/clientes/{self.sample_client['id']}/",
            f"/clientes/{self.sample_client['id']}/buscar-fundos/",
        ]
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path, HTTP_HOST="127.0.0.1")
                self.assertEqual(response.status_code, 200)

    def test_catalogo_exibe_atalho_para_sincronizar_cvm(self):
        response = self.client.get("/fundos/", HTTP_HOST="127.0.0.1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'action="/cvm/"')
        self.assertContains(response, 'aria-label="Atualizar dados da CVM"')

    def test_analise_comercial_processes_uploaded_workbooks(self):
        response = self.client.post(
            "/dashboard/comercial/",
            {
                "scorecard": self._build_scorecard_upload(),
                "base_fundos": self._build_base_upload(),
            },
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visao geral da operacao")
        self.assertContains(response, "Receita do mes")
        self.assertContains(response, "Negocios ganhos")
        self.assertContains(response, "scorecard.xlsx")
        self.assertContains(response, "base.xlsx")

    def test_dashboard_usuario_uses_only_flagged_funds(self):
        response = self.client.get("/dashboard/usuario/", HTTP_HOST="127.0.0.1")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fundo Solis Alpha")
        self.assertNotContains(response, "Fundo Solis Beta")
        self.assertContains(response, "Fundos da minha carteira")

    def test_catalogo_fundos_filters_administrator(self):
        response = self.client.get(
            "/fundos/",
            {
                "administrator_operator": "eq",
                "administrator_filter": "QITech Administracao",
            },
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fundo Solis Alpha")
        self.assertNotContains(response, "Fundo Solis Beta")
        self.assertContains(response, "Administrador igual a: QITech Administracao")
        self.assertContains(response, "05/05/2026 às 10:00")
        self.assertContains(response, "01/05/2026")

    def test_catalogo_filter_chip_removes_only_selected_filter(self):
        response = self.client.get(
            "/fundos/",
            {
                "fund_type": "FIDC",
                "manager_operator": "contains",
                "manager_filter": "Solis",
            },
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tipo: FIDC")
        self.assertContains(response, "Gestora contém: Solis")
        self.assertContains(response, "manager_filter=Solis")

    def test_export_funds_allows_column_selection_and_reference_date(self):
        response = self.client.get(
            "/fundos/exportar/",
            {
                "fund_type": "FIDC",
                "columns": ["fund_name", "pl", "pl_date"],
            },
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        workbook = load_workbook(io.BytesIO(response.content))
        worksheet = workbook["Fundos"]
        self.assertEqual(
            [cell.value for cell in worksheet[1]],
            ["Fundo", "PL", "Data de referencia do PL"],
        )
        self.assertEqual(worksheet["A2"].value, "Fundo Solis Alpha")
        self.assertEqual(worksheet["B2"].value, 1200000)
        self.assertEqual(worksheet["C2"].value.date().isoformat(), "2026-05-01")
        self.assertIsNone(worksheet["A3"].value)

    def test_toggle_user_fund_redirects(self):
        response = self.client.post(
            f"/clientes/{self.sample_client['id']}/fundos/{self.other_fund['id']}/usuario/",
            {
                "is_user_fund": "1",
                "next": f"/clientes/{self.sample_client['id']}/",
            },
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], f"/clientes/{self.sample_client['id']}/")

    def _build_scorecard_upload(self) -> SimpleUploadedFile:
        workbook = Workbook()
        scorecard = workbook.active
        scorecard.title = "Scorecard"
        scorecard.append(["Kathleen Perim", "", datetime(2026, 2, 1), 14])
        scorecard.append(["Dados até:", "", datetime(2026, 2, 25), "1Q26"])
        scorecard.append(
            ["KPI", "Peso", "Cenário"]
            + [datetime(2026, month, 1) for month in range(1, 13)]
            + [None, "1Q26", "2Q26", "3Q26", "4Q26"]
        )
        scorecard.append(["Receita Base", 0.2, "Target"] + [1000] * 12 + [None, 3000, 0, 0, 0])
        scorecard.append([None, None, "Realizado"] + [900] * 12 + [None, 2700, 0, 0, 0])
        scorecard.append([None, None, "Ating."] + [0.9] * 12 + [None, 0.9, 0, 0, 0])
        scorecard.append([None, None, "Ating. Ponderado"] + [0.18] * 12 + [None, 0.18, 0, 0, 0])

        clientes = workbook.create_sheet("Clientes")
        clientes.append([None, "YTD", "YTD"])
        clientes.append([None, 1, 2])
        clientes.append(
            ["CLIENTES RECEITA"]
            + [datetime(2025, month, 1) for month in range(1, 13)]
            + [datetime(2026, month, 1) for month in range(1, 13)]
            + [None]
            + [datetime(2026, month, 1) for month in range(1, 13)]
            + [None, "M0-M1", "%", None, datetime(2025, 2, 1), datetime(2026, 2, 1), "Delta", "%", None, "Act YTD", "Bdgt YTD", "Delta", "%"]
        )
        clientes.append(["Cliente A"] + [0] * 12 + [500, 700] + [0] * 10 + [None] + [600, 800] + [0] * 10 + [None, 200, 0.4, None, 0, 700, 700, 0.0, None, 1200, 1500, -300, 0.8])
        clientes.append(["Cliente B"] + [0] * 12 + [300, 400] + [0] * 10 + [None] + [500, 600] + [0] * 10 + [None, 100, 0.3, None, 0, 400, 400, 0.0, None, 900, 1000, -100, 0.9])

        carteira = workbook.create_sheet("Carteira Fundos")
        carteira.append(["CNPJ", "FUNDO", "GESTORA", "CLIENT GROUP"])
        carteira.append(["11.111.111/0001-11", "Fundo A", "Gestora A", "Grupo A"])
        carteira.append(["22.222.222/0001-22", "Fundo B", "Gestora B", "Grupo B"])

        propostas = workbook.create_sheet("BD_Propostas_Vendas")
        propostas.append(["Record ID", "Nome do negócio", "Proprietário", "Data", "Aux", "Date", "Quarter", "Record ID", "Deal", "Proprietário", "Data_Treated", "Source"])
        propostas.append([1, "Negocio A", "Kathleen", datetime(2026, 1, 2), "", datetime(2026, 1, 1), "1Q26", 1, "Negocio A", "Kathleen", datetime(2026, 1, 1), "Base"])

        fup = workbook.create_sheet("BD_FUP")
        fup.append(["Proprietário do negócio", "Tipo de atividade", "Data da atividade", "Data da criação", "Negócio ID", "Engagement ID", "Aux_Pessoa", "Aux_Date", "Empresa", "Delta Dias", "Notes"])
        fup.append(["Kathleen", "E-mail", datetime(2026, 2, 3), datetime(2026, 1, 27), 1, 1, "Kathleen", datetime(2026, 2, 1), "Empresa A", 7, False])
        fup.append(["Kathleen", "Chamada", datetime(2026, 2, 4), datetime(2026, 1, 28), 2, 2, "Kathleen", datetime(2026, 2, 1), "Empresa A", 7, False])

        negocios = workbook.create_sheet("BD_Negócios")
        negocios.append(["Record ID", "Nome do negócio", "Proprietário do negócio", "Etapa do negócio", "Empresas associadas", "Data Prospec", "Aux_Pessoa", "Data_Treated"])
        negocios.append([1, "Negocio A", "Kathleen", "Venda Ganha", "Empresa A", datetime(2026, 1, 3), "Kathleen", datetime(2026, 1, 1)])
        negocios.append([2, "Negocio B", "Kathleen", "Proposta Enviada", "Empresa B", datetime(2026, 1, 4), "Kathleen", datetime(2026, 1, 1)])

        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return SimpleUploadedFile(
            "scorecard.xlsx",
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def _build_base_upload(self) -> SimpleUploadedFile:
        workbook = Workbook()
        abertos = workbook.active
        abertos.title = "Fundos Abertos por mês"
        abertos.append(["Mês", "Numero de Fundos Abertos em 2024", "Numero de Fundos Abertos em 2025"])
        abertos.append(["Jan", 3, 5])
        abertos.append(["Fev", 4, 6])

        base = workbook.create_sheet("Base_Fundos")
        base.append(["Fundo", "CNPJ", "Patrímonio Liquído ", "Receita Mensal ", "Gestor", "Consultoria", "Numbervalue"])
        base.append(["Fundo A", "11.111.111/0001-11", None, None, "Gestora A", "Consultoria A", 11111111000111])
        base.append(["Fundo C", "33.333.333/0001-33", None, None, "Gestora C", "Consultoria C", 33333333000133])

        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return SimpleUploadedFile(
            "base.xlsx",
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
