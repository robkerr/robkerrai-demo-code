import os
import torch
import argparse
from datasets import load_dataset
from typing import Optional
from trl import SFTConfig, SFTTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import get_peft_model, LoraConfig, TaskType

TRAINER_OUTPUT_DIR = "trainer_output"

# A concise system prompt tailored for NL→SQL
PHI_SYSTEM_PROMPT = (
    "You are an expert Text-to-SQL assistant. "
    "Return ONLY executable SQL for the given question and schema. "
    "Do not include explanations, comments, or markdown. "
    "Prefer ANSI SQL; use tables/columns exactly as provided."
)

# Plain-text fallback template (used only if tokenizer is not provided)
PHI_CHAT_FALLBACK_TEMPLATE = (
    "<|system|>\n{system}\n"
    "<|user|>\n{user}\n"
    "<|assistant|>\n{assistant}"
)

def _coalesce(s: Optional[str]) -> str:
    return "" if s is None else str(s)

def get_dataset(
    data_file: str,
    eos_token: str,
    dataset_size: Optional[int] = None,
    tokenizer=None,  # pass AutoTokenizer if you want apply_chat_template
    system_prompt: str = PHI_SYSTEM_PROMPT,
):
    """
    Expects Alpaca-style JSON with fields: instruction, input, output
      - instruction: high-level task (e.g., 'Convert question to SQL')
      - input: the concrete question and (optionally) schema/context
      - output: the target SQL
    Produces a 'text' field containing Phi-3.5 chat-formatted training examples.
    """

    ds = load_dataset("json", data_files={"train": data_file}, split="train")

    if dataset_size is not None:
        ds = ds.select(range(min(dataset_size, len(ds))))

    def build_example(inst: str, inp: str, out: str) -> str:
        inst = _coalesce(inst).strip()
        inp = _coalesce(inp).strip()
        out = _coalesce(out).strip()

        # Common user turn: put instruction first, then input if present.
        # For NL→SQL, "input" usually contains the question and schema snippet.
        user_msg = inst if not inp else f"{inst}\n\n{inp}"

        if tokenizer is not None and hasattr(tokenizer, "apply_chat_template"):
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": out},
            ]
            # add_generation_prompt=False because we’re training with gold outputs included
            return tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False
            ) + eos_token

        # Fallback: plain text that mirrors Phi chat tokens
        return PHI_CHAT_FALLBACK_TEMPLATE.format(
            system=system_prompt,
            user=user_msg,
            assistant=out,
        ) + eos_token

    def preprocess(batch):
        texts = [
            build_example(inst, inp, out)
            for inst, inp, out in zip(batch["instruction"], batch["input"], batch["output"])
        ]
        return {"text": texts}

    return ds.map(preprocess, remove_columns=ds.column_names, batched=True)

