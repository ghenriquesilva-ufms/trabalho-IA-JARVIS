from openai import OpenAI


def main() -> None:
    client = OpenAI(
        base_url="https://llm.liaufms.org/v1/gemma-3-12b-it",
        api_key="Cxt2ftLF7d3mHS2JdiFqB-eSDAQeZvFATPXPs02lV9A",
    )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "ping",
                "description": "Responde com 'pong'.",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]

    try:
        response = client.chat.completions.create(
            model="google/gemma-3-12b-it",
            messages=[{"role": "user", "content": "Chame a ferramenta ping."}],
            tools=tools,
            tool_choice="auto",
        )
        print("Suporte a tool calling: OK")
        print(response.choices[0].message)
    except Exception as exc:  # pragma: no cover - used for manual validation
        print("Suporte a tool calling: FALHOU")
        print(exc)


if __name__ == "__main__":
    main()
