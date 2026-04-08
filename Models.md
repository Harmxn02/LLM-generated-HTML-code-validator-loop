# Models used (so far) in this experiment

| Model             | Reasoning | Billion parameters | Size (GB) | Context | Note                                             |
| ----------------- | --------- | ------------------ | --------- | ------- | ------------------------------------------------ |
| gemma4:e2b        | YES ✔     | 5.12               | 7.2       | 128K    | Seems to work nicely                             |
| qwen3:8b          | YES ✔     | 8.19               | 5.2       | 40K     | Seems to work nicely                             |
| qwen2.5-coder:14b | NO ❌     | 14.8               | 9.0       | 32K     | Does not have reasoning, and does not fix issues |
| qwen3.5:9b        | YES ✔     | 9.65               | 6.6       | 256K    | In my testing it took a long time                |

The reasoning models (models with thinking capabilities) are able to fix the issues in the generated HTML and produce valid HTML. Even though qwen2.5-coder:14b is a larger model (has more parameters) than the other two COMBINED, it was not able to fix the issues in the generated HTML. I believe it is because it does not have the reasoning capabilities that the other two models have. It is a code generation model, and it is not trained to reason and fix issues in the generated code. It is trained to generate code based on the given input, but it is not trained to reason and fix issues in the generated code.

## Worth looking into

I suppose the question is whether low-parameter reasoning models can outperform high-parameter non-reasoning models. In this experiment, I would say so, yes.
