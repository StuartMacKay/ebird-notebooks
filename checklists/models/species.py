# pyright: reportArgumentType=false

from django.db import models
from django.utils.translation import gettext_lazy as _


SPECIES_CATEGORY = {
    "species": _("Species"),
    "sub-species": _("Sub-species"),
    "hybrid": _("Hybrid"),
    "intergrade": _("Intergrade"),
    "spuh": _("Genus"),
    "slash": _("Species group"),
    "domestic": _("Domestic"),
    "form": _("Form"),
}

EXOTIC_CODE = {
    "": "",  # NATIVE
    "N": _("Naturalized"),
    "P": _("Provisional"),
    "X": _("Escapee"),
}


class SpeciesQuerySet(models.QuerySet):
    pass


class Species(models.Model):
    class Meta:
        verbose_name = _("species")
        verbose_name_plural = _("species")

    taxon_order = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("taxonomy order"),
        help_text=_("The position in the eBird/Clements taxonomic order."),
    )

    order = models.TextField(
        blank=True,
        verbose_name=_("order"),
        help_text=_(
            "The order, e.g. Struthioniformes, from the eBird/Clements taxonomy."
        ),
    )

    category = models.TextField(
        blank=True,
        verbose_name=_("category"),
        help_text=_("The category from the eBird/Clements taxonomy."),
    )

    species_code = models.TextField(
        blank=True,
        verbose_name=_("species code"),
        help_text=_("The species code, e.g. ostric2, used in the eBird API."),
    )

    family_code = models.TextField(
        blank=True,
        verbose_name=_("family code"),
        help_text=_("The family code, e.g. struth1, used in the eBird API."),
    )

    common_name = models.TextField(
        verbose_name=_("common name"),
        help_text=_("The species common name in the eBird/Clements taxonomy."),
    )

    scientific_name = models.TextField(
        verbose_name=_("scientific name"),
        help_text=_("The species scientific name in the eBird/Clements taxonomy."),
    )

    family_common_name = models.TextField(
        blank=True,
        verbose_name=_("family common name"),
        help_text=_(
            "The common name for the species family in the eBird/Clements taxonomy."
        ),
    )

    family_scientific_name = models.TextField(
        blank=True,
        verbose_name=_("family scientific name"),
        help_text=_(
            "The scientific name for the species family in the eBird/Clements taxonomy."
        ),
    )

    subspecies_common_name = models.TextField(
        blank=True,
        verbose_name=_("subspecies common name"),
        help_text=_(
            "The subspecies, group or form common name in the eBird/Clements taxonomy."
        ),
    )

    subspecies_scientific_name = models.TextField(
        blank=True,
        verbose_name=_("Scientific name"),
        help_text=_(
            "The subspecies, group or form scientific name in the eBird/Clements taxonomy."
        ),
    )

    exotic_code = models.TextField(
        blank=True,
        verbose_name=_("exotic code"),
        help_text=_("The code used if the species is non-native."),
    )

    data = models.JSONField(
        verbose_name=_("Data"),
        help_text=_("Data describing a Species."),
        default=dict,
        blank=True,
    )

    objects = SpeciesQuerySet.as_manager()  # pyright: ignore [reportCallIssue]

    def __str__(self):
        return str(self.subspecies_common_name or self.common_name)

    def is_identified(self) -> bool:
        return self.category in ["species", "sub-species", "domestic"]
