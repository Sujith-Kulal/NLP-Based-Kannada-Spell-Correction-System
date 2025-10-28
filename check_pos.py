import sys
import pandas as pd
import os
import importlib.util
from wxconv import WXC

# ----------- Usage -----------
# python process_pos_input.py category_map.py input.txt output.txt
# -----------------------------

def read_excel(path):
    """Safely read Excel file into pandas DataFrame"""
    try:
        df = pd.read_excel(path, header=None, dtype=str)
        df = df.fillna("")
        return df
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None


def search_in_paradigm_folder(wx_word, paradigm_dir):
    """Search for a WX word in all .txt files inside a paradigm folder"""
    matched_files = []
    if not os.path.exists(paradigm_dir):
        return matched_files

    for root, _, files in os.walk(paradigm_dir):
        for f in files:
            if not f.endswith(".txt"):
                continue
            fpath = os.path.join(root, f)
            try:
                with open(fpath, "r", encoding="utf-8") as fin:
                    content = fin.read()
                    if wx_word in content:
                        matched_files.append(fpath)
            except Exception:
                pass
    return matched_files


def main():
    if len(sys.argv) != 4:
        print("Usage: python process_pos_input.py category_map.py input.txt output.txt")
        sys.exit(1)

    map_file = sys.argv[1]
    input_file = sys.argv[2]
    output_file = sys.argv[3]

    # Load mapping file dynamically
    spec = importlib.util.spec_from_file_location("category_map", map_file)
    category_map = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(category_map)
    fs_dict = category_map.fs_dict_double

    # Excel files by category
    excel_files = {
        "n": "Noun Distribution.xlsx",
        "pn": "Pronoun Distribution .xlsx",
        "v": "Verb Distribution - Copy.xlsx"
    }

    # Paradigm folders
    paradigm_folders = {
        "n": os.path.join("paradigms", "Noun"),
        "pn": os.path.join("paradigms", "Pronouns"),
        "v": os.path.join("paradigms", "Verb"),
    }

    # Initialize wx converter
    converter = WXC(order="utf2wx", lang="kan")

    # Read input
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    results = []

    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue

        _, word, pos_tag = parts[:3]
        pos_tag = pos_tag.strip()

        # Skip NNP, punc, blk
        if pos_tag == "N__NNP":
            continue
        if fs_dict.get(pos_tag, "") in ["punc", "blk"]:
            continue

        category = fs_dict.get(pos_tag)
        if not category:
            continue

        # Convert to WX
        wx_word = converter.convert(word)

        # Search inside paradigm folder
        paradigm_dir = paradigm_folders.get(category)
        matches = search_in_paradigm_folder(wx_word, paradigm_dir)

        # Prepare message
        if matches:
            match_text = "\n".join(matches)
        else:
            match_text = f"No match found for {word} ({wx_word})"

        results.append({
            "word": word,
            "wx": wx_word,
            "pos_tag": pos_tag,
            "category": category,
            "found_files": matches,
            "result": match_text
        })

    # Write to output file
    with open(output_file, "w", encoding="utf-8") as out:
        for r in results:
            out.write(f"Word: {r['word']} → WX: {r['wx']}\n")
            out.write(f"POS: {r['pos_tag']}, Category: {r['category']}\n")
            out.write(f"Matches:\n{r['result']}\n")
            out.write("-" * 60 + "\n")

    print(f"✅ Done! Checked paradigms and saved results to {output_file}")


if __name__ == "__main__":
    main()
