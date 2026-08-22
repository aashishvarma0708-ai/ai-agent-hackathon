import asyncio

from dotenv import load_dotenv

from app.agent import CallAgent
from app.call_state import CallState


load_dotenv()


async def main():
    agent = CallAgent()
    state = CallState()

    print()
    print("CivicResolve Call Agent Test")
    print("Type 'quit' to stop.")
    print()

    while True:
        try:
            caller = input(
                "CALLER > "
            ).strip()

        except KeyboardInterrupt:
            print()
            print("👋 Test stopped.")
            break

        except EOFError:
            print()
            print("👋 Test stopped.")
            break

        # Ignore accidental blank Enter presses.
        if not caller:
            continue

        if caller.lower() in {
            "quit",
            "exit",
        }:
            print("👋 Test stopped.")
            break

        try:
            result = await agent.handle_turn(
                state,
                caller,
            )

        except asyncio.CancelledError:
            print()
            print("👋 Test cancelled.")
            break

        except KeyboardInterrupt:
            print()
            print("👋 Test stopped.")
            break

        except Exception as exc:
            print()
            print(
                "❌ Test error:",
                repr(exc),
            )
            print()
            continue

        print()

        print(
            "BOT    >",
            result["spoken_reply"],
        )

        print(
            "ROUTE  >",
            result["route"],
        )

        print(
            "SUBMIT >",
            result["ready_to_submit"],
        )

        print(
            "STATE  >",
            {
                "issue": state.issue,
                "location": state.location,
                "severity": state.severity,
                "safety_risk": state.safety_risk,
                "confirmed": state.confirmed,
                "awaiting_confirmation":
                    state.awaiting_confirmation,
            },
        )

        print()


if __name__ == "__main__":
    try:
        asyncio.run(
            main()
        )

    except KeyboardInterrupt:
        print()
        print("👋 Test stopped.")
