from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-only-secret-key-change-before-production"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "carteira",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# O projeto usa armazenamento em arquivos, entao o backend de banco fica desativado.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.dummy",
    }
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
CVM_CACHE_DIR = DATA_DIR / "cvm"
QITECH_MATCH_KEYWORDS = [
    "QITECH",
    "QI GESTAO",
    "QI GESTÃO",
    "QI CORRETORA",
    "QI DTVM",
    "QI DISTRIBUIDORA",
    "QI SOCIEDADE DE CREDITO",
]
QITECH_ENTITY_CNPJS = [
    "30620610000159",
]
PUBLIC_COMPANY_ENRICHMENT_URL = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
