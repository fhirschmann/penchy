class JVMNodeConfiguration(object):
    """
    Represents the combination of a jvm with a node.
    """
    def __init__(self, jvm, node, name=""):
        """
        :param jvm: :class:`JVM` to execute the job
        :param node: :class:`NodeConfiguration` to execute on
        :param name: decorative name of the configuration
        """
        self.jvm = jvm
        self.node = node
        self.name = name


class Job(object):
    """
    Represents a job.
    """
    def __init__(self, configurations, client_flow, server_flow, invocations=1):
        """
        :param configurations: :class:`JVMNodeConfiguration` to execute jobs on
        :param client_flow: sequence of :class:`Edge` that describes the
                            execution of the job on nodes
        :param server_flow: sequence of :class:`Edge` that describes the
                            execution of the job on nodes
        :param invocations: number of times to run job on each configuration
        """
        self.configurations = configurations
        self.client_flow = client_flow
        self.server_flow = server_flow
        self.invocations = invocations

        # to be set by client before executing job
        self.return_address = None

    def run(self):
        """
        Run Job.
        """
        # FIXME: implement me!
        # for invocations: make tmpdir and change working directory to it
        pass

    def check(self):
        """
        Check job for plausibility.

        :returns: if job is plausible, i.e. no failure is expected.
        :rtype: bool
        """
        # FIXME: implement me!
        pass
