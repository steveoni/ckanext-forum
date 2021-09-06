import pytest
import bs4

from ckan.plugins import toolkit
from ckan.tests import helpers
from ckan.tests import factories

from ckanext.issues import model as issue_model
from ckanext.issues.tests import factories as issue_factories
from ckanext.issues.tests.fixtures import issues_setup, owner


@pytest.fixture
def org(owner):
    return factories.Organization(user=owner)

@pytest.fixture
def dataset(owner, org):
    return factories.Dataset(user=owner, owner_org=org['name'])


class TestSearchBox(object):
    @pytest.fixture
    def issue(self, owner, dataset):
        return issue_factories.Issue(user=owner,
                                user_id=owner['id'],
                                dataset_id=dataset['id'])

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_search_box_appears_issue_dataset_page(self, app, dataset, issue):
        response = app.get(toolkit.url_for('issues.dataset',
                                        dataset_id=dataset['id'],
                                        issue_number=issue['number']),
        )

        soup = bs4.BeautifulSoup(response.body)
        edit_button = soup.find('form', {'class': 'search-form'})
        assert edit_button is not None

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_search_box_submits_q_get(self, app, owner, dataset, issue):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        in_search = [issue_factories.Issue(user_id=owner['id'],
                                           dataset_id=dataset['id'],
                                           title=title)
                     for title in ['some titLe', 'another Title']]

        # some issues not in the search
        [issue_factories.Issue(user_id=owner['id'],
                               dataset_id=dataset['id'],
                               title=title)
         for title in ['blah', 'issue']]

        submit_form = app.get(toolkit.url_for('issues.dataset',
                                    q='title',
                                    dataset_id=dataset['id'],
                                    issue_number=issue['number']),
            extra_environ=env,
        )
        soup = bs4.BeautifulSoup(submit_form.body)
        issue_links = soup.find(id='issue-list').find_all('h4')
        titles = set([i.a.text.strip() for i in issue_links])
        assert set([i['title'] for i in in_search]) == titles


class TestSearchFilters(object):
    @pytest.fixture
    def issues(self, owner, dataset):
        issues = {
            'visible': issue_factories.Issue(user=owner,
                                             title='visible_issue',
                                             dataset_id=dataset['id']),
            'closed': issue_factories.Issue(user=owner,
                                            title='closed_issue',
                                            dataset_id=dataset['id']),
            'hidden': issue_factories.Issue(user=owner,
                                            title='hidden_issue',
                                            dataset_id=dataset['id'],
                                            visibility='hidden'),
        }
        # close our issue
        helpers.call_action('issue_update',
                            issue_number=issues['closed']['number'],
                            dataset_id=dataset['id'],
                            context={'user': owner['name']},
                            status='closed'
        )
        issue = issue_model.Issue.get(issues['hidden']['id'])
        issue.visibility = 'hidden'
        issue.save()
        return issues

    @pytest.mark.usefixtures("clean_db", "issues_setup", "issues")
    def test_click_visiblity_links(self, app, owner, dataset):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.dataset',
                                            dataset_id=dataset['id']),
            extra_environ=env,
        )

        # visible and hidden should be shown, but not closed
        assert '2 issues found' in response
        assert 'visible_issue' in response
        assert 'hidden_issue' in response
        assert 'closed_issue' not in response

        # click the hidden filter
        response = app.get(toolkit.url_for('issues.dataset',
                                            visibility='hidden',
                                            dataset_id=dataset['id']),
            extra_environ=env,
        )
        assert '1 issue found' in response
        assert 'visible_issue' not in response
        assert 'hidden_issue' in response
        assert 'closed_issue' not in response

        # click the visible filter
        response = app.get(toolkit.url_for('issues.dataset',
                                            visibility='visible',
                                            dataset_id=dataset['id']),
            extra_environ=env,
        )
        assert '1 issue found' in response
        assert 'visible_issue' in response
        assert 'hidden_issue' not in response
        assert 'closed_issue' not in response

#         # clear the filter by clikcing on visible again
#         response = response.click(linkid='visible-filter', extra_environ=env)
#         assert_in('2 issues found', response)
#         assert_in('visible_issue', response)
#         assert_in('hidden_issue', response)
#         assert_not_in('closed_issue', response)

    @pytest.mark.usefixtures("clean_db", "issues_setup", "issues")
    def test_click_status_links(self, app, owner, dataset):
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.dataset',
                                dataset_id=dataset['id']),
            extra_environ=env,
        )
        # visible and hidden should be shown, but not closed
        assert '2 issues found' in response
        assert 'visible_issue' in response
        assert 'hidden_issue' in response
        assert 'closed_issue' not in response

        # click the closed filter
        response = app.get(toolkit.url_for('issues.dataset',
                                status='closed',
                                dataset_id=dataset['id']),
            extra_environ=env,
        )
        assert '1 issue found' in response
        assert 'visible_issue' not in response
        assert 'hidden_issue' not in response
        assert 'closed_issue' in response

        # click the open filter
        response = app.get(toolkit.url_for('issues.dataset',
                                status='open',
                                dataset_id=dataset['id']),
            extra_environ=env,
        )
        assert '2 issues found' in response
        assert 'visible_issue' in response
        assert 'hidden_issue' in response
        assert 'closed_issue' not in response

    @pytest.mark.usefixtures("clean_db", "issues_setup", "issues")
    def test_visiblity_links_do_not_appear_for_unauthed_user(self, app, dataset):
        response = app.get(toolkit.url_for('issues.dataset',
                                dataset_id=dataset['id']),
        )
        assert 'filter-hidden' not in response
        assert 'filter-visible' not in response
