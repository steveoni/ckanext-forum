import pytest
import bs4

from ckan.plugins import toolkit
from ckan.tests import helpers
from ckan.tests import factories

from ckanext.issues.tests import factories as issue_factories
from ckanext.issues import model as issue_model
from ckanext.issues.tests.fixtures import issues_setup, owner
from nose.tools import (assert_is_not_none, assert_equals, assert_in,
                        assert_not_in)

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

        issue_dataset = app.get(toolkit.url_for('issues.dataset',
                                    dataset_id=dataset['id'],
                                    issue_number=issue['number']),
            extra_environ=env,
        )

        search_form = bs4.BeautifulSoup(issue_dataset.body).\
            find('form', class_="search-form")
        print(search_form)
        search_form['q'] = 'title'

        res = issue_dataset
        print(res)
        soup = bs4.BeautifulSoup(res.body)
        issue_links = soup.find(id='issue-list').find_all('h4')
        titles = set([i.a.text.strip() for i in issue_links])
        assert set([i['title'] for i in in_search]) == titles


class TestSearchFilters(object):

        # self.issues = {
        #     'visible': issue_factories.Issue(user=self.owner,
        #                                      title='visible_issue',
        #                                      dataset_id=self.dataset['id']),
        #     'closed': issue_factories.Issue(user=self.owner,
        #                                     title='closed_issue',
        #                                     dataset_id=self.dataset['id']),
        #     'hidden': issue_factories.Issue(user=self.owner,
        #                                     title='hidden_issue',
        #                                     dataset_id=self.dataset['id'],
        #                                     visibility='hidden'),
        # }
        # # close our issue
        # helpers.call_action(
        #     'issue_update',
        #     issue_number=self.issues['closed']['number'],
        #     dataset_id=self.dataset['id'],
        #     context={'user': self.owner['name']},
        #     status='closed'
        # )
        # issue = issue_model.Issue.get(self.issues['hidden']['id'])
        # issue.visibility = 'hidden'
        # issue.save()
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

    # @pytest.mark.usefixtures("clean_db", "issues_setup", "issues")
    # def test_click_visiblity_links(self, app, owner, dataset):
    #     env = {'REMOTE_USER': owner['name'].encode('ascii')}
    #     response = app.get(toolkit.url_for('issues.dataset',
    #                                         dataset_id=dataset['id']),
    #         extra_environ=env,
    #     )
    #     #response = vars(response)
    #     soup = bs4.BeautifulSoup(response.data)
    #     print(dir(response))
    #     print(soup)
    #     # visible and hidden should be shown, but not closed
    #     assert '2 issues found' in soup
    #     assert 'visible_issue' in soup
    #     assert 'hidden_issue' in soup
    #     assert 'closed_issue' not in soup

#         # click the hidden filter
#         response = response.click(linkid='hidden-filter', extra_environ=env)
#         assert_in('1 issue found', response)
#         assert_not_in('visible_issue', response)
#         assert_in('hidden_issue', response)
#         assert_not_in('closed_issue', response)

#         # click the visible filter
#         response = response.click(linkid='visible-filter', extra_environ=env)
#         assert_in('1 issue found', response)
#         assert_in('visible_issue', response)
#         assert_not_in('hidden_issue', response)
#         assert_not_in('closed_issue', response)

#         # clear the filter by clikcing on visible again
#         response = response.click(linkid='visible-filter', extra_environ=env)
#         assert_in('2 issues found', response)
#         assert_in('visible_issue', response)
#         assert_in('hidden_issue', response)
#         assert_not_in('closed_issue', response)

#     def test_click_status_links(self):
#         env = {'REMOTE_USER': self.owner['name'].encode('ascii')}
#         response = self.app.get(
#             url=toolkit.url_for('issues_dataset',
#                                 dataset_id=self.dataset['id']),
#             extra_environ=env,
#         )
#         # visible and hidden should be shown, but not closed
#         assert_in('2 issues found', response)
#         assert_in('visible_issue', response)
#         assert_in('hidden_issue', response)
#         assert_not_in('closed_issue', response)

#         # click the closed filter
#         response = response.click(linkid='closed-filter', extra_environ=env)
#         assert_in('1 issue found', response)
#         assert_not_in('visible_issue', response)
#         assert_not_in('hidden_issue', response)
#         assert_in('closed_issue', response)

#         # click the open filter
#         response = response.click(linkid='open-filter', extra_environ=env)
#         assert_in('2 issues found', response)
#         assert_in('visible_issue', response)
#         assert_in('hidden_issue', response)
#         assert_not_in('closed_issue', response)

#     def test_visiblity_links_do_not_appear_for_unauthed_user(self):
#         response = self.app.get(
#             url=toolkit.url_for('issues_dataset',
#                                 dataset_id=self.dataset['id']),
#         )
#         assert_not_in('filter-hidden', response)
#         assert_not_in('filter-visible', response)
