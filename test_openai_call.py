from openai import OpenAI

client = OpenAI(
    api_key="sk-005b8b72587cf0b316a60f12dd2d9607b8c43a9122bf57d3",
    base_url="https://model-router.edu-aliyun.com/v1",
)

completion = client.chat.completions.create(
    model="qwen/kimi-k2.6",
    messages=[
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
)
print(completion.choices[0].message.content)
