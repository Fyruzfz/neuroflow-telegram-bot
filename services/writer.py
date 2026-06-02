"""
NeuroFlow AI Bot - Content Writer Service
Uses Ollama (qwen2.5:7b) for content generation
"""

import subprocess
import json


async def generate_content(topic: str, content_type: str = "blog") -> dict:
    """
    Generate content using local Ollama model.
    Returns {"success": bool, "content": str, "error": str}
    """
    try:
        prompts = {
            "blog": f"Write a detailed, professional blog post about: {topic}. "
                    "Include introduction, 3-4 key points with subheadings, and conclusion. "
                    "Target audience: business professionals. Length: 500-800 words. "
                    "Use clear, engaging language. Format with markdown headings.",

            "social": f"Write 3 engaging social media posts about: {topic}. "
                      "Make them punchy, use relevant hashtags. Platform: LinkedIn/Twitter. "
                      "Each post should be 100-200 words. Include call to action.",

            "email": f"Write a professional email about: {topic}. "
                     "Include subject line, greeting, body, and signature. "
                     "Tone: professional but friendly. Length: 200-300 words.",

            "summary": f"Summarize the following topic in 3-5 bullet points: {topic}. "
                       "Make each point clear and actionable.",
        }

        prompt = prompts.get(content_type, prompts["blog"])

        # Call Ollama
        result = subprocess.run(
            [
                "curl", "-s", "http://localhost:11434/api/generate",
                "-d", json.dumps({
                    "model": "qwen2.5:7b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 1024}
                })
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            return {"success": False, "error": f"Ollama error: {result.stderr[:200]}"}

        response = json.loads(result.stdout)
        content = response.get("response", "").strip()

        if not content:
            return {"success": False, "error": "Model returned empty response"}

        # Format
        header = f"*{topic.title()}*\n\n"
        return {"success": True, "content": header + content}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Content generation timed out. Try a shorter topic."}
    except Exception as e:
        return {"success": False, "error": f"Writer error: {str(e)[:300]}"}
