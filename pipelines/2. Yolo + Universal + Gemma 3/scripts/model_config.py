from dotenv import load_dotenv
load_dotenv()
from transformers import pipeline, AutoProcessor, AutoTokenizer, Gemma3ForCausalLM
import torch

def load_vlm():
    model_id = "google/gemma-3-4b-it" # "google/gemma-3-12b-it", "google/gemma-3-27b-it"
    pipe = pipeline(
        "image-text-to-text",
        model=model_id,
        device="cuda",
        torch_dtype=torch.bfloat16
    )
    return pipe

def load_format_llm():
    model_id = "google/gemma-3-4b-it" # "google/gemma-3-12b-it", "google/gemma-3-27b-it"
    model = Gemma3ForCausalLM.from_pretrained(
        model_id, torch_dtype=torch.bfloat16, attn_implementation="eager"
    ).to("cuda").eval()
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    return model, tokenizer