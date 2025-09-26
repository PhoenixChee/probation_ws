import os
from ament_pep257.main import main
import pytest


@pytest.mark.linter
@pytest.mark.pep257
def test_pep257():
    rc = main(argv=['test', os.path.join(os.path.dirname(__file__), '..', '..')])
    assert rc == 0