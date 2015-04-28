class HaasRestTestError(Exception):
    pass


class YamlParseError(HaasRestTestError):
    pass


class JqCompileError(HaasRestTestError):
    pass


class InvalidAssertionClass(HaasRestTestError):
    pass


class InvalidParameterClass(HaasRestTestError):
    pass


class InvalidVariable(HaasRestTestError):
    pass


class InvalidVariableType(HaasRestTestError):
    pass


class VariableLoopError(HaasRestTestError):
    pass
