from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from huggingface_hub import hf_hub_download
import torch, os, json, shutil

base_model_id = "microsoft/phi-3.5-mini-instruct"
adapter_dir   = "trainer_output"
output_dir    = "merged_model"
os.makedirs(output_dir, exist_ok=True)

# 1) Load full-precision/bf16 base on CPU to avoid offload artifacts in save
base = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    torch_dtype=torch.bfloat16,
    device_map=None,             # <- important for clean merge+save
    low_cpu_mem_usage=True
)

# 2) Merge LoRA
merged = PeftModel.from_pretrained(base, adapter_dir).merge_and_unload()

# 3) Save merged weights
merged.save_pretrained(output_dir, safe_serialization=True)

# 4) Save tokenizer (this writes tokenizer.json, config, etc.)
tok = AutoTokenizer.from_pretrained(base_model_id, use_fast=True)
tok.save_pretrained(output_dir)

# 5) Ensure tokenizer.model is present (required by llama.cpp)
spm_path = os.path.join(output_dir, "tokenizer.model")
if not os.path.exists(spm_path):
    spm_src = hf_hub_download(repo_id=base_model_id, filename="tokenizer.model")
    shutil.copy(spm_src, spm_path)

# 6) (Safety) Make sure tokenizer_class matches Llama/SentencePiece
tc_path = os.path.join(output_dir, "tokenizer_config.json")
if os.path.exists(tc_path):
    with open(tc_path, "r", encoding="utf-8") as f:
        tc = json.load(f)
    tc["tokenizer_class"] = tc.get("tokenizer_class", "LlamaTokenizer")
    with open(tc_path, "w", encoding="utf-8") as f:
        json.dump(tc, f, ensure_ascii=False, indent=2)

print("✅ Merged HF model ready at:", output_dir)