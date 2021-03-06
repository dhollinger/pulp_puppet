import json
import unittest
import base64
import urlparse

import mock
from pulp_puppet.forge.views.releases import ReleasesView, ReleasesPost36View
from django.test.client import RequestFactory


class TestReleasesView(unittest.TestCase):
    """
    Tests for ReleasesView.
    """
    FAKE_VIEW_DATA = {'foo/bar': [{'version': '1.0.0', 'file': '/tmp/foo', 'dependencies': []}]}

    @mock.patch('pulp_puppet.forge.views.releases.ReleasesView._get_credentials')
    def test_releases_missing_module(self, mock_get_credentials):
        """
        Test that proper response is returned when module name is not specified
        """
        mock_get_credentials.return_value = ()
        rf = RequestFactory()
        mock_request = rf.get('/blah/')

        releases_view = ReleasesView()
        response = releases_view.get(mock_request, resource_type='repository', resource='repo-id')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, 'Module name is missing.')

    @mock.patch('pulp_puppet.forge.views.releases.ReleasesView._get_parameters')
    @mock.patch('pulp_puppet.forge.views.releases.ReleasesView._get_credentials')
    def test_releases_missing_auth(self, mock_get_credentials, mock_get_parameters):
        """
        Test that 401 is returned when basic auth is not used for pre 3.3
        """
        mock_get_parameters.return_value = {'module': 'fake-module'}
        mock_get_credentials.return_value = ()
        mock_request = mock.MagicMock()

        releases_view = ReleasesView()
        response = releases_view.get(mock_request)
        self.assertEqual(response.status_code, 401)

    @mock.patch('pulp_puppet.forge.views.releases.ReleasesView._get_parameters')
    @mock.patch('pulp_puppet.forge.views.releases.ReleasesView._get_credentials')
    def test_releases_bad_resource_type(self, mock_get_credentials, mock_get_parameters):
        """
        Test that only consumer or repository resource type is allowed
        """
        mock_get_parameters.return_value = {'module': 'fake-module'}
        mock_get_credentials.return_value = ()
        mock_request = mock.MagicMock()

        releases_view = ReleasesView()
        response = releases_view.get(mock_request, resource_type='foo')
        self.assertEqual(response.status_code, 404)

    @mock.patch('pulp_puppet.forge.releases.view')
    @mock.patch('pulp_puppet.forge.views.releases.ReleasesView._get_parameters')
    @mock.patch('pulp_puppet.forge.views.releases.ReleasesView._get_credentials')
    def test_releases_get_module_without_version(self, mock_get_credentials, mock_get_parameters,
                                                 mock_view):
        """
        Test getting a module without specifying a version
        """
        mock_get_parameters.return_value = {'module': 'food/bar'}
        mock_get_credentials.return_value = ('consumer1', 'repo1')
        mock_request = mock.MagicMock()
        mock_view.return_value = self.FAKE_VIEW_DATA

        releases_view = ReleasesView()
        response = releases_view.get(mock_request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, json.dumps(self.FAKE_VIEW_DATA))

    def test_releases_get_credentials(self):
        """
        Test getting credentials from header
        """
        releases_view = ReleasesView()
        real_creds = ('test', '123')
        encoded_creds = base64.encodestring('test:123')
        headers = {'HTTP_AUTHORIZATION': encoded_creds}
        creds = releases_view._get_credentials(headers)
        self.assertEqual(real_creds, creds)

    def test_releases_get_bad_credentials(self):
        """
        Test getting improperly formatted credentials from header
        """
        releases_view = ReleasesView()
        encoded_creds = base64.encodestring('blah')
        headers = {'HTTP_AUTHORIZATION': encoded_creds}
        creds = releases_view._get_credentials(headers)
        self.assertEqual(creds, None)

    def test_releases_get_parameters(self):
        """
        Test getting request parameters from HTTP GET request
        """
        releases_view = ReleasesView()
        module = 'test-module'
        path = '/test/'
        formatted_module_name = 'test/module'
        get_dict = {'module': module}
        parameters = releases_view._get_parameters(get_dict, path)
        self.assertEqual(formatted_module_name, parameters.get('module'))


