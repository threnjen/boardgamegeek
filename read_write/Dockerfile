FROM python:3.12
RUN apt-get update -y && apt-get install -y build-essential

COPY Pipfile* ./

RUN pip3 install pipenv && pipenv sync

COPY ./ ./

ARG FILE_NAME
ENV FILE_NAME=$FILE_NAME

ENTRYPOINT ["pipenv", "run", "python", "data_pull.py"]
CMD ["$FILE_NAME"]