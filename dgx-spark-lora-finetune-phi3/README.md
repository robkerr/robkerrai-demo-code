# Shell scripts used in the video

## Pull the container if needed

```bash
docker pull nvcr.io/nvidia/pytorch:25.09-py3
```

## Change to the correct folder

```bash
cd ~/projects/dgx-spark-lora-finetune-phi3
```

## Launch Docker

```bash
docker run --gpus all -it --rm --ipc=host \
-v $HOME/.cache/huggingface:/root/.cache/huggingface \
-v ${PWD}:/workspace -w /workspace \
nvcr.io/nvidia/pytorch:25.09-py3
```

## Install dependencies inside the container

```bash
pip install -r requirements.txt
```

## Authenticate with Huggingface

```bash
huggingface-cli login
#<input your huggingface token.
#<Enter n for git credential>
```

## Run Fine-Tuning Script 

```bash
python lora_finetune.py
```

## Merge the LoRA adapters with the base model 

```bash
python merge_model.py
```

## Download llama.cpp

```bash
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
```

## Create a gguf file from the merged model files

```bash
cd llama.cpp
pip install -r requirements.txt

mkdir ../gguf

python convert_hf_to_gguf.py \
  --outfile ../gguf/phi-3.5-mini-sql-1-f16.gguf \
  --outtype f16 \
  ../merged_model
```

## Build binaries needed to quantize and serve models

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON 
cmake --build build --parallel
```
 
##Create a 4-bit quantized version of the model

```bash
build/bin/llama-quantize \
  ../gguf/phi-3.5-mini-sql-1-f16.gguf \
  ../gguf/phi-3.5-mini-sql-1-Q4.gguf \
  Q4_K
```

## Serve and test the Model

```bash
build/bin/llama-cli \
  -m ../gguf/phi-3.5-mini-sql-1-Q4.gguf \
  -n 1000 -t 8 \
  -p "Tell a joke."
```

## Copy model to Synology NAS

```bash
cp gguf/phi-3.5-mini-sql-1-Q4.gguf /mnt/synology
```