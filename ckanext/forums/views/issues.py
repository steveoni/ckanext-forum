import collections
from logging import getLogger
import re
from click.core import Context

from sqlalchemy import func
from flask import Blueprint

from ckan.lib.base import render
import ckan.lib.helpers as h
from ckan.lib import mailer
import ckan.model as model
import ckan.logic as logic
import ckan.plugins as p
from ckan.plugins.toolkit import config, request, _, g
from ckan.plugins import toolkit

import ckanext.forums.model as issuemodel
from ckanext.forums.views import show
from ckanext.forums.exception import ReportAlreadyExists
from ckanext.forums.lib import helpers as issues_helpers
from ckanext.forums.logic import schema
from ckanext.forums.lib.helpers import (Pagination, get_forum_per_page,
                                        get_issue_subject)

log = getLogger(__name__)

forums = Blueprint('forums', __name__)

AUTOCOMPLETE_LIMIT = 10
VALID_CATEGORY = re.compile(r"[0-9a-z\-\._]+")


def _before_dataset(dataset_id):
    '''Returns the dataset dict and checks issues are enabled for it.'''
    context = {'for_view': True}
    try:
        pkg = logic.get_action('package_show')(context,
                                                {'id': dataset_id})
        # need this as some templates in core explicitly reference
        # g.pkg_dict
        g.pkg = pkg
        g.pkg_dict = g.pkg

        # keep the above lines to keep current code working till it's all
        # refactored out, otherwise, we should pass pkg as an extra_var
        # directly that's returned from this function
        if not issues_helpers.forum_enabled(pkg):
            p.toolkit.abort(404, _('Issues have not been enabled for this dataset'))
        return pkg
    except logic.NotFound:
        p.toolkit.abort(404, _('Dataset not found'))
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401,
                        _('Unauthorized to view issues for this dataset'))

def _before_org(org_id):
    '''Returns the organization dict and checks issues are enabled for it.'''
    context = {'for_view': True}
    try:
        org = logic.get_action('organization_show')(context,
                                                    {'id': org_id})

        # we should pass org to the template as an extra_var
        # directly that's returned from this function
        if not issues_helpers.forum_enabled_for_organization(org):
            p.toolkit.abort(404, _('Issues have not been enabled for this organization'))
        return org
    except logic.NotFound:
        p.toolkit.abort(404, _('Dataset not found'))
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401,
                        _('Unauthorized to view issues for this organization'))

def new():
    context = {'for_view': True}
    
    if not g.user:
        p.toolkit.abort(401, _('Please login to add a new issue'))

    data_dict = {
        'dataset_id': "forum",
        'creator_id': g.userobj.id
    }
    try:
        logic.check_access('forum_create', context, data_dict)
    except logic.NotAuthorized:
        p.toolkit.abort(403, _('Not authorized to add a new issue'))

    g.errors, g.error_summary = {}, {}

    if request.method == 'POST':
        # TODO: ? use dictization etc
        #    data = logic.clean_dict(
        #        df.unflatten(
        #            logic.tuplize_dict(
        #                logic.parse_params(request.params))))
        data_dict.update({
            'title': request.form.get('title'),
            'description': request.form.get('description')
            })

        if not data_dict['title']:
            g.error_summary['title'] = ["Please enter a title"]
        g.errors = g.error_summary

        if not g.error_summary:  # save and redirect
            issue_dict = logic.get_action('forum_create')(
                data_dict=data_dict
            )
            h.flash_success(_('Your issue has been registered, '
                                'thank you for the feedback'))
            return p.toolkit.redirect_to('forums.show_issue',
                issue_number=issue_dict['number'])

    g.data_dict = data_dict
    return render("forums/add.html")

# RENAMED it conflicted with views.show.show
def show_issue(issue_number):
    try:
        extra_vars = show.show(issue_number,
                                'forum',
                                session=model.Session)   
    except toolkit.ValidationError as e:
        p.toolkit.abort(
            404, toolkit._('Discussion not found: {0}'.format(e.error_summary)))
    except toolkit.ObjectNotFound as e:
        p.toolkit.abort(
            404, toolkit._('Discussion not found: {0}'.format(e)))
    extra_vars['dataset'] = dataset
    # passing the user object as well, because it is needed in the HTML
    user_issue = model.Session.query(model.User)\
        .filter(model.User.id==extra_vars['issue']['user_id']).first()
    extra_vars['issue']['user'] = vars(user_issue)

    return p.toolkit.render('forums/show.html', extra_vars=extra_vars)

