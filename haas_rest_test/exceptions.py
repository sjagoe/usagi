class HaasRestTestError(Exception):
    pass


class YamlParseError(HaasRestTestError):
    pass


class InvalidAssertionClass(HaasRestTestError):
    pass


class InvalidVariable(HaasRestTestError):
    pass


class InvalidVariableType(HaasRestTestError):
    pass


class VariableLoopError(HaasRestTestError):
    pass
