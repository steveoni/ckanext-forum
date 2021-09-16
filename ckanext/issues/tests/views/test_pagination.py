from math import ceil
from urllib.parse import urlparse, parse_qs

import pytest
from bs4 import BeautifulSoup

from ckan.plugins import toolkit
from ckan.tests import factories

from ckanext.issues.lib.helpers import ISSUES_PER_PAGE
from ckanext.issues.tests import factories as issue_factories
from ckanext.issues.tests.fixtures import issues_setup, owner

def number_of_pages(items, per_page):
    return int(ceil(items / float(per_page)))


class TestPagination(object):
    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)

    @pytest.fixture
    def dataset(self, owner, org):
        return factories.Dataset(user=owner, owner_org=org['name'])

    @pytest.fixture
    def issues(self, owner, dataset):
        issues = [issue_factories.Issue(user=owner,dataset_id=dataset['id'])
            for x in range(0, 51)
        ]
        return issues


    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_click_per_page_link(self, app, dataset, issues):
        for per_page in ISSUES_PER_PAGE:
            response = app.get(toolkit.url_for('issues.dataset',
                dataset_id=dataset['id'], sort='oldest', per_page=per_page),
        )
            for i in issues[:per_page]:
                assert i['title'] in response.body
            for i in issues[per_page:]:
                assert i['title'] not in response.body

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_next_button(self, app, dataset, issues):
        for per_page in ISSUES_PER_PAGE:
            response = app.get(toolkit.url_for('issues.dataset',
                    dataset_id=dataset['id'],
                    sort='oldest',
                    per_page=per_page
                ),
            )
            self.click_through_all_pages_using_next_button(app, response, 
                                                            per_page, issues, dataset)

    def click_through_all_pages_using_next_button(self, app, response, step, issues, dataset):
        num_issues = len(issues)
        pages = number_of_pages(num_issues, step)

        for page, x in enumerate(range(0, num_issues, step)):
            soup = BeautifulSoup(response.body)
            issues_html = soup.find(id='issue-list').text.strip()
            for i in issues[x:x+step]:
                assert i['title'] in issues_html

            for i in issues[:x]:
                assert i['title'] not in issues_html

            for i in issues[x+step:]:
                assert i['title'] not in issues_html

            if (page + 1) != pages:
                # if we're on the last page there is no link to click
                #response = response.click(linkid='pagination-next-link')
                next_button =soup.find("a", id="pagination-next-link").attrs['href']
                assert next_button is not None
                parsed_url = urlparse(next_button)
                captured_value = parse_qs(parsed_url.query)['page'][0]

                response = app.get(toolkit.url_for('issues.dataset',
                    dataset_id=dataset['id'],
                    sort='oldest',
                    per_page=step,
                    page=captured_value),
                )
                
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_previous_button(self, app, dataset, issues):
        for per_page in ISSUES_PER_PAGE:
            pages = number_of_pages(len(issues), per_page)
            response = app.get(toolkit.url_for('issues.dataset',
                    dataset_id=dataset['id'],
                    sort='oldest',
                    per_page=per_page,
                    page=pages
                ),
            )
            self.click_through_all_pages_using_previous_button(app, response, 
                                                            per_page, issues, dataset)

    def click_through_all_pages_using_previous_button(self, app, response, per_page, issues, dataset):
        num_issues = len(issues)
        pages = number_of_pages(num_issues, per_page)
        page = pages

        while True:
            soup = BeautifulSoup(response.body)
            issues_html = soup.find(id='issue-list').text.strip()

            # x is the index of the issue expected at the top of this page
            x = (page - 1) * per_page

            for i in issues[x:x+per_page]:
                assert i['title'] in issues_html

            for i in issues[:x]:
                assert i['title'] not in issues_html

            for i in issues[x+per_page:]:
                assert i['title'] not in issues_html

            page -= 1
            if page == 0:
                break
            previous_button =soup.find("a", id="pagination-previous-link").attrs['href']
            assert previous_button is not None
            parsed_url = urlparse(previous_button)
            captured_value = parse_qs(parsed_url.query)['page'][0]
            
            response = app.get(toolkit.url_for('issues.dataset',
                    dataset_id=dataset['id'],
                    sort='oldest',
                    per_page=per_page,
                    page=captured_value
                )
            )
            #response = response.click(linkid='pagination-previous-link')
