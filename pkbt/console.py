def for_console(value) -> str:
    """Return text the Windows console can print.

    The male and female signs become -M and -F. Every other character outside
    plain ASCII is written as a \\x or \\u escape, so a failed read still
    reaches the log and can be copied into a comparison.
    """
    text = str(value).replace("♂", "-M").replace("♀", "-F")
    return text.encode("unicode_escape").decode("ascii")
