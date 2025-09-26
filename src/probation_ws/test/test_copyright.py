import os
from ament_copyright.main import main
import pytest


@pytest.mark.copyright
@pytest.mark.linter
def test_copyright():
    rc = main(argv=['test', os.path.join(os.path.dirname(__file__), '..', '..')])
    assert rc == 0