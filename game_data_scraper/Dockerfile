# syntax=docker/socerfile:1

FROM python:3.12
RUN apt-get update && apt-get install -y python3-pip

ARG ARG_HERE
ENV ARG_HERE=$ARG_HERE

RUN pip3 install pipenv && pipenv sync

COPY ./ ./

ENTRYPOINT ["pipenv", "run", "python", "main.py"]
CMD ["--argument", "$ARG_HERE"]