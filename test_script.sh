#!/bin/bash
# first run this command to generate few shot informal proof sketch
$BENCHMARK_NAME="simple_benchmark_lean"
python src/main/eval_benchmark.py benchmark=$BENCHMARK_NAME eval_settings=n_4_informal_gpt4_turbo env_settings=bm25_retrieval prompt_settings=lean_few_shot_informal

$DATE_TIME="20240115-210441" #edit this to match the date and time that the first command is run
# note that the informal proof sketch will be stored at 
#  .log/proofs/eval_driver/informal_few_shot/gpt4/$BENCHMARK_NAME/$DATE_TIME/informal_proofs

# then run the below command to use the few shot informal proof sketch
python src/main/eval_benchmark.py prompt_settings=lean_few_shot_informal_to_formal_dfs_gpt4_turbo env_settings=bm25_retrieval eval_settings=n_60_dfs_gpt4_always_retrieve_no_ex benchmark=simple_benchmark_lean 

# but this doesn't work... what went wrong? 