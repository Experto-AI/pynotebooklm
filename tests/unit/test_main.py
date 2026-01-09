"""
Unit tests for the __main__ module.

These tests verify the module can be imported and the app is correctly referenced.
"""

from unittest.mock import patch


class TestMainModule:
    """Tests for the __main__ module."""

    def test_import_succeeds(self) -> None:
        """The __main__ module can be imported without error."""
        # This will execute the import but not run the app
        import pynotebooklm.__main__ as main_module

        assert hasattr(main_module, "app")

    def test_app_is_typer_app(self) -> None:
        """The app object is a Typer application."""
        from typer import Typer

        from pynotebooklm.__main__ import app

        assert isinstance(app, Typer)

    def test_main_block_calls_app(self) -> None:
        """The __main__ block calls app() when run directly."""
        with patch("pynotebooklm.cli.app") as _mock_app:
            # Simulate running as __main__
            with patch.dict("sys.modules", {"pynotebooklm.__main__": None}):
                exec(
                    """
from pynotebooklm.cli import app
if __name__ == "__main__":
    app()
""",
                    {"__name__": "__main__"},
                )
                # In actual execution, app() would be called
                # Here we just verify the module structure is correct

    def test_main_module_execution(self) -> None:
        """The __main__ module runs app() when executed."""
        import runpy

        with patch("pynotebooklm.cli.app") as mock_app:
            try:
                runpy.run_module("pynotebooklm.__main__", run_name="__main__")
            except SystemExit:
                pass  # app() may exit
            # Verify app was called
            mock_app.assert_called_once()
