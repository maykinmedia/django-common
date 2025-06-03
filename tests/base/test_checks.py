from pathlib import Path

from django.core.checks import Warning

from maykin_common.checks import check_missing_init_files


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
