import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Import all necessary configuration variables from your new config file
from config import MODEL_NAME, NUM_LABELS, CONFIG, DEVICE

def load_model_and_tokenizer(model_name=MODEL_NAME, num_labels=NUM_LABELS, config=CONFIG, device=DEVICE):
    """
    Loads the Hugging Face tokenizer and AutoModel for Sequence Classification 
    based on the centralized configuration.

    This function is robust to switching between models like RoBERTa and Qwen3-0.5b
    by reading the required flags (like trust_remote_code) from the CONFIG dictionary.

    Args:
        model_name (str): The name of the Hugging Face model (e.g., 'roberta-base').
        num_labels (int): The number of output classes.
        config (dict): Model-specific settings from config.py.
        device (torch.device): The device (CPU or CUDA) to place the model on.

    Returns:
        tuple: (model, tokenizer)
    """
    print(f"Loading tokenizer for: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        # Dynamically applies the required flag per model
        trust_remote_code=config.get("trust_remote_code", False) 
    )

    # Apply Model-Specific Tokenizer Fixes (Qwen needs padding fix)
    if config.get("special_token_handling") == "pad_to_eos" and tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        print(f"   [Tokenizer Fix]: Set pad_token to eos_token for {model_name}.")

    print(f"Loading model: {model_name} for Sequence Classification...")
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=num_labels,
        # Dynamically applies the required flag
        trust_remote_code=config.get("trust_remote_code", False)
    )

    # Place model on the specified device
    model.to(device)
    print(f"   [Device]: Model placed on {device}.")

    return model, tokenizer

# --- Local Testing Block ---
if __name__ == '__main__':
    print(f"Using device: {DEVICE}")
    try:
        model, tokenizer = load_model_and_tokenizer()
        print(f"\n✅ Successfully initialized {MODEL_NAME}.")
        print(f"   Model structure: {type(model).__name__}")
        print(f"   Model parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad) / 1e6:.2f}M")
    except Exception as e:
        print(f"\n❌ Error during local model loading test: {e}")