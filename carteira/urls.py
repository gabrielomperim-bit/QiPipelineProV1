from django.urls import path

from . import views

urlpatterns = [
    path("", views.catalogo_fundos, name="home"),
    path("visao-geral/", views.dashboard, name="dashboard"),
    path("dashboard/usuario/", views.dashboard_usuario, name="dashboard_usuario"),
    path("dashboard/comercial/", views.analise_comercial, name="analise_comercial"),
    path("clientes/", views.lista_clientes, name="lista_clientes"),
    path("fundos/", views.catalogo_fundos, name="catalogo_fundos"),
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
