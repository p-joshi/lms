from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError
from requests import Response

from lms.resources import LTILaunchResource
from lms.services import HAPIError, HAPINotFoundError
from lms.services.group_info_upsert import GroupInfoUpsert
from lms.services.h_api_requests import HAPIRequests
from lms.services.lti_h import LTIHService
from lms.values import HUser, LTIUser


class TestUpsertCourseGroup:
    def test_it_does_nothing_if_the_feature_isnt_enabled(
        self, context, pyramid_request, hapi_svc, lti_h_svc
    ):
        # If the auto provisioning feature isn't enabled for this application
        # instance then upsert_course_group() doesn't do anything - just calls the
        # wrapped view.
        context.provisioning_enabled = False

        lti_h_svc.upsert_course_group()

        hapi_svc.patch.assert_not_called()
        hapi_svc.put.assert_not_called()

    def test_it_defaults_to_None_if_request_params_are_missing(
        self, context, group_info_upsert, params, pyramid_request, lti_h_svc
    ):
        pyramid_request.params = {}

        lti_h_svc.upsert_course_group()

        target_call = mock.call(
            context.h_authority_provided_id,
            "TEST_OAUTH_CONSUMER_KEY",
            **{param: None for param in params.keys()}
        )

        assert group_info_upsert.call_args_list == [target_call]

    def test_it_calls_the_group_update_api(
        self, context, pyramid_request, hapi_svc, lti_h_svc
    ):
        lti_h_svc.upsert_course_group()

        hapi_svc.patch.assert_called_once_with(
            "groups/test_groupid", {"name": "test_group_name"}
        )

    def test_it_raises_if_updating_the_group_fails(
        self, context, pyramid_request, hapi_svc, lti_h_svc
    ):
        # If the group update API call fails for any non-404 reason then the
        # view raises an exception and an error page is shown.
        hapi_svc.patch.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            lti_h_svc.upsert_course_group()

    def test_it_creates_the_group_if_it_doesnt_exist(
        self, context, pyramid_request, hapi_svc, lti_h_svc
    ):
        pyramid_request.lti_user = LTIUser(
            user_id="TEST_USER_ID",
            oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY",
            roles="instructor",
        )
        hapi_svc.patch.side_effect = HAPINotFoundError()

        lti_h_svc.upsert_course_group()

        hapi_svc.put.assert_called_once_with(
            "groups/test_groupid",
            {"groupid": "test_groupid", "name": "test_group_name"},
            "acct:test_username@TEST_AUTHORITY",
        )

    def test_it_raises_if_creating_the_group_fails(
        self, context, pyramid_request, hapi_svc, lti_h_svc
    ):
        pyramid_request.lti_user = LTIUser(
            user_id="TEST_USER_ID",
            oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY",
            roles="instructor",
        )
        hapi_svc.patch.side_effect = HAPINotFoundError()
        hapi_svc.put.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            lti_h_svc.upsert_course_group()

    def test_it_400s_with_missing_group_and_unpriviledged_user(
        self, context, pyramid_request, hapi_svc, lti_h_svc
    ):
        pyramid_request.lti_user = LTIUser(
            user_id="TEST_USER_ID",
            oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY",
            roles="learner",
        )
        hapi_svc.patch.side_effect = HAPINotFoundError()

        with pytest.raises(
            HTTPBadRequest, match="Instructor must launch assignment first"
        ):
            lti_h_svc.upsert_course_group()

        hapi_svc.put.assert_not_called()

    def test_it_upserts_the_GroupInfo_into_the_db(
        self, params, group_info_upsert, context, pyramid_request, lti_h_svc
    ):
        lti_h_svc.upsert_course_group()

        assert group_info_upsert.call_args_list == [
            mock.call(
                context.h_authority_provided_id, "TEST_OAUTH_CONSUMER_KEY", **params
            )
        ]

    def test_it_doesnt_upsert_GroupInfo_into_the_db_if_creating_the_group_fails(
        self, group_info_upsert, context, pyramid_request, hapi_svc, lti_h_svc
    ):
        hapi_svc.patch.side_effect = HAPINotFoundError()
        hapi_svc.put.side_effect = HAPIError("Oops")

        try:
            lti_h_svc.upsert_course_group()
        except:
            pass

        group_info_upsert.assert_not_called()

    @pytest.fixture
    def params(self):
        return dict(
            context_id="test_context_id",
            context_title="test_context_title",
            context_label="test_context_label",
            tool_consumer_info_product_family_code="test_tool_consumer_info_product_family_code",
            tool_consumer_info_version="test_tool_consumer_info_version",
            tool_consumer_instance_name="test_tool_consumer_instance_name",
            tool_consumer_instance_description="test_tool_consumer_instance_description",
            tool_consumer_instance_url="test_tool_consumer_instance_url",
            tool_consumer_instance_contact_email="test_tool_consumer_instance_contact_email",
            tool_consumer_instance_guid="test_tool_consumer_instance_guid",
            custom_canvas_api_domain="test_custom_canvas_api_domain",
            custom_canvas_course_id="test_custom_canvas_course_id",
        )

    @pytest.fixture
    def pyramid_request(self, params, pyramid_request):
        pyramid_request.params = params
        return pyramid_request


