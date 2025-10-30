import os
import subprocess
import argparse

def run_tokenizer(project_dir, input_path, tokenizer_output, lang):
    print("\n[1/6] Running tokenizer...")
    # try several known tokenizer locations / filenames (case-insensitive)
    candidates = [
        os.path.join(project_dir, "token", "tokenizer_for_indian_languages_on_files.py"),
        os.path.join(project_dir, "token", "tokenizer.py"),
        os.path.join(project_dir, "Token", "tokenizer.py"),
    ]
    tokenizer_script = None
    for c in candidates:
        if os.path.exists(c):
            tokenizer_script = c
            break
    if tokenizer_script is None:
        raise FileNotFoundError(
            "Tokenizer script not found. Tried:\n  " + "\n  ".join(candidates) +
            "\nPlease ensure the tokenizer script exists or update all.py to point to the correct file."
        )

    cmd = f'python "{tokenizer_script}" --input "{input_path}" --output "{tokenizer_output}" --lang {lang}'
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=True, check=True)
    print("✅ Tokenizer completed.\n")


def run_create_conll(project_dir, tokenizer_output, conll_output):
    print("[2/6] Creating CoNLL file...")
    create_conll_script = os.path.join(project_dir, "pos_tag", "create_conll.py")
    if not os.path.exists(create_conll_script):
        raise FileNotFoundError(f"❌ CoNLL script not found at: {create_conll_script}")
    cmd = f'python "{create_conll_script}" "{tokenizer_output}" "{conll_output}"'
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=True, check=True)
    print("✅ CoNLL file created.\n")


def run_pos_tag(project_dir, conll_input, pos_output, model_path):
    print("[3/6] Running POS Tagger...")
    pos_tag_dir = os.path.join(project_dir, "pos_tag")
    run_pos_script = os.path.join(pos_tag_dir, "run_pos_new.py")
    if not os.path.exists(run_pos_script):
        raise FileNotFoundError(f"❌ POS script not found at: {run_pos_script}")

    # Run from inside pos_tag folder so encoding_dict.pickle is found
    cmd = f'python "{run_pos_script}" --input "{conll_input}" --output "{pos_output}" --model "{model_path}"'
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=pos_tag_dir)
    print("✅ POS tagging completed.\n")


def run_chunk_tag(project_dir, pos_input, chunk_output, model_path):
    print("[4/6] Running Chunk Tagger...")
    chunk_tag_dir = os.path.join(project_dir, "chunk_tag")
    chunk_script = os.path.join(chunk_tag_dir, "generate_features.py")
    if not os.path.exists(chunk_script):
        raise FileNotFoundError(f"❌ Chunk script not found at: {chunk_script}")

    # Run from inside chunk_tag folder so chunk_encoding_dict.pickle is found
    cmd = f'python "{chunk_script}" --input "{pos_input}" --output "{chunk_output}" --model "{model_path}"'
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=chunk_tag_dir)
    print("✅ Chunk tagging completed.\n")


def run_ssf_conversion(project_dir, chunk_input, ssf_output):
    print("[5/6] Converting to SSF format...")
    chunk_tag_dir = os.path.join(project_dir, "chunk_tag")
    ssf_script = os.path.join(chunk_tag_dir, "read_feature_files_and_convert_into_ssf.py")
    if not os.path.exists(ssf_script):
        raise FileNotFoundError(f"❌ SSF conversion script not found at: {ssf_script}")

    # opr=1 for chunking
    cmd = f'python "{ssf_script}" --input "{chunk_input}" --output "{ssf_output}" --opr 1'
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=True, check=True)
    print("✅ SSF conversion completed.\n")


def run_check_pos(project_dir, ssf_input, final_output):
    print("[6/6] Running Check POS...")
    check_pos_dir = os.path.join(project_dir, "check_pos")
    check_pos_script = os.path.join(check_pos_dir, "check_pos.py")
    category_map = os.path.join(check_pos_dir, "category_map.py")
    
    if not os.path.exists(check_pos_script):
        raise FileNotFoundError(f"❌ Check POS script not found at: {check_pos_script}")
    if not os.path.exists(category_map):
        raise FileNotFoundError(f"❌ Category map not found at: {category_map}")

    # Run from project_dir so paradigms folder can be found
    cmd = f'python "{check_pos_script}" "{category_map}" "{ssf_input}" "{final_output}"'
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=project_dir)
    print("✅ Check POS completed.\n")


def main():
    parser = argparse.ArgumentParser(description="Unified pipeline: Tokenizer + CoNLL + POS Tagger + Chunk Tagger + SSF Conversion + Check POS")
    parser.add_argument("--input", default="Input.txt", help="Path to input text file")
    parser.add_argument("--output", default="Checked_Output.txt", help="Final output file after check_pos")
    parser.add_argument("--pos-model", default=os.path.join("pos_tag", "xlm-base-2"), help="POS Model folder path")
    parser.add_argument("--chunk-model", default=os.path.join("chunk_tag", "checkpoint-18381"), help="Chunk Model folder path")
    parser.add_argument("--lang", required=True, help="Language code (e.g., 0/1/2)")
    args = parser.parse_args()

    project_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"📂 Project directory: {project_dir}")
    print(f"🧾 Input file: {os.path.join(project_dir, args.input)}")
    print(f"📘 POS Model path: {os.path.join(project_dir, args.pos_model)}")
    print(f"� Chunk Model path: {os.path.join(project_dir, args.chunk_model)}")
    print(f"�💾 Final output will be: {os.path.join(project_dir, args.output)}\n")

    # Intermediate file paths
    tokenizer_output = os.path.join(project_dir, "tokenized_output.txt")
    conll_output = os.path.join(project_dir, "conll_output.txt")
    pos_output = os.path.join(project_dir, "Final_POS_Output.txt")
    chunk_output = os.path.join(project_dir, "chunk_output.txt")
    ssf_output = os.path.join(project_dir, "ssf_output.txt")

    # Run the complete pipeline
    run_tokenizer(project_dir, os.path.join(project_dir, args.input), tokenizer_output, args.lang)
    run_create_conll(project_dir, tokenizer_output, conll_output)
    run_pos_tag(project_dir, conll_output, pos_output, os.path.join(project_dir, args.pos_model))
    run_chunk_tag(project_dir, pos_output, chunk_output, os.path.join(project_dir, args.chunk_model))
    run_ssf_conversion(project_dir, chunk_output, ssf_output)
    run_check_pos(project_dir, ssf_output, os.path.join(project_dir, args.output))

    print(f"\n🎉 Complete pipeline finished successfully!")
    print(f"📄 Intermediate files:")
    print(f"   - Tokenized: {tokenizer_output}")
    print(f"   - CoNLL: {conll_output}")
    print(f"   - POS Tagged: {pos_output}")
    print(f"   - Chunk Tagged: {chunk_output}")
    print(f"   - SSF Format: {ssf_output}")
    print(f"📝 Final output: {os.path.join(project_dir, args.output)}")


if __name__ == "__main__":
    main()