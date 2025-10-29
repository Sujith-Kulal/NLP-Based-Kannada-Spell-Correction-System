import os
import subprocess
import argparse

# -------------------------
#  STEP 1 – TOKENIZER
# -------------------------
def run_tokenizer(project_dir, input_path, tokenizer_output, lang):
    print("\n[1/5] Running tokenizer...")
    tokenizer_script = os.path.join(project_dir, "Token", "tokenizer.py")
    cmd = f'python "{tokenizer_script}" --input "{input_path}" --output "{tokenizer_output}" --lang {lang}'
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=True, check=True)
    print("Tokenizer completed.\n")


# -------------------------
#  STEP 2 – CREATE CoNLL
# -------------------------
def run_create_conll(project_dir, tokenizer_output, conll_output):
    print("[2/5] Creating CoNLL file...")
    create_conll_script = os.path.join(project_dir, "pos_tag", "create_conll.py")
    if not os.path.exists(create_conll_script):
        raise FileNotFoundError(f"CoNLL script not found at: {create_conll_script}")
    cmd = f'python "{create_conll_script}" "{tokenizer_output}" "{conll_output}"'
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=True, check=True)
    print("CoNLL file created.\n")


# -------------------------
#  STEP 3 – POS TAGGING
# -------------------------
def run_pos_tag(project_dir, conll_input, pos_output, model_path):
    print("[3/5] Running POS Tagger...")
    pos_tag_dir = os.path.join(project_dir, "pos_tag")
    run_pos_script = os.path.join(pos_tag_dir, "run_pos_new.py")
    if not os.path.exists(run_pos_script):
        raise FileNotFoundError(f"POS script not found at: {run_pos_script}")

    # Run inside pos_tag folder so encoding_dict.pickle is found
    cmd = f'python "{run_pos_script}" --input "{conll_input}" --output "{pos_output}" --model "{model_path}"'
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=pos_tag_dir)
    print("POS tagging completed.\n")


# -------------------------
#  STEP 4 – GENERATE CHUNK FEATURES
# -------------------------
def run_generate_chunk_features(project_dir, pos_output, chunk_features_output):
    print("[4/5] Generating Chunk Features...")
    chunk_dir = os.path.join(project_dir, "chunk_tag")
    generate_features_script = os.path.join(chunk_dir, "generate_features.py")
    model_path = os.path.join(chunk_dir, "checkpoint-18381")
    if not os.path.exists(generate_features_script):
        raise FileNotFoundError(f"generate_features.py not found at: {generate_features_script}")

    cmd = f'python "{generate_features_script}" --input "{pos_output}" --output "{chunk_features_output}" --model "{model_path}"'
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=chunk_dir)
    print("Chunk features generated.\n")


# -------------------------
#  STEP 5 – CONVERT TO SSF
# -------------------------
def run_convert_to_ssf(project_dir, chunk_features_output, final_output):
    print("[5/5] Converting Chunk Features to SSF Format...")
    chunk_dir = os.path.join(project_dir, "chunk_tag")
    convert_script = os.path.join(chunk_dir, "read_feature_files_and_convert_into_ssf.py")
    if not os.path.exists(convert_script):
        raise FileNotFoundError(f"Conversion script not found at: {convert_script}")

    cmd = f'python "{convert_script}" --input "{chunk_features_output}" --opr 1 --output "{final_output}"'
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=chunk_dir)
    print("Final SSF Output generated.\n")


# -------------------------
#  MAIN FUNCTION
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="Unified pipeline: Tokenizer + CoNLL + POS + Chunk Tagging")
    parser.add_argument("--input", default="Input.txt", help="Path to input text file")
    parser.add_argument("--output", default="Final_SSF_Output.txt", help="Final SSF output file")
    parser.add_argument("--pos_model", default=os.path.join("pos_tag", "xlm-base-2"), help="POS model folder path")
    parser.add_argument("--lang", required=True, help="Language code (e.g., 0/1/2)")
    args = parser.parse_args()

    project_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"Project directory: {project_dir}")
    print(f"Input file: {os.path.join(project_dir, args.input)}")
    print(f"POS model path: {os.path.join(project_dir, args.pos_model)}")
    print(f"Final SSF output will be: {os.path.join(project_dir, args.output)}\n")

    # Intermediate files
    tokenizer_output = os.path.join(project_dir, "tokenized_output.txt")
    conll_output = os.path.join(project_dir, "conll_output.txt")
    pos_output = os.path.join(project_dir, "pos_output.txt")
    chunk_features_output = os.path.join(project_dir, "chunk_features_output.txt")

    # Pipeline execution
    run_tokenizer(project_dir, os.path.join(project_dir, args.input), tokenizer_output, args.lang)
    run_create_conll(project_dir, tokenizer_output, conll_output)
    run_pos_tag(project_dir, conll_output, pos_output, os.path.join(project_dir, args.pos_model))
    run_generate_chunk_features(project_dir, pos_output, chunk_features_output)
    run_convert_to_ssf(project_dir, chunk_features_output, os.path.join(project_dir, args.output))


if __name__ == "__main__":
    main()
