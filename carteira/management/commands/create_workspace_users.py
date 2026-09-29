import secrets
import string

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


DEFAULT_USERS = {
    "kathleen": "Kathleen",
    "cristal": "Cristal",
    "julia": "Julia",
}


def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "Cria os usuarios iniciais do workspace e gera senhas temporarias."

    def add_arguments(self, parser):
        parser.add_argument("usernames", nargs="*", default=list(DEFAULT_USERS))
        parser.add_argument("--reset-passwords", action="store_true")

    def handle(self, *args, **options):
        user_model = get_user_model()
        credentials = []
        for username in options["usernames"]:
            normalized = username.strip().lower()
            if not normalized:
                continue
            user, created = user_model.objects.get_or_create(
                username=normalized,
                defaults={"first_name": DEFAULT_USERS.get(normalized, normalized.title())},
            )
            if created or options["reset_passwords"]:
                password = generate_password()
                user.set_password(password)
                user.save(update_fields=["password"])
                credentials.append((normalized, password))
                action = "criado" if created else "senha redefinida"
                self.stdout.write(self.style.SUCCESS(f"{normalized}: {action}"))
            else:
                self.stdout.write(f"{normalized}: ja existe (senha preservada)")

        if credentials:
            self.stdout.write("\nCredenciais temporarias — copie agora:")
            for username, password in credentials:
                self.stdout.write(f"  {username}: {password}")
