import json
import random
import time

import requests


def choose_prompt(file_path: str) -> str:
	with open(file_path, "r") as f:
		all_data = json.load(f)
	prompts = all_data["prompts"]
	prompt_to_use = random.choice(prompts)
	print(f"\nSelected prompt: {prompt_to_use}\n")
	return prompt_to_use


def setup_payload(
	model_name: str,
	api_url: str,
	prompt: str,
):
	url = api_url if api_url else ValueError("`api_url` is required")
	payload = {
		"model": model_name if model_name else ValueError("`model_name` is required"),
		"messages": [
			{
				"role": "user",
				"content": prompt if prompt else ValueError("`prompt` is required"),
			}
		],
	}

	return url, payload


def parse_response(response, output_path: str):
	if response.status_code == 200:
		html_output = ""
		for line in response.iter_lines(decode_unicode=True):
			if line:
				try:
					json_data = json.loads(line)
					if "message" in json_data and "content" in json_data["message"]:
						print(json_data["message"]["content"], end="")
						html_output += json_data["message"]["content"]
				except json.JSONDecodeError:
					print(f"Failed to parse line: {line}")

		with open(f"{output_path}", "w", encoding="utf-8") as f:
			f.write(html_output)
		print(f"HTML saved to {output_path}")
	else:
		print(
			f"Failed to get response from Ollama. Status code: {response.status_code}"
		)


if __name__ == "__main__":
	prompt = choose_prompt("./prompts/prompts.json")
	# qwen3:8b

	url, payload = setup_payload(
		model_name="gemma3:1b", api_url="http://localhost:11434/api/chat", prompt=prompt
	)

	current_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
	output_path = f"./html/generated_{current_time}.html"

	response = requests.post(url, json=payload, stream=True)
	parse_response(response, output_path=output_path)
