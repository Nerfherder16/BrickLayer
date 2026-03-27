"""masonry/scripts/finetune_lxc.py

QLoRA fine-tune of llama3.1:8b on BrickLayer ShareGPT training data.
Runs on LXC 104 (bricklayer-train) — RTX 3060 12GB.

Requirements (already installed on LXC 104):
  torch 2.5.1+cu121, transformers, peft, trl, accelerate, bitsandbytes

Input:  sharegpt_train.jsonl  (ShareGPT conversation format)
Output: ./output/             (HF adapter)
        ./output/model.gguf   (after GGUF conversion)

Usage:
    # On LXC 104:
    python finetune_lxc.py --data sharegpt_train.jsonl
    python finetune_lxc.py --data sharegpt_train.jsonl --max-steps 200 --dry-run

    # After training, convert to GGUF:
    python finetune_lxc.py --gguf-only --adapter ./output
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


# ── Hyperparameters ──────────────────────────────────────────────────────────

# Qwen2.5-7B-Instruct: ungated, no HF token needed, similar perf to llama3.1:8b
# Switch to meta-llama/Meta-Llama-3.1-8B-Instruct if you have HF token + Meta license
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
OLLAMA_BASE = "llama3.1:8b"   # reference only (Ollama weights are GGUF, not usable for training)

LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
TARGET_MODULES = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

BATCH_SIZE = 2
GRAD_ACCUM = 4          # effective batch = 8
MAX_SEQ_LEN = 2048
LEARNING_RATE = 2e-4
MAX_STEPS = 500         # ~30-45 min on RTX 3060
WARMUP_STEPS = 20
SAVE_STEPS = 100
LOG_STEPS = 10

OUTPUT_DIR = "./output"


# ── Dataset loader ────────────────────────────────────────────────────────────

def load_sharegpt(path: str) -> list[str]:
    """Load ShareGPT JSONL and format as chat strings for tokenization."""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            convos = obj.get("conversations", [])
            system = next((c["value"] for c in convos if c["from"] == "system"), "")
            human = next((c["value"] for c in convos if c["from"] == "human"), "")
            gpt = next((c["value"] for c in convos if c["from"] == "gpt"), "")

            if not human or not gpt:
                continue

            # Format as Qwen2.5 chat template (ChatML)
            text = ""
            if system:
                text += f"<|im_start|>system\n{system}<|im_end|>\n"
            text += f"<|im_start|>user\n{human}<|im_end|>\n"
            text += f"<|im_start|>assistant\n{gpt}<|im_end|>"

            records.append(text)

    return records


# ── Training ─────────────────────────────────────────────────────────────────

def train(data_path: str, max_steps: int, dry_run: bool) -> None:
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from trl import SFTTrainer

    print(f"[finetune] CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"[finetune] GPU: {torch.cuda.get_device_name(0)}")
        print(f"[finetune] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    print(f"[finetune] Loading training data from {data_path}")
    texts = load_sharegpt(data_path)
    print(f"[finetune] {len(texts)} training examples")

    if dry_run:
        print("[finetune] Dry run — showing first example:")
        print(texts[0][:500] if texts else "(no examples)")
        return

    if len(texts) < 10:
        print(f"[finetune] WARNING: only {len(texts)} examples — run gen_training_data.py --all first")
        sys.exit(1)

    # 4-bit quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    print(f"[finetune] Loading model: {MODEL_ID}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    # LoRA config
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=TARGET_MODULES,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Dataset
    dataset = Dataset.from_dict({"text": texts})

    # Training args
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=1,
        max_steps=max_steps,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LEARNING_RATE,
        warmup_steps=WARMUP_STEPS,
        logging_steps=LOG_STEPS,
        save_steps=SAVE_STEPS,
        save_total_limit=2,
        bf16=True,
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        report_to="none",
        dataloader_pin_memory=False,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LEN,
    )

    print(f"[finetune] Training for {max_steps} steps...")
    trainer.train()

    print(f"[finetune] Saving adapter to {OUTPUT_DIR}")
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("[finetune] Done. Run --gguf-only to convert for Ollama.")


# ── GGUF conversion ───────────────────────────────────────────────────────────

def convert_gguf(adapter_dir: str) -> None:
    """Merge adapter + base model, then convert to GGUF via llama.cpp."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    merged_dir = str(Path(adapter_dir) / "merged")
    gguf_path = str(Path(adapter_dir) / "model.gguf")

    print(f"[gguf] Merging adapter into base model → {merged_dir}")
    tokenizer = AutoTokenizer.from_pretrained(adapter_dir)
    base = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        device_map="cpu",  # merge on CPU to avoid VRAM spike
    )
    model = PeftModel.from_pretrained(base, adapter_dir)
    model = model.merge_and_unload()
    model.save_pretrained(merged_dir)
    tokenizer.save_pretrained(merged_dir)
    print(f"[gguf] Merged model saved to {merged_dir}")

    # Convert via llama.cpp convert script
    print(f"[gguf] Converting to GGUF (q4_k_m)...")
    result = subprocess.run(
        [
            sys.executable, "-m", "llama_cpp.convert",
            merged_dir,
            "--outfile", gguf_path,
            "--outtype", "q4_k_m",
        ],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        # Try llama.cpp standalone script
        print("[gguf] llama_cpp module not found, trying convert_hf_to_gguf.py...")
        result2 = subprocess.run(
            ["python3", "convert_hf_to_gguf.py", merged_dir,
             "--outfile", gguf_path, "--outtype", "q4_k_m"],
            capture_output=True, text=True
        )
        if result2.returncode != 0:
            print("[gguf] ERROR: GGUF conversion failed.")
            print(result2.stderr[-500:])
            print("\nManual conversion:")
            print(f"  git clone https://github.com/ggerganov/llama.cpp")
            print(f"  cd llama.cpp && pip install -r requirements.txt")
            print(f"  python convert_hf_to_gguf.py {merged_dir} --outfile {gguf_path} --outtype q4_k_m")
            return
        print(result2.stdout)
    else:
        print(result.stdout)

    print(f"[gguf] GGUF saved: {gguf_path}")
    print(f"\nLoad into Ollama:")
    print(f"  ollama create bricklayer-sft -f Modelfile")
    print(f"  # Where Modelfile contains: FROM {gguf_path}")
    print(f"\nOr use the load_adapter.sh script if it exists.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="QLoRA fine-tune llama3.1:8b on BrickLayer data")
    parser.add_argument("--data", default="sharegpt_train.jsonl", help="ShareGPT JSONL path")
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS)
    parser.add_argument("--dry-run", action="store_true", help="Show data sample, don't train")
    parser.add_argument("--gguf-only", action="store_true", help="Skip training, just convert adapter to GGUF")
    parser.add_argument("--adapter", default=OUTPUT_DIR, help="Adapter dir for --gguf-only")
    args = parser.parse_args()

    if args.gguf_only:
        convert_gguf(args.adapter)
        return

    train(args.data, args.max_steps, args.dry_run)


if __name__ == "__main__":
    main()
