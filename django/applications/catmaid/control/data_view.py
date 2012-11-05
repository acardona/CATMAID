import json

from django.conf import settings
from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import Context, loader

from catmaid.control.common import makeJSON_legacy_list
from catmaid.models import DataView, DataViewType, Project

import re

def get_data_view_type_comment( request ):
    """ Return the comment of a specific data view type.
    """
    requested_id = request.REQUEST["data_view_type_id"]
    if requested_id == "":
        text = "Please select a valid data view type."
    else:
        try:
            data_view_type_id = int(requested_id)
            text = DataViewType.objects.get(pk=data_view_type_id).comment
        except:
            text = "Sorry, the configuration help text couldn't be retrieved."
    result = { 'comment':text }
    return HttpResponse(json.dumps(result), mimetype="text/json")

def dataview_to_dict( dataview ):
    """ Creates a dicitonary of the dataviews' properties.
    """
    return {
        'id': dataview.id,
        'title': dataview.title,
        'code_type': dataview.data_view_type.code_type,
        'config': dataview.config,
        'note': dataview.comment
    }

def get_available_data_views( request ):
    """ Returns a list of all available data views.
    """
    all_views = DataView.objects.order_by("position")
    dataviews = map(dataview_to_dict, all_views)

    return HttpResponse(json.dumps(makeJSON_legacy_list(dataviews)), mimetype="text/json")

def get_default_properties( request ):
    """ Return the properies of the default data view.
    """
    default = DataView.objects.filter(is_default=True)[0]
    default = dataview_to_dict( default )

    return HttpResponse(json.dumps(default), mimetype="text/json")

def get_default_data_view( request ):
    """ Return the data view that is marked as the default. If there
    is more than one view marked as default, the first one is returned.
    """
    default = DataView.objects.filter(is_default=True)[0]

    return get_data_view( request, default.id )

def natural_sort(l, field):
    """ Natural sorting of a list wrt. to its 'title' attribute.
    Based on: http://stackoverflow.com/questions/4836710
    """
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', getattr(key, field)) ]
    return sorted(l, key = alphanum_key)

def get_data_view( request, data_view_id ):
    """ Returns a rendered template for the given view.
    """
    # Load the template
    dv = get_object_or_404(DataView, pk=data_view_id)
    code_type = dv.data_view_type.code_type
    template = loader.get_template( "catmaid/" + code_type + ".html" )
    # Get project information and pass all to the template context
    config = json.loads( dv.config )
    projects = Project.objects.all()
    # Sort by default
    if "sort" not in config or config[sort] == True:
        projects = natural_sort( projects, "title" )

    context = Context({
        'data_view': dv,
        'projects': projects,
        'config': config
    })

    return HttpResponse( template.render( context ) );
