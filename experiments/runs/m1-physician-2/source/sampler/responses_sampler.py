import os
import time
from typing import Any

import openai
from openai import OpenAI

from ..types import MessageList, SamplerBase, SamplerResponse


class ResponsesSampler(SamplerBase):
    """
    Sample from OpenAI's responses API
    """

    def __init__(
        self,
        model: str = "gpt-4.1",
        system_message: str | None = None,
        temperature: float = 0.5,
        max_tokens: int = 1024,
        reasoning_model: bool = False,
        reasoning_effort: str | None = None,
    ):
        self.api_key_name = "OPENAI_API_KEY"
        assert os.environ.get("OPENAI_API_KEY"), "Please set OPENAI_API_KEY"
        self.client = OpenAI(timeout=120.0, max_retries=3)
        self.model = model
        self.system_message = system_message
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.image_format = "url"
        self.reasoning_model = reasoning_model
        self.reasoning_effort = reasoning_effort

    def _handle_image(
        self,
        image: str,
        encoding: str = "base64",
        format: str = "png",
        fovea: int = 768,
    ) -> dict[str, Any]:
        new_image = {
            "type": "input_image",
            "image_url": f"data:image/{format};{encoding},{image}",
        }
        return new_image

    def _handle_text(self, text: str) -> dict[str, Any]:
        return {"type": "input_text", "text": text}

    def _pack_message(self, role: str, content: Any) -> dict[str, Any]:
        return {"role": role, "content": content}

    def __call__(self, message_list: MessageList) -> SamplerResponse:
        if self.system_message:
            message_list = [
                self._pack_message("developer", self.system_message)
            ] + message_list
        kwargs = dict(model=self.model, input=message_list, max_output_tokens=self.max_tokens)
        if self.reasoning_model:
            if self.reasoning_effort:
                kwargs["reasoning"] = {"effort": self.reasoning_effort}
        else:
            kwargs["temperature"] = self.temperature
        response = self.client.responses.create(**kwargs)
        return SamplerResponse(response.output_text, message_list, {"usage": response.usage})
