import pytest

from ..utils import is_dependency_installed

pytestmark = [
    pytest.mark.skipif(
        not is_dependency_installed("structlog"), reason="Structlog not installed"
    ),
]
