import argparse
import os
import subprocess
import time

def parse_arguments():
    parser = argparse.ArgumentParser(description='BGG Orchestrator')
    parser.add_argument("-asset", type=str, help="Asset to run", default="all")
    parser.add_argument('-env', type=str, help='Environment? Defaults to dev'), default=os.environ.get('ENV', 'dev')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    ENV = args.__dict__.get('env')
    asset = args.__dict__.get('asset')

    subprocess.Popen("dagster-webserver -h 0.0.0.0 -p 3000".split(" "))
    print("Started webserver")

    time.sleep(5)
    print("Launching BGG Orchestrator...")

    if args.asset == "all":
        print("Executing all assets...")
        subprocess.run(f"dagster job execute --package-name bgg_orchestrator -j bgg_job".split(" "))
    else:
        print(f"Executing asset: {asset}...")
        subprocess.run(f"dagster asset materialize --select {asset} --package-name bgg_orchestrator".split(" "))

    print("Orchestration complete.")