# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import functools

import mock
import pytest
from pyramid import testing
from pyramid.request import apply_request_extensions

from lti import constants
from lti.services.auth_data import AuthDataService


def autopatcher(request, target, **kwargs):
    """Patch and cleanup automatically. Wraps :py:func:`mock.patch`."""
    options = {'autospec': True}
    options.update(kwargs)
    patcher = mock.patch(target, **options)
    obj = patcher.start()
    request.addfinalizer(patcher.stop)
    return obj


@pytest.fixture
def patch(request):
    return functools.partial(autopatcher, request)


@pytest.fixture
def pyramid_request():
    """
    Return a dummy Pyramid request object.

    This is the same dummy request object as is used by the pyramid_config
    fixture below.

    """
    pyramid_request = testing.DummyRequest()

    pyramid_request.POST.update({
        constants.OAUTH_CONSUMER_KEY: 'TEST_OAUTH_CONSUMER_KEY',
        constants.CUSTOM_CANVAS_USER_ID: 'TEST_CUSTOM_CANVAS_USER_ID',
        constants.CUSTOM_CANVAS_COURSE_ID: 'TEST_CUSTOM_CANVAS_COURSE_ID',
        constants.CUSTOM_CANVAS_ASSIGNMENT_ID: 'TEST_CUSTOM_CANVAS_ASSIGNMENT_ID',
        constants.EXT_CONTENT_RETURN_TYPES: 'TEST_EXT_CONTENT_RETURN_TYPES',
        constants.EXT_CONTENT_RETURN_URL: 'TEST_EXT_CONTENT_RETURN_URL',
        constants.LIS_OUTCOME_SERVICE_URL: 'TEST_LIS_OUTCOME_SERVICE_URL',
        constants.LIS_RESULT_SOURCEDID: 'TEST_LIS_RESULT_SOURCEDID',
    })

    return pyramid_request


@pytest.yield_fixture
def pyramid_config(pyramid_request):
    """
    Return a test Pyramid config (Configurator) object.

    The returned Configurator uses the dummy request from the pyramid_request
    fixture above.

    """
    # Settings that will end up in pyramid_request.registry.settings.
    settings = {
        'lti_server': 'http://TEST_LTI_SERVER.com',
    }

    with testing.testConfig(request=pyramid_request, settings=settings) as config:
        config.include('pyramid_services')

        apply_request_extensions(pyramid_request)

        auth_data_svc = mock.create_autospec(AuthDataService, instance=True)
        auth_data_svc.get_canvas_server.return_value = 'https://TEST_CANVAS_SERVER.com'
        auth_data_svc.get_lti_secret.return_value = 'TEST_CLIENT_SECRET'
        auth_data_svc.get_lti_token.return_value = 'TEST_OAUTH_ACCESS_TOKEN'
        auth_data_svc.get_lti_refresh_token.return_value = 'TEST_OAUTH_REFRESH_TOKEN'
        config.register_service(auth_data_svc, name='auth_data')

        yield config


@pytest.fixture
def auth_data_svc(pyramid_request):
    return pyramid_request.find_service(name='auth_data')


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    """Add all the routes that would be added in production."""
    pyramid_config.add_route('lti_setup', '/lti_setup')
