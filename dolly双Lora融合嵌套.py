import torch
from peft import PeftModel
import transformers
import gradio as gr

from transformers import GPTNeoXTokenizerFast,  GenerationConfig, GPTNeoXForCausalLM

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

#放在本地工程根目录文件夹

#dollyV1基于GPT-J，Lora偏向于llama
#dollyV2基于GPT-NEO-X,Lora偏向于GLM

model = GPTNeoXForCausalLM.from_pretrained("dollyv2-finetune",trust_remote_code=False,device_map='auto')

#多Lora嵌套融合


model1= PeftModel.from_pretrained(model, "./lora-alpaca")
torch.set_default_tensor_type(torch.cuda.FloatTensor)

model2 = PeftModel.from_pretrained(model1, "./lora-out")
torch.set_default_tensor_type(torch.cuda.FloatTensor)



tokenizer = GPTNeoXTokenizerFast.from_pretrained("dollyv2-finetune",trust_remote_code=False)

def generate_prompt(instruction, input=None):
    if input:
        return f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input}

### Response:"""
    else:
        return f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Response:"""



def evaluate(
    instruction,
    input=None,
    temperature=0.1,
    top_p=0.75,
    top_k=40,
    num_beams=4,
    max_new_tokens=128,
    **kwargs,
):
    prompt = generate_prompt(instruction, input)
    inputs = tokenizer(prompt, return_tensors="pt")
    input_ids = inputs["input_ids"].to(device)
    generation_config = GenerationConfig(
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        num_beams=num_beams,
        **kwargs,
    )
    with torch.no_grad():
        generation_output = model2.generate(
            input_ids=input_ids,
            generation_config=generation_config,
            return_dict_in_generate=True,
            output_scores=True,
            max_new_tokens=max_new_tokens,
        )
    s = generation_output.sequences[0]
    output = tokenizer.decode(s)
    return output.split("### Response:")[1].split("### End")[0].strip()


gr.Interface(
    fn=evaluate,#接口函数
    inputs=[
        gr.components.Textbox(
            lines=2, label="Instruction", placeholder="Tell me about alpacas."
        ),
        gr.components.Textbox(lines=2, label="Input", placeholder="none"),
        gr.components.Slider(minimum=0, maximum=1, value=0.1, label="Temperature"),
        gr.components.Slider(minimum=0, maximum=1, value=0.75, label="Top p"),
        gr.components.Slider(minimum=0, maximum=100, step=1, value=40, label="Top k"),
        gr.components.Slider(minimum=1, maximum=4, step=1, value=4, label="Beams"),
        gr.components.Slider(
            minimum=1, maximum=2000, step=1, value=128, label="Max tokens"
        ),
    ],
    outputs=[
        gr.inputs.Textbox(
            lines=5,
            label="Output",
        )
    ],
    title="ChatUni",
    description="Chat,Your Own World",
).launch()

# Old testing code follows.

# if __name__ == "__main__":
#     # testing code for readme
#     for instruction in [
#         "Tell me about alpacas.",
#         "Tell me about the president of Mexico in 2019.",
#         "Tell me about the king of France in 2019.",
#         "List all Canadian provinces in alphabetical order.",
#         "Write a Python program that prints the first 10 Fibonacci numbers.",
#         "Write a program that prints the numbers from 1 to 100. But for multiples of three print 'Fizz' instead of the number and for the multiples of five print 'Buzz'. For numbers which are multiples of both three and five print 'FizzBuzz'.",
#         "Tell me five words that rhyme with 'shock'.",
#         "Translate the sentence 'I have no mouth but I must scream' into Spanish.",
#         "Count up from 1 to 500.",
#     ]:
#         print("Instruction:", instruction)
#         print("Response:", evaluate(instruction))
#         print()

