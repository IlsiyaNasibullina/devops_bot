FROM postgres:15

RUN apt-get update && apt-get install -y gosu

RUN echo "listen_addresses = 'localhost, db'" >> /etc/postgresql/postgresql.conf
RUN echo "port = 5432" >> /etc/postgresql/postgresql.conf

EXPOSE 5432

