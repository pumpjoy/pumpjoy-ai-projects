import os
import shutil
import pandas as pd
import re
import torch
from scipy.special import softmax
from sklearn.metrics import roc_auc_score
from transformers import TrainingArguments, Trainer

# Import configuration and data functions
from config import BATCH_SIZE, DEVICE
from data_loader import get_analysis_dataframes 

# --- Helper Function for Display ---
def remove_links_for_display(text):
    """
    Removes common URLs from text for clean printing/display only.
    """ 
    url_pattern = re.compile(r'https?://\S+|www\.\S+|\S+\.(com|org|net|gov|edu|co)\b')
    # Use the basic_clean function from data_loader if available, or just sub
    text = url_pattern.sub(r'[LINK REMOVED]', str(text))
    return text

# --- Core Evaluation Function ---

def run_evaluation(model, tokenizer, val_dataset, full_df, val_indices, y_val_series):
    """
    Performs prediction on the validation set, calculates AUC, and runs 
    the detailed error analysis (FP/FN).

    Args:
        model (PreTrainedModel): The trained or loaded model.
        tokenizer (PreTrainedTokenizer): The tokenizer used for encodings.
        val_dataset (Dataset): The validation set PyTorch Dataset.
        full_df (pd.DataFrame): The original, full DataFrame.
        val_indices (pd.Index): The original indices of the validation set rows.
        y_val_series (pd.Series): The true labels of the validation set (for direct use).
    """
    print("\n" + "="*50)
    print("--- Performing Final Manual Validation (AUC Calculation) ---")
    print("="*50)

    # Ensure model is on the correct device for prediction
    model.to(DEVICE)

    # 1. Setup Prediction Trainer
    PREDICT_ARGS = TrainingArguments(
        output_dir='./temp_predict',
        per_device_eval_batch_size=BATCH_SIZE,
        report_to="none",
        # Disable logging to keep the output clean
        disable_tqdm=True, 
    )

    predict_trainer = Trainer(
        model=model,
        args=PREDICT_ARGS,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
    )

    # 2. Get predictions (logits and labels)
    predictions = predict_trainer.predict(val_dataset)

    # Unpack the predictions
    logits = predictions.predictions
    labels = predictions.label_ids # These are the true labels

    # 3. Calculate Probabilities and AUC
    # Softmax converts logits to probabilities
    probabilities = softmax(logits, axis=1)
    # We only care about the probability of the POSITIVE class (index 1)
    probabilities_for_auc = probabilities[:, 1] 

    # Calculate the final AUC
    auc_score = roc_auc_score(labels, probabilities_for_auc)

    print(f"\n✅ Final Validation AUC Score: {auc_score:.4f} (Target for Phase 6: ~0.87)")

    # Clean up temporary directory
    if os.path.exists('./temp_predict'):
        shutil.rmtree('./temp_predict')
        
    print("\n" + "-"*50)
    print("--- Detailed Error Analysis (FP/FN) ---")
    print("-"*50)

    # --- 4. Prepare Analysis DataFrame ---

    # 4.1 Convert predictions/labels to a DataFrame
    analysis_data = pd.DataFrame({
        'true_label': labels,
        'prob_violation': probabilities_for_auc
    })

    # 4.2 Merge with original comment data
    # Map the prediction results back to the original DataFrame using validation indices
    analysis_data.index = val_indices
    analysis_df = full_df.loc[val_indices].copy()
    analysis_df = analysis_df.merge(analysis_data, left_index=True, right_index=True)

    # 4.3 Create the prediction and Error Type columns
    THRESHOLD = 0.5 
    analysis_df['predicted_label'] = (analysis_df['prob_violation'] >= THRESHOLD).astype(int)

    def get_error_type(row):
        if row['true_label'] == row['predicted_label']:
            return 'Correct'
        elif row['true_label'] == 0 and row['predicted_label'] == 1:
            return 'False Positive (FP)' # Model cried violation (1), but none existed (0)
        else: # true_label == 1 and predicted_label == 0
            return 'False Negative (FN)' # Model missed a true violation (1), predicted none (0)

    analysis_df['error_type'] = analysis_df.apply(get_error_type, axis=1)

    print("Error Distribution (by Type):")
    error_counts = analysis_df['error_type'].value_counts(normalize=True).mul(100)
    print(error_counts.round(2).astype(str) + '%')

    # --- 5. Display High-Confidence Errors (For Presentation Artifacts) ---

    # False Positives (High Confidence)
    fp_df = analysis_df[analysis_df['error_type'] == 'False Positive (FP)'].sort_values(by='prob_violation', ascending=False)
    
    print("\n--- Top 3 False Positives (Nuance/Legal/FP Insight) ---")
    for i, row in fp_df.head(3).iterrows():
        print(f"\n[FP - Confidence: {row['prob_violation']:.4f}]")
        print(f"  Rule: {row['rule']}")
        print(f"  Comment: {remove_links_for_display(row['body'])}")
    
    # False Negatives (Missed Violations)
    fn_df = analysis_df[analysis_df['error_type'] == 'False Negative (FN)'].sort_values(by='prob_violation', ascending=True) # Lowest confidence FN are the "blind spots"
    
    print("\n--- Top 3 False Negatives (Blind Spot/FN Insight) ---")
    for i, row in fn_df.head(3).iterrows():
        print(f"\n[FN - Confidence: {row['prob_violation']:.4f}]")
        print(f"  Rule: {row['rule']}")
        print(f"  Comment: {remove_links_for_display(row['body'])}")
        
    print("\n" + "="*50)
    print("Evaluation complete. Results are available in the analysis_df DataFrame.")
    print("="*50)

    return analysis_df