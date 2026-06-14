import os
import sys
import modal

# Define Modal App for training
app = modal.App("vyber-training")

# Configure persistent volume for huggingface cache
cache_volume = modal.Volume.from_name("huggingface-cache", create_if_missing=True)

# Build custom container image with PyTorch, TRL, PEFT and Llama.cpp converter
image = (
    modal.Image.debian_slim()
    .apt_install("git", "curl", "build-essential")
    .pip_install(
        "torch",
        "transformers",
        "peft",
        "trl>=0.12.0",
        "accelerate",
        "datasets",
        "huggingface_hub",
        "sentencepiece",
        "gguf"
    )
    .run_commands("git clone --depth 1 https://github.com/ggerganov/llama.cpp.git /llama.cpp")
)

@app.function(
    image=image,
    gpu="A10G",
    volumes={"/cache": cache_volume},
    timeout=1800
)
def train_and_convert_gguf(hf_token: str, repo_id: str):
    import torch
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
    from peft import LoraConfig, get_peft_model
    from trl import SFTTrainer
    import subprocess
    from huggingface_hub import HfApi

    print("Starting fine-tuning pipeline on serverless GPU...")
    print(f"Base model: Qwen/Qwen2.5-1.5B-Instruct")
    print(f"Target repository: {repo_id}")

    # 1. Load cybersecurity instruction dataset
    print("Loading cybersecurity instruction dataset...")
    # Load first 500 samples to keep training fast and focused
    dataset = load_dataset("Trendyol/Trendyol-Cybersecurity-Instruction-Tuning-Dataset", split="train[:500]")

    # Format dataset for Qwen Chat
    def format_prompts(batch):
        formatted = []
        for u, a in zip(batch["user"], batch["assistant"]):
            formatted.append(f"<|im_start|>system\nYou are Vyber, an expert cybersecurity AI assistant.<|im_end|>\n<|im_start|>user\n{u}<|im_end|>\n<|im_start|>assistant\n{a}<|im_end|>")
        return {"text": formatted}

    dataset = dataset.map(format_prompts, batched=True)

    # 2. Initialize Base Model and Tokenizer (in FP16 to fit easily in A10G VRAM)
    print("Loading model and tokenizer...")
    model_id = "Qwen/Qwen2.5-1.5B-Instruct"
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        device_map="auto",
        cache_dir="/cache"
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir="/cache")
    tokenizer.pad_token = tokenizer.eos_token

    # 3. Setup LoRA
    print("Configuring LoRA parameters...")
    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    # 4. Training Arguments (Using SFTConfig to support modern TRL versions)
    from trl import SFTConfig
    training_args = SFTConfig(
        output_dir="/tmp/results",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=5,
        max_steps=50, # Fast training suitable for a demo/badge verification
        fp16=True,
        optim="adamw_torch",
        report_to="none",
        dataset_text_field="text",
        max_length=512
    )

    # 5. Initialize SFTTrainer
    print("Initializing trainer...")
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        processing_class=tokenizer,
        args=training_args
    )

    # 6. Execute Training
    print("Running training loop...")
    trainer.train()
    print("Training finished. Saving model...")
    trainer.save_model("/tmp/lora_checkpoint")

    # Free memory
    del model
    del trainer
    import gc
    gc.collect()
    torch.cuda.empty_cache()

    # 7. Merge weights
    print("Merging LoRA adapters back into base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        device_map="auto",
        cache_dir="/cache"
    )
    from peft import PeftModel
    peft_model = PeftModel.from_pretrained(base_model, "/tmp/lora_checkpoint")
    merged_model = peft_model.merge_and_unload()
    merged_model.save_pretrained("/tmp/merged_model")
    tokenizer.save_pretrained("/tmp/merged_model")
    print("Model merged successfully.")

    # 8. Convert to GGUF format
    print("Converting merged model to GGUF format using llama.cpp...")
    gguf_output_path = "/tmp/vyber-security-1.5b.gguf"
    
    # Run convert_hf_to_gguf.py
    res = subprocess.run([
        sys.executable,
        "/llama.cpp/convert_hf_to_gguf.py",
        "--outfile", gguf_output_path,
        "/tmp/merged_model"
    ], capture_output=True, text=True)
    
    if res.returncode != 0:
        print(f"GGUF conversion failed: {res.stderr}")
        raise RuntimeError("GGUF Conversion Failed")
    
    print("GGUF model converted successfully.")

    # 9. Upload GGUF file to Hugging Face
    print(f"Uploading GGUF model to Hugging Face repository {repo_id}...")
    api = HfApi()
    api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True, token=hf_token)
    api.upload_file(
        path_or_fileobj=gguf_output_path,
        path_in_repo="vyber-security-1.5b.gguf",
        repo_id=repo_id,
        token=hf_token
    )
    print(f"GGUF model successfully published to Hugging Face Hub!")
    return f"Success! Model published at https://huggingface.co/{repo_id}"

@app.local_entrypoint()
def main(repo_name: str = "vyber-security-1.5b-gguf"):
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("Error: HF_TOKEN environment variable is required to publish the model.")
        print("Please run: export HF_TOKEN=your_token")
        sys.exit(1)
        
    username = os.environ.get("HF_USERNAME")
    if not username:
        # Resolve username from token
        from huggingface_hub import WhoAmI
        from huggingface_hub.utils import HfHubHTTPError
        try:
            from huggingface_hub import HfApi
            api = HfApi()
            user_info = api.whoami(token=hf_token)
            username = user_info["name"]
        except Exception as e:
            print(f"Could not automatically resolve HF username: {e}")
            print("Please run: export HF_USERNAME=your_username")
            sys.exit(1)
            
    repo_id = f"{username}/{repo_name}"
    print(f"Resolved Repository: {repo_id}")
    
    # Trigger Modal training function
    result = train_and_convert_gguf.remote(hf_token, repo_id)
    print(result)