def edit(issue_number):
    dataset_id = 'forum'
    issue = p.toolkit.get_action('forum_show')(
        data_dict={
            'issue_number': issue_number,
            'dataset_id': 'forum',
        }
    )

    if request.method == 'GET':
        return p.toolkit.render(
            'forums/edit.html',
            extra_vars={
                'issue': issue,
                'errors': None,
            },
        )
    elif request.method == 'POST':
        data_dict = dict(request.form)
        data_dict['issue_number'] = issue_number
        data_dict['dataset_id'] = 'forum'
        print(data_dict)
        try:
            p.toolkit.get_action('forum_update')(data_dict=data_dict)
            return p.toolkit.redirect_to('forums.show_issue',
                                            issue_number=issue_number)
        except p.toolkit.ValidationError as e:
            errors = e.error_dict
            return p.toolkit.render(
                'forums/edit.html',
                extra_vars={
                    'issue': issue,
                    'errors': errors,
                },
            )
        except p.toolkit.NotAuthorized as e:
            p.toolkit.abort(401, e.message)

def comments(issue_number):
    # POST only
    context = {'for_view': True}
    if request.method != 'POST':
        p.toolkit.abort(500, _('Invalid request'))

    dataset_id = "forum"

    auth_dict = {
        'dataset_id': dataset_id,
        'issue_number': issue_number
        }
    # Are we not repeating stuff in logic ???
    try:
        logic.check_access('forum_create', context, auth_dict)
    except logic.NotAuthorized:
        p.toolkit.abort(403, _('Not authorized'))

    next_url = h.url_for('forums.show_issue',
                            issue_number=issue_number)

    # TODO: (?) move validation somewhere better than controller
    comment = request.form.get('comment')
    if not comment or comment.strip() == '':
        h.flash_error(_('Comment cannot be empty'))
        return p.toolkit.redirect_to(next_url)

    # do this first because will error here if not allowed and do not want
    # comment created in that case
    if 'close' in request.form or 'reopen' in request.form:
        status = (issuemodel.ISSUE_STATUS.closed if 'close' in request.form
                    else issuemodel.ISSUE_STATUS.open)
        issue_dict = {
            'issue_number': issue_number,
            'dataset_id': dataset_id,
            'status': status
            }
        try:
            logic.get_action('forum_update')(context, issue_dict)
        except logic.NotAuthorized:
            p.toolkit.abort(403, _('Not authorized'))

        if 'close' in request.form:
            h.flash_success(_("Discussion closed"))
        else:
            h.flash_success(_("Discussion re-opened"))

    data_dict = {
        'author_id': g.userobj.id,
        'comment': comment.strip(),
        'dataset_id': dataset_id,
        'issue_number': issue_number,
        }
    logic.get_action('forum_comment_create')(context, data_dict)

    return p.toolkit.redirect_to(next_url)

def dataset():
    """
    Display a page containing a list of all issues items for a dataset,
    sorted by category.
    """
    dataset_id="forum"
    extra_vars = {}
    try:
        extra_vars = issues_for_dataset('forum', request.args)
        extra_vars['pkg_dict'] = {}
    except toolkit.ValidationError as e:
        _dataset_handle_error(dataset_id, e)
    return render("forums/dataset.html", extra_vars=extra_vars)

def delete(issue_number):
    dataset_id = "forum"
    if 'cancel' in request.form:
        return p.toolkit.redirect_to('forums.show_issue',
                                issue_number=issue_number)

    if request.method == 'POST':
        try:
            toolkit.get_action('forum_delete')(
                data_dict={'issue_number': issue_number,
                            'dataset_id': dataset_id}
            )
        except toolkit.NotAuthorized:
            msg = _('Unauthorized to delete issue {0}'.format(
                issue_number))
            toolkit.abort(401, msg)

        h.flash_notice(
            _('Discussion {0} has been deleted.'.format(issue_number))
        )
        return p.toolkit.redirect_to('forums.dataset')
    else:
        return render('forums/confirm_delete.html',
                        extra_vars={
                            'issue_number': issue_number
                        })

