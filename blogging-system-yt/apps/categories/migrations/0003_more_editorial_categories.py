from django.db import migrations


EXTRA_CATEGORIES = (
    ("Sports", "Games, athletes, and competition."),
    ("Opinion", "Arguments, essays, and commentary."),
    ("Environment", "Climate, energy, and the living world."),
)


def seed_categories(apps, schema_editor):
    Category = apps.get_model("categories", "Category")
    extras = EXTRA_CATEGORIES + (
        ("Business", "Companies, work, money, and the economy."),
        ("Culture", "Arts, media, ideas, and everyday life."),
        ("Health", "Wellbeing, fitness, and evidence-based health."),
        ("Lifestyle", "Habits, home, food, and personal growth."),
        ("Science", "Research, nature, and discovery."),
        ("Technology", "Technology, software, and the internet."),
        ("Travel", "Places, practical guides, and local stories."),
    )
    for name, description in extras:
        category, created = Category.objects.get_or_create(
            name=name,
            defaults={"slug": name.lower(), "description": description, "is_active": True},
        )
        if not category.is_active:
            category.is_active = True
            category.description = category.description or description
            category.save(update_fields=["is_active", "description"])


class Migration(migrations.Migration):
    dependencies = [("categories", "0002_seed_editorial_categories")]

    operations = [migrations.RunPython(seed_categories, migrations.RunPython.noop)]