class TestUpsertHUser:
    def test_it_invokes_patch_for_user_update(
        self, context, pyramid_request, hapi_svc, lti_h_svc
    ):

        lti_h_svc.upsert_h_user()

        hapi_svc.patch.assert_called_once_with(
            "users/test_username", {"display_name": "test_display_name"}
        )

    def test_it_raises_if_patch_raises_unexpected_error(
        self, context, pyramid_request, hapi_svc, lti_h_svc
    ):
        hapi_svc.patch.side_effect = HAPIError("whatever")

        with pytest.raises(HTTPInternalServerError, match="whatever"):
            lti_h_svc.upsert_h_user()

    def test_it_raises_if_post_raises(
        self, context, pyramid_request, hapi_svc, lti_h_svc
    ):
        # It will only invoke POST if PATCH raises HAPINotFoundError
        hapi_svc.patch.side_effect = HAPINotFoundError("whatever")
        hapi_svc.post.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            lti_h_svc.upsert_h_user()

    def test_it_doesnt_use_the_h_api_if_feature_not_enabled(
        self, context, hapi_svc, pyramid_request, lti_h_svc
    ):
        context.provisioning_enabled = False

        lti_h_svc.upsert_h_user()

        hapi_svc.post.assert_not_called()

    def test_it_raises_if_h_user_raises(self, context, pyramid_request, lti_h_svc):
        type(context).h_user = mock.PropertyMock(side_effect=HTTPBadRequest("Oops"))

        with pytest.raises(HTTPBadRequest, match="Oops"):
            lti_h_svc.upsert_h_user()

    def test_it_raises_if_h_provider_raises(self, context, pyramid_request, lti_h_svc):
        type(context).h_provider = mock.PropertyMock(side_effect=HTTPBadRequest("Oops"))

        with pytest.raises(HTTPBadRequest, match="Oops"):
            lti_h_svc.upsert_h_user()

    def test_it_raises_if_provider_unique_id_raises(
        self, context, pyramid_request, lti_h_svc
    ):
        type(context).h_provider_unique_id = mock.PropertyMock(
            side_effect=HTTPBadRequest("Oops")
        )

        with pytest.raises(HTTPBadRequest, match="Oops"):
            lti_h_svc.upsert_h_user()

    def test_it_creates_the_user_in_h_if_it_does_not_exist(
        self, context, hapi_svc, pyramid_request, lti_h_svc
    ):
        hapi_svc.patch.side_effect = HAPINotFoundError("whatever")

        lti_h_svc.upsert_h_user()

        hapi_svc.post.assert_called_once_with(
            "users",
            {
                "username": "test_username",
                "display_name": "test_display_name",
                "authority": "TEST_AUTHORITY",
                "identities": [
                    {
                        "provider": "test_provider",
                        "provider_unique_id": "test_provider_unique_id",
                    }
                ],
            },
        )


class TestAddUserToGroup:
    def test_it_doesnt_post_to_the_api_if_feature_not_enabled(
        self, context, pyramid_request, hapi_svc, lti_h_svc
    ):
        context.provisioning_enabled = False

        lti_h_svc.add_user_to_group()

        hapi_svc.post.assert_not_called()

    def test_it_adds_the_user_to_the_group(
        self, context, pyramid_request, hapi_svc, lti_h_svc
    ):
        lti_h_svc.add_user_to_group()

        hapi_svc.post.assert_called_once_with(
            "groups/test_groupid/members/acct:test_username@TEST_AUTHORITY"
        )

    def test_it_raises_if_post_raises(
        self, context, pyramid_request, hapi_svc, lti_h_svc
    ):
        hapi_svc.post.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            lti_h_svc.add_user_to_group()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params[
            "tool_consumer_instance_guid"
        ] = "test_tool_consumer_instance_guid"
        pyramid_request.params["context_id"] = "test_context_id"
        return pyramid_request


@pytest.fixture
def lti_h_svc(pyramid_request):
    return LTIHService(None, pyramid_request)


@pytest.fixture
def context():
    class TestContext:
        h_user = HUser(
            authority="TEST_AUTHORITY",
            username="test_username",
            display_name="test_display_name",
        )
        h_groupid = "test_groupid"
        h_group_name = "test_group_name"
        h_provider = "test_provider"
        h_provider_unique_id = "test_provider_unique_id"
        provisioning_enabled = True
        h_authority_provided_id = "test_authority_provided_id"

    return TestContext()


@pytest.fixture
def pyramid_request(context, pyramid_request):
    pyramid_request.context = context
    return pyramid_request


@pytest.fixture(autouse=True)
def hapi_svc(patch, pyramid_config):
    hapi_svc = mock.create_autospec(HAPIRequests, spec_set=True, instance=True)
    hapi_svc.patch.return_value = mock.create_autospec(
        Response, instance=True, status_code=200, reason="OK", text=""
    )
    hapi_svc.post.return_value = mock.create_autospec(
        Response, instance=True, status_code=200, reason="OK", text=""
    )
    pyramid_config.register_service(hapi_svc, name="h_api_requests")
    return hapi_svc


@pytest.fixture(autouse=True)
def group_info_upsert(pyramid_config):
    group_info_upsert = mock.create_autospec(
        GroupInfoUpsert, instance=True, spec_set=True
    )
    pyramid_config.register_service(group_info_upsert, name="group_info_upsert")
    return group_info_upsert