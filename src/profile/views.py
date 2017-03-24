from django.shortcuts import render, redirect
from django.contrib.auth.models import User

from ckan_model import production as ckan

def default(request):
    if request.user.is_authenticated():
        url_to_redirect = linkFactory.getUser(request.user.username)
    else:
        url_to_redirect = linkFactory.getHome()
    return redirect(url_to_redirect)


def show_profile(request, user_id):
    payload = {}
    payload['this_page'] = linkFactory.getUser(user_id)
    selected_user = User.objects.get(username=user_id)

    if selected_user.first_name:
        try:
            ckan_selected_user = ckan.User(id=selected_user.first_name)
            payload['student'] = {
                'fullname': ckan_selected_user.fullname,
                'about': ckan_selected_user.about,
                'email': ckan_selected_user.email
            }
            admin_of = ckan_selected_user.admin_of()
            member_of = ckan_selected_user.member_of()
            payload['uni_owned'] = [{
                        'title': org.title,
                        'link': linkFactory.getOrg(org.id),
                        } for org in admin_of if org.is_university]
            payload['uni_member'] = [{
                        'title': org.title,
                        'link': linkFactory.getOrg(org.id),
                        }  for org in member_of if org.is_university and org not in admin_of]
            payload['comp_owned'] = [{
                        'title': org.title,
                        'link': linkFactory.getOrg(org.id),
                        }  for org in admin_of if not org.is_university]
            payload['comp_member'] = [{
                        'title': org.title,
                        'link': linkFactory.getOrg(org.id),
                        }  for org in member_of if not org.is_university and org not in admin_of]
            if request.user.first_name:
                ckan_this_user = ckan.User(id=request.user.first_name)
                if request.method == 'POST':
                    ckan_this_user.add_to_organization(
                        organization=request.POST['company'],
                        )
                recruit_bar = []
                for comp in ckan_this_user.admin_of():
                    recruit_bar.append({
                        'title': comp.title,
                        'id': comp.id,
                        })
                payload['action'] = recruit_bar

        except Exception as e:
            payload['warning'] = repr(e)
    
    return render(request, 'profile.html', payload)


def create_student_portfolio(request, user_id):
    payload = {}
    payload['this_page'] = linkFactory.createUser(user_id)

    if request.method == 'POST' and \
      (user_id == request.user.username or request.user.is_staff):
        try:
            ckan_user_id = ckan.User.create_new(
                login=user_id,
                email=request.POST['email'],
                fullname=request.POST['fullname'],
                about=request.POST['about'],
                ).id
            selected_user = User.objects.get(username=user_id)
            selected_user.first_name = ckan_user_id
            selected_user.save()
            return redirect(linkFactory.getUser())
        except Exception as e:
            payload['warning'] = repr(e)

    return render(request, 'create/portfolio.html', payload)


def create_organization(request, user_id):
    payload = {}
    payload['this_page'] = linkFactory.createOrg(user_id)
    
    if request.method == 'POST':
        try:
            if request.POST['type'] == 'uni':
                ckan.Organization.create_university(
                    ckan=ckan.User(request.user.first_name).ckan,
                    name=request.POST['name'],
                    title=request.POST['title'],
                    description=request.POST['description'],
                    )
            elif request.POST['type'] == 'comp':
                ckan.Organization.create_company(
                    ckan=ckan.User(request.user.first_name).ckan,
                    name=request.POST['name'],
                    title=request.POST['title'],
                    description=request.POST['description'],
                    )
            return redirect(linkFactory.getUser())
        except Exception as e:
            payload['warning'] = repr(e)

    return render(request, 'create/organization.html', payload)


class linkFactory:
    """creates links"""

    def getHome():
        return "/"

    def getOrg(orgID):
        return "/organization/{}/".format(orgID)

    def getUser(userID=None):
        if not userID:
            return "/profile/"
        return "/profile/{}/".format(userID)
    
    def createUser(userID):
        return "/profile/{}/create/student/".format(userID)

    def createOrg(userID):
        return "/profile/{}/create/organization/".format(userID)