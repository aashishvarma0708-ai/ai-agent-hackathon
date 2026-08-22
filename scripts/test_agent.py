from app.agent import CallAgent


def main():

    print("🤖 Starting CivicResolve agent test")
    print("Type 'quit' to stop.\n")

    agent = CallAgent()

    greeting = (
        "Hello, this is CivicResolve. "
        "What issue would you like to report?"
    )

    print(f"BOT: {greeting}")

    while True:

        user_text = input("\nYOU: ").strip()

        if user_text.lower() in {
            "quit",
            "exit"
        }:
            print("\n🛑 Test ended")
            break

        try:

            response = agent.respond(
                user_text
            )

            print(
                f"\nBOT: {response}"
            )

        except Exception as exc:

            print(
                f"\n❌ Agent error: {exc}"
            )

            break


if __name__ == "__main__":
    main()

