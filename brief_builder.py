class HandoffBriefBuilder:
    """Builds prompts and verifies output for shift handoff briefs."""

    REQUIRED_SECTIONS = (
        "Shift Summary:",
        "Open Issues:",
        "Action Items:",
        "Follow-Up Questions:",
        "Risk Notes:",
    )

    def build_brief_prompt(self, notes):
        """
        Build a prompt for creating a new shift handoff brief.

        Requirements:
        - Reject blank notes with ValueError.
        - Include the original notes.
        - Include all required section labels.
        - Tell the model not to invent unsupported details.
        - Tell the model to use "Unknown" when details are not provided.
        """
        pass

    def build_revision_prompt(self, feedback):
        """
        Build a prompt for revising the previous handoff brief.

        Requirements:
        - Reject blank feedback with ValueError.
        - Reference the previous brief/conversation.
        - Include the manager's feedback.
        - Include all required section labels.
        - Tell the model not to invent unsupported details.
        """
        pass

    def is_usable_brief(self, response_text):
        """
        Return True only when response_text is a nonblank string that contains
        every required handoff section.
        """
        pass

    def format_brief(self, response_text):
        """Return a user-facing formatted handoff brief."""
        pass

    def create_brief(self, ai_client, notes):
        """
        Build a new brief prompt, send it through ai_client, verify the response,
        and return a formatted user-facing brief.
        """
        pass

    def revise_brief(self, ai_client, feedback):
        """
        Build a revision prompt, send it through ai_client, verify the response,
        and return a formatted user-facing revised brief.
        """
        pass