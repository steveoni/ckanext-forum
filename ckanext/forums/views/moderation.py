from flask import Blueprint

from ckan.plugins import toolkit
import ckan.lib.helpers as h

moderation = Blueprint(u'moderation', __name__)

#this was renamed!!! if any issue arises check this
def moderate_all_reported_issues(organization_id):
    '''show all issues over max_strikes and are not moderated'''
    try:
        issues, organization = all_reported_issues(organization_id)
        extra_vars = {
            'issues': issues.get('results', []),
            'organization': organization,
        }
        return toolkit.render("issues/moderation.html",
                                extra_vars=extra_vars)
    except toolkit.ObjectNotFound:
        toolkit.abort(404, toolkit._('Organization not found'))


def moderate(organization_id):
    if toolkit.request.method == 'POST':
        if not toolkit.c.user:
            msg = toolkit._('You must be logged in to moderate issues')
            toolkit.abort(401, msg)

        data_dict = toolkit.request.form.mixed()
        try:
            if data_dict.get('abuse_status') == 'abuse':
                toolkit.get_action('forum_report')(data_dict=data_dict)
                h.flash_success(toolkit._('Issue permanently hidden'))
            elif data_dict.get('abuse_status') == 'not_abuse':
                toolkit.get_action('forum_report_clear')(
                    data_dict=data_dict)
                h.flash_success(toolkit._('All issue reports cleared'))
        except toolkit.ValidationError:
            toolkit.abort(404)

    h.redirect_to('moderation.moderate_all_reported_issues',
                    organization_id=organization_id)


def all_reported_issues(organization_id, include_sub_organizations=False):
    organization = toolkit.get_action('organization_show')(data_dict={
        'id': organization_id,
    })

    issues = toolkit.get_action('forum_search')(data_dict={
        'organization_id': organization['id'],
        'abuse_status': 'unmoderated',
        'include_reports': True,
        'include_sub_organizations': include_sub_organizations,
        'visibility': 'hidden',
    })

    return [issues, organization]


def reported_comments(organization_id):
    try:
        organization = toolkit.get_action('organization_show')(data_dict={
            'id': organization_id,
        })
        comments = toolkit.get_action('forum_comment_search')(data_dict={
            'organization_id': organization['id'],
            'only_hidden': True,
        })

        return toolkit.render(
            'issues/comment_moderation.html',
            extra_vars={
                'comments': comments,
                'organization': organization,
            }
        )
    except toolkit.ObjectNotFound:
        toolkit.abort(404, toolkit._('Organization not found'))


def moderate_comment(organization_id):
    if toolkit.request.method == 'POST':
        if not toolkit.c.user:
            msg = toolkit._('You must be logged in to moderate comment')
            toolkit.abort(401, msg)

        data_dict = toolkit.request.form.mixed()
        try:
            if data_dict.get('abuse_status') == 'abuse':
                toolkit.get_action('forum_comment_report')(data_dict=data_dict)
                h.flash_success(toolkit._('Comment permanently hidden'))
            elif data_dict.get('abuse_status') == 'not_abuse':
                toolkit.get_action('forum_comment_report_clear')(
                    data_dict=data_dict)
                h.flash_success(toolkit._('All comment reports cleared'))
        except toolkit.ValidationError:
            toolkit.abort(404)

    h.redirect_to('moderation.moderate_all_reported_issues',
                    organization_id=organization_id)



# Show all issues over max_strikes and are not moderated
moderation.add_url_rule('/organization/<organization_id>/issues/reported', view_func=moderate_all_reported_issues, methods=['GET'])

# Moderate issues
moderation.add_url_rule('/organization/<organization_id>/issues/moderate', view_func=moderate, methods=['GET', 'POST'])

# Reported comments
moderation.add_url_rule('/organization/<organization_id>/issues/reported_comments', view_func=reported_comments, methods=['GET'])

# Reported comments
moderation.add_url_rule('/organization/<organization_id>/issues/moderate_comment', view_func=moderate_comment, methods=['GET', 'POST'])
