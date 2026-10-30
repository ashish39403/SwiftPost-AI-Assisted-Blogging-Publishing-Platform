from django.db import migrations


DEFAULT_CATEGORIES = (
    ("Business", "Companies, work, money, and the economy."),
    ("Culture", "Arts, media, ideas, and everyday life."),
    ("Health", "Wellbeing, fitness, and evidence-based health."),
    ("Lifestyle", "Habits, home, food, and personal growth."),
    ("Science", "Research, nature, and discovery."),
    ("Technology", "Technology, software, and the internet."),
    ("Travel", "Places, practical guides, and local stories."),
)


def seed_categories(apps, schema_editor):
    Category = apps.get_model("categories", "Category")
    for name, description in DEFAULT_CATEGORIES:
        category, created = Category.objects.get_or_create(
            name=name,
            defaults={"slug": name.lower(), "description": description, "is_active": True},
        )
        if not created and not category.is_active:
            category.is_active = True
            category.save(update_fields=["is_active"])


class Migration(migrations.Migration):
    dependencies = [("categories", "0001_initial")]

    operations = [migrations.RunPython(seed_categories, migrations.RunPython.noop)]
