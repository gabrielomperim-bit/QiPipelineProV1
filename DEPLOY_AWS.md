# Deploy rapido em uma EC2

## Na EC2 Amazon Linux 2023

```bash
sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
exit
```

Reconecte antes de continuar. Clone o repositorio usando uma deploy key do GitHub:

```bash
git clone git@github.com:gabrielomperim-bit/QiPipelineProV1.git
cd QiPipelineProV1
git checkout develop
```

## Dados persistentes

```bash
mkdir -p persistent/data persistent/uploads
cp -a data/. persistent/data/
chmod -R u+rwX persistent
```

## Configuracao

Transforme o Elastic IP em hostname, substituindo os pontos por hifens. Exemplo:

```text
54.10.20.30 -> 54-10-20-30.sslip.io
```

Crie o arquivo local de ambiente:

```bash
cp .env.example .env
chmod 600 .env
```

Gere a chave Django:

```bash
openssl rand -hex 32
```

Gere um hash para cada senha (a senha nao fica salva no arquivo):

```bash
docker run --rm caddy:2-alpine caddy hash-password --plaintext 'SENHA-FORTE-AQUI'
```

Edite `.env`, substituindo dominio, chave, usuarios e os tres hashes:

```bash
nano .env
```

Mantenha os hashes entre aspas simples para preservar os caracteres `$`.

## Inicializacao

```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=100
```

Acesse `https://SEU-IP-COM-HIFENS.sslip.io`.

## Atualizacao

```bash
git pull --ff-only
docker compose up -d --build
docker image prune -f
```
