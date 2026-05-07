import pytest

from brief_builder import HandoffBriefBuilder


VALID_BRIEF = """
Shift Summary:
The closing shift had a register issue and unfinished returns.

Open Issues:
Register 2 froze during closing. Three carts of returns remain unsorted.

Action Items:
Ask IT to review Register 2. Assign morning staff to process returns.

Follow-Up Questions:
Did Register 2 generate an error code?

Risk Notes:
Delayed returns may affect opening workflow.
""".strip()


class RecordingClient:
    def __init__(self, response=VALID_BRIEF, error=None):
        self.response = response
        self.error = error
        self.prompts = []

    def send(self, prompt):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return self.response


def test_required_sections_are_defined():
    builder = HandoffBriefBuilder()

    assert builder.REQUIRED_SECTIONS == (
        "Shift Summary:",
        "Open Issues:",
        "Action Items:",
        "Follow-Up Questions:",
        "Risk Notes:",
    )


@pytest.mark.parametrize("bad_notes", [None, "", "   ", "\n\t"])
def test_build_brief_prompt_rejects_blank_notes(bad_notes):
    builder = HandoffBriefBuilder()

    with pytest.raises(ValueError, match="Shift notes cannot be empty"):
        builder.build_brief_prompt(bad_notes)


def test_build_brief_prompt_includes_notes_sections_and_safety_guidance():
    builder = HandoffBriefBuilder()
    notes = "Register 2 froze twice during closing. Maya restarted it."

    prompt = builder.build_brief_prompt(notes)
    prompt_lower = prompt.lower()

    assert notes in prompt

    for section in builder.REQUIRED_SECTIONS:
        assert section in prompt

    assert "do not invent" in prompt_lower or "do not make up" in prompt_lower
    assert "unsupported" in prompt_lower
    assert "unknown" in prompt_lower
    assert "shift" in prompt_lower
    assert "handoff" in prompt_lower


@pytest.mark.parametrize("bad_feedback", [None, "", "   ", "\n\t"])
def test_build_revision_prompt_rejects_blank_feedback(bad_feedback):
    builder = HandoffBriefBuilder()

    with pytest.raises(ValueError, match="Revision feedback cannot be empty"):
        builder.build_revision_prompt(bad_feedback)


def test_build_revision_prompt_includes_feedback_previous_context_and_sections():
    builder = HandoffBriefBuilder()
    feedback = "Make the action items more specific."

    prompt = builder.build_revision_prompt(feedback)
    prompt_lower = prompt.lower()

    assert feedback in prompt
    assert "previous" in prompt_lower or "earlier" in prompt_lower
    assert "revise" in prompt_lower or "revision" in prompt_lower
    assert "do not invent" in prompt_lower or "do not make up" in prompt_lower

    for section in builder.REQUIRED_SECTIONS:
        assert section in prompt


def test_is_usable_brief_returns_true_when_all_required_sections_exist():
    builder = HandoffBriefBuilder()

    assert builder.is_usable_brief(VALID_BRIEF) is True


@pytest.mark.parametrize(
    "response_text",
    [
        None,
        "",
        "   ",
        "Shift Summary:\nOnly one section exists.",
        """
Shift Summary:
Summary here.

Open Issues:
Issue here.

Action Items:
Action here.

Follow-Up Questions:
Question here.
""",
    ],
)
def test_is_usable_brief_returns_false_for_missing_or_blank_sections(response_text):
    builder = HandoffBriefBuilder()

    assert builder.is_usable_brief(response_text) is False


def test_format_brief_adds_user_facing_heading():
    builder = HandoffBriefBuilder()

    formatted = builder.format_brief(VALID_BRIEF)

    assert formatted.startswith("\nShift Handoff Brief")
    assert VALID_BRIEF in formatted


def test_create_brief_sends_built_prompt_and_returns_formatted_result():
    builder = HandoffBriefBuilder()
    client = RecordingClient()
    notes = "Stockroom has three carts of unsorted returns."

    result = builder.create_brief(client, notes)

    assert len(client.prompts) == 1
    assert notes in client.prompts[0]
    assert "Shift Summary:" in client.prompts[0]
    assert result.startswith("\nShift Handoff Brief")
    assert "Action Items:" in result


def test_create_brief_raises_runtime_error_for_unusable_ai_response():
    builder = HandoffBriefBuilder()
    client = RecordingClient(response="Shift Summary:\nMissing most required sections.")

    with pytest.raises(RuntimeError, match="AI response did not include required sections"):
        builder.create_brief(client, "Closing shift notes go here.")

    assert len(client.prompts) == 1


def test_create_brief_allows_client_runtime_errors_to_propagate():
    builder = HandoffBriefBuilder()
    client = RecordingClient(error=RuntimeError("AI service request failed: offline"))

    with pytest.raises(RuntimeError, match="offline"):
        builder.create_brief(client, "Register issue during close.")


def test_revise_brief_sends_revision_prompt_and_returns_formatted_result():
    builder = HandoffBriefBuilder()
    client = RecordingClient()
    feedback = "Make the risk notes more specific."

    result = builder.revise_brief(client, feedback)

    assert len(client.prompts) == 1
    assert feedback in client.prompts[0]
    assert "previous" in client.prompts[0].lower() or "earlier" in client.prompts[0].lower()
    assert result.startswith("\nRevised Shift Handoff Brief")
    assert "Risk Notes:" in result


def test_revise_brief_raises_runtime_error_for_unusable_ai_response():
    builder = HandoffBriefBuilder()
    client = RecordingClient(response="This does not use the required structure.")

    with pytest.raises(RuntimeError, match="AI response did not include required sections"):
        builder.revise_brief(client, "Make the brief more specific.")