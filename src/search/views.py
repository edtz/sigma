import urllib.parse

from django.shortcuts import render


#from ckan_model import stub as ckan
from ckan_model import production as ckan

#from ..ckan_model import production as ckan
import django.http


def index(request: django.http.HttpRequest):
    payload = {}
    google = ckan.Search()
    payload['top_tags'] = google.top_tags()
    return render(request, 'index.html', context=payload)


def search(request: django.http.HttpRequest):
    # it's a search engine!
    google = ckan.Search()
    payload = {}
    payload['tags'] = google.tags_list()
    payload['unis'] = google.university_list()

    page = int(request.GET.get('page', 1))
    page_size = 10
    start_pos = (page - 1) * page_size

    if request.GET:
        response = google.students(request.GET.getlist('selected_tags'),
                                   request.GET.getlist('selected_unis'),
                                   start=start_pos,
                                   rows=page_size
                                   )
    else:
        response = google.students()

    total = response['total']
    pages_count = total//10+bool(total%10)
    actual_page = start_pos//page_size + 1

    parsed_url = list(urllib.parse.urlparse(request.get_full_path()))
    options = dict(urllib.parse.parse_qsl(parsed_url[4]))

    def change_url(n):
        options['page'] = n
        parsed_url[4] = urllib.parse.urlencode(options)
        return urllib.parse.urlunparse(parsed_url)

    pages = [{'number': n,
              'url': change_url(n),
              'active': n == actual_page} for n in range(1, pages_count)]

    payload["pagination"] = { "pages": pages,
                              "prev": actual_page > 1,
                              "next": actual_page < pages_count,
                              }
    payload['results'] = response['results']
    return render(request, 'search.html', payload)