def assign(dataset_id, issue_number):
    dataset = _before_dataset(dataset_id)
    if request.method == 'POST':
        try:
            assignee_id = request.form.get('assignee')
            assignee = toolkit.get_action('user_show')(
                data_dict={'id': assignee_id})
        except toolkit.ObjectNotFound:
            h.flash_error(_('User {0} does not exist'.format(assignee_id)))
            return p.toolkit.redirect_to('forums.show_issue',
                                            issue_number=issue_number,
                                            dataset_id=dataset_id)

        try:
            issue = toolkit.get_action('forum_update')(
                data_dict={
                    'issue_number': issue_number,
                    'assignee_id': assignee['id'],
                    'dataset_id': dataset_id,
                    'assignee': assignee_id
                }
            )

            notifications = p.toolkit.asbool(
                config.get('ckanext.forums.send_email_notifications')
            )

            if notifications:
                subject = get_issue_subject(issue)
                body = u'Доделено на {user}.\n\n---\nCaktuar për {user}.\n\n---\nAssigned to {user}.'.format(
                        user=assignee['display_name'])

                user_obj = model.User.get(assignee_id)
                try:
                    mailer.mail_user(user_obj, subject, body)
                except mailer.MailerException as e:
                    log.debug(e.message)

        except toolkit.NotAuthorized:
            msg = _('Unauthorized to assign users to issue'.format(
                issue_number))
            toolkit.abort(401, msg)
        except toolkit.ObjectNotFound as e:
            toolkit.abort(404)
        except toolkit.ValidationError as e:
            toolkit.abort(404)

        return p.toolkit.redirect_to('forums.show_issue',
                                    issue_number=issue_number,
                                    dataset_id=dataset_id)

def report(issue_number):
    dataset_id = 'forum'
    if not g.user:
        msg = _('You must be logged in to report issues')
        toolkit.abort(403, msg)
    if request.method == 'POST':
        try:
            report_info = toolkit.get_action('forum_report')(
                data_dict={
                    'issue_number': issue_number,
                    'dataset_id': dataset_id
                }
            )
            if report_info:
                # we have this info if it is an admin
                msgs = [_('Report acknowledged.')]
                if report_info['abuse_status'] == \
                    issuemodel.AbuseStatus.abuse.value:
                    msgs.append(_('Marked as abuse/spam.'))
                msgs.append(_('Discussion is visible.')
                            if report_info['visibility'] == 'visible' else
                            _('Discussion is invisible to normal users.'))
                h.flash_success(' '.join(msgs))
            else:
                h.flash_success(_('Discussion reported to an administrator'))
        except toolkit.ValidationError:
            toolkit.abort(404)
        except toolkit.ObjectNotFound:
            toolkit.abort(404)
        except ReportAlreadyExists as e:
            h.flash_error(e.message)

        return p.toolkit.redirect_to('forums.show_issue',
                                dataset_id=dataset_id,
                                issue_number=issue_number)

def report_comment(issue_number, comment_id):
    dataset_id = "forum"
    if request.method == 'POST':
        if not g.user:
            msg = _('You must be logged in to report comments')
            toolkit.abort(403, msg)
        try:
            report_info = toolkit.get_action('forum_comment_report')(
                data_dict={
                    'comment_id': comment_id,
                    'issue_number': issue_number,
                    'dataset_id': dataset_id
                }
            )
            if report_info:
                # we have this info if it is an admin
                msgs = [_('Report acknowledged.')]
                if report_info['abuse_status'] == \
                        issuemodel.AbuseStatus.abuse.value:
                    msgs.append(_('Marked as abuse/spam.'))
                msgs.append(_('Comment is visible.')
                            if report_info['visibility'] == 'visible' else
                            _('Comment is invisible to normal users.'))
                h.flash_success(' '.join(msgs))
            else:
                h.flash_success(_('Comment has been reported to an administrator'))
            return p.toolkit.redirect_to('forums.show_issue',
                                    dataset_id=dataset_id,
                                    issue_number=issue_number)
        except toolkit.ValidationError:
            toolkit.abort(404)
        except toolkit.ObjectNotFound:
            toolkit.abort(404)
        except ReportAlreadyExists as e:
            h.flash_error(e.message)
        return p.toolkit.redirect_to('forums.show_issue', dataset_id=dataset_id,
                                issue_number=issue_number)

