from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, ClassVar

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from .cache import invalidate_directives_cache
from .constants import CSPDirective
from .typing import DirectiveMapping


class CSPSettingQuerySet(models.QuerySet["CSPSetting"]):
    def as_dict(self) -> DirectiveMapping:
        """
        Collect the CSP settings in the queryset into a directive mapping.

        Duplicate values for the same directive are collapsed, and both the
        directives and their values are sorted so that the result is stable.
        """
        # clear Meta.ordering avoid db sorting, which we do below
        unordered_directives = self.order_by()

        collected: defaultdict[str, set[str]] = defaultdict(set)
        for directive, value in unordered_directives.values_list("directive", "value"):
            collected[directive].add(value)
        return {
            directive: sorted(values) for directive, values in sorted(collected.items())
        }


class CSPSettingManager(models.Manager.from_queryset(CSPSettingQuerySet)):  # pyright: ignore[reportMissingTypeArgument]
    @transaction.atomic
    def set_for(
        self,
        obj: models.Model,
        settings: list[tuple[CSPDirective, str]],
        identifier: str = "",
    ) -> None:
        """
        Replace the CSP settings connected to ``obj`` with the provided ones.

        All existing settings for the object (and ``identifier``) are deleted before the
        new ones are created, making this safe to call repeatedly, e.g. from the
        ``save`` method of a configuration model.

        :param obj: The configuration model providing these CSP entries.
        :param settings: Two-tuples of the directive and value to create.
        :param identifier: An optional string to further identify the source of these
          CSP entries. Entries recorded under a different identifier are left alone.
        """
        instances = [
            CSPSetting(
                content_object=obj,
                directive=directive,
                value=value,
                identifier=identifier,
            )
            for directive, value in settings
        ]

        content_type = ContentType.objects.get_for_model(obj, for_concrete_model=False)
        self.filter(
            content_type=content_type,
            object_id=str(obj.pk),
            identifier=identifier,
        ).delete()

        self.bulk_create(instances)

        # ``bulk_create`` does not emit ``post_save``, so the cache must be dropped
        # explicitly here.
        invalidate_directives_cache()

    if TYPE_CHECKING:
        # ``from_queryset`` copies the queryset methods onto the manager and keeps
        # returning the custom queryset, but type checkers cannot see that.
        def as_dict(self) -> DirectiveMapping: ...

        def get_queryset(self) -> CSPSettingQuerySet: ...

        def filter(self, *args: object, **kwargs: object) -> CSPSettingQuerySet: ...


class CSPSetting(models.Model):
    directive = models.CharField(
        _("directive"),
        max_length=64,
        choices=CSPDirective.choices,
        help_text=_("CSP header directive."),
    )
    value = models.CharField(
        _("value"),
        max_length=255,
        help_text=_("CSP header value."),
    )

    identifier = models.CharField(
        _("identifier"),
        max_length=64,
        blank=True,
        help_text=_(
            "An optional free-form label recording where this entry came from. "
            "It is never sent to the browser."
        ),
    )

    # Generic relation fields used by CSPSettingManager.set_for
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("content type"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    object_id = models.TextField(
        verbose_name=_("object id"),
        blank=True,
        db_index=True,
    )
    content_object = GenericForeignKey("content_type", "object_id")

    objects: ClassVar[CSPSettingManager] = CSPSettingManager()  # pyright: ignore[reportIncompatibleVariableOverride]

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        verbose_name = _("CSP setting")
        verbose_name_plural = _("CSP settings")
        ordering = ("directive", "value")

    def __str__(self):
        return f"{self.directive} '{self.value}'"
