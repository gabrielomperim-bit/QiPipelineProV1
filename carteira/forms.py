from django import forms


class UploadCarteiraForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha da carteira",
        help_text="Aceita .csv e .xlsx.",
    )


class ClienteForm(forms.Form):
    nome = forms.CharField(label="Cliente", max_length=140)
    categoria = forms.ChoiceField(
        label="Categoria",
        choices=[
            ("gestora", "Gestora"),
            ("consultoria", "Consultoria"),
            ("banco", "Banco"),
            ("securitizadora", "Securitizadora"),
            ("outros", "Outros"),
        ],
    )
    receita_mensal = forms.DecimalField(
        label="Receita mensal",
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=14,
    )
    fonte_receita = forms.CharField(
        label="Fonte da receita",
        max_length=200,
        required=False,
        help_text="Ex.: site da CVM, planilha interna, contrato.",
    )
    observacoes = forms.CharField(
        label="Observacoes",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class FundoBuscaForm(forms.Form):
    consulta = forms.CharField(
        label="Buscar por nome do cliente/gestor/administrador",
        max_length=140,
        required=False,
    )
    somente_qi = forms.BooleanField(
        label="Mostrar apenas registros com sinais de relacionamento com a Qi",
        required=False,
        initial=True,
    )


class RegraReceitaForm(forms.Form):
    product_type = forms.CharField(
        label="Tipo de produto",
        max_length=160,
    )
    annual_fee_rate = forms.DecimalField(
        label="Taxa anual (%)",
        min_value=0,
        max_digits=8,
        decimal_places=4,
        help_text="Ex.: 1,2500 para 1,25% ao ano.",
    )
    notes = forms.CharField(
        label="Observacoes",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class FundoReceitaForm(forms.Form):
    fund_id = forms.CharField(widget=forms.HiddenInput())
    annual_fee_rate = forms.DecimalField(
        label="Taxa anual (%)",
        min_value=0,
        max_digits=8,
        decimal_places=4,
    )


class ContatoForm(forms.Form):
    nome = forms.CharField(label="Nome", max_length=140)
    cargo = forms.ChoiceField(
        label="Cargo",
        choices=[
            ("co", "CO"),
            ("chefe", "Chefe"),
            ("gerente", "Gerente"),
            ("outro", "Outro"),
        ],
    )
    area = forms.CharField(label="Area", max_length=140, required=False)
    email = forms.EmailField(label="E-mail", required=False)
    telefone = forms.CharField(label="Telefone", max_length=40, required=False)
    linkedin = forms.URLField(label="LinkedIn", required=False)
    observacoes = forms.CharField(
        label="Observacoes",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class ClienteQiBuscaForm(forms.Form):
    consulta = forms.CharField(
        label="Pesquisar cliente",
        max_length=140,
        required=False,
        help_text="Busque por nome, CNPJ ou categoria.",
    )
