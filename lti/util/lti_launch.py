from pylti.common import verify_request_common
from lti.models import application_instance as ai

def lti_launch(view_function):

  def wrapper(request):
    consumer_key = request.params["oauth_consumer_key"]
    instance = request.db.query(ai.ApplicationInstance).filter(
    ai.ApplicationInstance.consumer_key == consumer_key).one()

    consumers = {}

    consumers[consumer_key] = { "secret": instance.shared_secret }

    # TODO rescue from an invalid lti launch
    verify_request_common(consumers, request.url, request.method, dict(request.headers), dict(request.params))
    return view_function(request)

  return wrapper