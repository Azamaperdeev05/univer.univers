def to_initials(fullname: str):
    firstname, *lostnames = fullname.split(" ")

    return " ".join([firstname] + [f"{name[0]}." for name in lostnames])


def compare_str_without_spaces(a: str, b: str):
    return a.lower().replace(" ", "") == b.lower().replace(" ", "")
