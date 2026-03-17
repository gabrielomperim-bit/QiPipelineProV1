# QiPipelineProV1

Base inicial de um gestor local de carteiras em Django, pensado para uso simples no computador de uma pessoa nao tecnica.

## O que ja existe

- Dashboard com resumo da carteira por categoria.
- Cadastro manual de clientes.
- Importacao de planilhas `.csv` e `.xlsx`.
- Persistencia em arquivos `CSV`, sem banco de dados.
- Sincronizacao manual com os dados abertos da CVM.
- Busca e vinculacao de fundos por cliente a partir da base local sincronizada.
- Calculo automatico de receita mensal por fundo com base em regra local de taxa anual.

## Estrutura de dados

Os dados ficam na pasta `data/`:

- `data/clients.csv`: clientes da carteira.
- `data/funds.csv`: fundos associados aos clientes.

## Formatos de importacao aceitos

### 1. Planilha em colunas por categoria

Exemplo:

| Gestora | Consultoria | Banco | Securitizadora | Outros |
| --- | --- | --- | --- | --- |
| Alpha Asset | Consult Prime | Banco Horizonte | Securi XPTO | Cliente avulso |

### 2. Tabela padrao

Colunas sugeridas:

- `cliente`
- `categoria`
- `receita mensal`
- `fonte_receita`
- `observacoes`


## Como rodar localmente

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py runserver
```

Depois, abra `http://127.0.0.1:8000/`.

Se quiser deixar facil para a usuaria final:

- Primeira instalacao: `scripts\instalar_primeira_vez.bat`
- Uso diario: `scripts\abrir_qi_pipeline.bat`
- Reiniciar para outro usuario: `scripts\reiniciar_projeto.bat`

## Reiniciar o projeto do zero

Quando quiser limpar o projeto para outro usuario, execute:

- `scripts\reiniciar_projeto.bat`

O script oferece 2 modos:

- `1`: limpa clientes, fundos, contatos, regras e uploads, mas preserva a base CVM ja sincronizada.
- `2`: limpa tudo, incluindo os arquivos da CVM, exigindo nova sincronizacao depois.

## Proximos passos recomendados

1. Criar a rotina de consulta dos fundos na CVM.
2. Relacionar clientes com os fundos encontrados.
3. Enriquecer a receita mensal por tipo de produto.
4. Gerar um executavel simples para a usuaria final abrir com duplo clique.

## Fonte de dados da CVM

Documentei a proxima etapa em `docs/cvm-roadmap.md`.

## Novo fluxo de fundos CVM

1. Abra `Sincronizar CVM`.
2. Baixe a base oficial mais recente.
3. Entre no cliente desejado.
4. Use `Buscar fundos na CVM`.
5. Vincule os fundos encontrados a esse cliente.

## Calculo de receita mensal

1. Abra `Regras de receita`.
2. Cadastre a taxa anual para cada tipo de produto.
3. O sistema calcula a receita mensal do fundo com a formula `PL x taxa anual / 12`.
4. A receita do cliente passa a ser a soma das receitas dos fundos vinculados.
