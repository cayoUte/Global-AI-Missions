-- Runs once when the gam_pgdata volume is first initialised (docker-entrypoint-initdb.d).
-- A separate database for pytest, so the test suite never touches the dev/demo data in `gam`.
CREATE DATABASE gam_test OWNER gam;
