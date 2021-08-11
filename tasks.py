"""Project CI/CD tools."""
from invoke import Collection, task

from ops import MyTask, config, lint, package, publish, test


@task(lint.all, test.all, klass=MyTask)
def pipeline_buildout(c):
    """Lint and test."""
    pass


ns = Collection()
ns.add_task(pipeline_buildout)
ns.add_task(config.all, "config")
ns.add_collection(lint)
ns.add_collection(test)
ns.add_task(package.all, "package")
ns.add_collection(publish)
