#!/usr/bin/env python3
"""
Script to update FakeAI with context window validation.
This script updates the model initialization and adds context window limits.
"""

import re

# Read the fakeai_service.py file
with open("fakeai/fakeai_service.py", "r") as f:
    content = f.read()

# Find and replace the new_model function and model initialization
pattern = r"        def new_model\(model_id: str\) -> Model:.*?self\.models = \{[^}]+\}"

replacement = '''        def new_model(
            model_id: str,
            owned_by: str = "custom",
            context_window: int = 8192,
            max_output_tokens: int = 4096,
        ) -> Model:
            """Create a new model instance with specified properties."""
            return Model(
                id=model_id,
                created=creation_time,
                owned_by=owned_by,
                permission=[base_permission],
                root=None,
                parent=None,
                context_window=context_window,
                max_output_tokens=max_output_tokens,
            )

        # Initialize with a dictionary for explicit models with proper context window limits
        self.models = {
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0": new_model("TinyLlama/TinyLlama-1.1B-Chat-v1.0", "openai", 1024, 1024),
            "meta-llama/Llama-3.1-8B-Instruct": new_model("meta-llama/Llama-3.1-8B-Instruct", "openai", 16384, 4096),
            "openai/gpt-oss-120b": new_model("openai/gpt-oss-120b", "openai", 8192, 4096),
            "openai/gpt-oss-120b": new_model("openai/gpt-oss-120b", "openai", 128000, 4096),
            "openai/gpt-oss-120b": new_model("openai/gpt-oss-120b", "openai", 128000, 4096),
            "openai/gpt-oss-20b": new_model("openai/gpt-oss-20b", "openai", 128000, 16384),
            "sentence-transformers/all-mpnet-base-v2": new_model("sentence-transformers/all-mpnet-base-v2", "openai", 8191, 0),
            "stabilityai/stable-diffusion-2-1": new_model("stabilityai/stable-diffusion-2-1", "openai", 1000, 0),
            "stabilityai/stable-diffusion-xl-base-1.0": new_model("stabilityai/stable-diffusion-xl-base-1.0", "openai", 4000, 0),
            "deepseek-ai/DeepSeek-R1-Distill-Llama-8B": new_model(
                "deepseek-ai/DeepSeek-R1-Distill-Llama-8B", "deepseek-ai", 8192, 4096
            ),
            "meta-llama/Llama-3.1-8B-Instruct": new_model("meta-llama/Llama-3.1-8B-Instruct", "openai", 4096, 4096),
            "gpt-oss-120b": new_model("gpt-oss-120b", "openai", 128000, 4096),
            "gpt-oss-20b": new_model("gpt-oss-20b", "openai", 32768, 4096),
            "deepseek-ai/DeepSeek-R1": new_model("deepseek-ai/DeepSeek-R1", "openai", 200000, 100000),
            "deepseek-ai/DeepSeek-R1": new_model("deepseek-ai/DeepSeek-R1", "openai", 128000, 32768),
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": new_model("deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", "openai", 128000, 65536),
            "mixtral-8x7b": new_model("mixtral-8x7b", "mistralai", 32768, 4096),
            "mixtral-8x22b": new_model("mixtral-8x22b", "mistralai", 65536, 4096),
            "deepseek-v3": new_model("deepseek-v3", "deepseek-ai", 64000, 8192),
        }'''

# Use re.DOTALL to match across newlines
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

print("Script created. Now you need to run it manually to update the file.")
print("This is a placeholder - the actual update should be done with the Edit tool.")
