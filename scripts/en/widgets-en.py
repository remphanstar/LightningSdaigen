# Cell 2: Download All Accelerator LoRAs
!pip install -q huggingface_hub
from huggingface_hub import hf_hub_download
import os
import shutil

# --- Define Target Directories ---
lora_dir = "/teamspace/studios/this_studio/Wan2GP/loras/"
os.makedirs(lora_dir, exist_ok=True)

lora_i2v_dir = "/teamspace/studios/this_studio/Wan2GP/loras_i2v/"
os.makedirs(lora_i2v_dir, exist_ok=True)

# --- Define LoRAs and Their Destinations ---
loras_to_download = {
    # Text-to-Video LoRAs -> going into 'loras/'
    "Wan2.1_T2V_14B_FusionX_LoRA.safetensors": ("DeepBeepMeep/Wan2.1", lora_dir),
    "Wan21_AccVid_T2V_14B_lora_rank32_fp16.safetensors": ("DeepBeepMeep/Wan2.1", lora_dir),
    "Wan21_CausVid_14B_T2V_lora_rank32.safetensors": ("DeepBeepMeep/Wan2.1", lora_dir),
    "Wan21_T2V_14B_MoviiGen_lora_rank32_fp16.safetensors": ("DeepBeepMeep/Wan2.1", lora_dir),
    "Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors": ("DeepBeepMeep/Wan2.1", lora_dir),
    
    # Image-to-Video LoRAs -> going into 'loras_i2v/'
    "Wan2.1-Fun-14B-InP-MPS_reward_lora.safetensors": ("DeepBeepMeep/Wan2.1", lora_i2v_dir),
    "Wan2.1_I2V_14B_FusionX_LoRA.safetensors": ("DeepBeepMeep/Wan2.1", lora_i2v_dir),
    "Wan21_AccVid_I2V_480P_14B_lora_rank32_fp16.safetensors": ("DeepBeepMeep/Wan2.1", lora_i2v_dir)
}

# --- Download Logic ---
for lora_file, (repo_id, target_dir) in loras_to_download.items():
    print(f"Downloading {lora_file} to {target_dir}...")
    try:
        # Download the file, which will create the subfolder structure locally
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=lora_file,
            repo_type="model",
            subfolder="loras_accelerators",
            local_dir=target_dir,
            local_dir_use_symlinks=False,
            token="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"
        )
        
        # Construct the incorrect path where the file was placed
        incorrect_path = os.path.join(target_dir, "loras_accelerators", lora_file)
        
        # Construct the correct final path
        correct_path = os.path.join(target_dir, lora_file)

        # Move the file from the subfolder to the correct target directory
        if os.path.exists(incorrect_path):
            shutil.move(incorrect_path, correct_path)
        
        print(f"✅ Successfully placed {lora_file} in {target_dir}")

    except Exception as e:
        print(f"❌ Failed to download {lora_file}. Error: {e}")

# --- Cleanup ---
# Clean up the now-empty 'loras_accelerators' subdirectories
if os.path.exists(os.path.join(lora_dir, "loras_accelerators")):
    shutil.rmtree(os.path.join(lora_dir, "loras_accelerators"))
if os.path.exists(os.path.join(lora_i2v_dir, "loras_accelerators")):
    shutil.rmtree(os.path.join(lora_i2v_dir, "loras_accelerators"))

print("\nAll LoRA downloads and file moves are complete.")
