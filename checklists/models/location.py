# pyright: reportArgumentType=false

import re

from django.db import models
from django.utils.translation import gettext_lazy as _

LOCATION_TYPE = {
    "C": _("County"),
    "H": _("Hotspot"),
    "P": _("Personal"),
    "PC": _("Postal/Zip Code"),
    "S": _("State"),
    "T": _("Town"),
}


class LocationQuerySet(models.QuerySet):
    def for_country(self, code: str):
        if not re.match(r"[A-Z]{2}", code):
            raise ValueError("Unsupported country code: %s" % code)
        return self.filter(country__code=code)

    def for_region(self, code: str):
        if not re.match(r"[A-Z]{2}-[A-Z0-9]{2,3}", code):
            raise ValueError("Unsupported state code: %s" % code)
        return self.filter(region__code=code)

    def for_district(self, code: str):
        if not re.match(r"[A-Z]{2}-[A-Z0-9]{2,3}-[A-Z0-9]{2,3}", code):
            raise ValueError("Unsupported county code: %s" % code)
        return self.filter(district__code=code)

    def for_identifier(self, identifier: str):
        return self.get(identifier=identifier)


class Location(models.Model):
    class Meta:
        verbose_name = _("location")
        verbose_name_plural = _("locations")

    identifier = models.TextField(
        unique=True,
        verbose_name=_("identifier"),
        help_text=_("The unique identifier for the location"),
    )

    type = models.TextField(
        blank=True,
        verbose_name=_("type"),
        help_text=_("The location type, e.g. personal, hotspot, town, etc."),
    )

    name = models.TextField(
        verbose_name=_("name"), help_text=_("The name of the location")
    )

    country = models.ForeignKey(
        "checklists.Country",
        related_name="locations",
        on_delete=models.PROTECT,
        verbose_name=_("country"),
        help_text=_("The country for the location."),
    )

    region = models.ForeignKey(
        "checklists.Region",
        related_name="locations",
        on_delete=models.PROTECT,
        verbose_name=_("region"),
        help_text=_("The region for the location."),
    )

    district = models.ForeignKey(
        "checklists.District",
        blank=True,
        null=True,
        related_name="locations",
        on_delete=models.PROTECT,
        verbose_name=_("district"),
        help_text=_("The district for the location."),
    )

    area = models.ForeignKey(
        "checklists.Area",
        blank=True,
        null=True,
        related_name="locations",
        on_delete=models.PROTECT,
        verbose_name=_("area"),
        help_text=_("The area for the location."),
    )

    iba_code = models.TextField(
        blank=True,
        verbose_name=_("IBA code"),
        help_text=_("The code used to identify an Important Bird Area."),
    )

    bcr_code = models.TextField(
        blank=True,
        verbose_name=_("BCR code"),
        help_text=_("The code used to identify a Bird Conservation Region."),
    )

    usfws_code = models.TextField(
        blank=True,
        verbose_name=_("USFWS code"),
        help_text=_("The code used to identify a US Fish & Wildlife Service region."),
    )

    atlas_block = models.TextField(
        blank=True,
        verbose_name=_("atlas block"),
        help_text=_("The code used to identify an area for an atlas."),
    )

    latitude = models.DecimalField(
        blank=True,
        null=True,
        decimal_places=7,
        max_digits=9,
        verbose_name=_("latitude"),
        help_text=_("The decimal latitude of the location, relative to the equator"),
    )

    longitude = models.DecimalField(
        blank=True,
        null=True,
        decimal_places=7,
        max_digits=10,
        verbose_name=_("longitude"),
        help_text=_(
            "The decimal longitude of the location, relative to the prime meridian"
        ),
    )

    url = models.URLField(
        blank=True,
        verbose_name=_("url"),
        help_text=_("URL of the location page on eBird."),
    )

    hotspot = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_("is hotspot"),
        help_text=_("Is the location a hotspot"),
    )

    data = models.JSONField(
        verbose_name=_("Data"),
        help_text=_("Data describing a Location"),
        default=dict,
        blank=True,
    )

    objects = LocationQuerySet.as_manager()  # pyright: ignore [reportCallIssue]

    def __str__(self):
        return str(self.name)
