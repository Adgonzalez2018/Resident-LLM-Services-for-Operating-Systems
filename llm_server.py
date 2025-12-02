#!/usr/bin/env python3

# Simple LLM inference server that logs latency for each request.

import time
import sys
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class LLMServer:
    def __init__(self, model_name="gpt2"):
        print(f"Loading model: {model_name}", file=sys.stderr)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype = torch.float32
        )
        print("Model loaded!", file=sys.stderr)
        
    def generate(self, prompt, max_tokens=50):
        # Generate text and return output & latency (ms)
        start = time.time()
        
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=True,
            temperature=.7
        )
        
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        latency_ms = (time.time() - start) * 1000
        return result, latency_ms
        	
def main():
	server = LLMServer()
	
	# read prompts from stdin, one per line
	print("Ready. send prompts (one per line):", file=sys.stderr)
	for line in sys.stdin:
		prompt = line.strip()
		if not prompt:
			continue
			
		result, latency = server.generate(prompt)
		
		# Log format: timestamp, latency_ms_prompt_length
		print(f"{time.time()},{latency:.2f},{len(prompt)}")
		sys.stderr.flush()
		sys.stdout.flush()
		
if __name__ == "__main__":
	main()
	
		



