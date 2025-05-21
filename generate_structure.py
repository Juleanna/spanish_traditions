import os
import django
from pathlib import Path
from django.apps import apps

# Настройка пути к settings.py
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spanish_traditions.settings')  # Замените my_project на имя вашего проекта
django.setup()

def generate_structure_report(output_file='project_structure.txt'):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Физическая структура Django проекта\n")
        f.write("=" * 50 + "\n\n")

        # Файловая структура
        f.write("1. Файловая структура:\n")
        for root, dirs, files in os.walk(BASE_DIR):
            level = root.replace(str(BASE_DIR), '').count(os.sep)
            indent = ' ' * 4 * level
            f.write(f"{indent}{os.path.basename(root)}/\n")
            sub_indent = ' ' * 4 * (level + 1)
            for file in files:
                f.write(f"{sub_indent}{file}\n")
        
        f.write("\n2. Структура моделей:\n")
        # Список моделей
        for app_config in apps.get_app_configs():
            f.write(f"\nПриложение: {app_config.name}\n")
            f.write("-" * 50 + "\n")
            for model in app_config.get_models():
                f.write(f"Модель: {model.__name__}\n")
                for field in model._meta.fields:
                    f.write(f"    {field.name} ({field.get_internal_type()})\n")
                f.write("\n")
    print(f"Файл структуры создан: {output_file}")

if __name__ == '__main__':
    generate_structure_report()
