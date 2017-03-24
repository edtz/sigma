import random
import ckanapi
import string
import operator
import re
import uuid

sysadmin = ckanapi.RemoteCKAN("http://ckan.local",
                              "cd609119-9305-48bb-8b9c-5b3083252d80")


class Search:
    def __init__(self, ckan: ckanapi.RemoteCKAN = None):
        if ckan is None:
            self.ckan = ckanapi.RemoteCKAN("http://ckan.local")
        else:
            self.ckan = ckan

    def students(self, tags=None, universities=None, start=0, rows=10):
        """Search for students by their tags. Use parameters
        start and rows for handle pagination.
        Format of dict in returned list:
        {'name': Student's name,
         'tags_matched': [list of matched tags]
         'tags_unmatched: [tags which this student have,
                           but was not specified in query]
        }

        :param universities: List of universities (names)
        :param tags: List of tags
        :param start: position of first item
        :param rows: limit of returned results [max value: 1000]
        :return: Dictionary with keys total and results.
                'results' contains:
                List of dictionaries with information about students
        """
        if rows > 1000:
            raise ValueError('Parameter rows over limit 1000')
        if not universities:
            universities = []
        if not tags:
            tags = []

        query = self._prepare_query(tags, 'students', universities)
        res = self.ckan.action.package_search(q=query, start=start, rows=rows)
        for student in res['results']:
            student['tags_matched'] = [tag['name'] for tag in student['tags']
                                       if tag['name'] in tags]
            student['tags_unmatched'] = [tag['name'] for tag in student['tags']
                                         if tag['name'] not in tags]
        return {'total': res['count'],
                'results': select(res['results'],
                                  ["title",
                                   "name",
                                   'tags_matched',
                                   'tags_unmatched'])}

    def top_tags(self, limit=10):
        """Get most used tags in descending order

        :param limit: Limit of returned tags, default 10
        :return: List of dictionaries: {'count', 'name'}
        """
        res = self.ckan.call_action('package_search',
                                    {'facet.field': ['tags'],
                                     'facet.limit': limit})
        res = res['search_facets']['tags']['items']
        res = sorted(res,
                     key=operator.itemgetter('count'),
                     reverse=True)
        res = select(res, ["count", "name"])
        return res

    def tags_list(self):
        """Get all tags

        :return: List of tags
        """
        return self.ckan.call_action('tag_list')

    @staticmethod
    def _prepare_query(tags, group, organizations):
        q = "groups:{}".format(group)
        if len(tags) > 0:
            tags = " OR ".join(tags)
            q += " AND tags:(\"{}\")".format(tags)
        if len(organizations) > 0:
            q += " AND organization:({})".format(" OR ".join(organizations))

        return q

    def university_list(self):
        """Get list of universities

        :return: List of universities [{'name': ID, 'title': NAME}, ...]
        """

        def filter_uni(org):
            if not org['extras']:
                return False
            category = [extra['value'] for extra in org['extras']
                        if extra['key'] == 'Category']
            return category and category[0] == "University"

        res = self.ckan.call_action('organization_list',
                                    {'all_fields': True,
                                     'include_extras': True})
        res = filter(filter_uni, res)
        return select(res, {'name': 'name', 'display_name': 'title'})


