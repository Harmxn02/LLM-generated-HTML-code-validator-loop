import ollama


def generate_html(model_name: str, prompt: str, output_path: str) -> None:
	"""Stream a response from a local Ollama model and save the output as an HTML file."""
	html_output = ""

	stream = ollama.chat(
		model=model_name,
		messages=[{"role": "user", "content": prompt}],
		stream=True,
	)

	for chunk in stream:
		content = chunk.get("message", {}).get("content", "")
		print(content, end="", flush=True)
		html_output += content

	with open(output_path, "w", encoding="utf-8") as f:
		f.write(html_output)
	print(f"\nHTML saved to {output_path}")
