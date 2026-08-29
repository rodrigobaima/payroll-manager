from .models import Company


def company_context(request):
    if not request.user.is_authenticated:
        return {}
    return {"current_company": Company.objects.first()}
