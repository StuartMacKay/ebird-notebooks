# pyright: reportArgumentType=false

import datetime
import re

from django.db import models
from django.utils.translation import gettext_lazy as _
from ebird.codes.locations import (
    is_country_code,
    is_state_code,
    is_county_code,
    is_location_code,
)


class ChecklistQuerySet(models.QuerySet):
    def for_country(self, code: str):
        if not is_country_code(code):
            raise ValueError("Unsupported country code: %s" % code)
        return self.filter(country__code=code)

    def for_region(self, code: str):
        if not is_state_code(code):
            raise ValueError("Unsupported state code: %s" % code)
        return self.filter(region__code=code)

    def for_district(self, code: str):
        if not is_county_code(code):
            raise ValueError("Unsupported county code: %s" % code)
        return self.filter(district__code=code)

    def for_location(self, identifier: str):
        if not is_location_code(identifier):
            raise ValueError("Unsupported location identifier: %s" % identifier)
        return self.filter(location__identifier=identifier)

    def for_identifier(self, identifier: str):
        return self.get(identifier=identifier)

    def for_date(self, date: datetime.date):
        return self.filter(date=date)

    def for_dates(self, start: datetime.date, end: datetime.date):
        return self.filter(date__gte=start).filter(date__lt=end)

    def for_protocol(self, code: str):
        if not re.match(r"P\d{2}", code):
            raise ValueError("Unsupported protocol: %s" % code)
        return self.filter(protocol_code=code)

    def for_observer(self, value: str):
        if re.match(r"obsr\d+", value):
            return self.filter(observer__identifier=value)
        else:
            return self.filter(observer__name__exact=value)

    def for_hotspots(self):
        return self.filter(location__hotspot=True)

    def complete(self):
        return self.filter(complete=True)


class ChecklistManager(models.Manager):

    def in_region_with_dates(self, code, start, end):
        return (
            self.get_queryset()
            .for_region(code)
            .for_dates(start, end)
            .select_related("location", "observer")
            .order_by("-started")
        )


class Checklist(models.Model):
    class Meta:
        verbose_name = _("checklist")
        verbose_name_plural = _("checklists")

    created = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_("The date and time the checklist was added to eBird"),
        verbose_name=_("created"),
    )

    edited = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_("The date and time the eBird checklist was last edited"),
        verbose_name=_("edited"),
    )

    identifier = models.TextField(
        unique=True,
        verbose_name=_("identifier"),
        help_text=_("The unique identifier for the checklist."),
    )

    country = models.ForeignKey(
        "checklists.Country",
        related_name="checklists",
        on_delete=models.PROTECT,
        verbose_name=_("country"),
        help_text=_("The country where the checklist was made."),
    )

    region = models.ForeignKey(
        "checklists.Region",
        related_name="checklists",
        on_delete=models.PROTECT,
        verbose_name=_("region"),
        help_text=_("The region where the checklist was made."),
    )

    district = models.ForeignKey(
        "checklists.District",
        blank=True,
        null=True,
        related_name="checklists",
        on_delete=models.PROTECT,
        verbose_name=_("district"),
        help_text=_("The district where the checklist was made."),
    )

    area = models.ForeignKey(
        "checklists.Area",
        blank=True,
        null=True,
        related_name="checklists",
        on_delete=models.PROTECT,
        verbose_name=_("area"),
        help_text=_("The area where the checklist was made."),
    )

    location = models.ForeignKey(
        "checklists.Location",
        related_name="checklists",
        on_delete=models.PROTECT,
        verbose_name=_("location"),
        help_text=_("The location where checklist was made."),
    )

    observer = models.ForeignKey(
        "checklists.Observer",
        related_name="checklists",
        on_delete=models.PROTECT,
        verbose_name=_("observer"),
        help_text=_("The person who submitted the checklist."),
    )

    group = models.TextField(
        blank=True,
        verbose_name=_("group"),
        help_text=_("The identifier for a group of observers."),
    )

    observer_count = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("observer count"),
        help_text=_("The total number of observers."),
    )

    species_count = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("species count"),
        help_text=_("The number of species reported."),
    )

    date = models.DateField(
        db_index=True,
        verbose_name=_("date"),
        help_text=_("The date the checklist was started."),
    )

    time = models.TimeField(
        blank=True,
        null=True,
        verbose_name=_("time"),
        help_text=_("The time the checklist was started."),
    )

    started = models.DateTimeField(
        blank=True,
        db_index=True,
        null=True,
        verbose_name=_("date & time"),
        help_text=_("The date and time the checklist was started."),
    )

    protocol = models.TextField(
        blank=True,
        verbose_name=_("protocol"),
        help_text=_("The protocol followed, e.g. travelling, stationary, etc."),
    )

    protocol_code = models.TextField(
        blank=True,
        verbose_name=_("protocol code"),
        help_text=_("The code used to identify the protocol."),
    )

    project_code = models.TextField(
        blank=True,
        verbose_name=_("project code"),
        help_text=_("The code used to identify the project (portal)."),
    )

    duration = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("duration"),
        help_text=_("The number of minutes spent counting."),
    )

    distance = models.DecimalField(
        blank=True,
        null=True,
        decimal_places=3,
        max_digits=6,
        verbose_name=_("distance"),
        help_text=_("The distance, in metres, covered while travelling."),
    )

    coverage = models.DecimalField(
        blank=True,
        null=True,
        decimal_places=3,
        max_digits=6,
        verbose_name=_("area"),
        help_text=_("The area covered, in hectares."),
    )

    complete = models.BooleanField(
        default=False,
        verbose_name=_("complete"),
        help_text=_("All species seen are reported."),
    )

    comments = models.TextField(
        blank=True,
        verbose_name=_("comments"),
        help_text=_("Any comments about the checklist."),
    )

    url = models.URLField(
        blank=True,
        verbose_name=_("url"),
        help_text=_("URL where the original checklist can be viewed."),
    )

    data = models.JSONField(
        verbose_name=_("Data"),
        help_text=_("Data describing a Checklist."),
        default=dict,
        blank=True,
    )

    objects = ChecklistManager.from_queryset(ChecklistQuerySet)()

    def __str__(self):
        return "%s %s, %s" % (self.date, self.time, self.location.name)
