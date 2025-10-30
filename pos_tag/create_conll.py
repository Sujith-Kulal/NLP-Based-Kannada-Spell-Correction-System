import sys
import os
import re
import tempfile
import subprocess


def _ensure_gdown():
    try:
        import gdown  # noqa: F401
        return True
    except Exception:
        # Try to install gdown
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "gdown"], check=True)
            import gdown  # noqa: F401
            return True
        except Exception:
            return False


def _download_drive_path(url_or_id, dest_dir):
    """Download a Google Drive file or folder into dest_dir using gdown CLI.

    Returns the path (file or directory) that should be used as input.
    """
    if not _ensure_gdown():
        raise RuntimeError("gdown is required to download from Google Drive. Please install it: pip install gdown")

    # Use CLI to support both files and folders
    # If the url contains '/folders/' treat as folder
    if 'drive.google.com' in url_or_id and '/folders/' in url_or_id:
        # download folder
        cmd = ["gdown", "--folder", url_or_id, "-O", dest_dir]
        subprocess.run(cmd, check=True)
        return dest_dir
    else:
        # treat as file url or id
        cmd = ["gdown", url_or_id, "-O", dest_dir]
        subprocess.run(cmd, check=True)
        # Try to find a single downloaded file in dest_dir
        for root, _, files in os.walk(dest_dir):
            for fn in files:
                return os.path.join(root, fn)
        return dest_dir


def _is_drive_url(s):
    return isinstance(s, str) and 'drive.google.com' in s


def _prepare_input_path(input_arg):
    """Given an input argument (local path or Drive URL), return a local file path for processing."""
    # Direct path exists (relative to current working directory)
    if os.path.exists(input_arg):
        # If it's a directory, try to find a suitable file inside
        if os.path.isdir(input_arg):
            for root, _, files in os.walk(input_arg):
                for fn in files:
                    if fn.lower().endswith(('.xml', '.txt')):
                        return os.path.join(root, fn)
            return input_arg
        return input_arg
    # Try resolving relative to this script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    alt_path = os.path.join(script_dir, input_arg)
    if os.path.exists(alt_path):
        if os.path.isdir(alt_path):
            for root, _, files in os.walk(alt_path):
                for fn in files:
                    if fn.lower().endswith(('.xml', '.txt')):
                        return os.path.join(root, fn)
            return alt_path
        return alt_path
    if _is_drive_url(input_arg):
        tmp = tempfile.mkdtemp(prefix='create_conll_')
        downloaded = _download_drive_path(input_arg, tmp)
        # If a folder was downloaded, try to find the first .xml or .txt file
        if os.path.isdir(downloaded):
            for root, _, files in os.walk(downloaded):
                for fn in files:
                    if fn.lower().endswith(('.xml', '.txt')):
                        return os.path.join(root, fn)
            # fallback: return folder path
            return downloaded
        return downloaded
    raise FileNotFoundError(f"Input path not found and not a Drive URL: {input_arg}")


def main():
    inputfile = sys.argv[1]
    inputfile_local = _prepare_input_path(inputfile)

    with open(inputfile_local, "r", encoding='utf-8') as f:
        data = f.readlines()

    data = [i for i in data if i != "\n"]

    output = sys.argv[2]

    key_words = ["<document", "<head>", "</head>", "</document"]
    with open(output, "w", encoding='utf-8') as outf:
        for i in range(len(data)):
            line = data[i]
            # print(f"Line --> {line}")
            if i < len(data) - 1:
                next_line = data[i + 1]
            else:
                next_line = "NULL"

            flag = 0
            for key in key_words:
                if key in line:
                    flag = 1
                    # f.write(f"{line}")
                    break
            if flag == 0:
                if "((" in line or "))" in line or "<Sentence" in line:
                    # f.write(f"{line}")
                    continue
                # print(f"Line --> {line}")
                if "</Sentence" in line:
                    outf.write("\n")
                else:
                    parts = line.split("\t")
                    if len(parts) < 2:
                        continue
                    word = parts[1]
                    if "\n" in word:
                        word = word.replace("\n", "")
                    outf.write(f"{word}\n")


if __name__ == '__main__':
    main()

        
