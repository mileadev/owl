"""Explicit safety gate for legacy autonomous tools. This is not sandboxing."""

import os


def require_legacy_opt_in() -> None:
    if os.getenv("OWL_ENABLE_UNSAFE_LEGACY_TOOLS") != "I_ACCEPT_THE_RISK":
        raise PermissionError(
            "Legacy workflows may run untrusted model-generated code and browser actions. "
            "Use the safe OWL CLI or set OWL_ENABLE_UNSAFE_LEGACY_TOOLS=I_ACCEPT_THE_RISK "
            "only inside an isolated VM without sensitive credentials."
        )


def guarded_code_execution_toolkit(*args, **kwargs):
    require_legacy_opt_in()
    from camel.toolkits import CodeExecutionToolkit
    return CodeExecutionToolkit(*args, **kwargs)
