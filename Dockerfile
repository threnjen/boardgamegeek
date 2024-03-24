FROM python 3.10
RUN apt-get update -y && apt-get install -y build-essential

COPY Pipfile* ./

RUN pip3 install pipenv && pipenv sync

COPY ./ ./

ARG GROUP
ENV GROUP=$GROUP

ENTRYPOINT ["pipenv","run","main.py"]
CMD ["$GROUP"]