import pandas as pd
import re
import torch
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer
from torch.utils.data import Dataset

# Import configuration from your config file
from config import MODEL_NAME, MAX_LEN, CONFIG

# --- Configuration for Data Paths ---
# NOTE: Ensure your CSV file is located at this path relative to the project root
DATA_PATH = './data/raw/train.csv' 
TEST_SIZE = 0.2
RANDOM_STATE = 42

# --- 1. Custom PyTorch Dataset Class ---

class RedditCommentDataset(Dataset):
    """Custom Dataset to correctly package data as dictionaries for the Trainer."""
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        # Package inputs and labels into a dictionary
        # Keys MUST match the model's forward pass arguments (input_ids, attention_mask)
        item = {key: val[idx].clone().detach() for key, val in self.encodings.items()}
        item['labels'] = self.labels[idx]
        return item

    def __len__(self):
        return len(self.labels)

# --- 2. Data Cleaning and Feature Engineering ---

def basic_clean(text):
    """Minimal cleaning for Transformer input."""
    # Remove HTML tags (if any)
    text = re.sub(r'<.*?>', '', text)
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def create_transformer_input(row):
    """
    Creates a structured text prompt combining the comment, rule, and examples.
    This is the input feature for RoBERTa.
    """
    
    # 1. Rule Context
    # Apply cleaning within the function to ensure final text is clean
    rule_text = f"RULE: {basic_clean(row['rule'])}"
    
    # 2. Positive Examples (What IS a violation)
    pos_examples = (
        f"POSITIVE EXAMPLES (Violation): "
        f"{basic_clean(row['positive_example_1'])} | "
        f"{basic_clean(row['positive_example_2'])}"
    )
    
    # 3. Negative Examples (What is NOT a violation)
    neg_examples = (
        f"NEGATIVE EXAMPLES (No Violation): "
        f"{basic_clean(row['negative_example_1'])} | "
        f"{basic_clean(row['negative_example_2'])}"
    )
    
    # 4. The Comment to be Classified
    comment_body = f"COMMENT TO CLASSIFY: {basic_clean(row['body'])}"
    
    # Combine all parts with clear separators using the placeholder
    combined_text = (
        f"{comment_body} [SEP_TOKEN] "
        f"{rule_text} [SEP_TOKEN] "
        f"{pos_examples} [SEP_TOKEN] "
        f"{neg_examples}"
    )
    # NOTE: The [SEP_TOKEN] will be replaced with the actual tokenizer.sep_token later.
    return combined_text

def encode_data(texts, tokenizer, max_len):
    """Tokenizes and prepares data for the Transformer model."""
    return tokenizer.batch_encode_plus(
        texts, # Note: texts should already be a list/Series of strings
        add_special_tokens=True,
        max_length=max_len,
        padding='max_length',
        truncation=True,
        return_attention_mask=True,
        return_tensors='pt'
    )

# --- 3. Main Orchestrator Function ---

def load_and_preprocess_data():
    """
    Loads raw data, applies feature engineering, splits, tokenizes, and creates Datasets.
    """
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        print(f"Error: Data file not found at {DATA_PATH}. Please check the path.")
        raise

    # 3.1. Apply Feature Engineering
    print("Applying structured Few-Shot Prompting transformation...")
    # Create the structured text feature
    df['model_input_text_raw'] = df.apply(create_transformer_input, axis=1)
    
    # Define features (X) and target (y)
    # NOTE: Assuming your target column is named 'rule_violation' as in your notebook code.
    X = df['model_input_text_raw'] 
    y = df['rule_violation']

    # 3.2. Split the data
    print(f"Splitting data (Test Size: {TEST_SIZE}, Stratified)...")
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, 
        test_size=TEST_SIZE, 
        random_state=RANDOM_STATE, 
        stratify=y 
    )

    # 3.3. Initialize Tokenizer (requires dynamic loading based on config)
    print(f"Initializing tokenizer ({MODEL_NAME})...")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=CONFIG.get("trust_remote_code", False) 
    )
    
    # Apply special padding fix if needed (e.g., for Qwen)
    if CONFIG.get("special_token_handling") == "pad_to_eos" and tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        print(f"Warning: Set pad_token to eos_token for {MODEL_NAME}")
        
    # 3.4. Replace placeholder and Tokenize
    print(f"Replacing [SEP_TOKEN] and tokenizing data (Max length: {MAX_LEN})...")
    
    # Use the tokenizer's SEP token to replace the placeholder
    train_texts = [
        text.replace('[SEP_TOKEN]', tokenizer.sep_token) for text in X_train.tolist()
    ]
    val_texts = [
        text.replace('[SEP_TOKEN]', tokenizer.sep_token) for text in X_val.tolist()
    ]
    
    train_encodings = encode_data(train_texts, tokenizer, MAX_LEN)
    val_encodings = encode_data(val_texts, tokenizer, MAX_LEN)

    # 3.5. Convert labels and create Datasets
    train_labels = torch.tensor(y_train.values, dtype=torch.long)
    val_labels = torch.tensor(y_val.values, dtype=torch.long)
    
    train_dataset = RedditCommentDataset(train_encodings, train_labels)
    val_dataset = RedditCommentDataset(val_encodings, val_labels)

    print(f"Data loading complete. Train size: {len(train_dataset)}, Validation size: {len(val_dataset)}")
    
    # Return both datasets for train.py, and the tokenizer for use in the Trainer
    return train_dataset, val_dataset, tokenizer

# Add this to src/data_loader.py
def get_analysis_dataframes():
    """
    Reloads the full DataFrame and re-splits it to retrieve the 
    X_val/y_val indices and full data required for error analysis mapping.
    """
    df = pd.read_csv(DATA_PATH) # Reload the data
    X = df.apply(create_transformer_input, axis=1) # Re-create the input text (X)
    y = df['rule_violation'] # The true labels (y)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, 
        test_size=TEST_SIZE, 
        random_state=RANDOM_STATE, 
        stratify=y 
    )
    
    # Return the full DF, the X_val series (to get its index), and the y_val labels
    return df, X_val, y_val