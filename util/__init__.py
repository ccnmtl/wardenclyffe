import re


def uuidparse(s):
    """
    parse something that looks like a a uuid out of a string

    >>> uuidparse('4a6e4a20-fd8f-4e2a-9808-4ed612b1f0d0.mov')
    '4a6e4a20-fd8f-4e2a-9808-4ed612b1f0d0'
    >>> uuidparse('not a uuid')
    ''

    """
    pattern = re.compile(
        r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})")
    m = pattern.match(s)
    if m:
        return m.group()
    else:
        return ""