def main(args):
    # Load the model and tokenizer
    print(f"Loading model: {args.model_name}")

    # map CLI string -> torch dtype
    dtype_map = {"float32": torch.float32, "float16": torch.float16, "bfloat16": torch.bfloat16}
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        torch_dtype=dtype_map[args.dtype],
        device_map="auto"
    )

    # Print out what modules are available in the model
    hits = set()
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Linear) and any(k in name for k in ["attn", "mlp", "proj", "fc", "qkv"]):
            hits.add(name)

    print(f"#####  Modules available in the model: {'\n'.join(sorted(hits))}")


    tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    tokenizer.pad_token = tokenizer.eos_token

    # Configure LoRA config
    model = get_peft_model(model, LoraConfig(
        r=args.lora_rank,
        target_modules=["qkv_proj", "o_proj", "fc1", "fc2"],
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM))
    print(f"Trainable parameters = {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

    # Load and preprocess the dataset
    print(f"Loading dataset with {args.dataset_size} samples...")
    dataset = get_dataset(args.data_file, tokenizer.eos_token, args.dataset_size, tokenizer, PHI_SYSTEM_PROMPT)

    os.makedirs(TRAINER_OUTPUT_DIR, exist_ok=True)

    # Configure the SFT config
    config = {
        "per_device_train_batch_size": args.batch_size,
        "num_train_epochs": 0.01,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "learning_rate": args.learning_rate,
        "optim": "adamw_torch",
        "save_strategy": 'epoch',
        "save_total_limit": 1,
        "output_dir": TRAINER_OUTPUT_DIR,
        "remove_unused_columns": False,
        "seed": 42,
        "dataset_text_field": "text",
        "packing": False,
        "max_seq_length": args.seq_length,
        "torch_compile": False,
        "report_to": "none",
        "logging_dir": args.log_dir,
        "logging_steps": args.logging_steps
    }

    # Warmup for torch compile
    model = torch.compile(model)
    SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=SFTConfig(**config),
    ).train()

    # Train the model
    print(f"\nStarting LoRA fine-tuning for {args.num_epochs} epoch(s)...")
    config["num_train_epochs"] = args.num_epochs
    config["report_to"] = "tensorboard"
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=SFTConfig(**config),
    )
    
    trainer_stats = trainer.train()

    
    # Save the PEFT LoRA adapter (adapter_model.safetensors + adapter_config.json)
    trainer.model.save_pretrained(TRAINER_OUTPUT_DIR)
    # Save tokenizer alongside (important for later use)
    tokenizer.save_pretrained(TRAINER_OUTPUT_DIR)

    # Print training statistics
    print(f"\n{'='*60}")
    print("TRAINING COMPLETED")
    print(f"{'='*60}")
    print(f"Training runtime: {trainer_stats.metrics['train_runtime']:.2f} seconds")
    print(f"Samples per second: {trainer_stats.metrics['train_samples_per_second']:.2f}")
    print(f"Steps per second: {trainer_stats.metrics['train_steps_per_second']:.2f}")
    print(f"Train loss: {trainer_stats.metrics['train_loss']:.4f}")
    print(f"{'='*60}\n")


def parse_arguments():
    parser = argparse.ArgumentParser(description="microsoft/phi-3.5-mini-instruct Fine-tuning with LoRA")
    
    # Model configuration
    parser.add_argument("--data_file", type=str, default="training_data.jsonl",
                        help="Path to the training data file")
    parser.add_argument("--model_name", type=str, default="microsoft/phi-3.5-mini-instruct",
                        help="Model name or path")
    parser.add_argument("--dtype", type=str, default="bfloat16",
                        choices=["float32", "float16", "bfloat16"],
                        help="Model dtype")
    
    # Training configuration
    parser.add_argument("--batch_size", type=int, default=2,
                        help="Per device training batch size")
    parser.add_argument("--seq_length", type=int, default=2048,
                        help="Maximum sequence length")
    parser.add_argument("--num_epochs", type=int, default=3,
                        help="Number of training epochs")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=1,
                        help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=2e-4,
                        help="Learning rate")
    
    # LoRA configuration
    parser.add_argument("--lora_rank", type=int, default=8,
                        help="LoRA rank")
    
    # Dataset configuration
    parser.add_argument("--dataset_size", type=int, default=500,
                        help="Number of samples to use from dataset")
    
    # Logging configuration
    parser.add_argument("--logging_steps", type=int, default=1,
                        help="Log every N steps")
    parser.add_argument("--log_dir", type=str, default="logs",
                        help="Directory for logs")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    print(f"\n{'='*60}")
    print("microsoft/phi-3.5-mini-instruct LoRA FINE-TUNING CONFIGURATION")
    print(f"{'='*60}")
    print(f"Model: {args.model_name}")
    print(f"Batch size: {args.batch_size}")
    print(f"Sequence length: {args.seq_length}")
    print(f"Number of epochs: {args.num_epochs}")
    print(f"Learning rate: {args.learning_rate}")
    print(f"LoRA rank: {args.lora_rank}")
    print(f"Dataset size: {args.dataset_size}")
    print(f"{'='*60}\n")
    
    main(args)
