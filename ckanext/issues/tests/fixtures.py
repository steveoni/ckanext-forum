
import pytest

import ckan.model as model
from ckan.tests import factories

from ckanext.issues import model

@pytest.fixture
def issues_setup():
    model.setup()

@pytest.fixture
def user():
    return factories.User()

@pytest.fixture
def owner():
    return factories.User()
