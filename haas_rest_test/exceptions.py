class HaasRestTestError(Exception):
    pass


class YamlParseError(HaasRestTestError):
    pass


class InvalidAssertionClass(HaasRestTestError):
    pass
