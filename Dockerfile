FROM rust:1.72.0

RUN apt-get update
RUN apt-get install -y protobuf-compiler
RUN cd /opt/ && git clone https://github.com/breez/breez-sdk.git


WORKDIR /opt/breez-sdk/libs/sdk-bindings


ENV TARGET=x86_64-unknown-linux-gnu
RUN make init
RUN make python-linux


RUN cp /opt/breez-sdk/libs/sdk-bindings/ffi/python/* /usr/lib/python3.11/
WORKDIR /opt/


WORKDIR /opt/bitzipbot


# installing the redis-cli
RUN     apt-get update && \
        apt-get -y install redis-tools 


# installing mariadb client
RUN     apt-get -y install mariadb-client


# prerequisites for bitcoinlib
RUN     apt-get -y install build-essential python-dev-is-python3 python3-dev libgmp3-dev python3-pip && \
        apt-get -y install libssl-dev


# prerequisites for encrypted database for bitcoinlib
RUN     apt-get -y install sqlcipher libsqlcipher0 libsqlcipher-dev


# add requirements.txt
COPY ./requirements.txt /opt/bitzipbot/requirements.txt


# upgrading pip3
##RUN     /usr/local/bin/python3 -m pip install --upgrade pip


# install requirements
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


CMD [ "./entrypoint.sh" ]

