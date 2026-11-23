import io
import sys
import unittest
from unittest.mock import patch

import c64_file_explorer


class DependencyBootstrapTests(unittest.TestCase):
    def test_noninteractive_session_exits_without_prompt(self):
        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "missing_dependency":
                raise ImportError("missing_dependency")
            return real_import(name, *args, **kwargs)

        with patch.object(c64_file_explorer, "MANDATORY_LIBS", {"missing_dependency": "missing_pkg"}):
            with patch("builtins.__import__", side_effect=fake_import):
                with patch.object(sys, "stdin", io.StringIO()):
                    sys.stdin.isatty = lambda: False
                with patch.object(sys, "stdout", io.StringIO()):
                    sys.stdout.isatty = lambda: False
                    with self.assertRaises(SystemExit) as context:
                        c64_file_explorer.verify_and_bootstrap_dependencies()
                    self.assertEqual(context.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
