from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="UserFund",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("catalog_key", models.CharField(max_length=80)),
                ("fund_name", models.CharField(max_length=300)),
                ("cnpj", models.CharField(blank=True, max_length=24)),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="portfolio_funds",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["fund_name"]},
        ),
        migrations.AddConstraint(
            model_name="userfund",
            constraint=models.UniqueConstraint(fields=("user", "catalog_key"), name="unique_user_catalog_fund"),
        ),
    ]
