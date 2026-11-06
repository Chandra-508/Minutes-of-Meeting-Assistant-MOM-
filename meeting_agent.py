import json
import ollama

from prompts import MEETING_PROMPT


class MeetingAgent:

    def __init__(self, model="llama3:8b"):
        self.model = model


    def analyze_meeting(self, transcript):

        prompt = MEETING_PROMPT.replace(
            "{transcript}",
            transcript
        )


        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0,
                "num_predict": 4096
            }
        )


        output = response["message"]["content"]


        print("\n========== RAW MODEL OUTPUT ==========")
        print(output)
        print("======================================\n")


        return self.extract_json(output)



    def extract_json(self, text):

        cleaned = text.strip()


        # Remove markdown JSON formatting
        cleaned = cleaned.replace(
            "```json",
            ""
        )

        cleaned = cleaned.replace(
            "```",
            ""
        )

        cleaned = cleaned.strip()


        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1


        if start == -1 or end == 0:
            raise ValueError(
                "No JSON found in model response"
            )


        cleaned = cleaned[start:end]


        try:

            return json.loads(cleaned)


        except json.JSONDecodeError as e:

            print("\n========== INVALID JSON ==========")
            print(cleaned)
            print("==================================\n")

            raise ValueError(
                f"Invalid JSON returned: {e}"
            )