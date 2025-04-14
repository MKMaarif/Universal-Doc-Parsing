from dotenv import load_dotenv
load_dotenv()
from ultralytics import YOLO
from qwen_vl_utils import process_vision_info
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, AutoTokenizer, Gemma3ForCausalLM
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

def load_yolo():
    model = YOLO('model/yolo11_best.pt')
    return model

class VLMProcessor:
    def __init__(self):
        self.model_id = "Qwen/Qwen2.5-VL-7B-Instruct"
        self.model = model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.model_id,
            torch_dtype="auto",
            device_map="auto"
        )
        self.processor = AutoProcessor.from_pretrained(self.model_id)

    def generate(self, image_path, system_prompt, user_prompt):
        messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": system_prompt}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image_path},
                    {"type": "text", "text": user_prompt}
                ]
            }
        ]

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        ).to(device)

        generated_ids = self.model.generate(**inputs, max_new_tokens=250)
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        result = output_text[0]

        return result
    
class LLMFormatter:
    def __init__(self):
        self.model_id = "google/gemma-3-4b-it"
        self.model = Gemma3ForCausalLM.from_pretrained(
            self.model_id, 
            torch_dtype=torch.bfloat16, 
            attn_implementation="eager"
        ).to(device).eval()
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)

    def generate(self, system_prompt, user_prompt):
        
        messages = [
            [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": system_prompt},]
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_prompt},]
                },
            ],
        ]

        inputs = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt"
        ).to(self.model.device)

        input_len = inputs["input_ids"].shape[-1]

        generation = self.model.generate(**inputs, max_new_tokens=4096)
        generation = generation[0][input_len:]

        decoded_text = self.tokenizer.decode(generation, skip_special_tokens=True)

        return decoded_text