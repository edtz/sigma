from django.shortcuts import render, redirect
from django.contrib.auth.models import User

from ckan_model import production as ckan

def show_organization(request, org_id):
    payload = {}
    payload['this_page'] = '/organization/' + org_id + '/'

    try:
        this_user = ckan.User(id=request.user.first_name)
        this_org = ckan.Organization(ckan=this_user.ckan, id=org_id)
        if not any(org.name == this_org.name for org in this_user.member_of()):
            payload['can_edit'] = False
        else:
            payload['can_edit'] = True
        if request.method == 'POST' and payload['can_edit']:
            this_org.title = request.POST['title']
            this_org.description = request.POST['description']
        payload['name'] = this_org.name
        payload['title'] = this_org.title
        payload['description'] = this_org.description
    except Exception as e:
        return redirect('/')


    return render(request, 'organization.html', payload)