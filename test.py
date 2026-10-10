import django
import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)


django.setup()


from bses_module.tasks.task1 import test_task

result = test_task.enqueue(message="Hello from Django Tasks")

print(result)
