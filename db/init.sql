CREATE DATABASE bot;

CREATE TABLE hba ( lines text );
COPY hba FROM '/var/lib/postgresql/data/pg_hba.conf';
INSERT INTO hba (lines) VALUES ('host replication all 0.0.0.0/0 md5');
COPY hba TO '/var/lib/postgresql/data/pg_hba.conf';
SELECT pg_reload_conf();


GRANT ALL PRIVILEGES ON DATABASE bot TO postgres;

CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD '1234';

SELECT pg_create_physical_replication_slot('replication_slot');

\c bot;

CREATE TABLE Phones (id SERIAL PRIMARY KEY, Phone VARCHAR(255));

CREATE TABLE Emails (id SERIAL PRIMARY KEY, Email VARCHAR(255));
