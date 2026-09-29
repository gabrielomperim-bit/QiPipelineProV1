from django.conf import settings
from django.db import models


class UserFund(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portfolio_funds")
    catalog_key = models.CharField(max_length=80)
    fund_name = models.CharField(max_length=300)
    cnpj = models.CharField(max_length=24, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "catalog_key"], name="unique_user_catalog_fund"),
        ]
        ordering = ["fund_name"]

    def __str__(self):
        return f"{self.user.username}: {self.fund_name}"