class User:
    def __init__(self, id):

        try:
            self.user = sysadmin.call_action('user_show', {'id': id})
        except ckanapi.NotFound as e:
            raise UserNotFound from e

        self.ckan = ckanapi.RemoteCKAN("http://ckan.local",
                                       self.user["apikey"])
        self.search = Search(self.ckan)

    @staticmethod
    def password_generator(length=16):
        """Generate random password. Password can contain
        all printable characters except whitespace.

        :param length: Length of password
        :return: string
        """
        return ''.join(random.SystemRandom().choice(
            string.printable.replace(string.whitespace, ''))
                       for _ in range(length))

    @classmethod
    def create_new(cls, login, email, fullname, about=None):
        """Create user in CKAN.

        :param login: username
        :param email: user's email
        :return: object of class User
        :raise UserCreateError
        """
        password = cls.password_generator(256)

        try:
            res = sysadmin.call_action('user_create',
                                       {'name': login,
                                        'email': email,
                                        'fullname': fullname,
                                        'password': password,
                                        'about': about})
        except ckanapi.ValidationError as e:
            raise UserCreateError from e
        return cls(res["id"])

    @property
    def id(self):
        return self.user['id']

    @property
    def fullname(self):
        return self.user['fullname']

    @fullname.setter
    def fullname(self, value):
        self._update('fullname', value)

    @property
    def about(self):
        return self.user['about']

    @about.setter
    def about(self, value):
        self._update('about', value)

    @property
    def email(self):
        return self.user['email']

    @email.setter
    def email(self, value):
        self._update('email', value)

    def _update(self, key, value):
        self.user = self.ckan.call_action('user_show', {'id': self.id})
        self.user[key] = value
        self.user = self.ckan.call_action('user_update', self.user)

    def delete(self):
        """Mark user as deleted.
        User is not actually deleted.

        """
        # TODO With students delete also portfolio
        self.ckan.call_action("user_delete", {"id": self.id})

    def student_portfolio(self):
        """get students portfolio

        :raise NotFound
        :raise CKANConsistentError
        :return: StudentPortfolio class
        """
        return StudentPortfolio(self.ckan, username=self.user['name'])

    def is_student(self):
        try:
            self.student_portfolio()
        except NotFound:
            return False
        return True

    def create_student_profile(self, university=None):
        if self.is_student():
            return self.student_portfolio()

        try:
            if university is None:
                university = next(self.universities())
            else:
                university = next(filter(
                    lambda uni: uni.name == university,
                    self.universities()))
        except Exception as e:
            raise PermissionError from e

        self.add_to_group('students')
        self.add_to_group('students-work')
        return StudentPortfolio.create_student_portfolio(
            self.ckan,
            self.user['name'],
            self.user['display_name'],
            university.id)

    def add_to_organization(self, organization):
        sysadmin.call_action('organization_member_create',
                             {'id': organization,
                              'username': self.id,
                              'role': 'editor'})

    def add_to_group(self, group):
        sysadmin.call_action('group_member_create',
                             {'id': group,
                              'username': self.id,
                              'role': 'member'})

    def member_of(self):
        """List of organizations, of which user is a member
        :return: list which contains short names for university
        """
        res = self.ckan.call_action('organization_list_for_user',
                                    {'permission': 'read'})
        return [Organization(self.ckan, org['id']) for org in res]

    def admin_of(self):
        """List of organizations, of which user is a admin
        :return: list which contains Organization
        """
        res = self.ckan.call_action('organization_list_for_user',
                                    {'permission': 'admin'})
        return [Organization(self.ckan, org['id']) for org in res]

    def universities(self):
        """List of universities for user
        :return: list if short names (url) for universities
        """
        return filter(lambda org:
                      org.name in
                      [uni['name'] for uni in self.search.university_list()],
                      self.member_of())

    def companies(self):
        raise NotImplementedError  # TODO


