FROM python:3.10.12

RUN apt-get update

COPY ./bot /opt/breezerbot
WORKDIR /opt/breezerbot


# installing the redis-cli
RUN     apt-get update && \
        apt-get -y install redis-tools 


# installing mariadb client
RUN     apt-get -y install mariadb-client


# prerequisites for bitcoinlib
RUN     apt-get -y install build-essential python3-dev libgmp3-dev python3-pip && \
        apt-get -y install libssl-dev


# add requirements.txt
COPY ./requirements.txt /opt/breezerbot/requirements.txt


# install requirements
#RUN pip install --break-system-packages --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


CMD [ "./entrypoint.sh" ]

