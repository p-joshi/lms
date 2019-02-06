import pytest
from pyramid import testing

from lms.validation import CANVAS_OAUTH_CALLBACK_ARGS
from lms.validation import parser
from lms.validation import ValidationError


class TestCanvasOauthCallbackArgs:
    def test_it_returns_the_parsed_args_for_a_valid_request(self, valid_request):
        parsed_args = parser.parse(CANVAS_OAUTH_CALLBACK_ARGS, valid_request)

        assert parsed_args == {"code": "test_code", "state": "test_state"}

    def test_its_invalid_if_state_is_missing(self, valid_request):
        del valid_request.params["state"]

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(CANVAS_OAUTH_CALLBACK_ARGS, valid_request)

        assert exc_info.value.messages == {
            "state": ["Missing data for required field."]
        }

    def test_its_invalid_if_state_isnt_a_string(self, valid_request):
        valid_request.params["state"] = 23

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(CANVAS_OAUTH_CALLBACK_ARGS, valid_request)

        assert exc_info.value.messages == {"state": ["Not a valid string."]}

    def test_its_invalid_if_state_is_null(self, valid_request):
        valid_request.params["state"] = None

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(CANVAS_OAUTH_CALLBACK_ARGS, valid_request)

        assert exc_info.value.messages == {"state": ["Field may not be null."]}

    def test_its_invalid_if_code_is_missing(self, valid_request):
        del valid_request.params["code"]

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(CANVAS_OAUTH_CALLBACK_ARGS, valid_request)

        assert exc_info.value.messages == {"code": ["Missing data for required field."]}

    def test_its_invalid_if_code_isnt_a_string(self, valid_request):
        valid_request.params["code"] = 23

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(CANVAS_OAUTH_CALLBACK_ARGS, valid_request)

        assert exc_info.value.messages == {"code": ["Not a valid string."]}

    def test_its_invalid_if_code_is_null(self, valid_request):
        valid_request.params["code"] = None

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(CANVAS_OAUTH_CALLBACK_ARGS, valid_request)

        assert exc_info.value.messages == {"code": ["Field may not be null."]}

    @pytest.fixture
    def valid_request(self):
        """Return a minimal valid request.

        All required fields are present and valid.
        """
        valid_request = testing.DummyRequest()
        valid_request.params["code"] = "test_code"
        valid_request.params["state"] = "test_state"
        return valid_request
