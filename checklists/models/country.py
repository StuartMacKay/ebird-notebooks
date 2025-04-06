# pyright: reportArgumentType=false

from django.db import models
from django.utils.translation import gettext_lazy as _


class Country(models.Model):
    class Meta:
        verbose_name = _("country")
        verbose_name_plural = _("countries")

    code = models.CharField(
        max_length=2,
        db_index=True,
        verbose_name=_("code"),
        help_text=_("The code used to identify the country."),
    )

    name = models.TextField(
        verbose_name=_("name"), help_text=_("The name of the country.")
    )

    place = models.TextField(
        verbose_name=_("place"), help_text=_("The hierarchical name of the country.")
    )

    def __str__(self):
        return str(self.name)
