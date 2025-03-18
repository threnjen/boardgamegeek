import os
import subprocess
import sys
import time

if __name__ == "__main__":
    asset = sys.argv[1]
    job = sys.argv[2]

    subprocess.Popen("dagster-webserver -h 0.0.0.0 -p 3000".split(" "))
    print("Started webserver")

    time.sleep(5)
    print("Launching BGG Orchestrator...")

    if asset == "all":
        print(f"Executing all assets... for job {job}")
        subprocess.run(
            f"dagster job execute --package-name dagster_orchestration -j {job}".split(
                " "
            )
        )
    else:
        print(f"Executing asset: {asset}...")
        subprocess.run(
            f"dagster asset materialize --select {asset} --package-name dagster_orchestration".split(
                " "
            )
        )

    print("Orchestration complete.")
