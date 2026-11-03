import os

from dotenv import load_dotenv
from openai import OpenAI

from .schemas import MeetingAnalysisRequest, ImplementationUpdate


if not os.getenv("OPENAI_API_KEY"):
    load_dotenv(".env.development")


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def analyze_meeting(request: MeetingAnalysisRequest) -> ImplementationUpdate:

    consultant_notes = request.consultant_notes or "No additional consultant notes provided."

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "You are an AI implementation analyst supporting a technical "
                    "implementation consultant. Analyze customer implementation meeting "
                    "notes and extract an accurate implementation update. "
                    "Do not invent information that is not present in the notes. "
                    "If no information exists for a category, return an empty list. "
                    "Separate customer responsibilities from internal team responsibilities. "

                    "A dependency is something that must happen before a later implementation "
                    "step can proceed. "

                    "A blocker is a significant obstacle preventing meaningful implementation "
                    "progress. A blocker exists when there is a confirmed product or platform "
                    "limitation that prevents a customer requirement from being supported, or when "
                    "confirmed engineering, code changes, or custom technical work are required "
                    "before implementation can continue. The solution to a confirmed product "
                    "limitation does not need to be known yet for it to be considered a blocker. "
                    "A failed API call or technical issue that is still being investigated is not "
                    "automatically a blocker. Classify it as a technical issue and follow-up until "
                    "the investigation identifies whether a product limitation, engineering work, "
                    "code changes, or other blocking condition exists. Do not classify normal "
                    "follow-up tasks, outstanding customer action items, or unresolved technical "
                    "investigations as blockers. "

                    "Constraints are rules or boundaries that must be followed during the "
                    "implementation. "
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Customer: {request.customer}\n\n"
                    f"Meeting Notes:\n{request.meeting_notes}\n\n"
                    f"Consultant Notes:\n{consultant_notes}"
                ),
            },
        ],
        text_format=ImplementationUpdate,
    )

    return response.output_parsed