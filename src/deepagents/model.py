from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI


def get_vertexai_model():
    return ChatVertexAI(model_name="gemini-2.5-flash", max_tokens=64000)


def get_anthropic_model():
    return ChatAnthropic(model_name="claude-sonnet-4-0", max_tokens=64000)


def get_openai_model():
    return ChatOpenAI(model_name="gpt-5-mini", max_tokens=64000)


def get_default_model():
    return get_vertexai_model()
