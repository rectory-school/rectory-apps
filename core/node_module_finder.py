import django_node_assets.finders  # type: ignore

INCLUDE_PATTERNS = {"*.map"}


class NodeModulesFinder(django_node_assets.finders.NodeModulesFinder):
    ignore_patterns = [
        item
        for item in django_node_assets.finders.NodeModulesFinder.ignore_patterns
        if item not in INCLUDE_PATTERNS
    ]
