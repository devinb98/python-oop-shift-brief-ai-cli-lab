import inspect

import pytest

import ai_client as ai_client_module
from ai_client import OllamaChatClient


def test_client_initializes_default_model_and_empty_history():
    client = OllamaChatClient()

    assert client.model_name == "llama3.2"
    assert client.history == []


def test_client_accepts_custom_model_name():
    client = OllamaChatClient(model_name="custom-model")

    assert client.model_name == "custom-model"
    assert client.history == []


def test_client_uses_instance_specific_history():
    first_client = OllamaChatClient()
    second_client = OllamaChatClient()

    first_client.history.append({"role": "user", "content": "Hello"})

    assert first_client.history == [{"role": "user", "content": "Hello"}]
    assert second_client.history == []


@pytest.mark.parametrize("bad_prompt", [None, "", "   ", "\n\t"])
def test_send_rejects_blank_prompts_without_calling_service(monkeypatch, bad_prompt):
    client = OllamaChatClient()
    called = False

    def fake_chat(model, messages):
        nonlocal called
        called = True
        return {"message": {"role": "assistant", "content": "Should not happen"}}

    monkeypatch.setattr(ai_client_module.ollama, "chat", fake_chat)

    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        client.send(bad_prompt)

    assert called is False
    assert client.history == []


def test_send_calls_ollama_with_model_and_history(monkeypatch):
    client = OllamaChatClient(model_name="test-model")
    call_details = {}

    def fake_chat(model, messages):
        call_details["model"] = model
        call_details["messages_id"] = id(messages)
        call_details["messages_at_call_time"] = list(messages)

        return {
            "message": {
                "role": "assistant",
                "content": "  Usable assistant response.  ",
            }
        }

    monkeypatch.setattr(ai_client_module.ollama, "chat", fake_chat)

    result = client.send("   Create a handoff summary.   ")

    assert result == "Usable assistant response."
    assert call_details["model"] == "test-model"
    assert call_details["messages_id"] == id(client.history)
    assert call_details["messages_at_call_time"] == [
        {"role": "user", "content": "Create a handoff summary."}
    ]
    assert client.history == [
        {"role": "user", "content": "Create a handoff summary."},
        {"role": "assistant", "content": "Usable assistant response."},
    ]


def test_send_returns_text_without_printing(monkeypatch, capsys):
    client = OllamaChatClient()

    def fake_chat(model, messages):
        return {
            "message": {
                "role": "assistant",
                "content": "Returned only.",
            }
        }

    monkeypatch.setattr(ai_client_module.ollama, "chat", fake_chat)

    result = client.send("Say hello.")

    captured = capsys.readouterr()

    assert result == "Returned only."
    assert captured.out == ""


def test_send_preserves_multi_turn_history(monkeypatch):
    client = OllamaChatClient()
    responses = iter(["First response.", "Second response."])

    def fake_chat(model, messages):
        return {
            "message": {
                "role": "assistant",
                "content": next(responses),
            }
        }

    monkeypatch.setattr(ai_client_module.ollama, "chat", fake_chat)

    first_result = client.send("First prompt")
    second_result = client.send("Second prompt")

    assert first_result == "First response."
    assert second_result == "Second response."
    assert client.history == [
        {"role": "user", "content": "First prompt"},
        {"role": "assistant", "content": "First response."},
        {"role": "user", "content": "Second prompt"},
        {"role": "assistant", "content": "Second response."},
    ]


def test_reset_clears_history():
    client = OllamaChatClient()
    client.history = [
        {"role": "user", "content": "Old prompt"},
        {"role": "assistant", "content": "Old response"},
    ]

    client.reset()

    assert client.history == []


def test_message_count_returns_number_of_stored_messages():
    client = OllamaChatClient()
    client.history = [
        {"role": "user", "content": "Prompt"},
        {"role": "assistant", "content": "Response"},
    ]

    assert client.message_count() == 2


def test_get_transcript_returns_copy_not_internal_list():
    client = OllamaChatClient()
    client.history = [{"role": "user", "content": "Original"}]

    transcript = client.get_transcript()
    transcript.append({"role": "assistant", "content": "Changed"})

    assert transcript != client.history
    assert client.history == [{"role": "user", "content": "Original"}]


def test_get_transcript_returns_copies_of_message_dicts():
    client = OllamaChatClient()
    client.history = [{"role": "user", "content": "Original"}]

    transcript = client.get_transcript()
    transcript[0]["content"] = "Mutated"

    assert client.history == [{"role": "user", "content": "Original"}]


def test_send_raises_runtime_error_and_removes_failed_user_message(monkeypatch):
    client = OllamaChatClient()
    client.history = [{"role": "user", "content": "Previous prompt"}]

    def fake_chat(model, messages):
        raise ConnectionError("service offline")

    monkeypatch.setattr(ai_client_module.ollama, "chat", fake_chat)

    with pytest.raises(RuntimeError, match="AI service request failed"):
        client.send("Prompt that fails")

    assert client.history == [{"role": "user", "content": "Previous prompt"}]


@pytest.mark.parametrize(
    "bad_response",
    [
        {},
        {"message": None},
        {"message": {}},
        {"message": {"role": "assistant"}},
        {"message": {"role": "assistant", "content": None}},
        {"message": {"role": "assistant", "content": ""}},
        {"message": {"role": "assistant", "content": "   "}},
    ],
)
def test_send_rejects_unusable_assistant_responses(monkeypatch, bad_response):
    client = OllamaChatClient()

    def fake_chat(model, messages):
        return bad_response

    monkeypatch.setattr(ai_client_module.ollama, "chat", fake_chat)

    with pytest.raises(RuntimeError, match="AI service request failed"):
        client.send("Prompt with unusable response")

    assert client.history == []


def test_client_stays_generic_and_domain_neutral():
    source = inspect.getsource(OllamaChatClient).lower()

    forbidden_terms = [
        "shift",
        "handoff",
        "brief",
        "action item",
        "open issue",
        "risk note",
        "store",
        "inventory",
        "retail",
        "manager",
    ]

    for term in forbidden_terms:
        assert term not in source, (
            "OllamaChatClient should stay generic and should not include "
            f"domain-specific term: {term}"
        )