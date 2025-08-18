from django.views.generic import TemplateView

from maykin_common.api_reference.views import ComponentIndexView


class ApiLandingPageView(TemplateView):
    template_name = "testapp/api/index.html"


class CustomComponentIndexView(ComponentIndexView):
    template_name = "testapp/api/component.html"
