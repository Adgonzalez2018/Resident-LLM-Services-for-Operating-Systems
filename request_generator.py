#!/usr/bin/env python3
# Generate concurrent LLM requests and log results
import sys
import subprocess
import time 
import argparse
from concurrent.futures import ThreadPoolExecuter, as_completed

# Sample prompts of varying lengths
PROMPTS = [
    "Write a short story about a robot",
    "Explain quantum computing in simple terms",
    "What are the benefits of exercise?",
    "Describe the process of photosynthesis",
    "How does the internet work?",
    "What is machine learning?",
    "Explain the water cycle",
    "Why is the sky blue?",
]

def send_request(prompt, server_proc):
	# send single request and return (timestamp, latency, prompt_len)
	start = time.time()
	
	server_proc.stdin.write(prompt + '\n')
	server_proc.stdin.flush()
	
	response = server_proc.stdout.readline().strip()
	
	end = time.time()
	
	# Parse response: timestamp, latency_ms, prompt_length
	parts = response.split(',')
	if len(parts) == 3:
		return float(parts[0]), float(parts[1]), int(parts[2])
		
	return end, (end-start)*1000, len(prompt)
	
def run_experiment(concurrency, num_requests, server_cmd, output_file):
	# Run experiment with N concurrent requests
	print(f"Starting experiment: concurrency={concurrency}, requests={num_requests}",
		file=sys.stderr)
		
	# start server process
	server = subprocess.Popen(
		server_cmd,
		stdin=subprocess.PIPE,
		stdout=subprocess.PIPE,
		stderr=sys.stderr,
		text=True,
		bufsize=1
	)
	
	# wait for server startup
	time.sleep(3)
	
	results = []
	
	# generate requests
	with ThreadPoolExecutor(max_workers=concurrency) as executor:
		futures = []
		for i in range(num_requests):
			prompt = PROMPTS[i % len(PROMPTS)]
			future = executor.submit(send_request, prompt, server)
			futures.append(future)
			
			
			# space out request submissions slightly
			time.sleep(.1)
			
		# collect results
		for future in as_completed(futures):
			try:
				result = future.result(timeout=60)
				results.append(result)
			except Exception as e:
				print(f"Request failed: {e}", file=sys.stderr)
				
	server.terminate()
	server.wait()
	
	# write results
	with open(output_file, 'w') as f:
		f.write("timestamp,latency_ms,prompt_length\n")
		for ts, lat, plen in results:
			f.write(f"{ts},{lat},{plen}\n")
			
	print(f"Wrote {len(results)} results to {output_file}", file=sys.stderr)
	
def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--concurrency', type=int, required=True)
	parser.add_argument('--requests', type=int, default=20)
	parser.add_argument('--mode', choices=['baseline', 'cgroups', 'psi'], required=True)
	parser.add_argument('--output', required=True)
	args = parser.parse_args()
	
	# determine server command based on mode
	if args.mode == 'baseline':
		server_cmd = [sys.executable, 'llm_server.py']
	elif args.mode == 'cgroups':
		server_cmd = [sys.executable, 'llm_server.py']
	elif args.mode == 'psi':
		server_cmd = [sys.executable, 'psi_admission.py', '--threshold', '50.0']
		
	run_experiment(args.concurrency, args.requests, server_cmd, args.output)
	
if __name__ == "__main__":
	main()