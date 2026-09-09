"""EduTrack Breadcrumb and Context Navigation Framework."""
from typing import List, Dict

class BreadcrumbRegistry:
    """Central registry for generating responsive breadcrumb hierarchies."""
    @staticmethod
    def generate_trail(app_label: str, view_name: str, instance=None) -> List[Dict[str, str]]:
        trail = [{'title': 'Home', 'url': '/dashboards/'}]
        trail.append({'title': app_label.capitalize(), 'url': f'/{app_label}/'})
        if instance:
            trail.append({'title': str(instance), 'url': ''})
        return trail
