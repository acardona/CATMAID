import json

from catmaid.models import Class, ClassInstance, Relation, UserRole
from catmaid.control.authentication import requires_user_role
from catmaid.control.common import get_class_to_id_map, get_relation_to_id_map

from django.http import HttpResponse

# All classes needed by the tracing system alongside their
# descriptions.
needed_classes = {
    'group': "A group",
    'label': "A label",
    'neuron': "A neuron representation",
    'root': "The root node for the tracing system",
    'skeleton': "The representation of a skeleton"}

# All relations needed by the tracing system alongside their
# descriptions.
needed_relations = {
    'labeled_as': "Something is labeled by sth. else.",
    'is_a': "A generic is-a relationship",
    'element_of': "A generic element-of relationship",
    'model_of': "Marks something as a model of something else.",
    'part_of': "One thing is part of something else.",
    'presynaptic_to': "Something is presynaptic to something else.",
    'postsynaptic_to': "Something is postsynaptic to something else."}

def check_tracing_setup_view(request, project_id=None):
    all_good = check_tracing_setup(project_id)
    return HttpResponse(json.dumps({'all_good': all_good}))

def check_tracing_setup(project_id):
    """ Checks if all classes and relations needed by the
    tracing system are available.
    """
    all_good, _, _, _ = check_tracing_setup_detailed(project_id)
    return all_good

def check_tracing_setup_detailed(project_id):
    """ Checks if all classes and relations needed by the tracing system are
    available. It returns a four-tuple with a boolean indicating if all is
    setup, the missing class names, the missing relation names and the missing
    class instance names.
    """
    # Get class and relation data
    class_map = get_class_to_id_map(project_id)
    relation_map = get_relation_to_id_map(project_id)

    # Check if all classes and relations are available
    all_good = True
    missing_classes = []
    missing_relations = []
    missing_classinstances = []

    for c in needed_classes:
        if not c in class_map:
            all_good = False
            missing_classes.append(c)
    for r in needed_relations:
        if not r in relation_map:
            all_good = False
            missing_relations.append(r)
    # Check if the root node is there
    if 'root' in class_map:
        exists = ClassInstance.objects.filter(
            class_column=class_map['root'],
            project_id=project_id).exists()
        if not exists:
            all_good = False
            missing_classinstances.append('root')
    else:
            missing_classinstances.append('root')

    return all_good, missing_classes, missing_relations, missing_classinstances

@requires_user_role([UserRole.Admin])
def rebuild_tracing_setup_view(request, project_id=None):
    setup_tracing(project_id, request.user)
    all_good = check_tracing_setup(project_id)
    return HttpResponse(json.dumps({'all_good': all_good}))

def setup_tracing(project_id, user):
    """ Tests which of the needed classes and relations is missing
    from the project's semantic space and adds those.
    """
    # Remember available classes
    available_classes = {}

    # Add missing classes
    for c in needed_classes:
        class_object, _ = Class.objects.get_or_create(
            class_name=c,
            project_id=project_id,
            defaults={'user': user,
                      'description': needed_classes[c]})
        available_classes[c] = class_object
    # Add missing relations
    for r in needed_relations:
        Relation.objects.get_or_create(
            relation_name=r,
            project_id=project_id,
            defaults={'user': user,
                      'description': needed_relations[r]})
    # Add root node
    ClassInstance.objects.get_or_create(
        class_column=available_classes['root'],
        project_id=project_id,
        defaults={'user': user,
                  'name': 'neuropile'})
