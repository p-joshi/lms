from urllib.parse import unquote

from marshmallow import Schema, ValidationError, fields, post_load

from lms.validation._exceptions import LTIToolRedirect
from lms.validation._helpers import PyramidRequestSchema


class LaunchPresentationReturnURLSchema(Schema):
    """Schema containing only validation for the return URL."""
    launch_presentation_return_url = fields.URL()


class LaunchParamsSchema(PyramidRequestSchema):
    """
    Schema describing the minimum requirements for LTI launch parameters.

    This *DOES NOT* contain all of the fields required for authentication.
    For that see `lms.validation.authentication.LaunchParamsAuthSchema`
    """

    resource_link_id = fields.Str(required=True)
    launch_presentation_return_url = fields.Str()

    # If we have an error in one of these fields we should redirect back to
    # the calling LMS if possible
    lti_redirect_fields = {"resource_link_id"}

    locations = ["form"]

    def handle_error(self, error, data, *, many, **kwargs):
        messages = error.messages

        try:
            # Extract the launch_presentation_return_url and check it's a real
            # URL
            return_url = LaunchPresentationReturnURLSchema().load(data).get(
                "launch_presentation_return_url")
        except ValidationError:
            return_url = None

        if return_url:
            reportable_fields = set(messages.keys()) & self.lti_redirect_fields
            if reportable_fields:
                raise LTIToolRedirect(return_url, messages)

        super().handle_error(error, data, many=many, **kwargs)


class LaunchParamsURLConfiguredSchema(LaunchParamsSchema):
    """
    Schema for an "URL-configured" Basic LTI Launch.

    An URL-configured launch is one where the content URL is provided by a "url"
    launch param.
    """

    url = fields.Str(required=True)

    @post_load
    def _decode_url(self, _data, **_kwargs):  # pylint:disable=no-self-use
        # Work around a bug in Canvas's handling of LTI Launch URLs in
        # SpeedGrader launches. In that context, query params get
        # doubly-encoded. This is worked around by detecting when this has
        # happened and decoding the URL a second time.
        #
        # See https://github.com/instructure/canvas-lms/issues/1486
        url = _data["url"]
        if url.lower().startswith("http%3a") or url.lower().startswith("https%3a"):
            url = unquote(url)
            _data["url"] = url

        return _data
