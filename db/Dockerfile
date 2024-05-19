FROM postgres:15

RUN mkdir -p /oracle/pg_data/archive && chown -R postgres:postgres /oracle/pg_data

EXPOSE 5432

COPY init.sql /docker-entrypoint-initdb.d/

