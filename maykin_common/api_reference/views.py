from django.views.generic import TemplateView


class ComponentIndexView(TemplateView):
    template_name = "index_component.html"

    component = ""
    api_version = ""
    notification_url = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "component": self.component,
                "api_version": self.api_version,
                "notification_url": self.notification_url,
            }
        )
        return context
