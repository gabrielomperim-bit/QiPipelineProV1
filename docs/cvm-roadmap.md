# Roadmap de integracao com CVM

## Recomendacao de fonte

Para a fase de enriquecimento dos dados, a fonte mais segura nao e raspar a tela do `CVMWeb/SWB`, e sim consumir os arquivos oficiais do Portal de Dados Abertos da CVM.

Motivos:

- O conjunto `Fundos de Investimento: Documentos: Informe Diario` traz patrimonio liquido, valor da cota, captacoes, resgates e numero de cotistas.
- A atualizacao e diaria.
- O portal expõe arquivos em `csv` compactado, mais estaveis para automacao do que uma tela HTML antiga.

## O que buscar em cada fonte

### Cadastro/base de consulta

Usar a consulta publica da CVM ou os datasets cadastrais para localizar:

- nome do fundo
- CNPJ
- situacao do fundo
- administrador
- gestor

### Informe diario

Usar para enriquecer com:

- patrimonio liquido (PL)
- data do PL
- numero de cotistas
- serie historica util para validacoes

## Observacao sobre receita mensal

A `receita mensal` do cliente ou do fundo normalmente nao aparece de forma direta na base publica da CVM. Em geral, isso precisa ser:

- calculado a partir de regra comercial interna, como `PL x fee rate / 12`
- ou importado de planilha/contrato interno

Por isso, a recomendacao tecnica e manter no sistema:

- `PL` vindo da CVM
- `fee rate` informado manualmente ou por planilha interna
- `receita mensal calculada`
- `fonte da receita` para auditoria

## Proxima implementacao sugerida

1. Criar um servico que baixa o arquivo mais recente do Informe Diario.
2. Indexar por CNPJ do fundo.
3. Permitir vincular varios fundos a um cliente.
4. Calcular receita mensal por tipo de produto usando uma tabela local de regras.

