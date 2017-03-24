def select(result, keys):
    return [{key: orig[key] for key in keys} for orig in result]


def search_students(tags=[], universities=[]):
    thing = [{'title': 'Eduard', 'tags_matched': [ 'Python'], 'tags_unmatched': ['Django']},
             {'title': 'Vita', 'tags_matched': [ 'Python'], 'tags_unmatched': ['MySQL']},
            ]
    return thing


def top_tags(limit=10):
    thing = [{'count': 5, 'name': u'WWW'},
             {'count': 3, 'name': u'PHP'},
             {'count': 2, 'name': u'Python'},
             {'count': 2, 'name': u'CSHARP'},
             {'count': 2, 'name': u'CPP'},
             {'count': 1, 'name': u'NETWORKING'},
             {'count': 1, 'name': u'Django'}]
    return thing


def tags_list():
    thing = ('PHP', 'Python', 'Django', 'Bootstrap', 'JavaScript')
    return thing


def university_list():
    thing = [{'name': 'brno-university-of-technology',
              'title': 'Brno University of Technology'},
             {'name': 'lut',
              'title': 'Lappeenranta University of Technology'}]
    return thing