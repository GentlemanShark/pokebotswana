def callable_name(fn) -> str:
    """Name a function in a log line.

    A lambda is named by the function it calls, so an assertion written as
    lambda: assert_hex_at_position(...) is reported as assert_hex_at_position.
    """
    if fn.__name__ != "<lambda>":
        return fn.__name__
    names = fn.__code__.co_names
    return names[0] if names else fn.__name__

def for_console(value) -> str:
    """Return text the Windows console can print.

    The male and female signs become -M and -F. Every other character outside
    plain ASCII is written as a \\x or \\u escape, so a failed read still
    reaches the log and can be copied into a comparison.
    """
    text = str(value).replace("♂", "-M").replace("♀", "-F")
    return text.encode("unicode_escape").decode("ascii")
