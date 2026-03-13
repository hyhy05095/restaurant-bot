from agents import (
    Agent,
    output_guardrail,
    Runner,
    RunContextWrapper,
    GuardrailFunctionOutput,
)
from models import ComplaintsOutputGuardRailOutput, UserAccountContext


complaints_output_guardrail_agent = Agent(
    name="Complaints Output Guardrail",
    instructions="""
    Analyze the complaints specialist's response to check if it inappropriately contains:
    
    - Technical details (database queries, error codes, internal logs, API endpoints)
    - Sensitive customer data (full credit card info, passwords, private emails without consent)
    - Non-complaint related info (menu details, order processing, reservations unless directly relevant)
    
    Complaints agents should ONLY handle complaints, empathy, solutions, and escalations.
    Return true for any field that contains inappropriate content for a complaints response.
    """,
    output_type=ComplaintsOutputGuardRailOutput,
)


@output_guardrail
async def technical_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent,
    output: str,
):
    result = await Runner.run(
        complaints_output_guardrail_agent,
        output,
        context=wrapper.context,
    )

    validation = result.final_output

    triggered = (
    validation.contains_technical_details
    or validation.contains_billing_data     
    or validation.contains_account_data      
    or validation.contains_off_topic
)

    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered,
    )