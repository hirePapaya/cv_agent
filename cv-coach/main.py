from dotenv import load_dotenv

load_dotenv()

from agent.graph import chat_agent
from agent.states import ChatState


def main() -> None:
    print("CV Coach Agent CLI. Paste a job posting. Type 'exit' or 'quit' to stop.")
    while True:
        try:
            message = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if message.lower() in {"exit", "quit"}:
            break
        if not message:
            continue

        result = chat_agent.invoke(ChatState(message=message))
        print(result["reply"])


if __name__ == "__main__":
    main()
