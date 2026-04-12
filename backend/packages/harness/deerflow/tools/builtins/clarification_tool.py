from typing import Literal

from langchain.tools import tool


@tool("ask_clarification", parse_docstring=True, return_direct=True)
def ask_clarification_tool(
    question: str,
    clarification_type: Literal[
        "missing_info",
        "ambiguous_requirement",
        "approach_choice",
        "risk_confirmation",
        "suggestion",
    ],
    context: str | None = None,
    options: list[str] | None = None,
) -> str:
    """Ask the resident for clarification when you need more information to proceed with home automation or configuration.

    Use this tool when you encounter situations where you cannot proceed without resident input:

    - **Missing information**: Required details not provided (e.g., room location, device name, specific automation trigger)
    - **Ambiguous requirements**: Multiple valid interpretations exist (e.g., "cool the room" could mean 18°C or 24°C)
    - **Approach choices**: Several valid automation strategies exist and you need resident preference
    - **Risky operations**: Actions that might impact security or comfort (e.g., unlocking doors, disabling alarms, factory resetting devices)
    - **Suggestions**: You have a recommended scene or automation but want approval before applying it

    The configuration flow will be interrupted and the question will be presented to the resident.
    Wait for the resident's response before continuing.

    When to use ask_clarification:
    - You need device or room IDs that weren't provided
    - The automation logic can be interpreted in multiple ways
    - Multiple valid IoT protocols or device choices exist
    - You're about to perform a potentially high-impact security change
    - You have a better automation suggestion but need approval

    Best practices:
    - Ask ONE clarification at a time for clarity in the home environment
    - Be specific and clear about which device or room is affected
    - Don't make assumptions about resident habits or comfort levels
    - For security-sensitive operations, ALWAYS ask for confirmation
    - After calling this tool, the system will pause for feedback

    Args:
        question: The clarification question to ask the resident. Be specific and clear.
        clarification_type: The type of clarification needed (missing_info, ambiguous_requirement, approach_choice, risk_confirmation, suggestion).
        context: Optional context explaining why clarification is needed. Helps the resident understand the system's reasoning.
        options: Optional list of choices (for approach_choice or suggestion types). Present clear options (e.g. "Eco Mode", "Performance Mode") for the resident to choose from.
    """
    # This is a placeholder implementation
    # The actual logic is handled by ClarificationMiddleware which intercepts this tool call
    # and interrupts execution to present the question to the user
    return "Clarification request processed by middleware"
