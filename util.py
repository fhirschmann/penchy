
def topological_sort(start_nodes, dependencies):
    """
    Return a topologically sorted list of :param:`start_nodes` and
    :param:`dependencies`.

    Nodes are checked on identity, not equality.

    Raises a ValueError if no topological sort is possible.

    :param start_nodes: list of nodes of graph with no incoming edges
    :param dependencies: list of dependency edges; ([dependencies], target),
                         dependencies may be of any sequence or be atomic
    :returns: topologically sorted nodes
    :rtype: list of nodes
    """
    seen = set(start_nodes)
    for deps, target in dependencies:
        if deps is None:
            seen.add(target)
    order = list(seen)
    old_dependencies = []
    while True:
        dependencies = [(deps, target) for deps, target in dependencies if target not in seen]
        if not dependencies:
            return order
        if old_dependencies == dependencies:
            raise ValueError("no topological sort possible")

        for deps, target in dependencies:
            # test for sequences
            try:
                deps = iter(deps)
            # atomic object
            except TypeError:
                deps = [deps]
            if all(dep in seen for dep in deps):
                order.append(target)
                seen.add(target)
        # copy dependencies to check progress
        old_dependencies = list(dependencies)
