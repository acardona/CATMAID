import json

from collections import defaultdict
from django.contrib import auth
from django.db import transaction, connection
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from catmaid.models import *
from catmaid.control.authentication import *
from catmaid.control.common import *
from catmaid.transaction import *

from guardian.shortcuts import get_objects_for_user

@requires_user_role([UserRole.Annotate, UserRole.Browse])
def list_project_tags(request, project_id=None):
    """ Return the tags associated with the project.
    """
    p = get_object_or_404(Project, pk=project_id)
    tags = [ str(t) for t in p.tags.all()]
    result = {'tags':tags}
    return HttpResponse(json.dumps(result, sort_keys=True, indent=4), mimetype="text/json")

@requires_user_role([UserRole.Annotate, UserRole.Browse])
def update_project_tags(request, project_id=None, tags=None):
    """ Updates the given project with the supplied tags. All
    existing tags will be replaced.
    """
    p = get_object_or_404(Project, pk=project_id)
    # Create list of sigle stripped tags
    if tags is None:
        tags = []
    else:
        tags = tags.split(",")
        tags = [t.strip() for t in tags]

    # Add tags to the model
    p.tags.set(*tags)

    # Return an empty closing response
    return HttpResponse(json.dumps(""), mimetype="text/json")

class ExProject:
    """ A wrapper around the Project model to include additional
    properties.
    """
    def __init__(self, project, is_editable, is_catalogueable):
        self.project = project
        self.is_editable = is_editable
        self.is_catalogueable = is_catalogueable

    def __getattr__(self, attr):
        """ Return own property when available, otherwise proxy
        to project.
        """
        if attr in self.__dict__:
            return getattr(self,attr)
        return getattr(self.project, attr)

def extend_projects(request, projects):
    """ Adds the properties is_editable and is_catalogueable to all
    projects passed.
    """
    # Mark projects that are editable according to the project_user table:
    if request.user.is_authenticated():
        # Create sets of projects that are administrable and annotatable
        # by the current user and unify them to one set. This will only
        # work for authenticated users (i.e. not AnonymousUser)
        user = auth.get_user(request)
        administrable_projects = set(get_objects_for_user(user, 'can_administer', Project))
        annotatable_projects = set(get_objects_for_user(user, 'can_annotate', Project))
        administrable_projects.union(annotatable_projects)
        # Just for readability, have another reference to the union
        editable_projects = administrable_projects
    else:
        # An anonymous user has no editing permissions
        editable_projects = []

    # Find all the projects that are editable:
    catalogueable_projects = set(x.project.id for x in \
        Class.objects.filter(class_name='driver_line').select_related('project'))

    result = []
    for p in projects:
        ex_p = ExProject(p,
            request.user.is_superuser or p in editable_projects,
            p.id in catalogueable_projects)
        result.append(ex_p)

    return result

def projects(request):
    # This is somewhat ridiculous - four queries where one could be
    # used in raw SQL.  The problem here is chiefly that
    # 'select_related' in Django doesn't work through
    # ManyToManyFields.  Development versions of Django have
    # introduced prefetch_related, but this isn't in the stable
    # version that I'm using.  (Another way around this would be to
    # query on ProjectStack, but the legacy CATMAID schema doesn't
    # include a single-column primary key for that table.)

    stacks = dict((x.id, x) for x in Stack.objects.all())

    # Create a dictionary that maps from projects to stacks:
    c = connection.cursor() #@UndefinedVariable
    c.execute("SELECT project_id, stack_id FROM project_stack")
    project_to_stacks = defaultdict(list)
    for project_id, stack_id in c.fetchall():
        project_to_stacks[project_id].append(stacks[stack_id])

    # Get projects with extra editable and catalogueable info
    if request.user.is_authenticated():
        projects = Project.objects.all().order_by('title')
    else:
        projects = Project.objects.filter(public=True).order_by('title')

    projects = extend_projects(request, projects)

    # Create a dictionary with those results that we can output as JSON:
    result = []
    for p in projects:
        if p.id not in project_to_stacks:
            continue
        stacks_dict = {}
        for s in project_to_stacks[p.id]:
            stacks_dict[s.id] = {
                'title': s.title,
                'comment': s.comment,
                'note': '',
                'action': 'javascript:openProjectStack(%d,%d)' % (p.id, s.id)}
        editable = p.is_editable
        result.append( {
            'pid': p.id,
            'title': p.title,
            'public_project': int(p.public),
            'editable': int(p.is_editable),
            'catalogue': int(p.is_catalogueable),
            'note': '[ editable ]' if p.is_editable else '',
            'action': stacks_dict} )
    return HttpResponse(json.dumps(result, sort_keys=True, indent=4), mimetype="text/json")

