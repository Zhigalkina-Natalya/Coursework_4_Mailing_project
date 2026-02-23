from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Создаёт или обновляет группу 'Менеджеры' и назначает нужные права."""

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name="Менеджеры")

        group.permissions.clear()

        # Собираем права только на просмотр (view_)
        view_perms = Permission.objects.filter(codename__startswith="view_")

        # Кастомное право: can_disable_mailings
        disable_perm = Permission.objects.filter(codename="can_disable_mailings")

        # Назначаем группе только нужные права
        group.permissions.add(*view_perms, *disable_perm)

        total = group.permissions.count()
        perm_list = [p.codename for p in group.permissions.all()]

        action = "создана" if created else "обновлена"
        self.stdout.write(
            self.style.SUCCESS(
                f"Группа 'Менеджеры' {action}. Назначено {total} прав:\n  - " + "\n  - ".join(perm_list)
            )
        )
