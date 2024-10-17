import os
import subprocess
import sys
import time

if __name__ == "__main__":
    ENV = sys.argv[1]
    asset = sys.argv[2]

    subprocess.Popen("dagster-webserver -h 0.0.0.0 -p 3000".split(" "))
    print("Started webserver")

    time.sleep(5)
    print("Launching BGG Orchestrator...")

    if asset == "all":
        print("Executing all assets...")
        subprocess.run(
            f"dagster job execute --package-name aws_dagster_bgg -j bgg_job".split(" ")
        )
    else:
        print(f"Executing asset: {asset}...")
        subprocess.run(
            f"dagster asset materialize --select {asset} --package-name aws_dagster_bgg".split(
                " "
            )
        )

    print("Orchestration complete.")
