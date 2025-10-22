from openai import OpenAI

client = OpenAI(
    api_key="vck_4SMXVOYmd2iweo70W2UxqgtZSlmPPwPYB96MP4r1nvGLE00uq93G2sEJ",
    base_url='https://ai-gateway.vercel.sh/v1'
)

system_msg = (
    "You are a friendly, human-like Telegram bot that sends medication reminders. "
    "Keep the tone warm, concise, and easy to understand. "
    "Only return the message text to be sent to the user — do not include explanations, markup, or metadata."
)
messages = [
    {"role": "system", "content": system_msg},
    {"role": "user", "content": "Create a friendly medication reminder message for a user to take their medicine named 'Aspirin'."}
]

response = client.chat.completions.create(
    model="openai/gpt-5-nano",
    messages=messages,
    temperature=0.8
)
response_text = response.choices[0].message.content.strip()
print(response_text)
