"""Automated Code Quality and Test Verification Script."""
import os
import re
import sys
import subprocess

def fix_duplicate_index_names():
    total_fixed = 0
    pattern = re.compile(r',\s*name="[^"]*"')
    for root, dirs, files in os.walk('.'):
        if any(p in root for p in ['.git', '__pycache__', 'builder', 'venv', 'env']):
            continue
        for f in files:
            if f.startswith('models_') and f.endswith('.py'):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                new_content = pattern.sub('', content)
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as fp:
                        fp.write(new_content)
                    total_fixed += 1
    print(f"Removed redundant index names across {total_fixed} model files.")

def consolidate_app_urls():
    import glob
    apps = ['core', 'accounts', 'academics', 'students', 'teachers', 'enrollment',
            'timetables', 'attendance', 'assignments', 'exams', 'grading', 'fees',
            'library', 'certificates', 'notifications', 'dashboards', 'analytics']

    for app in apps:
        view_files = glob.glob(f'{app}/views_*.py')
        imports = []
        routes = []
        for vf in view_files:
            with open(vf, 'r', encoding='utf-8') as fp:
                c = fp.read()
            m_cls = re.search(r'class\s+([A-Za-z0-9_]+)ListView\(ListView\):', c)
            m_csv = re.search(r'def\s+(export_[A-Za-z0-9_]+_csv)\(', c)
            m_json = re.search(r'def\s+(export_[A-Za-z0-9_]+_json)\(', c)
            if not m_cls:
                continue
            ent = m_cls.group(1)
            mod_name = os.path.splitext(os.path.basename(vf))[0]
            sub = mod_name.replace('views_', '')
            csv_fn = m_csv.group(1) if m_csv else f'export_{sub}_csv'
            json_fn = m_json.group(1) if m_json else f'export_{sub}_json'

            imports.append(f'from {app} import {mod_name} as views_{sub}')
            routes.append(f'    path("{sub}/", views_{sub}.{ent}ListView.as_view(), name="{sub}_list"),')
            routes.append(f'    path("{sub}/<int:pk>/", views_{sub}.{ent}DetailView.as_view(), name="{sub}_detail"),')
            routes.append(f'    path("{sub}/create/", views_{sub}.{ent}CreateView.as_view(), name="{sub}_create"),')
            routes.append(f'    path("{sub}/<int:pk>/edit/", views_{sub}.{ent}UpdateView.as_view(), name="{sub}_update"),')
            routes.append(f'    path("{sub}/<int:pk>/delete/", views_{sub}.{ent}DeleteView.as_view(), name="{sub}_delete"),')
            routes.append(f'    path("{sub}/<int:pk>/print/", views_{sub}.{ent}PrintView.as_view(), name="{sub}_print"),')
            routes.append(f'    path("{sub}/analytics/", views_{sub}.{ent}AnalyticsView.as_view(), name="{sub}_analytics"),')
            routes.append(f'    path("{sub}/export/csv/", views_{sub}.{csv_fn}, name="{sub}_export_csv"),')
            routes.append(f'    path("{sub}/export/json/", views_{sub}.{json_fn}, name="{sub}_export_json"),')

        content = '"""URL Routing Configuration for ' + app + '."""\n'
        content += 'from django.urls import path\n\n'
        content += '\n'.join(imports) + '\n\n'
        content += f'app_name = "{app}"\n\n'
        content += 'urlpatterns = [\n' + '\n'.join(routes) + '\n]\n'

        with open(f'{app}/urls.py', 'w', encoding='utf-8') as fp:
            fp.write(content)
    print("Consolidated all app URLs successfully.")

def run():
    fix_duplicate_index_names()
    consolidate_app_urls()
    print("Running Django system check...")
    res = subprocess.run([sys.executable, "manage.py", "check"])
    if res.returncode != 0:
        print("System check failed!")
        sys.exit(1)
    print("All system checks passed cleanly.")

if __name__ == "__main__":
    run()


