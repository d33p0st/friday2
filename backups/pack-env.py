
import subprocess
import base64

# Path to the Conda environment
conda_env_path = "/opt/homebrew/Caskroom/miniconda/base/envs/friday2-embedded"

# Output tar file
output_tar = "friday2-rasa3.6.21-arm64.tar.gz"

# Number of threads for compression
num_threads = 10

# Compression level (0-9)
compression_level = 9

def get_excluded_files(env_path):
    """Finds all problematic files (hard links, symlinks, empty files)"""
    exclude_files = []

    # Find hard-linked files
    hardlinked_result = subprocess.run(
        ["find", env_path, "-type", "f", "-links", "+1"],
        capture_output=True, text=True
    )
    hardlinked_files = hardlinked_result.stdout.strip().split("\n") if hardlinked_result.stdout else []

    # Find symbolic links
    symlink_result = subprocess.run(
        ["find", env_path, "-type", "l"],
        capture_output=True, text=True
    )
    symlink_files = symlink_result.stdout.strip().split("\n") if symlink_result.stdout else []

    # Find empty files (zero-byte)
    empty_result = subprocess.run(
        ["find", env_path, "-type", "f", "-empty"],
        capture_output=True, text=True
    )
    empty_files = empty_result.stdout.strip().split("\n") if empty_result.stdout else []

    # Collect all files to exclude
    exclude_files.extend(hardlinked_files)
    exclude_files.extend(symlink_files)
    exclude_files.extend(empty_files)

    # Filter out empty strings (caused by empty outputs)
    exclude_files = [file for file in exclude_files if file.strip()]

    return exclude_files

def pack_conda_env(env_path, output_tar, exclude_files, num_threads, compression_level):
    """Packs the Conda environment while excluding problematic files."""
    exclude_args = [f"--exclude={file}" for file in exclude_files]
    
    cmd = [
        "conda", "pack",
        "-p", env_path,
        "-o", output_tar,
        "-j", str(num_threads),
        "--compress-level", str(compression_level),
    ] + exclude_args

    try:
        subprocess.run(cmd, check=True)
        print(f"Conda environment packed successfully: {output_tar}")
    except subprocess.CalledProcessError as e:
        print("Error during conda pack:", e)

if __name__ == "__main__":
    print(f"Finding problematic files in {conda_env_path}...")
    excluded_files = get_excluded_files(conda_env_path)
    
    if excluded_files:
        print(f"Excluding {len(excluded_files)} problematic files.")
        with open("excluded_files.log", "w") as f:
            f.write("\n".join(excluded_files))
        print("List of excluded files saved in excluded_files.log")
    else:
        print("No problematic files found.")

    print("Packing Conda environment...")
    pack_conda_env(conda_env_path, output_tar, excluded_files, num_threads, compression_level)