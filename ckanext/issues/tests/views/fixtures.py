
import pytest

import ckan.model as model


from ckanext.issues import model


@pytest.fixture
def issues_setup():
    model.setup()