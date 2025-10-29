"""Read feature files or CoNLL files, convert them into SSF, and write them into files."""
import re
import argparse
import os


def read_feature_file_and_create_ssf_sentences(file_path, opr):
    """Read a feature file and create ssf sentences."""
    sent_count = 1
    cntr = 1
    subcntr = 1
    sent_string = ''
    prev_tag = ''
    prev_sent_count = 0
    sentences = []
    if opr == 1:
        lines = open(file_path, 'r', encoding='utf-8').readlines()
        sent_string += "<Sentence id='" + str(sent_count) + "'>\n"
        for line in lines:
            line = line.strip()
            if line:
                features = line.split('\t')
                chnk_info = features[2].split('-')
                if re.search('B-', features[2]) is not None:
                    subcntr = 1
                    if prev_sent_count != sent_count:
                        sent_string += str(cntr) + '\t((\t' + chnk_info[1] + '\t\n'
                        prev_sent_count = sent_count
                    else:
                        cntr += 1
                        sent_string += '\t))\n' + str(cntr) + '\t((\t' + chnk_info[1] + '\t\n'
                    sent_string += str(cntr) + '.' + str(subcntr) + '\t' + features[0] + '\t' + features[1] + '\t\n'
                    subcntr += 1
                    prev_tag = chnk_info[1]
                elif prev_tag and re.search('I-' + prev_tag, features[2]) is not None:
                    sent_string += str(cntr) + '.' + str(subcntr) + '\t' + features[0] + '\t' + features[1] + '\t\n'
                    subcntr += 1
                    prev_tag = chnk_info[1]
                if prev_tag and prev_tag != chnk_info[1] and chnk_info[0] == 'I':
                    subcntr = 1
                    cntr += 1
                    sent_string += '\t))\n' + str(cntr) + '\t((\t' + chnk_info[1] + '\t\n'
                    sent_string += str(cntr) + '.' + str(subcntr) + '\t' + features[0] + '\t' + features[1] + '\t\n'
                    subcntr += 1
                    prev_tag = chnk_info[1]
                if not prev_tag and chnk_info[0] == 'I':
                    sent_string += str(cntr) + '\t((\t' + chnk_info[1] + '\t\n'
                    sent_string += str(cntr) + '.' + str(subcntr) + '\t' + features[0] + '\t' + features[1] + '\t\n'
                    prev_sent_count = sent_count
                    prev_tag = chnk_info[1]
                    subcntr += 1
            else:
                if not re.search("<Sentence id='" + str(sent_count) + "'>\n$", sent_string):
                    sent_string += "\t))\n</Sentence>\n"
                    sentences.append(sent_string)
                    #final_string += sent_string + '\n'
                    sent_count += 1
                    sent_string = "<Sentence id='" + str(sent_count) + "'>\n"
                    cntr = 1
                    subcntr = 1
                    prev_tag = ''
    else:
        lines = open(file_path, 'r', encoding='utf-8').readlines()
        sent_string += "<Sentence id='" + str(sent_count) + "'>\n"
        for line in lines:
            line = line.strip()
            if line:
                features = line.split('\t')
                sent_string += str(cntr) + '\t' + features[0] + '\t' + features[-1] + '\t\n'
                cntr += 1
            else:
                if not re.search("<Sentence id='" + str(sent_count) + "'>\n$", sent_string):
                    sent_string += '</Sentence>\n'
                    sentences.append(sent_string)
                    # final_string += sent_string + '\n'
                    sent_count += 1
                    cntr = 1
                    subcntr = 1
                    sent_string = "<Sentence id='" + str(sent_count) + "'>\n"
    return sentences


def read_feature_files_create_ssf_sentences_and_write(input_folder_path, opr, output_folder_path):
    """Read feature files, convert them into SSF, write them into files based on POS or Chunk predictions."""
    for root, dirs, files in os.walk(input_folder_path):
        for fl in files:
            input_path = os.path.join(root, fl)
            sentences = read_feature_file_and_create_ssf_sentences(input_path, opr)
            output_path = os.path.join(output_folder_path, fl)
            write_list_to_file(output_path, sentences)


def affix_feats(token, length, type_aff):
    '''
    :param line: extract the token and its corresponding suffix list depending on its length
    :param token: the token in the line
    :param length: length of affix
    :param type: 0 for prefix and 1 for suffix
    :return suffix: returns the suffix
    '''
    if len(token) < length:
        return 'NULL'
    else:
        if type_aff == 0:
            return token[:length]
        else:
            return token[len(token) - length:]


def write_list_to_file(out_path, list_samples_string):
    '''
    :param out_path: Enter the path of the output file
    :param list_samples: Enter the token features of sentence separated by a blank line
    :return: None
    '''
    with open(out_path, 'w', encoding='utf-8') as fout:
        fout.write('\n'.join(list_samples_string) + '\n')
        # fout.close()


def main():
    """Pass arguments and call functions here."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='inp', help="Add the input path from where tokens and its features will be extracted")
    parser.add_argument('--output', dest='out', help="Add the output file where the features will be saved")
    parser.add_argument('--opr', dest='opr', help="Add the operation 0 pos tagging 1 chunking", type=int, choices=[0, 1])
    args = parser.parse_args()
    if not os.path.isdir(args.inp):
        sentences = read_feature_file_and_create_ssf_sentences(args.inp, args.opr)
        write_list_to_file(args.out, sentences)
    else:
        if not os.path.isdir(args.out):
            os.makedirs(args.out)
        read_feature_files_create_ssf_sentences_and_write(args.inp, args.opr, args.out)


if __name__ == '__main__':
    main()
