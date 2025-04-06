# pyright: reportArgumentType=false

from django.db import models
from django.utils.translation import gettext_lazy as _


class District(models.Model):
    class Meta:
        verbose_name = _("district")
        verbose_name_plural = _("districts")

    code = models.CharField(
        max_length=10,
        db_index=True,
        verbose_name=_("code"),
        help_text=_("The code used to identify the district."),
    )

    name = models.TextField(
        verbose_name=_("name"), help_text=_("The name of the district.")
    )

    place = models.TextField(
        verbose_name=_("place"), help_text=_("The hierarchical name of the district.")
    )

    def __str__(self):
        return str(self.name)
