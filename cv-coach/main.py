from agent.graph import AgentState, agent


def main() -> None:
    print("CV Coach Agent CLI. Type 'exit' or 'quit' to stop.")
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

        result: AgentState = agent.invoke(AgentState(message=message))
        print(result["message"])


if __name__ == "__main__":
    main()
