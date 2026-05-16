from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


BOT_PATH = Path(__file__).resolve().parents[1] / "apps" / "telegram-bot" / "courter_bot" / "main.py"


def load_bot_module():
    spec = spec_from_file_location("courter_bot_main", BOT_PATH)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_help_command_lists_known_commands() -> None:
    module = load_bot_module()
    text = module.handle_command("/help")
    assert "/status" in text
    assert "/verdict" in text


def test_unknown_command_returns_help_hint() -> None:
    module = load_bot_module()
    assert module.handle_command("/nope") == "Unknown command. Use /help."
