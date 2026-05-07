import ollama


class OllamaChatClient:
    """Generic reusable client for interacting with a local Ollama chat model."""

    def __init__(self, model_name="llama3.2"):
        self.model_name = model_name
        self.history = []

    def send(self, prompt):
        """
        Send a prompt to the AI service and return the assistant response text.

        Requirements:
        - Reject None, empty, or whitespace-only prompts with ValueError.
        - Strip the prompt before storing it.
        - Append the user message to self.history before calling the service.
        - Call ollama.chat(model=self.model_name, messages=self.history).
        - Extract assistant content from the response.
        - Reject missing, non-string, or blank assistant content.
        - Append assistant content to history only after a usable response.
        - Return the assistant response text.
        - If the service call or response extraction fails, remove the failed user message
          and raise RuntimeError.
        """
        pass

    def reset(self):
        """Clear the conversation history."""
        pass

    def message_count(self):
        """Return the number of stored messages."""
        pass

    def get_transcript(self):
        """
        Return a copy of the conversation history.

        The returned list should not allow callers to mutate the internal history list.
        """
        pass