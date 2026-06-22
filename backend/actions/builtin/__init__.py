"""
Register all built-in actions into the global registry on import.
"""

from actions.registry import registry
from actions.builtin.send_email import SendEmailAction
from actions.builtin.generate_report import GenerateReportAction
from actions.builtin.create_alert import CreateAlertAction

registry.register(SendEmailAction())
registry.register(GenerateReportAction())
registry.register(CreateAlertAction())

__all__ = ["SendEmailAction", "GenerateReportAction", "CreateAlertAction"]
