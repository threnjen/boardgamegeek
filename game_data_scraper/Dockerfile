FROM python:3.12
RUN apt-get update && apt-get install -y python3-pip

ARG FILENAME
ENV FILENAME=$FILENAME

# Install pipenv
RUN pip3 install pipenv

COPY ./ ./

# Install pipenv
RUN pipenv sync

ENTRYPOINT ["pipenv", "run", "python", "game_data_scraper.py"]
CMD ["$FILENAME"]