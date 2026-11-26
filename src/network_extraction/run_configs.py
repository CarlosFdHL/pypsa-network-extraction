"""Copy the yaml configs of a run next to its extracted data."""

import shutil
from pathlib import Path


def copy_run_configs(run_dir, out_dir, globs):
    """Copy the files matching `globs` (relative to run_dir), keeping their relative paths."""
    run_dir, out_dir = Path(run_dir), Path(out_dir)
    copied = []
    for pattern in globs:
        for src in sorted(run_dir.glob(pattern)):
            dst = out_dir / src.relative_to(run_dir)
            if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(dst)
    return copied
