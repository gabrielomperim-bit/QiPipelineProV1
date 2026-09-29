from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.urls import path
from django.urls import reverse_lazy

from . import views

urlpatterns = [
    path("entrar/", login_not_required(auth_views.LoginView.as_view(template_name="registration/login.html")), name="login"),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "minha-senha/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change.html",
            success_url=reverse_lazy("minha_carteira"),
        ),
        name="password_change",
    ),
    path("", views.catalogo_fundos, name="home"),
    path("visao-geral/", views.dashboard, name="dashboard"),
    path("dashboard/usuario/", views.dashboard_usuario, name="dashboard_usuario"),
    path("dashboard/comercial/", views.analise_comercial, name="analise_comercial"),
    path("clientes/", views.lista_clientes, name="lista_clientes"),
    path("fundos/", views.catalogo_fundos, name="catalogo_fundos"),
    path("minha-carteira/", views.minha_carteira, name="minha_carteira"),
    path("minha-carteira/exportar/", views.exportar_minha_carteira_excel, name="exportar_minha_carteira_excel"),
    path("fundos/minha-carteira/alternar/", views.alternar_fundo_carteira, name="alternar_fundo_carteira"),
    path("fundos/minha-carteira/adicionar/", views.adicionar_fundos_carteira, name="adicionar_fundos_carteira"),
    path("fundos/exportar/", views.exportar_fundos_excel, name="exportar_fundos_excel"),
    path("importar/", views.importar_carteira, name="importar_carteira"),
    path("cvm/", views.sincronizar_cvm, name="sincronizar_cvm"),
    path("cvm/clientes-qi/", views.clientes_qi_descobertos, name="clientes_qi_descobertos"),
    path("receita/regras/", views.regras_receita, name="regras_receita"),
    path("receita/regras/<str:product_type>/remover/", views.remover_regra_receita, name="remover_regra_receita"),
    path("clientes/novo/", views.novo_cliente, name="novo_cliente"),
    path("clientes/<str:client_id>/", views.detalhe_cliente, name="detalhe_cliente"),
    path("clientes/<str:client_id>/categoria/", views.atualizar_categoria_cliente, name="atualizar_categoria_cliente"),
    path("clientes/<str:client_id>/usuario/", views.alternar_cliente_usuario, name="alternar_cliente_usuario"),
    path("clientes/<str:client_id>/buscar-fundos/", views.buscar_fundos_cliente, name="buscar_fundos_cliente"),
    path("clientes/<str:client_id>/vincular-fundo/", views.vincular_fundo_cliente, name="vincular_fundo_cliente"),
    path("clientes/<str:client_id>/atualizar-receita-fundo/", views.atualizar_receita_fundo, name="atualizar_receita_fundo"),
    path("clientes/<str:client_id>/fundos/<str:fund_id>/usuario/", views.alternar_fundo_usuario, name="alternar_fundo_usuario"),
    path("clientes/<str:client_id>/adicionar-contato/", views.adicionar_contato_cliente, name="adicionar_contato_cliente"),
    path("clientes/<str:client_id>/enriquecer/", views.enriquecer_cliente, name="enriquecer_cliente"),
    path("clientes/<str:client_id>/remover/", views.remover_cliente, name="remover_cliente"),
]
