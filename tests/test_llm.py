import io
import os
import unittest
from unittest.mock import patch

from dotenv import load_dotenv

from llm import build_model


class BuildModelTests(unittest.TestCase):
    config = {
        "LLM_BASE_URL": "http://localhost:11434/v1",
        "LLM_MODEL": "beam:cloud",
        "LLM_API_KEY": "ollama",
    }

    def test_loads_dotenv_without_overriding_environment(self):
        dotenv = "\n".join(f"{name}={value}" for name, value in self.config.items())
        with patch.dict(os.environ, {"LLM_MODEL": "environment-model"}, clear=True):
            with patch("llm.load_dotenv", side_effect=lambda: load_dotenv(stream=io.StringIO(dotenv))):
                model = build_model()
        self.assertEqual(model.model_name, "environment-model")
        self.assertEqual(model.openai_api_base, self.config["LLM_BASE_URL"])
        self.assertEqual(model.openai_api_key.get_secret_value(), "ollama")

    def test_rejects_missing_or_blank_configuration(self):
        for name in self.config:
            for value in (None, "", "   "):
                with self.subTest(name=name, value=value):
                    config = dict(self.config)
                    config.pop(name)
                    if value is not None:
                        config[name] = value
                    with patch.dict(os.environ, config, clear=True), patch("llm.load_dotenv"):
                        with self.assertRaisesRegex(RuntimeError, name):
                            build_model()


if __name__ == "__main__":
    unittest.main()
