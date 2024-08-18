# syntax=docker/socerfile:1

FROM python:3.12
RUN apt-get update && apt-get install -y python3-pip

ARG FILENAME
ENV FILENAME=$FILENAME

RUN pip3 install pipenv && pipenv sync

COPY ./ ./

ENTRYPOINT ["pipenv", "run", "python", "game_data_scraper.py"]
CMD ["$FILENAME"]