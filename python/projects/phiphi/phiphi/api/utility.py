"""Utility file."""

import random
import string


def generate_random_string(length: int) -> str:
    """Funtion to generate random string."""
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))
