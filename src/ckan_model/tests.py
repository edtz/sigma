from django.test import TestCase
from . import production
import uuid
import time


class UserTest(TestCase):
    def setUp(self):
        super().setUp()
        self.users = []

    def tearDown(self):
        super().tearDown()
        # TODO delete users

    def test_new_basic_user(self):
        u = self._user()
        self.assertFalse(u.is_student())

    def _user(self):
        name = Helper.get_name()
        u = production.User.create_new(name, "user@name.example", name)
        self.assertIsInstance(u, production.User, "User create")
        self.assertEqual(name, u.user['name'], 'Username match')
        # self.users.append(u['id'])
        return u

    def _user_student_portfolio(self):
        u = self._user()
        u.add_to_organization('lut')  # TODO make general
        u.create_student_profile()
        p = u.student_portfolio()
        return p

    def test_create_student_profile(self):
        u = self._user()
        self.assertRaises(production.NotFound, u.student_portfolio)
        self.assertFalse(u.is_student())
        self.assertRaises(PermissionError, u.create_student_profile)
        self.assertRaises(PermissionError, u.create_student_profile, 'lut')
        u.add_to_organization('lut')  # TODO make general
        u.create_student_profile()
        self.assertTrue(u.is_student())
        p = u.student_portfolio()
        self.assertIsInstance(p, production.StudentPortfolio,
                              "Student has portfolio")

    def test_add_one_student_work(self):
        p = self._user_student_portfolio()
        p.add_item('Name', 'Description for item', ['AAA'])
        self.assertIn('AAA', p.tags())

    def test_add_more_student_work(self):
        p = self._user_student_portfolio()
        tags = [['Aaa', 'Bbb'],
                ['Aaa', 'Ccc', 'Bbb', 'Ddd'],
                ['Eee', 'Fff', 'Ggg'],
                ['Hhh']]
        flattened_tags = set([x for t in tags for x in t])
        for t in tags:
            p.add_item('Name', 'Desc', t)

        self.assertSetEqual(flattened_tags, set(p.tags()))

    def test_more_student_works(self):
        p = self._user_student_portfolio()
        p.inc = 5  # change to run loop more times
        tags = ["t{:04}".format(i) for i in range(11)]
        for t in tags:
            p.add_item("Same name for everyone" ,'Description', [t])

        self.assertEqual(len(p.tags()),len(tags))
        self.assertSetEqual(set(p.tags()),set(tags))

    def test_create_portfolio_conflict(self):

        name = Helper.get_name()
        u = production.User.create_new(name, "user@name.example", name)
        u.add_to_organization('lut')  # TODO make general
        u.create_student_profile()
        p1 = u.student_portfolio()
        p1.add_item('profile', 'Defect', [])
        self.assertTrue(u.is_student())
        name = p1.username + "-"
        u2 = production.User.create_new(name, "user@name.example", name)
        self.assertEqual(u2.user['name'], name)
        u2.add_to_organization('lut')  # TODO make general
        self.assertFalse(u2.is_student())
        p2 = u2.create_student_profile()
        self.assertIsInstance(p2, production.StudentPortfolio)
        self.assertTrue(u2.is_student())
        p2.add_item('PortfolioItem','', ['ConflictTag'])
        self.assertIn('ConflictTag', p2.tags())
        self.assertTrue(len(p1.tags()) == 0, "First portfolio without tags")
        p1.reload()
        self.assertTrue(len(p1.tags()) == 0, "1st portfolio after reload")


class PortfolioTest(TestCase):
    def setUp(self):
        name = Helper.get_name()
        self.user = production.User.create_new(name, "user@name.example", name)
        self.user.add_to_organization('lut')  # TODO make general
        self.user.create_student_profile()

    def test_default(self):
        p = self.user.student_portfolio()
        self.assertIsInstance(p, production.StudentPortfolio)
        self.assertEqual(len(p.tags()), 0, 'New portfolio withou tags')
        p.add_item('Name', 'description', ['test1'])
        self.assertIn('test1', p.tags())

    def test_portfolio_item_tags(self):
        p = self.user.student_portfolio()
        i = p.add_item('Name', 'description', [])
        self.assertEqual(len(i.tags()), 0)
        i.add_tags('test1')
        self.assertEqual(len(i.tags()), 1)
        self.assertListEqual(p.tags(), i.tags())
        self.assertListEqual(p.tags(), ['test1'])
        i.add_tags('test2')
        self.assertEqual(len(i.tags()), 2)
        self.assertListEqual(p.tags(), i.tags())
        self.assertListEqual(p.tags(), ['test1', 'test2'])
        i.set_tags([])
        self.assertEqual(len(i.tags()), 0)
        self.assertListEqual(p.tags(), i.tags())

        i2 = p.add_item('Name', 'description', [])
        i2.add_tags(['test3', 'test4'])
        self.assertEqual(len(i2.tags()), 2)
        self.assertListEqual(p.tags(), i2.tags())
        i.add_tags(['test3'])
        self.assertEqual(len(i2.tags()), 2)
        self.assertListEqual(p.tags(), i2.tags())
        self.assertListEqual(['test3'], i.tags())
        i2.set_tags(set(i2.tags()) - {'test3'})
        self.assertEqual(len(p.tags()), 2)
        self.assertListEqual(p.tags(), ['test3', 'test4'])


class StaticTest(TestCase):
    def test_select(self):
        data = [
            {'name': 'but', 'title': 'Brno', 'country': 'CZ'},
            {'name': 'lut', 'title': 'Lappeenranta', 'country': 'FI'},
            {'name': 'uef', 'title': 'Eastern Finnland', 'country': 'FI'}]

        r1 = production.select(data, ['name'])
        self.assertEqual(len(r1), len(data))
        self.assertIsInstance(r1, list)
        for x in r1: self.assertIn('name', x)
        for x in r1: self.assertNotIn('title', x)
        for x in r1: self.assertNotIn('country', x)

        r2 = production.select(data, ['name', 'title', 'country'])
        r3 = production.select(data, {'name':'country',
                                      'title':'name',
                                      'country':'title'})

        r4 = production.select(r3, {'country': 'name',
                                    'name':'title',
                                    'title':'country'})

        self.assertListEqual(r2, data)
        self.assertNotEqual(r3, data)
        self.assertListEqual(r4, data)




class Helper:
    i = 0

    @classmethod
    def get_name(cls):
        """Try to get unique name for test suite.
        Uniqueness is not guaranteed.
        :return: Name which can be used in CKAN url
        """
        cls.i+=1
        return production.ckan_url(
            "test_{}_{}_{}".format(str(time.time()).replace(".", "-"),
                                   cls.i, uuid.uuid4())
        )