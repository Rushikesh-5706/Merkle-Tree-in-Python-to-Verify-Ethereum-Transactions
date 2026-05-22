import subprocess
import sys

def run_part(script: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"Running {script}")
    print("=" * 60)
    subprocess.run([sys.executable, script], check=True)

if __name__ == "__main__":
    run_part("part1_tree.py")
    run_part("part2_fetch.py")
    run_part("part3_verify.py")