def report_clear(issue_number):
    dataset_id = "forum"
    if request.method == 'POST':
        try:
            toolkit.get_action('forum_report_clear')(
                data_dict={
                    'issue_number': issue_number,
                    'dataset_id': dataset_id
                }
            )
            h.flash_success(_('Discussion report cleared'))
            return p.toolkit.redirect_to('forums.show_issue',
                                    dataset_id=dataset_id,
                                    issue_number=issue_number)
        except toolkit.NotAuthorized:
            msg = _('You must be logged in clear abuse reports').format(
                issue_number
            )
            toolkit.abort(403, msg)
        except toolkit.ValidationError:
            toolkit.abort(404)
        except toolkit.ObjectNotFound:
            toolkit.abort(404)

def comment_report_clear(issue_number, comment_id):
    dataset_id = "forum"
    if request.method == 'POST':
        try:
            toolkit.get_action('forum_comment_report_clear')(
                data_dict={'comment_id': comment_id,
                            'issue_number': issue_number,
                            'dataset_id': dataset_id}
            )
            h.flash_success(_('Spam/abuse report cleared'))
            return p.toolkit.redirect_to('forums.show_issue',
                                    dataset_id=dataset_id,
                                    issue_number=issue_number)
        except toolkit.NotAuthorized:
            msg = _('You must be logged in to clear abuse reports').format(
                issue_number
            )
            toolkit.abort(401, msg)
        except toolkit.ValidationError:
            toolkit.abort(404)
        except toolkit.ObjectNotFound:
            toolkit.abort(404)

def issues_for_organization(org_id):
    """
    Display a page containing a list of all issues for a given organization
    """
    _before_org(org_id)
    try:
        template_params = issues_for_org(org_id, request.args)
    except toolkit.ValidationError as e:
        msg = toolkit._("Validation error: {0}".format(e.error_summary))
        log.warning(msg + ' - Issues for org: %s', org_id)
        h.flash(msg, category='alert-error')
        return p.toolkit.redirect_to('forums.issues_for_organization',
                                        org_id=org_id)

    # TO DELETE
    g.org = model.Group.get(org_id)

    q = """
        SELECT table_id
        FROM member
        WHERE group_id='{gid}'
            AND table_name='package'
            AND state='active'
    """.format(gid=g.org.id)
    results = model.Session.execute(q)

    dataset_ids = [x['table_id'] for x in results]
    issues = model.Session.query(issuemodel.Issue)\
        .filter(issuemodel.Issue.dataset_id.in_(dataset_ids))\
        .order_by(issuemodel.Issue.created.desc())

    g.results = collections.defaultdict(list)
    for issue in issues:
        g.results[issue.package].append(issue)
    g.package_set = sorted(set(g.results.keys()), key=lambda x: x.title)
    print(g.package_set)
    return render("issues/organization_forums.html", extra_vars=template_params)

def all_issues_page():
    """
    Display a page containing a list of all issues items
    """
    template_params = all_issues(request.args)
    return render("issues/all_forums.html", extra_vars=template_params)


def _dataset_handle_error(dataset_id, exc):
    msg = toolkit._("Validation error: {0}".format(exc.error_summary))
    h.flash(msg, category='alert-error')
    return p.toolkit.redirect_to('forums.dataset', dataset_id=dataset_id)


def issues_for_dataset(dataset_id, get_query_dict):
    query, errors = toolkit.navl_validate(
        dict(get_query_dict),
        schema.issue_dataset_controller_schema()
    )
    log.info("QUERY")
    log.info(query)
    if errors:
        raise toolkit.ValidationError(errors)
    query.pop('__extras', None)
    return _search_issues(dataset_id=dataset_id, **query)

