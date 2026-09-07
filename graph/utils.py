from langchain.chat_models import init_chat_model


def load_llm():
    return init_chat_model(
        "openai/gpt-oss-20b",
        model_provider="groq",
        temperature=0,
    )