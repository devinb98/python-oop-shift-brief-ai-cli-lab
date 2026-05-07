import inspect

import pytest

import brief_builder as brief_builder_module
import shift_cli as shift_cli_module
from shift_cli import ShiftBriefCLI


class FakeClient:
    def __init__(self, count=4):
        self.reset_count = 0
        self.count = count

    def reset(self):
        self.reset_count += 1
        self.count = 0

    def message_count(self):
        return self.count


class FakeBuilder:
    def __init__(self, error=None):
        self.error = error
        self.created_notes = []
        self.revision_feedback = []

    def create_brief(self, ai_client, notes):
        self.created_notes.append(notes)
        if self.error:
            raise self.error
        return "\nShift Handoff Brief\nAction Items:\nFollow up with IT."

    def revise_brief(self, ai_client, feedback):
        self.revision_feedback.append(feedback)
        if self.error:
            raise self.error
        return "\nRevised Shift Handoff Brief\nAction Items:\nAsk IT to review Register 2."


def test_cli_initializes_with_injected_client_and_optional_builder():
    client = FakeClient()
    builder = FakeBuilder()
    app = ShiftBriefCLI(client, builder)

    assert app.ai_client is client
    assert app.brief_builder is builder
    assert app.running is True


def test_display_welcome_prints_command_guidance(capsys):
    app = ShiftBriefCLI(FakeClient(), FakeBuilder())

    app.display_welcome()

    captured = capsys.readouterr()
    output = captured.out.lower()

    assert "shift" in output
    assert "brief" in output
    assert "revise" in output
    assert "history" in output
    assert "reset" in output
    assert "exit" in output or "quit" in output


def test_command_help_returns_guidance():
    app = ShiftBriefCLI(FakeClient(), FakeBuilder())

    help_text = app.command_help().lower()

    assert "brief <shift notes>" in help_text
    assert "revise <feedback>" in help_text
    assert "history" in help_text
    assert "reset" in help_text
    assert "exit" in help_text or "quit" in help_text


@pytest.mark.parametrize("blank_input", [None, "", "   ", "\n\t"])
def test_handle_command_blank_input_returns_input_error(blank_input):
    builder = FakeBuilder()
    app = ShiftBriefCLI(FakeClient(), builder)

    result = app.handle_command(blank_input)

    assert "input error" in result.lower()
    assert builder.created_notes == []
    assert builder.revision_feedback == []


def test_handle_command_unknown_command_returns_input_error():
    builder = FakeBuilder()
    app = ShiftBriefCLI(FakeClient(), builder)

    result = app.handle_command("summarize the closing shift")

    assert "input error" in result.lower()
    assert "unknown command" in result.lower()
    assert "help" in result.lower()
    assert builder.created_notes == []


def test_handle_command_help_returns_help_text():
    app = ShiftBriefCLI(FakeClient(), FakeBuilder())

    result = app.handle_command("  HELP  ")

    assert "brief <shift notes>" in result.lower()
    assert "revise <feedback>" in result.lower()


@pytest.mark.parametrize("command", ["exit", "quit", " EXIT ", " Quit "])
def test_handle_command_exit_and_quit_stop_running(command):
    builder = FakeBuilder()
    app = ShiftBriefCLI(FakeClient(), builder)

    result = app.handle_command(command)

    assert app.running is False
    assert "goodbye" in result.lower()
    assert builder.created_notes == []


def test_handle_command_reset_calls_client_reset():
    client = FakeClient(count=6)
    builder = FakeBuilder()
    app = ShiftBriefCLI(client, builder)

    result = app.handle_command("  RESET  ")

    assert client.reset_count == 1
    assert client.count == 0
    assert "reset" in result.lower()
    assert builder.created_notes == []


def test_handle_command_history_uses_message_count():
    client = FakeClient(count=6)
    app = ShiftBriefCLI(client, FakeBuilder())

    result = app.handle_command("history")

    assert "6" in result
    assert "message" in result.lower()


@pytest.mark.parametrize("command", ["brief", "brief   "])
def test_handle_command_brief_without_notes_returns_input_error(command):
    builder = FakeBuilder()
    app = ShiftBriefCLI(FakeClient(), builder)

    result = app.handle_command(command)

    assert "input error" in result.lower()
    assert "shift notes" in result.lower()
    assert builder.created_notes == []


def test_handle_command_brief_sends_payload_to_builder():
    builder = FakeBuilder()
    app = ShiftBriefCLI(FakeClient(), builder)

    result = app.handle_command(
        "brief Register 2 froze during closing and needs IT review."
    )

    assert builder.created_notes == [
        "Register 2 froze during closing and needs IT review."
    ]
    assert "Shift Handoff Brief" in result


@pytest.mark.parametrize("command", ["revise", "revise   "])
def test_handle_command_revise_without_feedback_returns_input_error(command):
    builder = FakeBuilder()
    app = ShiftBriefCLI(FakeClient(), builder)

    result = app.handle_command(command)

    assert "input error" in result.lower()
    assert "revision feedback" in result.lower()
    assert builder.revision_feedback == []


def test_handle_command_revise_sends_feedback_to_builder():
    builder = FakeBuilder()
    app = ShiftBriefCLI(FakeClient(), builder)

    result = app.handle_command("revise Make the action items more specific.")

    assert builder.revision_feedback == ["Make the action items more specific."]
    assert "Revised Shift Handoff Brief" in result


def test_handle_command_returns_service_error_when_builder_raises_runtime_error():
    builder = FakeBuilder(error=RuntimeError("AI service request failed: offline"))
    app = ShiftBriefCLI(FakeClient(), builder)

    result = app.handle_command("brief Register 2 froze.")

    assert "service error" in result.lower()
    assert "offline" in result


def test_handle_command_returns_input_error_when_builder_raises_value_error():
    builder = FakeBuilder(error=ValueError("Shift notes cannot be empty."))
    app = ShiftBriefCLI(FakeClient(), builder)

    result = app.handle_command("brief Something")

    assert "input error" in result.lower()
    assert "shift notes cannot be empty" in result.lower()


def test_shift_cli_and_brief_builder_do_not_import_ollama_or_call_chat_directly():
    shift_source = inspect.getsource(shift_cli_module).lower()
    builder_source = inspect.getsource(brief_builder_module).lower()

    assert "import ollama" not in shift_source
    assert "ollama.chat" not in shift_source
    assert "import ollama" not in builder_source
    assert "ollama.chat" not in builder_source


def test_cli_does_not_manage_ai_client_history_directly():
    source = inspect.getsource(ShiftBriefCLI).lower()

    assert ".history" not in source


def test_main_function_exists():
    assert callable(getattr(shift_cli_module, "main", None))


def test_run_loop_prints_welcome_responses_history_reset_and_goodbye(monkeypatch, capsys):
    client = FakeClient(count=2)
    builder = FakeBuilder()
    app = ShiftBriefCLI(client, builder)

    inputs = iter(
        [
            "brief Register 2 froze during close.",
            "history",
            "reset",
            "exit",
        ]
    )

    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    app.run()

    captured = capsys.readouterr()
    output = captured.out

    assert "Shift Handoff Brief CLI" in output
    assert "Shift Handoff Brief" in output
    assert "Conversation messages" in output
    assert "reset" in output.lower()
    assert "Goodbye" in output
    assert app.running is False
    assert builder.created_notes == ["Register 2 froze during close."]
    assert client.reset_count == 1