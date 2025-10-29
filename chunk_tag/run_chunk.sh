python generate_features.py --input $1 --output features.txt --model $3

python read_feature_files_and_convert_into_ssf.py --input features.txt --opr 1 --output $2


#rm features.txt
