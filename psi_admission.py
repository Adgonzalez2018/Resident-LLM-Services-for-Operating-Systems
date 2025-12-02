#!/usr/bin/env python3
# PSI-gated admission controller for LLM requests.
# Reads PSI, decides whether to admit request, sends to LLM server.

import time
import sys
import subprocess
import argparse

def read_psi_cpu():
	# Read CPU pressure avg10 value
	try:
		with open('/proc/pressure/cpu', 'r') as f:
			# Format: some avg10=X.XX avg60=Y.YY avg300=Z.ZZ total = NNNN
			line = f.readline()
			parts = line.split()
			for part in parts:
				if part.startswith('avg10='):
					return float(part.split('=')[1])
					
	except Exception as e:
		print(f"Error reading PSI: {e}", file=sys.stderr)
	return 0.0
	
def should_admit(threshold):
	# check if we admit a new request based on PSI
	psi = read_psi_cpu()
	admit = psi < threshold
	print(f"PSI avg10={psi:.2f}, threshold={threshold}, admit={admit}", file=sys.stderr)
	return admit, psi
	
def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--threshold', type=float, default=80.0,
						help='PSI threshold for admission (default: 50.0)')
	parser.add_argument('--check-interval', type=float, default=.5,
						help='How often to check PSI when deferring (seconds)')
	args = parser.parse_args()
	
	print(f"PSI Admission Controller: threshold={args.threshold}", file=sys.stderr)
	
	# start LLM server subprocess
	llm_proc = subprocess.Popen(
		[sys.executable,'llm_server.py'],
		stdin=subprocess.PIPE,
		stdout=subprocess.PIPE,
		stderr=sys.stderr,
		text=True,
		bufsize=1
	)
	
	# wait for server to be ready
	time.sleep(3)
	
	# read requests from stdin
	for line in sys.stdin:
		prompt = line.strip()
		if not prompt:
			continue	
			
		# check PSI before admitting
		admitted = False
		attempts = 0
		while not admitted and attempts < 10: # max 10 attempts (5s)
			admit, psi = should_admit(args.threshold)
			if admit:
				admitted = True
			else:
				attempts += 1
				time.sleep(args.check_interval)
				
		if not admitted:
			print(f"Rejected, {psi:.2f},{len(prompt)}")
			continue
			
		# send to LLM server
		llm_proc.stdin.write(prompt + '\n')
		llm_proc.stdin.flush()
		
		# read response
		response = llm_proc.stdout.readline()
		print(response.strip())
		sys.stdout.flush()
		
	llm_proc.terminate()
	
if __name__ == "__main__":
	main()