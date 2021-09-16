import pytest

from ckan.tests import factories

from ckanext.issues.tests import factories as issue_factories
from ckanext.issues.lib.util import issue_count, issue_comments, issue_comment_count
from ckanext.issues.tests.fixtures import issues_setup

@pytest.fixture
def org():
    return factories.Organization()

@pytest.fixture
def dataset(org):
    return factories.Dataset(owner_org=org['id'])

@pytest.fixture
def issue(dataset):
    return issue_factories.Issue(dataset_id=dataset['id'])

@pytest.fixture
def comment1(issue):
    comment1 = issue_factories.IssueComment(
                issue_number=issue['number'],
                dataset_id=issue['dataset_id'],
        )
    return comment1

@pytest.fixture
def comment2(issue):
    comment2 = issue_factories.IssueComment(
                issue_number=issue['number'],
                dataset_id=issue['dataset_id'],
        )
    return comment2

@pytest.fixture
def comment3(issue):
    comment3 = issue_factories.IssueComment(
                issue_number=issue['number'],
                dataset_id=issue['dataset_id'],
        )
    return comment3

@pytest.fixture
def comments(comment1, comment2, comment3):
    return [comment1, comment2, comment3]

class TestUtils(object):

    @pytest.mark.usefixtures("clean_db", "issues_setup", "issue")
    def test_issue_count(self, dataset):
        assert issue_count(dataset) == 1

    @pytest.mark.usefixtures("clean_db", "issues_setup", "comments")
    def test_issue_comment_count(self, issue):
        assert issue_comment_count(issue) == 3

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_comments(self, issue, comment1, comment2, comment3):
        comments_is = issue_comments(issue)
        assert [comment1['id'], comment2['id'], comment3['id']] ==\
               [comment.id for comment in comments_is]
