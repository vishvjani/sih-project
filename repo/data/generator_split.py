"""
SignalScope Generator Split & Attribution Taxonomy
Defines strict Seen vs Unseen generator partitions to prevent shortcut memorization
and guarantee true forensic generalization on held-out architectures.
"""

from typing import Dict, List, Tuple

# All 25 Generative Models in the DRAGON Benchmark
ALL_DRAGON_MODELS = [
    "Flux_1",
    "SD_3",
    "Flash_SD3",
    "SDXL",
    "SDXL_Lightning",
    "SDXL_Turbo",
    "Flash_SDXL",
    "SD_1.5",
    "SD_2.1",
    "Flash_SD",
    "PixArt_Sigma",
    "PixArt_Alpha",
    "Flash_PixArt",
    "Kandinsky",
    "Kolors",
    "Lumina",
    "Mobius",
    "Realistic_Stock_Photo",
    "JuggernautXL",
    "Hyper_SD",
    "LCM_SDXL",
    "LCM_SSD_1B",
    "SSD_1B",
    "SD_Cascade",
    "IF"
]

# Primary Architectural Families
GENERATOR_FAMILIES = {
    # 0: Pristine Real Capture
    "Pristine_Real": 0,
    # 1: Classic Latent Diffusion (UNet-based)
    "Latent_Diffusion_UNet": 1,
    # 2: Modern Flow Matching & Diffusion Transformers (DiT)
    "FlowMatching_DiT": 2,
    # 3: Multi-Stage / Cascaded Pixel Diffusion
    "Cascaded_Pixel_Diffusion": 3,
    # 4: Frontier Proprietary & Multimodal (Midjourney, DALL-E, GPT, Kimi, Banana)
    "Frontier_Proprietary": 4,
    # 5: Generative Adversarial Networks (GANs)
    "GAN": 5,
    # 6: Open-Set / Novel Emerging Generator
    "Novel_Unseen": 6
}

# Model to Family Mapping
MODEL_TO_FAMILY: Dict[str, str] = {
    # Flow Matching & Modern DiTs
    "Flux_1": "FlowMatching_DiT",
    "SD_3": "FlowMatching_DiT",
    "Flash_SD3": "FlowMatching_DiT",
    "PixArt_Sigma": "FlowMatching_DiT",
    "PixArt_Alpha": "FlowMatching_DiT",
    "Flash_PixArt": "FlowMatching_DiT",
    "Lumina": "FlowMatching_DiT",
    "Kolors": "FlowMatching_DiT",

    # Latent Diffusion UNets
    "SDXL": "Latent_Diffusion_UNet",
    "SDXL_Lightning": "Latent_Diffusion_UNet",
    "SDXL_Turbo": "Latent_Diffusion_UNet",
    "Flash_SDXL": "Latent_Diffusion_UNet",
    "SD_1.5": "Latent_Diffusion_UNet",
    "SD_2.1": "Latent_Diffusion_UNet",
    "Flash_SD": "Latent_Diffusion_UNet",
    "JuggernautXL": "Latent_Diffusion_UNet",
    "Hyper_SD": "Latent_Diffusion_UNet",
    "LCM_SDXL": "Latent_Diffusion_UNet",
    "LCM_SSD_1B": "Latent_Diffusion_UNet",
    "SSD_1B": "Latent_Diffusion_UNet",
    "Mobius": "Latent_Diffusion_UNet",
    "Realistic_Stock_Photo": "Latent_Diffusion_UNet",
    "Kandinsky": "Latent_Diffusion_UNet",

    # Cascaded / Multi-stage
    "IF": "Cascaded_Pixel_Diffusion",
    "SD_Cascade": "Cascaded_Pixel_Diffusion",

    # Frontier / External Proprietary (Supported during test and online inference)
    "Midjourney": "Frontier_Proprietary",
    "Midjourney_v6": "Frontier_Proprietary",
    "DALL-E_3": "Frontier_Proprietary",
    "GPT_4o": "Frontier_Proprietary",
    "Gemini_Nano": "Frontier_Proprietary",
    "Kimi": "Frontier_Proprietary",
    "Banana": "Frontier_Proprietary",

    # Real
    "Real": "Pristine_Real",
    "OpenImages_v7": "Pristine_Real"
}

# ----------------------------------------------------------------------
# STRICT FORENSIC PARTITIONING
# ----------------------------------------------------------------------
# Seen Generators: Present in Training and Validation sets
SEEN_GENERATORS = [
    "SD_1.5",
    "SD_2.1",
    "Flash_SD",
    "SDXL",
    "SDXL_Lightning",
    "SDXL_Turbo",
    "Flash_SDXL",
    "Hyper_SD",
    "JuggernautXL",
    "PixArt_Alpha",
    "Flash_PixArt",
    "Kandinsky",
    "SD_Cascade",
    "IF",
    "Mobius",
    "Realistic_Stock_Photo",
    "SSD_1B",
    "LCM_SDXL",
    "LCM_SSD_1B"
]

# Held-Out Unseen Generators: Strictly reserved for Test split.
# Never present in Training or Validation under any circumstances!
UNSEEN_GENERATORS = [
    "Flux_1",          # State-of-the-art Flow-Matching 12B DiT
    "SD_3",            # Multimodal Diffusion Transformer (MMDiT)
    "Flash_SD3",       # Distilled MMDiT
    "Kolors",          # ChatGLM-based DiT (Modern Chinese Diffusion)
    "Lumina",          # Next-gen Flow-Matching DiT
    "PixArt_Sigma"     # Weak-to-strong diffusion transformer
]


def is_seen_generator(model_name: str) -> bool:
    """Returns True if the model belongs to the Seen Generators set."""
    return model_name in SEEN_GENERATORS


def is_unseen_generator(model_name: str) -> bool:
    """Returns True if the model is reserved for the Unseen Test set."""
    return model_name in UNSEEN_GENERATORS


def get_generator_family_id(model_name: str) -> int:
    """Maps model name to numeric architecture family ID."""
    family = MODEL_TO_FAMILY.get(model_name, "Novel_Unseen")
    return GENERATOR_FAMILIES.get(family, GENERATOR_FAMILIES["Novel_Unseen"])


def get_family_name(family_id: int) -> str:
    """Reverse lookup from family ID to human-readable family name."""
    for name, fid in GENERATOR_FAMILIES.items():
        if fid == family_id:
            return name
    return "Novel_Unseen"
