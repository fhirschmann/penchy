import re

BENCHMARKS = set(( 'avrora'
                   , 'batik'
                   , 'eclipse'
                   , 'fop'
                   , 'h2'
                   , 'jython'
                   , 'luindex'
                   , 'lusearch'
                   , 'pmd'
                   , 'sunflow'
                   , 'tomcat'
                   , 'tradebeans'
                   , 'tradesoap'
                   , 'xalan'))

WALLCLOCK_RE = re.compile(r'((?P<succed>FAILED|PASSED) in (?P<time>\d+) msec)')

def dacapo_wallclock(output):
    """
    :param output: benchmark output
    :returns: list of relevant parts for wallclock time
    :rtype: list of tuples as (whole relevant part, PASSED/FAILED, time in msec)
    """
    return WALLCLOCK_RE.findall(output)
