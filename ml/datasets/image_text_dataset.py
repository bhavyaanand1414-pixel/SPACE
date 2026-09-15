import json
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image
import torch
from torch.utils.data import Dataset
import open_clip

class ImageTextPairDataset(Dataset):
    """
    Dataset for loading image-text pairs for CLIP fine-tuning.
    Expects a JSON/JSONL file containing [{"image_path": "...", "caption": "..."}, ...]
    or a directory structure. Here we assume a simple JSON format.
    """
    def __init__(
        self,
        json_path: str,
        image_dir: str,
        tokenizer,
        preprocess,
        is_train: bool = True
    ):
        self.image_dir = Path(image_dir)
        self.tokenizer = tokenizer
        self.preprocess = preprocess
        self.is_train = is_train

        # Load metadata
        self.samples: List[Dict[str, str]] = []
        if Path(json_path).exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.samples = data
                except json.JSONDecodeError:
                    # Try jsonl
                    f.seek(0)
                    for line in f:
                        if line.strip():
                            self.samples.append(json.loads(line))
        else:
            print(f"Warning: Dataset file {json_path} not found. Creating empty dataset.")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        sample = self.samples[idx]
        img_path = self.image_dir / sample["image_path"]
        caption = sample["caption"]

        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            # Fallback to empty image if missing
            image = Image.new("RGB", (224, 224), (0, 0, 0))

        image_tensor = self.preprocess(image)
        text_tensor = self.tokenizer([caption])[0]

        return image_tensor, text_tensor

def create_synthetic_image_text_dataset(
    num_samples: int = 32,
    img_size: int = 224,
    save_dir: str = "./data/synthetic_clip"
) -> Tuple[str, str]:
    """
    Creates a synthetic dataset for testing the CLIP fine-tuning pipeline.
    Returns (json_path, image_dir).
    """
    save_dir = Path(save_dir)
    img_dir = save_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    samples = []
    for i in range(num_samples):
        img_name = f"synth_{i}.jpg"
        img_path = img_dir / img_name
        
        # Create random image
        img = Image.new('RGB', (img_size, img_size), color=(
            int(torch.randint(0, 255, (1,)).item()),
            int(torch.randint(0, 255, (1,)).item()),
            int(torch.randint(0, 255, (1,)).item())
        ))
        img.save(img_path)
        
        samples.append({
            "image_path": img_name,
            "caption": f"Synthetic remote sensing image of area {i} showing terrain."
        })
        
    json_path = save_dir / "dataset.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2)
        
    return str(json_path), str(img_dir)