class StudentPortfolio:
    def __init__(self, ckan: ckanapi.RemoteCKAN, *, username=None, id=None):
        """Construct student portfolio from user name

        :param ckan: CKAN API from active user
        :param name: user name or id
        :raise CKANConsistentError: When student has more profile
        """
        self.inc = 1000  # results return at once from CKAN, maximum 1000
        self.ckan = ckan
        if id is not None:
            self.cv = self.ckan.action.package_show(id=id)
        elif username is not None:
            query = 'author:"{}" AND groups:students'.format(username)
            res = ckan.call_action('package_search', {'q': query})
            count = res['count']
            res = res['results']
            if count == 0:
                raise NotFound
            if count != 1:
                res = list(filter(lambda it: it['author']==username, res))
                if len(res) > 1:
                    raise CKANConsistentError
                elif len(res) == 0:
                    raise NotFound
            self.cv = res[0]

            if res[0]['author'] != username:
                raise NotFound("CKAN cheating")

        else:
            raise AttributeError("Missing id or name")

    @property
    def username(self):
        """Author's username
        """
        return self.cv['author']

    @property
    def university(self):
        return Organization(self.cv['owner_org']['id'])

    @classmethod
    def create_student_portfolio(cls, ckan, username, fullname, university):
        url = ckan_url(username + 'profile')
        data = {'name': url,
                'title': fullname,
                'groups': [{'name': 'students'}],
                'owner_org': university,
                'author': username,
                }

        res = url_retry(ckan, url, data)

        return cls(ckan, id=res['id'])

    def tags(self):
        """Get all tags from portfolio

        :return: List of tags name
        """
        return [tag['name'] for tag in self.cv['tags']]

    def items(self):
        """Get list of dictionaries with items from portfolio.

        :return: List: [{'id': str, 'title': str, 'tags': [str, ...]}, ...]
        """

        items = []
        start = 0

        while True:
            res = self.ckan.call_action('package_search', {
                'q': 'author:{} AND groups:students-work'.format(self.username),
                'start': start,
                'rows': self.inc})
            items += [PortfolioItem(self, data=item)
                      for item in res['results']]
            if len(items) < res['count']:
                start += self.inc
                continue
            else:
                break
        items = list(filter(lambda it: it.author==self.username, items))

        return items

    def add_item(self, title, description, tags):
        """ Add one item to students portfolio.

        :param name:
        :param description:
        :param tags:
        :return: :raise UrlConflictError:
        """
        url = ckan_url(self.username + "-" + title)
        data = {'name': url,
                'title': title,
                'owner_org': self.cv['organization']['name'],
                'author': self.cv['author'],
                'notes': description,
                'tags': [{'name': tag} for tag in tags],
                'groups': [{'name': 'students-work'}]
                }
        pkg = url_retry(self.ckan, url, data)
        self.reload()
        return PortfolioItem(self, data=pkg)

    def delete_all(self):
        raise NotImplementedError  # TODO

    def reload(self):
        # get tags from all students works
        tags = [tag for it in self.items() for tag in it.tags()]
        tags = list(set(tags))  # make list unique
        tags = [{'name': tag} for tag in tags]
        res = self.ckan.call_action('package_patch', {'id': self.cv['id'],
                                                      'tags': tags})
        self.cv = res

    def change_university(self):
        raise NotImplementedError  # TODO hard operation


class PortfolioItem:
    def __init__(self, portfolio: StudentPortfolio, *, id=None, data=None):
        """Load portfolio item from CKAN or make this class
        from loaded data. Use with id or data attribute.

        :param portfolio: Owning portfolio class
        :param id: id of portfolio item
        :param data: data of portfolio item
        :raise AttributeError: id and data not provided
        :raise ValueError: data dictionary missing required values
        """
        self.portfolio = portfolio
        self.ckan = portfolio.ckan
        if data is not None:
            if set(self.values) > set(data.keys()):
                raise ValueError('Data dictionary missing values:{}'
                                 .format(set(self.values) > set(data.keys())))
            self.item = data
        elif id is not None:
            self.item = self.ckan.action.package_show(id=id)
        else:
            raise AttributeError('Missing id or data')

    @property
    def author(self):
        return self.item['author']

    @property
    def id(self):
        return self.item['id']

    @property
    def name(self):
        return self.name['name']

    @property
    def title(self):
        return self.name['title']

    @title.setter
    def title(self, value):
        self.item = self.ckan.action.package_patch(id=self.id, title=value)

    @property
    def description(self):
        return self.item['description']

    @description.setter
    def description(self, value):
        self.item = self.ckan.action.package_patch(id=self.id,
                                                   description=value)

    def tags(self):
        return [tag['name'] for tag in self.item['tags']]

    def add_tags(self, tags):
        if isinstance(tags, str):
            tags=[tags]
        if not isinstance(tags, list):
            raise TypeError("tags must be list, or str")
        self.set_tags(self.tags() + tags)

    def set_tags(self, tags):
        tags = list(set(tags))
        self.item = self.ckan.action.package_patch(
            id=self.id,
            tags=[{'name': tag} for tag in tags],)
        self.portfolio.reload()

    values = ['id', 'tags', 'name', 'title', ]

    def upload_file(self, title, description, file):
        """Upload file to item. It is possible to upload file only to
        items not to portfolio. Can be upload more files.

        :param title: Title of new file
        :param description: Description of file
        :param file: File to upload.
        """
        self.ckan.call_action('resource_create',
                              {'package_id': self.id,
                               'url': '',
                               'name': title,
                               'description': description,
                               },
                              files={'upload': file})

    def delete_file(self, id):
        raise NotImplementedError  # TODO

    def file_list(self):
        raise NotImplementedError  # TODO

    def delete(self):
        raise NotImplementedError  # TODO


