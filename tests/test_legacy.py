import os
import unittest
from unittest.mock import patch

from owl.legacy import require_legacy_opt_in


class LegacyGateTests(unittest.TestCase):
    def test_unsafe_tools_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(PermissionError):
                require_legacy_opt_in()

    def test_explicit_opt_in(self):
        with patch.dict(os.environ, {"OWL_ENABLE_UNSAFE_LEGACY_TOOLS": "I_ACCEPT_THE_RISK"}):
            require_legacy_opt_in()