def issues_for_org(org_id, get_query_dict):
    query, errors = toolkit.navl_validate(
        dict(get_query_dict),
        schema.issue_dataset_controller_schema()
    )
    if errors:
        raise toolkit.ValidationError(errors)
    query.pop('__extras', None)
    template_params = _search_issues(organization_id=org_id,
                                     include_datasets=True,
                                     **query)
    template_params['org'] = \
        logic.get_action('organization_show')({}, {'id': org_id})
    return template_params

def all_issues(get_query_dict):
    query, errors = toolkit.navl_validate(
        dict(get_query_dict),
        schema.issue_dataset_controller_schema()
    )
    if errors:
        raise toolkit.ValidationError(errors)
    query.pop('__extras', None)
    return _search_issues(include_datasets=True,
                          **query)

def _search_issues(dataset_id=None,
                   organization_id=None,
                   status=issuemodel.ISSUE_STATUS.open,
                   sort='newest',
                   visibility=None,
                   abuse_status=None,
                   q='',
                   page=1,
                   per_page=get_forum_per_page()[0],
                   include_datasets=False,
                   include_reports=True):
    # use the function params to set default for our arguments to our
    # data_dict if needed
    params = locals().copy()

    # convert per_page, page parameters to api limit/offset
    limit = per_page
    offset = (page - 1) * limit
    params.pop('page', None)
    params.pop('per_page', None)

    # fetch only the results for the current page
    params.update({
        'include_count': False,
        'limit': limit,
        'offset': offset,
    })

    results_for_current_page = toolkit.get_action('forum_search')(
        data_dict=params
        )

    issues = results_for_current_page['results']
    
    # fetch the total count of all the search results without dictizing
    params['include_count'] = True
    params['include_results'] = False
    params.pop('limit', None)
    params.pop('offset', None)
    all_search_results = toolkit.get_action('forum_search')(data_dict=params)
    forum_count = all_search_results['count']
    
    pagination = Pagination(page, limit, forum_count)

    template_variables = {
        'issues': issues,
        'status': status,
        'sort': sort,
        'q': q,
        'pagination': pagination,
    }
    if visibility:
        template_variables['visibility'] = visibility

    return template_variables


# Show all issues for a dataset
forums.add_url_rule('/forum', view_func=dataset, methods=['GET'])

# New issue
forums.add_url_rule('/forums/new', view_func=new, methods=['GET', 'POST'])

# Shows an issue
forums.add_url_rule('/forums/<int:issue_number>', view_func=show_issue, methods=['GET'])

# Edit an issue
forums.add_url_rule('/forums/<int:issue_number>/edit', view_func=edit, methods=['GET', 'POST'])

# Delete an issue
forums.add_url_rule('/forums/<int:issue_number>/delete', view_func=delete, methods=['GET', 'POST'])

# Assign an issue
forums.add_url_rule('/dataset/<dataset_id>/issues/<int:issue_number>/assign', view_func=assign, methods=['POST'])

# Comment on an issue
forums.add_url_rule('/forums/<int:issue_number>/comments', view_func=comments, methods=['POST'])

# Report an issue
forums.add_url_rule('/forums/<int:issue_number>/report', view_func=report, methods=['GET', 'POST'])

# Clear issue report
forums.add_url_rule('/forums/<int:issue_number>/report_clear', view_func=report_clear, methods=['GET', 'POST'])

# Report comment
forums.add_url_rule('/forums/<int:issue_number>/comment/<comment_id>/report', view_func=report_comment, methods=['GET', 'POST'])

# Clear comment from report
forums.add_url_rule('/forums/<int:issue_number>/comment/<comment_id>/report_clear', view_func=comment_report_clear, methods=['GET', 'POST'])

# Show all issues
forums.add_url_rule('/issues', view_func=all_issues_page, methods=['GET'])

# All issues for an organization
forums.add_url_rule('/organization/<org_id>/issues', view_func=issues_for_organization, methods=['GET'])
