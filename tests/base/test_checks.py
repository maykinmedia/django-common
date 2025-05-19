from pathlib import Path

from django.core.checks import Error, Warning
from django.forms import ModelForm

from maykin_common.checks import check_missing_init_files, check_modelform_exclude


def test_check_modelform_exclude(settings):
    settings.DJANGO_PROJECT_DIR = settings.BASE_DIR

    class DummyForm(ModelForm):
        class Meta:
            exclude = ("id",)  # noqa DJ006

    errors = check_modelform_exclude(None)

    assert errors == [
        Error(
            "ModelForm tests.base.test_checks.DummyForm with Meta.exclude detected, "
            "this is a bad practice",
            hint="Use ModelForm.Meta.fields instead",
            obj=DummyForm,
            id="maykin.E001",
        )
    ]


def test_check_missing_init_files(settings):
    settings.DJANGO_PROJECT_DIR = Path(__file__).resolve().parent

    errors = check_missing_init_files(None)

    assert errors == [
        Warning(
            f"Directory {Path(__file__).resolve().parent}/missing_init does not "
            "contain an `__init__.py` file missing_init",
            hint="Consider adding this module to make sure tests are picked up",
            id="maykin.W001",
        )
    ]
