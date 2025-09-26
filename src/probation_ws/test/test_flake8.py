import os
from ament_flake8.main import main_with_errors
import pytest


@pytest.mark.flake8
@pytest.mark.linter
def test_flake8():
    rc, errors = main_with_errors(argv=['test', os.path.join(os.path.dirname(__file__), '..', '..')])
    assert rc == 0, \
        'Found %d error(s), %d warning(s) in %d file(s) scanned.' % \
        (errors.count('ERROR'), errors.count('WARNING'), len(errors))