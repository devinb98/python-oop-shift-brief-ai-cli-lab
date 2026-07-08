from ai_client import OllamaChatClient
from brief_builder import HandoffBriefBuilder


class ShiftBriefCLI:
    """Command-line workflow for generating and revising shift handoff briefs."""

    def __init__(self, ai_client, brief_builder=None):
        """
        Initialize the CLI application.

        Requirements:
        - Store the injected AI client.
        - Use the provided brief builder when one is passed in.
        - Create a HandoffBriefBuilder when one is not passed in.
        - Set self.running to True.
        """
        self.ai_client = ai_client
        self.brief_builder = brief_builder or HandoffBriefBuilder()
        self.running = True

    def display_welcome(self):
        """
        Print a welcome message and command guidance.

        Requirements:
        - Mention that this is a shift handoff brief CLI.
        - Include the available commands.
        """
        print("Shift Handoff Brief CLI")
        print("Generate and revise end-of-shift handoff briefs.\n")
        print(self.command_help())

    def command_help(self):
        """
        Return command guidance as a string.

        Required commands:
        - brief <shift notes>
        - revise <feedback>
        - history
        - reset
        - help
        - exit
        - quit
        """
        return (
            "Available commands:\n"
            "  brief <shift notes>   Create a new handoff brief from shift notes.\n"
            "  revise <feedback>     Revise the previous brief using feedback.\n"
            "  history               Show the conversation message count.\n"
            "  reset                 Clear the conversation history.\n"
            "  help                  Show this command guidance.\n"
            "  exit                  Stop the application.\n"
            "  quit                  Stop the application."
        )

    def handle_command(self, raw_input):
        """
        Route a user command.

        Requirements:
        - Return a readable input error for blank input.
        - Commands should be case-insensitive.
        - Extra spaces around commands should not break the app.
        - brief <shift notes> should call the brief builder's create_brief().
        - revise <feedback> should call the brief builder's revise_brief().
        - history should return the current message count.
        - reset should clear conversation history.
        - help should return command guidance.
        - exit and quit should stop the application.
        - Unknown commands should return a readable input error.
        - ValueError should become a readable Input Error.
        - RuntimeError should become a readable Service Error.
        """
        if raw_input is None or not str(raw_input).strip():
            return "Input Error: Please enter a command. Type 'help' to see options."

        stripped = str(raw_input).strip()
        parts = stripped.split(None, 1)
        command = parts[0].lower()
        payload = parts[1].strip() if len(parts) > 1 else ""

        if command in ("exit", "quit"):
            self.running = False
            return "Goodbye!"

        if command == "help":
            return self.command_help()

        if command == "history":
            count = self.ai_client.message_count()
            return f"Conversation messages: {count}"

        if command == "reset":
            self.ai_client.reset()
            return "Conversation history has been reset."

        if command == "brief":
            if not payload:
                return "Input Error: Please provide shift notes, e.g. 'brief <shift notes>'."
            try:
                return self.brief_builder.create_brief(self.ai_client, payload)
            except ValueError as error:
                return f"Input Error: {error}"
            except RuntimeError as error:
                return f"Service Error: {error}"

        if command == "revise":
            if not payload:
                return "Input Error: Please provide revision feedback, e.g. 'revise <feedback>'."
            try:
                return self.brief_builder.revise_brief(self.ai_client, payload)
            except ValueError as error:
                return f"Input Error: {error}"
            except RuntimeError as error:
                return f"Service Error: {error}"

        return (
            f"Input Error: Unknown command '{command}'. "
            "Type 'help' to see available commands."
        )

    def run(self):
        """
        Run the CLI input loop.

        Requirements:
        - Display the welcome message before the loop starts.
        - Continue while self.running is True.
        - Read user input.
        - Pass user input to handle_command().
        - Print returned messages.
        - Stop cleanly if EOFError occurs.
        """
        self.display_welcome()

        while self.running:
            try:
                user_input = input("\n> ")
            except EOFError:
                self.running = False
                break

            print(self.handle_command(user_input))


def main():
    client = OllamaChatClient(model_name="llama3.2")
    app = ShiftBriefCLI(client)
    app.run()


if __name__ == "__main__":
    main()