import torch

# --- Core Training Parameters ---
NUM_LABELS = 2               # Binary classification (Violation or No Violation)
BATCH_SIZE = 4               # Per device batch size (adjust based on your GPU)
ACCUMULATION_STEPS = 4       # Gradient accumulation steps (Effective batch size = 16)
NUM_EPOCHS = 3               # Number of training epochs

# --- Environment & Output ---
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# Base directory for general training results (used by the Trainer internally)
TRAINER_OUTPUT_DIR = './results_manual_eval' 
# Directory for logging/tensorboard
LOGGING_DIR = './logs' 

# --- Model Definitions ---
MODEL_CONFIGS = {
    # 1. RoBERTa Configuration (Default, stable, no special flags)
    "roberta-base": {
        "name": 'roberta-base',
        "trust_remote_code": False,
        "max_len": 512,
        "special_token_handling": None
    },
    
    # 2. Qwen Configuration (For reference/future use)
    "qwen-0.5b": {
        "name": 'Qwen/Qwen1.5-0.5B',
        "trust_remote_code": True, 
        "max_len": 512, 
        "special_token_handling": "pad_to_eos"
    }
}


# --- Model Selection (THE SINGLE SWITCH) ---
SELECTED_MODEL = "roberta-base" # # "roberta-base" | "qwen-0.5b"

# --- Derived Parameters ---
CONFIG = MODEL_CONFIGS[SELECTED_MODEL]
MODEL_NAME = CONFIG["name"]
MAX_LEN = CONFIG["max_len"]

# Final directory name includes the selected model name for clarity
OUTPUT_DIR = f'./model_{SELECTED_MODEL.replace("/", "_").lower()}' 