class Organization:
    def __init__(self, ckan, id):
        self.ckan = ckan
        self.org = ckan.call_action('organization_show',
                                    {'id': id,
                                     'include_users': False,
                                     'include_followers': False})

    @classmethod
    def create_university(cls, ckan: ckanapi.RemoteCKAN,
                          name, title, description=None):
        """Creates new university profile

        :param ckan: CKAN api from user which creates organization
        :param name: short name for University
        :param title: Full name for University
        :return: Organization class
        :raise NameAlreadyExistError:
        :raise ckanapi.CKANAPIError:
        """
        return cls(ckan, cls._create_organization(
            ckan, name, title, description, 'University')['id'])

    @classmethod
    def create_company(cls, ckan: ckanapi.RemoteCKAN,
                       name, title, description=None):
        """Creates new company profile.
        see create_university
        """
        return cls(ckan, cls._create_organization(
            ckan, name, title, description, 'Company')['id'])

    @staticmethod
    def _create_organization(ckan, name, title, description, category):
        """

        :type ckan: ckanapi.RemoteCKAN
        :raise NameAlreadyExistError: When name conflicts
        :raise ckanapi.CKANAPIError: superclass for CKAN related errors
        """
        try:
            res = ckan.action.organization_create(
                name=ckan_url(name),
                extras=[{'key': 'Category', 'value': category}],
                title=title,
                description=description,
            )
        except ckanapi.ValidationError as e:
            if e.error_dict['name'] == \
                    ['Group name already exists in database']:
                raise NameAlreadyExistError from e
            raise e
        return res

    @property
    def id(self):
        return self.org['id']

    @property
    def title(self):
        return self.org['title']

    @title.setter
    def title(self, value):
        self.org = self.ckan.action.organization_patch(
            id=self.id, title=value)

    @property
    def description(self):
        return self.org['description']

    @description.setter
    def description(self, value):
        self.org = self.ckan.action.organization_patch(
            id=self.id, description=value)

    @property
    def name(self):
        return self.org['name']

    def update(self, values: dict):
        """Update information at once used input dictionary.

        :param values: values to change
        """
        values['id'] = self.id
        self.org = self.ckan.call_action('organization_patch', values)

    @property
    def image_url(self):
        return self.org['image_display_url']

    def upload_logo(self, file):
        self.org = self.ckan.action.organization_patch(id=self.id,
                                                       image_upload=file)

    def is_university(self):
        if not self.org['extras']:
            return False
        category = [extra['value'] for extra in self.org['extras']
                    if extra['key'] == 'Category']
        return category and category[0] == "University"

    def is_company(self):
        if not self.org['extras']:
            return False
        category = [extra['value'] for extra in self.org['extras']
                    if extra['key'] == 'Category']
        return category and category[0] == "Company"

    def delete(self):
        raise NotImplementedError


