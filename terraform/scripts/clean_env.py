if __name__ == "__main__":
    new_env_file = ""
    with open("../.env", "r") as file:
        lines = file.readlines()
        print(lines)
        for line in lines:
            if (
                "TF_VAR_BUCKET" in line
                or "TF_VAR_REGION" in line
                or "TF_VAR_MY_IP_FIRST_THREE_BLOCKS" in line
                or "PYTHONPATH" in line
                or "IS_LOCAL" in line
                or "ENVIRONMENT" in line
            ):
                continue
            if line == "\n":
                continue
            new_env_file += line

    with open("../.env", "w") as file:
        file.write(new_env_file)
