import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import torch
from torch.utils.data import DataLoader, random_split
import open_clip

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.datasets.image_text_dataset import ImageTextPairDataset, create_synthetic_image_text_dataset
from ml.training.clip_trainer import CLIPTrainer

def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune RemoteCLIP on Image-Text Pairs")
    parser.add_argument("--dataset-json", type=str, default="./data/clip_pairs.json", help="Path to dataset JSON/JSONL")
    parser.add_argument("--image-dir", type=str, default="./data/images", help="Directory containing images")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic dataset for testing")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-5, help="Learning rate")
    parser.add_argument("--weight-decay", type=float, default=0.2, help="Weight decay")
    parser.add_argument("--temperature", type=float, default=0.07, help="Logit scaling temperature")
    parser.add_argument("--no-mixed-precision", action="store_true", help="Disable mixed precision training")
    parser.add_argument("--device", type=str, default="auto", help="Device: auto, cuda, mps, cpu")
    parser.add_argument("--checkpoint-dir", type=str, default="./ml/checkpoints/clip_finetuned", help="Output directory")
    parser.add_argument("--model-name", type=str, default="ViT-B-32", help="CLIP model architecture")
    parser.add_argument("--pretrained", type=str, default="hf-hub:chendinc/RemoteCLIP_ViT_B-32", help="Pretrained weights")
    parser.add_argument("--resume", type=str, default="", help="Path to checkpoint to resume training from")
    return parser.parse_args()

def main():
    args = parse_args()
    
    device_str = args.device
    if device_str == "auto":
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_str)
    
    ckpt_dir = Path(args.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("  SIH1518: RemoteCLIP FINE-TUNING PIPELINE")
    print("=" * 70)
    print(f"• Target Device     : {device}")
    print(f"• Model             : {args.model_name} ({args.pretrained})")
    print(f"• Target Epochs     : {args.epochs}")
    print(f"• Batch Size        : {args.batch_size}")
    print(f"• Learning Rate     : {args.lr}")
    print(f"• Checkpoint Dir    : {ckpt_dir.resolve()}")
    print("=" * 70)

    # 1. Load Model
    print(f"Loading {args.model_name}...")
    model, _, preprocess = open_clip.create_model_and_transforms(
        args.model_name,
        pretrained=args.pretrained,
        cache_dir="./ml/checkpoints/clip"
    )
    tokenizer = open_clip.get_tokenizer(args.model_name)

    # 2. Dataset
    if args.synthetic:
        print("  Creating synthetic dataset for testing...")
        json_path, img_dir = create_synthetic_image_text_dataset(num_samples=64)
    else:
        json_path, img_dir = args.dataset_json, args.image_dir

    print("  Loading dataset...")
    full_dataset = ImageTextPairDataset(
        json_path=json_path,
        image_dir=img_dir,
        tokenizer=tokenizer,
        preprocess=preprocess
    )
    
    if len(full_dataset) == 0:
        print("  Dataset is empty. Exiting.")
        sys.exit(1)
        
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    print(f"  Loaded {train_size} training pairs and {val_size} validation pairs.")

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, drop_last=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)

    # 3. Trainer
    trainer = CLIPTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        device=device,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        checkpoint_dir=str(ckpt_dir),
        mixed_precision=not args.no_mixed_precision
    )
    
    if args.resume:
        trainer.load_checkpoint(args.resume)

    # 4. Train
    history = trainer.train(epochs=args.epochs)
    
    # 5. Save final config/metrics
    config_path = ckpt_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(vars(args), f, indent=2)

    print("\n" + "=" * 70)
    print("  CLIP FINE-TUNING COMPLETED")
    print(f"• Best Validation Loss : {trainer.best_val_loss:.4f}")
    print(f"• Saved Checkpoint     : {ckpt_dir / 'clip_best.pt'}")
    print("=" * 70)

if __name__ == "__main__":
    main()
