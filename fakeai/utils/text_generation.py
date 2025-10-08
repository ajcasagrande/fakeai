"""
Simulated text generation for various prompt types.

This module provides the SimulatedGenerator class which generates realistic
responses for different types of prompts including greetings, questions, and
coding requests.
"""

#  SPDX-License-Identifier: Apache-2.0

import random
import re

from faker import Faker

from fakeai.utils.tokens import calculate_token_count


class SimulatedGenerator:
    """Generator for simulated responses."""

    # Pre-compiled regex patterns for better performance
    _GREETING_PATTERNS = [
        re.compile(r"\bhello\b"),
        re.compile(r"\bhi\b"),
        re.compile(r"\bhey\b"),
        re.compile(r"\bgreetings\b"),
        re.compile(r"\bgood (morning|afternoon|evening)\b"),
    ]

    _QUESTION_PATTERNS = [
        re.compile(r"\bwhat\b"),
        re.compile(r"\bwho\b"),
        re.compile(r"\bwhen\b"),
        re.compile(r"\bwhere\b"),
        re.compile(r"\bwhy\b"),
        re.compile(r"\bhow\b"),
        re.compile(r"\bcan you\b"),
        re.compile(r"\bcould you\b"),
    ]

    _CODING_PATTERNS = [
        re.compile(r"\bcode\b"),
        re.compile(r"\bfunction\b"),
        re.compile(r"\bclass\b"),
        re.compile(r"\bpython\b"),
        re.compile(r"\bjavascript\b"),
        re.compile(r"\btypescript\b"),
        re.compile(r"\bjava\b"),
        re.compile(r"\bc\+\+\b"),
        re.compile(r"\bruby\b"),
        re.compile(r"\brust\b"),
        re.compile(r"\bgo\b"),
        re.compile(r"\bprogram\b"),
        re.compile(r"\balgorithm\b"),
    ]

    _TOPIC_PHRASE_PATTERN = re.compile(
        r"(?:about|regarding|on) (\w+(?:\s+\w+){0,3})")
    _NOUN_PHRASE_PATTERN = re.compile(
        r"(?:what|who|when|where|why|how) (?:is|are|was|were) (\w+(?:\s+\w+){0,3})"
    )
    _KEYWORD_PATTERN = re.compile(r"\b\w{4,}\b")
    _CODE_CONCEPT_PATTERN = re.compile(
        r"\b(function|class|object|array|list|dictionary|map|sort|search|algorithm|api|http|request|response|json|xml|database|sql|query|insert|update|delete|select|from|where|join|group by|order by|file|read|write|input|output|print|log|debug|error|exception|try|catch|if|else|for|while|loop|recursion|callback|promise|async|await|thread|process|parallel)\b"
    )

    # Language detection patterns (pre-compiled)
    _LANGUAGE_PATTERNS = {
        "python": re.compile(r"\bpython\b"),
        "javascript": re.compile(r"\b(?:javascript|js)\b"),
        "typescript": re.compile(r"\b(?:typescript|ts)\b"),
        "java": re.compile(r"\bjava\b"),
        "c++": re.compile(r"\b(?:c\+\+|cpp)\b"),
        "rust": re.compile(r"\brust\b"),
        "go": re.compile(r"\b(?:golang|go)\b"),
        "ruby": re.compile(r"\bruby\b"),
        "php": re.compile(r"\bphp\b"),
        "c#": re.compile(r"\b(?:c#|csharp)\b"),
        "swift": re.compile(r"\bswift\b"),
        "kotlin": re.compile(r"\bkotlin\b"),
    }

    def __init__(self):
        """Initialize the simulated generator."""
        self.fake = Faker()

        # Common AI responses for different types of prompts with emojis and
        # markdown
        self.responses = {
            "greeting": [
                "👋 **Hello!** How can I assist you today?",
                "🎯 **Hi there!** I'm here to help you with any questions you might have.",
                "✨ **Greetings!** How may I be of service?",
                "🚀 **Hello!** I'm your AI assistant. What can I help you with?",
            ],
            "question": [
                "💡 **Great Question!**\n\nLet me provide you with a comprehensive answer.\n\n{}",
                "📚 **I'd Be Happy to Help**\n\nHere's what you need to know:\n\n{}",
                "🎯 **Excellent Inquiry!**\n\nLet me break this down for you:\n\n{}",
            ],
            "coding": [
                "💻 **Code Solution**\n\nHere's an example that should help:\n\n```{}\n{}\n```\n\n**How it works:**\n\nLet me explain the key concepts...",
                "🔧 **Implementation Guide**\n\nConsider this approach:\n\n```{}\n{}\n```\n\n**Key Points:**\n\n- The code demonstrates proper structure\n- Error handling is included\n- Best practices are followed",
            ],
            "default": [
                "🤔 **Understanding {}**\n\nLet me provide comprehensive information:\n\n{}",
                "📖 **About {}**\n\nThere are several important aspects to consider:\n\n{}",
                "✨ **Exploring {}**\n\nHere's what you should know:\n\n{}",
            ],
        }

        # Emojis for various contexts
        self.emojis = {
            "start": ["👋", "🎯", "💡", "✨", "🚀", "📚", "🔍", "💬"],
            "important": ["⚡", "🎯", "💎", "🌟", "🔥"],
            "tip": ["💡", "💭", "🔔", "📌"],
            "warning": ["⚠️", "⚡", "🚨"],
            "success": ["✅", "🎉", "✨", "🌟"],
            "technical": ["⚙️", "🔧", "💻", "🖥️", "📊"],
        }

    def generate_response(
        self,
        prompt: str,
        max_tokens: int = 100,
    ) -> str:
        """Generate a simulated response based on the prompt."""
        # Identify the type of prompt
        prompt_type = self._identify_prompt_type(prompt.lower())

        # Generate a response based on the prompt type
        if prompt_type == "greeting":
            response = random.choice(self.responses["greeting"])
        elif prompt_type == "question":
            base = random.choice(self.responses["question"])
            # Generate paragraphs based on keywords in the prompt
            content = self._generate_content_from_keywords(prompt, max_tokens)
            response = base.format(content)
        elif prompt_type == "coding":
            base = random.choice(self.responses["coding"])
            language = self._identify_coding_language(prompt)
            code = self._generate_simulated_code(language, prompt)
            response = base.format(language, code)
        else:
            base = random.choice(self.responses["default"])
            topic = self._extract_topic(prompt)
            content = self._generate_content_from_keywords(prompt, max_tokens)
            response = base.format(topic, content)

        # Trim to max tokens using actual token counting
        # Check actual token count
        current_tokens = calculate_token_count(response)

        # If over limit, trim by sentences
        if current_tokens > max_tokens:
            sentences = response.split(". ")
            trimmed_sentences = []
            for i, sentence in enumerate(sentences):
                # Reconstruct with proper delimiters: add ". " only between
                # sentences, not at end
                if trimmed_sentences:
                    test_text = ". ".join(trimmed_sentences + [sentence])
                    # Add final period if this isn't the last sentence
                    if i < len(sentences) - 1 or response.endswith("."):
                        test_text += "."
                else:
                    test_text = sentence
                    if i < len(sentences) - 1 or response.endswith("."):
                        test_text += "."

                if calculate_token_count(test_text) <= max_tokens:
                    trimmed_sentences.append(sentence)
                else:
                    break

            # If we got at least something, use it
            if trimmed_sentences:
                result = ". ".join(trimmed_sentences)
                # Add final period if original had one
                if response.endswith(".") and not result.endswith("."):
                    result += "."
                return result

            # Otherwise, hard trim by characters (fallback)
            max_chars = max_tokens * 4
            return response[:max_chars]

        return response

    def _identify_prompt_type(self, prompt: str) -> str:
        """Identify the type of prompt."""
        for pattern in self._GREETING_PATTERNS:
            if pattern.search(prompt):
                return "greeting"

        for pattern in self._CODING_PATTERNS:
            if pattern.search(prompt):
                return "coding"

        for pattern in self._QUESTION_PATTERNS:
            if pattern.search(prompt):
                return "question"

        return "default"

    def _extract_topic(self, prompt: str) -> str:
        """Extract a topic from the prompt."""
        # Simple topic extraction based on keywords
        topic_phrases = self._TOPIC_PHRASE_PATTERN.findall(prompt)
        if topic_phrases:
            return topic_phrases[0]

        # Look for nouns following question words
        noun_phrases = self._NOUN_PHRASE_PATTERN.findall(prompt)
        if noun_phrases:
            return noun_phrases[0]

        # Default to the first few words
        words = prompt.strip().split()
        if len(words) <= 3:
            return prompt.strip()
        else:
            return " ".join(words[:3]) + "..."

    def _generate_content_from_keywords(
            self, prompt: str, max_tokens: int) -> str:
        """Generate content based on keywords in the prompt with markdown formatting."""
        # Extract keywords from the prompt
        words = self._KEYWORD_PATTERN.findall(prompt.lower())
        relevant_words = [
            word for word in words if word not in self.fake.words()]

        if not relevant_words:
            relevant_words = ["topic"]

        # Detect prompt intent for contextual formatting
        prompt_lower = prompt.lower()
        is_how_to = any(
            word in prompt_lower for word in [
                "how to", "how do", "how can"])
        is_what_is = any(
            word in prompt_lower for word in [
                "what is",
                "what are",
                "define",
                "explain"])
        is_comparison = any(
            word in prompt_lower for word in [
                "compare",
                "versus",
                "vs",
                "difference",
                "better"])
        is_code_request = any(
            word in prompt_lower for word in [
                "code",
                "example",
                "implement",
                "function",
                "program"])

        # Vary token count based on max_tokens
        # Short: 10-200, Medium: 200-500, Long: 500-1000+
        if max_tokens < 50:
            # Very short responses (10-50 tokens)
            target_tokens = min(max_tokens, random.randint(10, 50))
        elif max_tokens < 200:
            target_tokens = random.randint(50, min(200, max_tokens))
        elif max_tokens < 500:
            target_tokens = random.randint(200, min(500, max_tokens))
        else:
            target_tokens = random.randint(500, max_tokens)

        # Generate sections with markdown formatting
        sections = []

        # Start with emoji and engaging intro
        start_emoji = random.choice(self.emojis["start"])

        # Contextual opening based on prompt type
        if is_how_to:
            sections.append(
                f"{start_emoji} **How to Get Started**\n\nLet me walk you through this step by step.")
        elif is_what_is:
            sections.append(
                f"{start_emoji} **Understanding the Concept**\n\nLet me explain this clearly.")
        elif is_comparison:
            sections.append(
                f"{start_emoji} **Comparison Overview**\n\nLet me break down the key differences and similarities.")
        else:
            sections.append(
                f"{start_emoji} **Overview**\n\nLet me provide you with comprehensive information about this.")

        # For "how to" questions, use numbered steps (always)
        if is_how_to:
            sections.append(
                f"\n## {
                    random.choice(
                        self.emojis['technical'])} **Step-by-Step Guide**\n")
            num_steps = random.randint(
                4, 6) if target_tokens > 300 else random.randint(
                3, 4)
            for i in range(1, num_steps + 1):
                keyword = relevant_words[(i - 1) % len(relevant_words)]
                sections.append(
                    f"{i}. **{keyword.capitalize()} Phase**: Start by understanding and implementing the {keyword} component. This is crucial for the overall process.")

        # For "what is" questions, use bullet points (always)
        elif is_what_is:
            sections.append(
                f"\n## {
                    random.choice(
                        self.emojis['important'])} **Key Characteristics**\n")
            num_bullets = random.randint(
                4, 6) if target_tokens > 300 else random.randint(
                3, 4)
            for i in range(num_bullets):
                keyword = relevant_words[i % len(relevant_words)]
                sections.append(
                    f"- **{keyword.capitalize()}**: A fundamental aspect that defines how this works")

        # For comparison questions, use table (always)
        elif is_comparison:
            sections.append(
                f"\n## {
                    random.choice(
                        self.emojis['technical'])} **Side-by-Side Comparison**\n")
            sections.append("| Feature | Option A | Option B |")
            sections.append("|---------|----------|----------|")
            for i in range(min(4, len(relevant_words))):
                keyword = relevant_words[i % len(relevant_words)]
                sections.append(
                    f"| {
                        keyword.capitalize()} | Excellent support | Good support |")

        # For other questions, mix bullet points and numbered lists
        else:
            # Add bullet points
            if target_tokens > 150:
                sections.append(
                    f"\n## {
                        random.choice(
                            self.emojis['important'])} **Key Points**\n")
                num_bullets = random.randint(3, 5)
                for i in range(num_bullets):
                    keyword = relevant_words[i % len(relevant_words)]
                    sections.append(
                        f"- **{keyword.capitalize()}**: Understanding the {keyword} is essential for mastery")

            # Add numbered list for medium/long responses
            if target_tokens > 300:
                sections.append(
                    f"\n## {
                        random.choice(
                            self.emojis['technical'])} **Implementation Steps**\n")
                num_steps = random.randint(3, 5)
                for i in range(1, num_steps + 1):
                    keyword = relevant_words[(i - 1) % len(relevant_words)]
                    sections.append(
                        f"{i}. *{keyword.capitalize()}* - Apply this concept with careful attention to detail")

        # Add code block for code requests (high priority)
        if is_code_request or (random.random() > 0.6 and target_tokens > 250):
            # Detect language from prompt
            lang = "python"  # default
            if "javascript" in prompt_lower or "js" in prompt_lower:
                lang = "javascript"
            elif "typescript" in prompt_lower or "ts" in prompt_lower:
                lang = "typescript"
            elif "bash" in prompt_lower or "shell" in prompt_lower:
                lang = "bash"
            elif "java" in prompt_lower:
                lang = "java"

            sections.append(
                f"\n## {
                    random.choice(
                        self.emojis['technical'])} **Code Example**\n")
            keyword = relevant_words[0]

            if lang == "python":
                sections.append(
                    f"```python\n# Example implementation\ndef process_{keyword}(data):\n    \"\"\"\n    Process {keyword} with the given data.\n    \"\"\"\n    result = {{\n        '{keyword}': data,\n        'status': 'success',\n        'processed': True\n    }}\n    return result\n\n# Usage\noutput = process_{keyword}(input_data)\nprint(f'Result: {{output}}')\n```")
            elif lang == "javascript":
                sections.append(
                    f"```javascript\n// Example implementation\nfunction process{
                        keyword.capitalize()}(data) {{\n  const result = {{\n    {keyword}: data,\n    status: 'success',\n    processed: true\n  }};\n  return result;\n}}\n\n// Usage\nconst output = process{
                        keyword.capitalize()}(inputData);\nconsole.log(`Result: ${{JSON.stringify(output)}}`);\n```")
            elif lang == "bash":
                sections.append(
                    f"```bash\n#!/bin/bash\n# Example script for {keyword}\n\n{keyword}_process() {{\n  local input=$1\n  echo \"Processing $input...\"\n  # Add your logic here\n  echo \"Done!\"\n}}\n\n# Usage\n{keyword}_process \"example_data\"\n```")
            else:
                sections.append(
                    f"```{lang}\n// Example {keyword} implementation\npublic class {
                        keyword.capitalize()}Processor {{\n  public Result process(Data input) {{\n    // Implementation here\n    return new Result(input);\n  }}\n}}\n```")

            sections.append(
                f"\n**How it works:**\n\nThe code demonstrates a practical implementation of {keyword}. Key features include proper structure, error handling, and clear documentation.")

        # Add a comparison table for non-comparison questions (occasionally)
        if not is_comparison and random.random() > 0.7 and target_tokens > 400:
            sections.append(
                f"\n## {
                    random.choice(
                        self.emojis['technical'])} **Quick Reference**\n")
            sections.append("| Aspect | Description | Status |")
            sections.append("|--------|-------------|--------|")
            for i in range(min(3, len(relevant_words))):
                keyword = relevant_words[i % len(relevant_words)]
                status = random.choice(
                    ["✅ Available", "⚡ Recommended", "🔧 In Progress"])
                sections.append(
                    f"| {
                        keyword.capitalize()} | Core functionality | {status} |")

        # Add a blockquote tip (medium/high frequency)
        if random.random() > 0.4 and target_tokens > 200:
            tip_emoji = random.choice(self.emojis["tip"])
            tips = [
                f"\n> {tip_emoji} **Pro Tip**: Always test your implementation thoroughly when working with `{relevant_words[0]}`.",
                f"\n> {tip_emoji} **Best Practice**: Consider edge cases and error handling for optimal `{relevant_words[0]}` usage.",
                f"\n> {tip_emoji} **Remember**: Performance optimization is key when dealing with `{relevant_words[0]}` at scale.",
            ]
            sections.append(random.choice(tips))

        # Add inline code in a descriptive paragraph (for variety)
        if target_tokens > 250 and random.random() > 0.6:
            sections.append(
                f"\n### **Additional Considerations**\n\nWhen working with `{
                    relevant_words[0]}`, it's important to consider the `{
                    relevant_words[
                        min(
                            1,
                            len(relevant_words) -
                            1)]}` aspect. You can use inline methods like `.configure()` and `.execute()` to streamline your workflow.")

        # Add concluding section with emoji
        if target_tokens > 200:
            conclusion_emoji = random.choice(self.emojis["success"])
            conclusions = [
                f"\n{conclusion_emoji} **Summary**\n\nYou now have a comprehensive understanding of this topic. Apply these concepts to achieve the best results!",
                f"\n{conclusion_emoji} **Conclusion**\n\nThese fundamentals will help you master the topic effectively. Keep practicing and experimenting!",
                f"\n{conclusion_emoji} **Next Steps**\n\nWith this knowledge, you're ready to implement these concepts in your projects. Good luck!",
            ]
            sections.append(random.choice(conclusions))
        else:
            # Short conclusion for brief responses
            conclusion_emoji = random.choice(self.emojis["success"])
            sections.append(f"\n{conclusion_emoji} Hope this helps!")

        # Join all sections
        content = "\n".join(sections)

        # Ensure we don't exceed max_tokens
        current_tokens = calculate_token_count(content)
        if current_tokens > max_tokens:
            # Trim by sections (keep intro and at least one main section)
            trimmed_sections = [sections[0]]  # Always keep intro
            for section in sections[1:]:
                test_content = "\n".join(trimmed_sections + [section])
                if calculate_token_count(test_content) <= max_tokens:
                    trimmed_sections.append(section)
                else:
                    break

            # If we have room, try to add a short conclusion
            if len(trimmed_sections) > 1:
                final_emoji = random.choice(self.emojis["success"])
                short_conclusion = f"\n{final_emoji} Hope this helps!"
                test_with_conclusion = "\n".join(
                    trimmed_sections + [short_conclusion])
                if calculate_token_count(test_with_conclusion) <= max_tokens:
                    trimmed_sections.append(short_conclusion)

            content = "\n".join(trimmed_sections)

        return content

    def _identify_coding_language(self, prompt: str) -> str:
        """Identify the coding language from the prompt."""
        prompt_lower = prompt.lower()
        for lang, pattern in self._LANGUAGE_PATTERNS.items():
            if pattern.search(prompt_lower):
                return lang

        # Default to Python if no language is specified
        return "python"

    def _generate_simulated_code(self, language: str, prompt: str) -> str:
        """Generate simulated code in the specified language."""
        # Extract relevant code concepts from the prompt
        concepts = set(self._CODE_CONCEPT_PATTERN.findall(prompt.lower()))

        if language == "python":
            return self._generate_python_code(concepts, prompt)
        elif language in ["javascript", "js"]:
            return self._generate_javascript_code(concepts, prompt)
        elif language in ["typescript", "ts"]:
            return self._generate_typescript_code(concepts, prompt)
        elif language == "java":
            return self._generate_java_code(concepts, prompt)
        elif language in ["c++", "cpp"]:
            return self._generate_cpp_code(concepts, prompt)
        else:
            # For other languages, generate a generic code sample
            return self._generate_generic_code(language, concepts, prompt)

    def _generate_python_code(self, concepts: set, prompt: str) -> str:
        """Generate Python code based on concepts."""
        if "class" in concepts:
            class_name = "".join(
                w.capitalize()
                for w in random.choice(
                    ["data", "user", "processing", "service"]
                ).split()
            )
            code = f"class {class_name}:\n"
            code += "    def __init__(self, name, value=None):\n"
            code += "        self.name = name\n"
            code += "        self.value = value or 0\n\n"
            code += "    def process(self):\n"
            code += "        return self.value * 2\n\n"
            code += f"# Create an instance\nobj = {class_name}('example', 42)\n"
            code += "result = obj.process()\n"
            code += "print(f'Processed {obj.name}: {result}')"
            return code
        elif "function" in concepts:
            func_name = random.choice(
                [
                    "process_data",
                    "calculate_result",
                    "transform_input",
                    "handle_request",
                ]
            )
            code = f"def {func_name}(data, option=None):\n"
            code += '    """\n'
            code += "    Process the input data and return a result.\n"
            code += "    \n"
            code += "    Args:\n"
            code += "        data: The input data to process\n"
            code += "        option: Optional processing parameter\n"
            code += "    \n"
            code += "    Returns:\n"
            code += "        The processed result\n"
            code += '    """\n'
            code += "    result = {}\n"
            code += "    if isinstance(data, list):\n"
            code += "        result['type'] = 'list'\n"
            code += "        result['length'] = len(data)\n"
            code += "        result['sum'] = sum(data) if all(isinstance(x, (int, float)) for x in data) else None\n"
            code += "    elif isinstance(data, dict):\n"
            code += "        result['type'] = 'dict'\n"
            code += "        result['keys'] = list(data.keys())\n"
            code += "    else:\n"
            code += "        result['type'] = str(type(data).__name__)\n"
            code += "        result['string'] = str(data)\n"
            code += "    \n"
            code += "    if option:\n"
            code += "        result['option'] = option\n"
            code += "    \n"
            code += "    return result\n\n"
            code += "# Example usage\n"
            code += "sample_data = [1, 2, 3, 4, 5]\n"
            code += f"output = {func_name}(sample_data, 'sum')\n"
            code += "print(output)"
            return code
        else:
            # General Python snippet
            code = "# Example Python code\n"
            code += "import json\n"
            code += "from datetime import datetime\n\n"
            code += "def analyze_data(data):\n"
            code += "    results = {\n"
            code += "        'timestamp': datetime.now().isoformat(),\n"
            code += "        'count': len(data),\n"
            code += "        'types': {}\n"
            code += "    }\n"
            code += "    \n"
            code += "    for item in data:\n"
            code += "        item_type = type(item).__name__\n"
            code += "        if item_type not in results['types']:\n"
            code += "            results['types'][item_type] = 0\n"
            code += "        results['types'][item_type] += 1\n"
            code += "    \n"
            code += "    return results\n\n"
            code += "# Sample data\n"
            code += "sample = [1, 'text', 3.14, {'key': 'value'}, [1, 2, 3]]\n"
            code += "result = analyze_data(sample)\n"
            code += "print(json.dumps(result, indent=2))"
            return code

    def _generate_javascript_code(self, concepts: set, prompt: str) -> str:
        """Generate JavaScript code based on concepts."""
        if "class" in concepts:
            class_name = "".join(
                w.capitalize()
                for w in random.choice(
                    ["data", "user", "processing", "service"]
                ).split()
            )
            code = f"class {class_name} {{\n"
            code += "  constructor(name, value = 0) {\n"
            code += "    this.name = name;\n"
            code += "    this.value = value;\n"
            code += "    this.created = new Date();\n"
            code += "  }\n\n"
            code += "  process() {\n"
            code += "    return this.value * 2;\n"
            code += "  }\n\n"
            code += "  getInfo() {\n"
            code += "    return {\n"
            code += "      name: this.name,\n"
            code += "      value: this.value,\n"
            code += "      processed: this.process(),\n"
            code += "      created: this.created\n"
            code += "    };\n"
            code += "  }\n"
            code += "}\n\n"
            code += (
                f"// Create an instance\nconst obj = new {class_name}('example', 42);\n")
            code += "console.log(obj.getInfo());"
            return code
        elif "async" in concepts or "await" in concepts or "promise" in concepts:
            func_name = random.choice(
                ["fetchData", "processAsync", "loadResources", "getApiResponse"]
            )
            code = f"async function {func_name}(url, options = {{}}) {{\n"
            code += "  console.log(`Fetching data from ${url}...`);\n\n"
            code += "  try {\n"
            code += "    const response = await fetch(url, {\n"
            code += "      method: options.method || 'GET',\n"
            code += "      headers: options.headers || { 'Content-Type': 'application/json' },\n"
            code += (
                "      body: options.body ? JSON.stringify(options.body) : undefined\n"
            )
            code += "    });\n\n"
            code += "    if (!response.ok) {\n"
            code += "      throw new Error(`HTTP error: ${response.status}`);\n"
            code += "    }\n\n"
            code += "    const data = await response.json();\n"
            code += "    return {\n"
            code += "      success: true,\n"
            code += "      data,\n"
            code += "      timestamp: new Date()\n"
            code += "    };\n"
            code += "  } catch (error) {\n"
            code += "    console.error(`Error in ${func_name}:`, error);\n"
            code += "    return {\n"
            code += "      success: false,\n"
            code += "      error: error.message,\n"
            code += "      timestamp: new Date()\n"
            code += "    };\n"
            code += "  }\n"
            code += "}\n\n"
            code += "// Example usage\n"
            code += f"{func_name}('https://api.example.com/data')\n"
            code += "  .then(result => console.log(result))\n"
            code += "  .catch(error => console.error(error));"
            return code
        else:
            # General JavaScript snippet
            code = "// Example JavaScript utility functions\n\n"
            code += "const utils = {\n"
            code += "  formatDate(date) {\n"
            code += "    const d = new Date(date);\n"
            code += "    const year = d.getFullYear();\n"
            code += "    const month = String(d.getMonth() + 1).padStart(2, '0');\n"
            code += "    const day = String(d.getDate()).padStart(2, '0');\n"
            code += "    return `${year}-${month}-${day}`;\n"
            code += "  },\n\n"
            code += "  generateId(prefix = 'id') {\n"
            code += (
                "    return `${prefix}_${Math.random().toString(36).substr(2, 9)}`;\n"
            )
            code += "  },\n\n"
            code += "  debounce(func, wait) {\n"
            code += "    let timeout;\n"
            code += "    return function executedFunction(...args) {\n"
            code += "      const later = () => {\n"
            code += "        clearTimeout(timeout);\n"
            code += "        func(...args);\n"
            code += "      };\n"
            code += "      clearTimeout(timeout);\n"
            code += "      timeout = setTimeout(later, wait);\n"
            code += "    };\n"
            code += "  }\n"
            code += "};\n\n"
            code += "// Example usage\n"
            code += "console.log(utils.formatDate(new Date()));\n"
            code += "console.log(utils.generateId('user'));\n\n"
            code += "const handleInput = utils.debounce(() => {\n"
            code += "  console.log('Input handled!');\n"
            code += "}, 300);\n\n"
            code += "// Call handleInput multiple times - it will only execute once after 300ms\n"
            code += "handleInput();\n"
            code += "handleInput();\n"
            code += "handleInput();"
            return code

    def _generate_typescript_code(self, concepts: set, prompt: str) -> str:
        """Generate TypeScript code based on concepts."""
        if "interface" in concepts or "type" in concepts or "class" in concepts:
            # Generate TypeScript with interfaces and classes
            interface_name = "".join(
                w.capitalize()
                for w in random.choice(["data", "user", "item", "config"]).split()
            )
            class_name = interface_name + "Service"

            code = f"interface {interface_name} {{\n"
            code += "  id: string;\n"
            code += "  name: string;\n"
            code += "  value: number;\n"
            code += "  createdAt: Date;\n"
            code += "  metadata?: Record<string, any>;\n"
            code += "}\n\n"

            code += (
                f"type {interface_name}Status = 'active' | 'inactive' | 'pending';\n\n"
            )

            code += f"class {class_name} {{\n"
            code += "  private items: Map<string, " + interface_name + ">;\n"
            code += "  private status: Map<string, " + interface_name + "Status>;\n\n"

            code += "  constructor() {\n"
            code += "    this.items = new Map();\n"
            code += "    this.status = new Map();\n"
            code += "  }\n\n"

            code += f"  create(name: string, value: number, metadata?: Record<string, any>): {interface_name} {{\n"
            code += "    const id = this.generateId();\n"
            code += "    const now = new Date();\n"
            code += "    const item = { id, name, value, createdAt: now, metadata };\n"
            code += "    this.items.set(id, item);\n"
            code += "    this.status.set(id, 'active');\n"
            code += "    return item;\n"
            code += "  }\n\n"

            code += f"  get(id: string): {interface_name} | undefined {{\n"
            code += "    return this.items.get(id);\n"
            code += "  }\n\n"

            code += f"  getStatus(id: string): {interface_name}Status | undefined {{\n"
            code += "    return this.status.get(id);\n"
            code += "  }\n\n"

            code += (
                "  update(id: string, updates: Partial<" +
                interface_name +
                ">): boolean {\n"
            )
            code += "    const item = this.items.get(id);\n"
            code += "    if (!item) return false;\n\n"
            code += "    this.items.set(id, { ...item, ...updates });\n"
            code += "    return true;\n"
            code += "  }\n\n"

            code += "  private generateId(): string {\n"
            code += "    return Math.random().toString(36).substr(2, 9);\n"
            code += "  }\n"
            code += "}\n\n"

            code += "// Example usage\n"
            code += f"const service = new {class_name}();\n"
            code += "const item = service.create('Example', 42, { tags: ['test'] });\n"
            code += "console.log(item);\n"
            code += "console.log(`Status: ${service.getStatus(item.id)}`);\n\n"
            code += "// Update the item\n"
            code += "service.update(item.id, { value: 100 });\n"
            code += "console.log(service.get(item.id));"

            return code
        else:
            # Default to JS-style with TypeScript types
            return (
                self._generate_javascript_code(
                    concepts,
                    prompt) .replace(
                    "function",
                    "function") .replace(
                    "const utils = {",
                    "interface Utils {\n  formatDate(date: Date | string): string;\n  generateId(prefix?: string): string;\n  debounce<T extends (...args: any[]) => any>(func: T, wait: number): (...args: Parameters<T>) => void;\n}\n\nconst utils: Utils = {",
                ) .replace(
                    ".padStart(2, '0')",
                    ".padStart(2, '0' as string)"))

    def _generate_java_code(self, concepts: set, prompt: str) -> str:
        """Generate Java code based on concepts."""
        class_name = "".join(
            w.capitalize()
            for w in random.choice(["data", "user", "processing", "service"]).split()
        )

        code = f"import java.util.HashMap;\nimport java.util.Map;\nimport java.time.LocalDateTime;\nimport java.time.format.DateTimeFormatter;\n\npublic class {class_name} {{\n"

        # Add class fields
        code += "    private String name;\n"
        code += "    private int value;\n"
        code += "    private LocalDateTime createdAt;\n"
        code += "    private Map<String, Object> properties;\n\n"

        # Constructor
        code += f"    public {class_name}(String name, int value) {{\n"
        code += "        this.name = name;\n"
        code += "        this.value = value;\n"
        code += "        this.createdAt = LocalDateTime.now();\n"
        code += "        this.properties = new HashMap<>();\n"
        code += "    }\n\n"

        # Methods
        code += "    public int processValue() {\n"
        code += "        return this.value * 2;\n"
        code += "    }\n\n"

        code += "    public void addProperty(String key, Object value) {\n"
        code += "        this.properties.put(key, value);\n"
        code += "    }\n\n"

        code += "    public Object getProperty(String key) {\n"
        code += "        return this.properties.get(key);\n"
        code += "    }\n\n"

        code += "    @Override\n"
        code += "    public String toString() {\n"
        code += "        DateTimeFormatter formatter = DateTimeFormatter.ISO_LOCAL_DATE_TIME;\n"
        code += "        return String.format(\"%s(name='%s', value=%d, createdAt='%s', properties=%s)\",\n"
        code += f"                {class_name}.class.getSimpleName(),\n"
        code += "                this.name,\n"
        code += "                this.value,\n"
        code += "                this.createdAt.format(formatter),\n"
        code += "                this.properties);\n"
        code += "    }\n\n"

        # Main method
        code += "    public static void main(String[] args) {\n"
        code += f'        {class_name} instance = new {class_name}("example", 42);\n'
        code += '        instance.addProperty("category", "test");\n'
        code += '        instance.addProperty("active", true);\n\n'
        code += "        System.out.println(instance);\n"
        code += '        System.out.println("Processed value: " + instance.processValue());\n'
        code += "    }\n"

        code += "}"
        return code

    def _generate_cpp_code(self, concepts: set, prompt: str) -> str:
        """Generate C++ code based on concepts."""
        class_name = "".join(
            w.capitalize()
            for w in random.choice(["data", "user", "processor", "calculator"]).split()
        )

        code = "#include <iostream>\n"
        code += "#include <string>\n"
        code += "#include <unordered_map>\n"
        code += "#include <vector>\n"
        code += "#include <ctime>\n\n"

        code += f"class {class_name} {{\nprivate:\n"
        code += "    std::string name;\n"
        code += "    int value;\n"
        code += "    time_t createdAt;\n"
        code += "    std::unordered_map<std::string, std::string> properties;\n\n"

        code += "public:\n"
        code += f"    {class_name}(const std::string& name, int value) : name(name), value(value) {{\n"
        code += "        createdAt = time(nullptr);\n"
        code += "    }}\n\n"

        code += "    int processValue() const {\n"
        code += "        return value * 2;\n"
        code += "    }\n\n"

        code += (
            "    void addProperty(const std::string& key, const std::string& value) {\n"
        )
        code += "        properties[key] = value;\n"
        code += "    }\n\n"

        code += "    std::string getProperty(const std::string& key) const {\n"
        code += "        auto it = properties.find(key);\n"
        code += "        if (it != properties.end()) {\n"
        code += "            return it->second;\n"
        code += "        }\n"
        code += '        return "";\n'
        code += "    }\n\n"

        code += (
            "    friend std::ostream& operator<<(std::ostream& os, const " +
            class_name +
            "& obj) {\n"
        )
        code += (
            '        os << "' +
            class_name +
            '(name=\'" << obj.name << "\', value=" << obj.value << ", ";\n'
        )
        code += '        os << "createdAt=\'" << std::ctime(&obj.createdAt) << "\', properties={";\n'
        code += "        \n"
        code += "        bool first = true;\n"
        code += "        for (const auto& pair : obj.properties) {\n"
        code += '            if (!first) os << ", ";\n'
        code += '            os << pair.first << ": \'" << pair.second << "\'";\n'
        code += "            first = false;\n"
        code += "        }\n"
        code += '        os << "})";\n'
        code += "        return os;\n"
        code += "    }\n"
        code += "};\n\n"

        code += "int main() {\n"
        code += f'    {class_name} instance("example", 42);\n'
        code += '    instance.addProperty("category", "test");\n'
        code += '    instance.addProperty("status", "active");\n\n'
        code += "    std::cout << instance << std::endl;\n"
        code += '    std::cout << "Processed value: " << instance.processValue() << std::endl;\n'
        code += "    \n"
        code += "    return 0;\n"
        code += "}"

        return code

    def _generate_generic_code(
            self,
            language: str,
            concepts: set,
            prompt: str) -> str:
        """Generate generic code for other languages."""
        func_name = random.choice(
            ["processData", "calculateValue", "transformInput", "handleRequest"]
        )

        # Create a simple generic function
        code = f"// Example {language} function\n"
        code += f"function {func_name}(data) {{\n"
        code += "  // Initialize result object/map\n"
        code += "  let result = {};\n\n"
        code += "  // Check data type\n"
        code += "  if (Array.isArray(data)) {{\n"
        code += "    result.type = 'array';\n"
        code += "    result.length = data.length;\n"
        code += "  }} else if (typeof data === 'object') {{\n"
        code += "    result.type = 'object';\n"
        code += "    result.keys = Object.keys(data);\n"
        code += "  }} else {{\n"
        code += "    result.type = typeof data;\n"
        code += "    result.value = String(data);\n"
        code += "  }}\n\n"
        code += "  // Add timestamp\n"
        code += "  result.timestamp = new Date().toISOString();\n\n"
        code += "  return result;\n"
        code += "}}\n\n"
        code += "// Example usage\n"
        code += f"const output = {func_name}([1, 2, 3, 'test']);\n"
        code += "console.log(output);\n"

        return code
