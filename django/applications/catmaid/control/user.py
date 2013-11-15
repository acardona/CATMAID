import json
import colorsys
from random import random
from string import upper

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

@login_required
def user_list(request):
    # Allow a request to pass users IDs to ignore
    if request.method == "POST":
        ignored_users = [v for k,v in request.POST.iteritems()
                if k.startswith('ignored_users[')]
    else:
        ignored_users = []

    result = []
    for u in User.objects.exclude(id__in=ignored_users).order_by(
            'last_name', 'first_name'):
        up = u.userprofile
        result.append({
            "id": u.id,
            "login": u.username,
            "full_name": u.get_full_name(),
            "first_name": u.first_name,
            "last_name": u.last_name,
            "color": (up.color.r, up.color.g, up.color.b) })
    
    return HttpResponse(json.dumps(result), mimetype='text/json')

@login_required
def user_list_datatable(request):
    display_start = int(request.POST.get('iDisplayStart', 0))
    display_length = int(request.POST.get('iDisplayLength', -1))
    if display_length < 0:
        display_length = 2000  # Default number of result rows

    should_sort = request.POST.get('iSortCol_0', False)

    user_query = User.objects.all()

    if should_sort:
        column_count = int(request.POST.get('iSortingCols', 0))
        sorting_directions = [request.POST.get('sSortDir_%d' % d, 'DESC')
                for d in range(column_count)]
        sorting_directions = map(lambda d: '-' if upper(d) == 'DESC' else '',
                sorting_directions)

        fields = ['username', 'first_name', 'last_name']
        sorting_index = [int(request.POST.get('iSortCol_%d' % d))
                for d in range(column_count)]
        sorting_cols = map(lambda i: fields[i], sorting_index)

        user_query = user_query.extra(order_by=[di + col for (di, col) in zip(
                sorting_directions, sorting_cols)])

    result = list(user_query[display_start:display_start + display_length])

    response = {'iTotalRecords': len(result),
            'iTotalDisplayRecords': len(result), 'aaData': []}
    for user in result:
        response['aaData'] += [[
            user.username,
            user.first_name,
            user.last_name,
        ]]

    return HttpResponse(json.dumps(response), mimetype='text/json')


initial_colors = [(1, 0, 0, 1), 
                  (0, 1, 0, 1), 
                  (0, 0, 1, 1), 
                  (1, 0, 1, 1), 
                  (0, 1, 1, 1), 
                  (1, 1, 0, 1), 
                  (1, 1, 1, 1), 
                  (1, 0.5, 0, 1), 
                  (1, 0, 0.5, 1), 
                  (0.5, 1, 0, 1), 
                  (0, 1, 0.5, 1), 
                  (0.5, 0, 1, 1), 
                  (0, 0.5, 1, 1)];


def distinct_user_color():
    users = User.objects.exclude(id__exact=-1).order_by('id')
    
    if len(users) < len(initial_colors):
        distinct_color = initial_colors[len(users)]
    else:
        distinct_color = colorsys.hsv_to_rgb(random(), random(), 1.0) + (1,)
    
    return distinct_color
