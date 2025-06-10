from django.views.generic import TemplateView


class ApiLandingPageView(TemplateView):
    template_name = "testapp/api/index.html"
