import os
import shutil
import torch
from transformers import TrainingArguments, Trainer, AutoModelForSequenceClassification, AutoTokenizer

# Import modular components 
from config import MODEL_NAME, CONFIG, NUM_EPOCHS, BATCH_SIZE, ACCUMULATION_STEPS, DEVICE, OUTPUT_DIR, NUM_LABELS
from model import load_model_and_tokenizer 
from data_loader import load_and_preprocess_data, RedditCommentDataset 
from evaluate import get_analysis_dataframes, run_evaluation

def main():
    """
    Main function to manage model loading, training, and saving.
    """
    # Load Data 
    print("Pre-processing and loading data...")
    train_dataset, val_dataset, tokenizer = load_and_preprocess_data() 
    
    # Check for Saved Model
    if os.path.exists(OUTPUT_DIR):
        # Model already exists, load it
        print(f"\n✅ Model found at {OUTPUT_DIR}. Loading saved model weights.")
        
        # Load the model components saved after training
        try:
            model = AutoModelForSequenceClassification.from_pretrained(OUTPUT_DIR)
            tokenizer = AutoTokenizer.from_pretrained(OUTPUT_DIR)
        except Exception as e:
            print(f"ERROR loading model from {OUTPUT_DIR}. It might be corrupted. Deleting directory.")
            shutil.rmtree(OUTPUT_DIR)
            # Recursively call main to restart the training process
            return main() 
        
        # Ensure model is on the correct device for evaluation/inference later
        model.to(DEVICE)

    else:
        # 3. Model does not exist, initialize and train
        print("\n⏳ Saved model not found. Starting fine-tuning process.")
        
        # Load initial model and tokenizer using the helper function
        model, tokenizer = load_model_and_tokenizer(
            model_name=MODEL_NAME, 
            num_labels=NUM_LABELS, 
            config=CONFIG,
            device=DEVICE
        )

        # 4. Define Training Arguments
        TRAINING_ARGS = TrainingArguments(
            output_dir='./results_manual_eval',
            num_train_epochs=NUM_EPOCHS,
            per_device_train_batch_size=BATCH_SIZE,
            per_device_eval_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=ACCUMULATION_STEPS, 
            warmup_steps=100,
            weight_decay=0.01,
            logging_dir='./logs',
            logging_steps=50,
            eval_strategy="no", 
            save_strategy="epoch",
            save_safetensors=False, # Per the previous fix
            load_best_model_at_end=False,
            report_to="none"
        )

        # 5. Create and Run the Trainer
        trainer = Trainer(
            model=model,
            args=TRAINING_ARGS,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=tokenizer,
        )
        
        print("\nStarting model training...")
        trainer.train()

        # 6. Save Final Model (if trained)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        trainer.save_model(OUTPUT_DIR)
        tokenizer.save_pretrained(OUTPUT_DIR)
        
        # Also clean up the temporary results directory after successful save
        if os.path.exists(TRAINING_ARGS.output_dir):
             shutil.rmtree(TRAINING_ARGS.output_dir)
             
        print(f"\n✅ Model and tokenizer successfully saved to: {OUTPUT_DIR}")
    # 3. Execution of Evaluation (The final step)
    print("\nStarting evaluation...")
    
    # Get the necessary DataFrames from data_loader (full data and val indices/labels)
    full_df, X_val_series, y_val_series = get_analysis_dataframes()
    
    # Run the evaluation
    run_evaluation(
        model=model, 
        tokenizer=tokenizer, 
        val_dataset=val_dataset,
        full_df=full_df,
        val_indices=X_val_series.index,
        y_val_series=y_val_series
    ) 
    # Return the final model and tokenizer for evaluation in evaluate.py
    return model, tokenizer, val_dataset

if __name__ == '__main__': 
    main()