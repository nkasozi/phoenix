"""Hugging face classsifier utility functions."""

import torch


def is_cuda_available() -> bool:
    """Checks if CUDA is available.

    Returns:
        bool: True if CUDA is available, False otherwise.
    """
    try:
        return torch.cuda.is_available()
    except Exception as e:
        raise RuntimeError(f"CUDA availability check failed: {e}")