class UserCreateError(Exception):
    pass


class NotFound(Exception):
    pass


class UserNotFound(NotFound):
    pass


class UrlConflictError(Exception):
    pass


class NameAlreadyExistError(Exception):
    pass


# TODO LOG TO DATABASE
class CKANConsistentError(Exception):
    pass


def select(result, keys):
    """Create new list of dictionaries from list of dictionaries,
    which contains only specified keys. Can be also used for change
    dictionary keys.
    example #1:
    SQL SELECT foo, bar, foobar FROM data;
    select(data, ['foo', 'bar', 'foobar'])

    example #2:
    SQL SELECT foo AS bar, ... FROM data;
    select(data, {'foo': 'bar', ...}

    :type keys: list or dict
    :param keys: Keys which will be included in result.
    :param result: List of dictionaries
    :return: List of dictionaries
    """
    if isinstance(keys, dict):
        return [{keys[key]: orig[key] for key in keys} for orig in result]
    else:
        return [{key: orig[key] for key in keys} for orig in result]


def ckan_url(text: str):
    """Make suitable string for CKAN url. This string is used
     in names of packages, users, organizations, groups,
     resources. This function doesn't handle uniqueness.
     CKAN url can contains only lowercase ASCII and -_
     url must have between 2 and 100 characters.


    :param text: Non empty Unicode string
    :return: String contains only lowercase ASCII or -_
    """
    text = text.strip().replace(" ", "-").lower()
    allow = string.ascii_lowercase + string.digits + "_-"
    url = re.sub('[^%s]' % allow, '', text)
    url = url * 2 if len(url) < 2 else url[:100]  # limits
    return url


def url_retry(ckan, name, data, retry=3):
    url = ckan_url(name)
    for attempt in range(retry):  # retry loop for conflicting urls
        try:
            data['name'] = url
            pkg = ckan.call_action('package_create', data)
            break  # success, end retry loop
        except ckanapi.ValidationError as e:
            if e.error_dict['name'][0] == 'That URL is already in use.':
                url = ckan_url(name + "_" + str(uuid.uuid4()))
                continue
            else:
                raise ValueError from e
    else:
        raise UrlConflictError({'url': url})
    return pkg

# from pprint import pprint
# cccp = ckanapi.RemoteCKAN("http://ckan.local")

# pprint(u.admin_of())
# u.create_student_profile()
# o = Organization.create_university(u.ckan, 'uni39', '')

# u.add_to_organization('lut')
# u.create_student_profile()
# u.fullname = 'Vítězslav Kříž'
# pprint(u.user['id'])

#
# u = User('vita')
# uni = Organization(u.ckan, 'uni39')
# pprint(uni.org)
# print(uni.is_company())
# print(uni.is_university())
#
# pprint(p.tags())
# pprint(p.items())
# u = User.create_new('vit-', 'email', 'Chuj Chujovy')
# pprint(u.user)
# p = u.student_portfolio()
# pprint(p.cv)
#
# u.add_to_organization('lut')
#

# u.create_student_profile()

# u = User('test_14476145916207347_1_6f8a0054-6c53-45bc-97d0-a329720f01e4')
# p = u.student_portfolio()
# pprint(p.add_item('Report46', 'Description', ['CKAN', 'PHP']))
# pprint(p.tags())
# pprint(len(p.items()))
# p.update()
# pprint(p.tags())

#

# p = u.student_portfolio()
# pprint(p.cv)

# pprint(u)
# pprint(u.id)
#
# pprint(search_students(['C Sharp'], []))
# pprint(top_tags())
# pprint(tags_list())
# pprint(university_list())

# user = "foo4"
# pprint.pprint(user_create(user, "email", "vita"))
# pprint.pprint(user_delete(user))