class TestReleasesPost36View(unittest.TestCase):
    """
    Tests for ReleasesPost36View.
    """

    def test_releases_post_36_get_path_parameters(self):
        """
        Test getting request parameters from HTTP GET request
        """
        releases_view = ReleasesPost36View()
        param = 'foo-bar-1.0.0'
        version = '1.0.0'
        formatted_module_name = 'foo/bar'
        parameters = releases_view._get_parameters({}, '/v3/releases/' + param)
        self.assertEqual(formatted_module_name, parameters.get('module'))
        self.assertEqual(version, parameters.get('version'))
        self.assertEqual(param, parameters.get('path'))

    def test_releases_post_36_get_query_parameters(self):
        """
        Test getting request parameters from HTTP GET request
        """
        releases_view = ReleasesPost36View()
        module = 'test-module'
        path = '/test/'
        formatted_module_name = 'test/module'
        get_dict = {'module': module}
        parameters = releases_view._get_parameters(get_dict, path)
        self.assertEqual(formatted_module_name, parameters.get('module'))

    @mock.patch('pulp_puppet.forge.views.releases.ReleasesPost36View._get_credentials')
    def test_releases_post_36_get_bad_parameters(self, mock_get_credentials):
        """
        Test getting malformed request parameters from HTTP GET request
        """
        mock_get_credentials.return_value = ('consumer1', 'repo1')
        rf = RequestFactory()
        mock_request = rf.get('/v3/releases/blah!')
        releases_view = ReleasesPost36View()
        response = releases_view.get(mock_request)
        self.assertEqual(response.status_code, 400)

    @mock.patch('pulp_puppet.forge.views.releases.ReleasesView._get_credentials')
    def test_releases_post_36_get_single_module_without_version(self, mock_get_credentials):
        """
        Test getting a single module without specifying a version
        """
        mock_get_credentials.return_value = ('consumer1', 'repo1')
        rf = RequestFactory()
        mock_request = rf.get('/v3/releases/foo-bar')
        releases_view = ReleasesPost36View()
        response = releases_view.get(mock_request)
        self.assertEqual(response.status_code, 400)

    def test_format_query_string_no_version(self):
        result = ReleasesPost36View._format_query_string(
            base_url='https://foo.com/api/v3/',
            module_name='modulename', module_version=None,
            offset=5, limit=2
        )

        data = urlparse.urlparse(result)
        self.assertEquals('https', data.scheme)
        self.assertEquals('foo.com', data.netloc)
        self.assertEquals('/api/v3/', data.path)

        query = urlparse.parse_qs(data.query)
        self.assertEquals(['modulename'], query['module'])
        self.assertEquals(['2'], query['limit'])
        self.assertEquals(['5'], query['offset'])
        self.assertTrue('version' not in query)

    def test_format_query_string_with_version(self):
        result = ReleasesPost36View._format_query_string(
            base_url='https://foo.com/api/v3/',
            module_name='modulename', module_version='3.5',
            offset=5, limit=2
        )
        data = urlparse.urlparse(result)
        query = urlparse.parse_qs(data.query)
        self.assertEquals(['3.5'], query['version'])

    def test_format_results_with_single_module(self):
        release = ReleasesPost36View()
        module = 'foo/bar'
        get_dict = {'module': module, 'version': '1.0.0', 'path': 'foo-bar-1.0.0'}
        result_str = release.format_results({'foo/bar': [
            {'dependencies': [('apple', '42.5')],
             'version': '1.0', 'file': 'foo', 'file_md5': 'bar'},
        ]}, get_dict, '/v3/releases').content
        module_data = json.loads(result_str)

        self.assertEquals('foo/bar', module_data['metadata']['name'])
        self.assertEquals('1.0', module_data['metadata']['version'])
        self.assertEquals('foo', module_data['file_uri'])
        self.assertEquals('bar', module_data['file_md5'])
        dependencies = module_data['metadata']['dependencies']
        self.assertEquals('apple', dependencies[0]['name'])
        self.assertEquals('42.5', dependencies[0]['version_requirement'])

    @mock.patch('pulp_puppet.forge.views.releases.ReleasesPost36View._get_parameters')
    def test_format_results_pagination_defaults(self, mock_get_parameters):
        mock_get_parameters.return_value = {'module': 'foo/bar'}
        release = ReleasesPost36View()
        module = 'foo/bar'
        get_dict = {'module': module}
        result_str = release.format_results({'foo/bar': []}, get_dict, '/v3/releases').content
        result = json.loads(result_str)

        self.assertEquals(20, result['pagination']['limit'])
        self.assertEquals(0, result['pagination']['offset'])
        self.assertEquals(0, result['pagination']['total'])
        self.assertEquals(u'/v3/releases?limit=20&module=foo%2Fbar&offset=0',
                          result['pagination']['first'])
        self.assertEquals(u'/v3/releases?limit=20&module=foo%2Fbar&offset=0',
                          result['pagination']['current'])
        self.assertEquals(None, result['pagination']['previous'])
        self.assertEquals(None, result['pagination']['next'])

    @mock.patch('pulp_puppet.forge.views.releases.ReleasesPost36View._get_parameters')
    def test_format_results_pagination_middle_page(self, mock_get_parameters):
        mock_get_parameters.return_value = {'module': 'foo/bar'}
        release = ReleasesPost36View()
        module = 'foo/bar'
        get_dict = {'module': module,
                    'limit': '1',
                    'offset': '1'}
        result_str = release.format_results({'foo/bar': [
            {'dependencies': [], 'version': '1.0', 'file': 'foo', 'file_md5': 'bar'},
            {'dependencies': [], 'version': '2.0', 'file': 'foo', 'file_md5': 'bar'},
            {'dependencies': [], 'version': '3.0', 'file': 'foo', 'file_md5': 'bar'},
        ]}, get_dict, '/v3/releases').content
        result = json.loads(result_str)

        self.assertEquals(1, result['pagination']['limit'])
        self.assertEquals(1, result['pagination']['offset'])
        self.assertEquals(3, result['pagination']['total'])
        self.assertEquals(u'/v3/releases?limit=1&module=foo%2Fbar&offset=0',
                          result['pagination']['first'])
        self.assertEquals(u'/v3/releases?limit=1&module=foo%2Fbar&offset=0',
                          result['pagination']['previous'])
        self.assertEquals(u'/v3/releases?limit=1&module=foo%2Fbar&offset=1',
                          result['pagination']['current'])
        self.assertEquals(u'/v3/releases?limit=1&module=foo%2Fbar&offset=2',
                          result['pagination']['next'])
        self.assertEquals(1, len(result['results']))
        self.assertEquals('2.0', result['results'][0]['metadata']['version'])

    @mock.patch('pulp_puppet.forge.views.releases.ReleasesPost36View._get_parameters')
    def test_format_results_pagination_last_page(self, mock_get_parameters):
        mock_get_parameters.return_value = {'module': 'foo/bar'}
        release = ReleasesPost36View()
        module = 'foo/bar'
        get_dict = {'module': module,
                    'limit': '1',
                    'offset': '2'}
        result_str = release.format_results({'foo/bar': [
            {'dependencies': [], 'version': '1.0', 'file': 'foo', 'file_md5': 'bar'},
            {'dependencies': [], 'version': '2.0', 'file': 'foo', 'file_md5': 'bar'},
            {'dependencies': [], 'version': '3.0', 'file': 'foo', 'file_md5': 'bar'},
        ]}, get_dict, '/v3/releases').content
        result = json.loads(result_str)

        self.assertEquals(1, result['pagination']['limit'])
        self.assertEquals(2, result['pagination']['offset'])
        self.assertEquals(3, result['pagination']['total'])
        self.assertEquals(u'/v3/releases?limit=1&module=foo%2Fbar&offset=0',
                          result['pagination']['first'])
        self.assertEquals(u'/v3/releases?limit=1&module=foo%2Fbar&offset=1',
                          result['pagination']['previous'])
        self.assertEquals(u'/v3/releases?limit=1&module=foo%2Fbar&offset=2',
                          result['pagination']['current'])
        self.assertEquals(None, result['pagination']['next'])
        self.assertEquals(1, len(result['results']))
        self.assertEquals('3.0', result['results'][0]['metadata']['version'])

    @mock.patch('pulp_puppet.forge.views.releases.ReleasesPost36View._get_parameters')
    def test_format_results_render_module(self, mock_get_parameters):
        mock_get_parameters.return_value = {'module': 'foo/bar'}
        release = ReleasesPost36View()
        module = 'foo/bar'
        get_dict = {'module': module}
        result_str = release.format_results({'foo/bar': [
            {'dependencies': [('apple', '42.5')],
             'version': '1.0', 'file': 'foo', 'file_md5': 'bar'},
        ]}, get_dict, '/v3/releases').content
        result = json.loads(result_str)

        module_data = result['results'][0]
        self.assertEquals('foo/bar', module_data['metadata']['name'])
        self.assertEquals('1.0', module_data['metadata']['version'])
        self.assertEquals('foo', module_data['file_uri'])
        self.assertEquals('bar', module_data['file_md5'])
        dependencies = module_data['metadata']['dependencies']
        self.assertEquals('apple', dependencies[0]['name'])
        self.assertEquals('42.5', dependencies[0]['version_requirement'])
