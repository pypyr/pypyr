"""Project CI/CD tools."""
from invoke import Collection, task

from ops import config, lint, package, publish, test


@task(pre=[lint.all, test.all])
def pipeline_buildout(c):
    """Lint and test."""
    pass


ns = Collection()
ns.add_task(pipeline_buildout)
ns.add_collection(test)
ns.add_collection(lint)
ns.add_collection(config)
ns.add_collection(package)
ns.add_collection(publish)
