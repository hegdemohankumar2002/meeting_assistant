try:
    import torchaudio
    import torch
    import noisereduce as nr
except Exception as e:
    print(f"[CLEANER] Audio libraries not fully available: {e}")
    torchaudio = None
    torch = None
    nr = None


def clean_audio(input_file: str, output_file: str) -> str:
    """Clean noisy audio using noisereduce if available; otherwise return original file."""
    try:
        if torchaudio is None or torch is None or nr is None:
            print("[CLEANER] torchaudio/torch/noisereduce unavailable; skipping cleaning")
            return input_file

        noisy, fs = torchaudio.load(input_file)

        if noisy.ndim == 1:
            noisy = noisy.unsqueeze(0)

        try:
            print("[CLEANER] Using noisereduce...")
            noisy_np = noisy.squeeze(0).numpy()
            reduced = nr.reduce_noise(y=noisy_np, sr=fs)
            enhanced_tensor = torch.tensor(reduced).unsqueeze(0)
            torchaudio.save(output_file, enhanced_tensor, fs)
            return output_file
        except Exception as e:
            print(f"[CLEANER] noisereduce failed: {e}")
            print("[CLEANER] Returning raw file (no cleaning)")
            return input_file

    except Exception as e:
        print(f"[CLEANER] Critical error: {e}")
        return input_file
