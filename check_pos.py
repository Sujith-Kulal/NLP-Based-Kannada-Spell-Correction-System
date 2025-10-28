import sys
import pandas as pd
import os
import importlib.util
from wxconv import WXC


# ----------- Usage -----------
# python process_pos_input.py category_map.py input.txt output.txt
# -----------------------------


# -------------------------------------------------------
# Algorithm 1 – Memoized Recursive Edit Distance Function
# -------------------------------------------------------
def edit_distance(s: str, t: str, memo=None):
    """
    Recursive memoized edit-distance implementation.
    Equivalent to Algorithm 1 EDIT-DISTANCE(s, t, h).
    """
    if memo is None:
        memo = {}

    key = (s, t)
    if key in memo:
        return memo[key]

    # Base cases
    if len(s) == 0:
        return len(t)
    if len(t) == 0:
        return len(s)

    # Recursive cases
    s_prime = s[:-1]
    t_prime = t[:-1]

    ka = edit_distance(s_prime, t_prime, memo)
    kb = edit_distance(s_prime, t, memo) + 1
    kc = edit_distance(s, t_prime, memo) + 1

    if s[-1] == t[-1]:
        kd = ka
    else:
        kd = ka + 1

    c = min(kb, kc, kd)
    memo[key] = c
    return c


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
    """Search for a WX word in all .txt files inside a paradigm folder."""
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
                        base_word = os.path.splitext(f)[0]
                        matched_files.append((fpath, base_word))
            except Exception:
                pass
    return matched_files


def find_closest_words_in_files(wx_word, paradigm_dir, top_n=3):
    """
    Search all paradigm files and find the closest matching words inside them.
    Returns a list of (file_path, found_word, distance).

    Cleans paradigm lines to extract only the true word token
    (removing grammar suffixes like +, _, or tags).
    """
    closest_matches = []
    if not os.path.exists(paradigm_dir):
        return closest_matches

    for root, _, files in os.walk(paradigm_dir):
        for f in files:
            if not f.endswith(".txt"):
                continue
            fpath = os.path.join(root, f)
            try:
                with open(fpath, "r", encoding="utf-8") as fin:
                    for line in fin:
                        line = line.strip()
                        if not line:
                            continue

                        # --- Clean to keep only the main token ---
                        token = line.split()[0]       # before any space
                        token = token.split('+')[0]   # before '+'
                        token = token.split('_')[0]   # before '_'
                        token = token.strip()

                        if not token:
                            continue

                        dist = edit_distance(wx_word, token)
                        closest_matches.append((fpath, token, dist))
            except Exception:
                pass

    # Sort by smallest edit distance
    closest_matches.sort(key=lambda x: x[2])
    return closest_matches[:top_n]


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

    # Paradigm folders for each category
    paradigm_folders = {
        "n": os.path.join("paradigms", "Noun"),
        "pn": os.path.join("paradigms", "Pronouns"),
        "v": os.path.join("paradigms", "Verb"),
    }

    # Initialize WX converter
    converter = WXC(order="utf2wx", lang="kan")

    # Read input file
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    results = []

    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue

        _, word, pos_tag = parts[:3]
        pos_tag = pos_tag.strip()

        # Skip unwanted
        if pos_tag == "N__NNP":
            continue
        if fs_dict.get(pos_tag, "") in ["punc", "blk"]:
            continue

        category = fs_dict.get(pos_tag)
        if not category:
            continue

        # Convert word to WX
        wx_word = converter.convert(word)

        # Search inside paradigm folder
        paradigm_dir = paradigm_folders.get(category)
        matches = search_in_paradigm_folder(wx_word, paradigm_dir)

        # If no direct match → compute edit distances
        if not matches:
            closest = find_closest_words_in_files(wx_word, paradigm_dir, top_n=3)
            if closest:
                suggestion_text = "\n".join(
                    [f"File: {fp}\nWord: {w}\nEdit Distance: {d}" for fp, w, d in closest]
                )
                match_text = (
                    f"No exact match found for {word} ({wx_word})\n"
                    f"Closest words found (based on edit distance):\n{suggestion_text}"
                )
            else:
                match_text = f"No match found for {word} ({wx_word})"
        else:
            match_lines = []
            for fpath, base in matches:
                match_lines.append(f"File: {fpath}\nBase Word: {base}")
            match_text = "\n".join(match_lines)

        results.append({
            "word": word,
            "wx": wx_word,
            "pos_tag": pos_tag,
            "category": category,
            "matches": matches,
            "result": match_text
        })

    # Write results to output file
    with open(output_file, "w", encoding="utf-8") as out:
        for r in results:
            out.write(f"Word: {r['word']} → WX: {r['wx']}\n")
            out.write(f"POS: {r['pos_tag']}, Category: {r['category']}\n")
            out.write(f"Matches / Base Words:\n{r['result']}\n")
            out.write("-" * 70 + "\n")

    print(f"✅ Done! Checked paradigms and suggested closest words if needed. Output → {output_file}")


if __name__ == "__main__":
    main()