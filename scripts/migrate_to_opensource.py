#!/usr/bin/env python3
"""
Migrate FakeAI to use 100% open-source models.

Replaces all OpenAI closed-source model references with open-source alternatives.
"""
import os
import re
from pathlib import Path


# Model replacement mapping
REPLACEMENTS = {
    # GPT-4 variants → openai/gpt-oss-120b (OpenAI's own open model)
    r'\bgpt-4o-mini\b': 'openai/gpt-oss-20b',
    r'\bgpt-4o\b': 'openai/gpt-oss-120b',
    r'\bgpt-4-turbo\b': 'openai/gpt-oss-120b',
    r'\bgpt-4\b': 'openai/gpt-oss-120b',

    # GPT-3.5 variants → meta-llama/Llama-3.1-8B-Instruct
    r'\bgpt-3\.5-turbo-instruct\b': 'meta-llama/Llama-3.1-8B-Instruct',
    r'\bgpt-3\.5-turbo\b': 'meta-llama/Llama-3.1-8B-Instruct',

    # deepseek-ai/DeepSeek-R1 models → DeepSeek-R1 (but keep gpt-oss as they're already open)
    r'\bo1-preview\b': 'deepseek-ai/DeepSeek-R1',
    r'\bo1-mini\b': 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B',
    r'(?<![a-z])\bo1\b(?![a-z-])': 'deepseek-ai/DeepSeek-R1',  # Match "deepseek-ai/DeepSeek-R1" but not "o1-" or letters around it

    # GPT-2 and legacy → TinyLlama
    r'\bgpt2\b': 'TinyLlama/TinyLlama-1.1B-Chat-v1.0',

    # Embedding models → sentence-transformers
    r'\btext-embedding-3-large\b': 'BAAI/bge-m3',
    r'\btext-embedding-3-small\b': 'nomic-ai/nomic-embed-text-v1.5',
    r'\btext-embedding-ada-002\b': 'sentence-transformers/all-mpnet-base-v2',

    # Codex models → Qwen Coder
    r'\bcode-davinci-002\b': 'Qwen/Qwen2.5-Coder-7B-Instruct',

    # DALL-E → Stable Diffusion (note: different API, may need adjustment)
    r'\bdall-e-3\b': 'stabilityai/stable-diffusion-xl-base-1.0',
    r'\bdall-e-2\b': 'stabilityai/stable-diffusion-2-1',
}

# Files to skip
SKIP_PATTERNS = [
    '.git',
    '__pycache__',
    '.pytest_cache',
    '.venv',
    'venv',
    'node_modules',
    '.pyc',
    '.log',
]


def should_skip(path: Path) -> bool:
    """Check if file should be skipped."""
    return any(pattern in str(path) for pattern in SKIP_PATTERNS)


def migrate_file(filepath: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """
    Migrate a single file to open-source models.

    Returns:
        (num_replacements, list of changes)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError):
        return 0, []

    original_content = content
    changes = []
    total_replacements = 0

    # Apply replacements
    for pattern, replacement in REPLACEMENTS.items():
        matches = list(re.finditer(pattern, content))
        if matches:
            content = re.sub(pattern, replacement, content)
            count = len(matches)
            total_replacements += count
            changes.append(f"  {pattern} → {replacement} ({count}x)")

    # Write back if changed
    if content != original_content and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return total_replacements, changes


def migrate_project(project_dir: str, dry_run: bool = False, file_extensions: list[str] = None):
    """
    Migrate entire project to open-source models.

    Args:
        project_dir: Root directory of project
        dry_run: If True, don't write changes (just report)
        file_extensions: File types to process (default: .py, .md)
    """
    if file_extensions is None:
        file_extensions = ['.py', '.md', '.txt', '.yaml', '.yml', '.json']

    project_path = Path(project_dir)

    print("=" * 70)
    print("  FakeAI Open-Source Model Migration")
    print("=" * 70)
    print()
    print(f"Project: {project_dir}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will modify files)'}")
    print()

    total_files_scanned = 0
    total_files_modified = 0
    total_replacements = 0
    all_changes = []

    # Scan all files
    for ext in file_extensions:
        for filepath in project_path.rglob(f'*{ext}'):
            if should_skip(filepath):
                continue

            total_files_scanned += 1
            num_replacements, changes = migrate_file(filepath, dry_run)

            if num_replacements > 0:
                total_files_modified += 1
                total_replacements += num_replacements

                print(f"✓ {filepath.relative_to(project_path)}")
                for change in changes:
                    print(change)
                print()

                all_changes.append((filepath, changes))

    # Summary
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"Files scanned: {total_files_scanned}")
    print(f"Files modified: {total_files_modified}")
    print(f"Total replacements: {total_replacements}")
    print()

    if dry_run:
        print("⚠️  DRY RUN - No files were modified")
        print("   Run with --execute to apply changes")
    else:
        print("✅ Migration complete!")

    print()

    return total_files_modified, total_replacements


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate FakeAI to use 100% open-source models"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually modify files (default: dry-run)"
    )
    parser.add_argument(
        "--project-dir",
        default="/home/anthony/projects/fakeai",
        help="Project directory to migrate"
    )

    args = parser.parse_args()

    migrate_project(
        args.project_dir,
        dry_run=not args.execute
    )
