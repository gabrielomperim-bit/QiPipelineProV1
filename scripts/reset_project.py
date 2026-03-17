from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reinicia os dados locais do projeto para uso por outro usuario."
    )
    parser.add_argument(
        "--mode",
        choices=["keep-cvm", "full"],
        default="keep-cvm",
        help="keep-cvm limpa os dados locais e preserva a base CVM; full limpa tudo, incluindo cache CVM.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra o que seria limpo sem alterar arquivos.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()

    from carteira.services.data_store import reset_storage

    clear_cvm_cache = args.mode == "full"
    targets = [
        "data/clients.csv",
        "data/funds.csv",
        "data/revenue_rules.csv",
        "data/contacts.csv",
        "data/company_profiles.csv",
        "uploads/*",
    ]
    if clear_cvm_cache:
        targets.append("data/cvm/*")

    print("Reinicio do projeto")
    print(f"Modo: {'com limpeza da CVM' if clear_cvm_cache else 'preservando base CVM'}")
    print("Arquivos afetados:")
    for target in targets:
        print(f"- {target}")

    if args.dry_run:
        print("\nDry-run concluido. Nenhum arquivo foi alterado.")
        return 0

    result = reset_storage(clear_cvm_cache=clear_cvm_cache, clear_uploads=True)
    print("\nProjeto reiniciado com sucesso.")
    print(f"CSV limpos: {', '.join(result['cleared_files'])}")
    print(f"Uploads removidos: {result['removed_uploads']}")
    if clear_cvm_cache:
        print(f"Arquivos CVM removidos: {result['removed_cvm_files']}")
        print("Na proxima abertura, sera preciso sincronizar a CVM novamente.")
    else:
        print("A base CVM foi preservada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
