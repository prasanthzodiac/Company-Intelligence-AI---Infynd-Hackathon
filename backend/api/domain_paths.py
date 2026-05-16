"""Re-export for API layer (implementation in services.domain_paths)."""
from services.domain_paths import domain_folder_variants, resolve_domain_dir

__all__ = ["domain_folder_variants", "resolve_domain_dir"]
