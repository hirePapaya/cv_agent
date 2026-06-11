from dotenv import load_dotenv

load_dotenv()

from agent.graph import agent
from agent.states import CVAgentState


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

        result = agent.invoke(CVAgentState(job_description=message))
        print(result["job_posting"])


if __name__ == "__main__":
    main()
