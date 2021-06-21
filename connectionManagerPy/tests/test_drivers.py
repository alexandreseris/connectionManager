"""

docker help
ports:
    -p 123:456
    bind le port 456 au port 123 du host
    on peut ajouter une adresse au besoin
    -p 127.0.0.1:123:456

passer en "ssh"
    docker exec -ti postgrestest /bin/bash
        => faire un alias powershell psk flemme de taper tout ça :3

restart un container déjà run:
    docker restart postgrestest

public servers:

mysql (https://m.ensembl.org/info/data/mysql.html)
    ensembldb.ensembl.org 	anonymous 	- 	3306 & 5306 	MySQL 5.6.33
    or docker run --name some-mysql -e MYSQL_ROOT_PASSWORD=my-secret-pw -d mysql:tag
    https://hub.docker.com/_/mysql

postgres (https://rnacentral.org/help/public-database)
    Hostname: hh-pgsql-public.ebi.ac.uk; Port: 5432; Database: pfmegrnargs; User: reader; Password: NWDMCE5xdipIjRrp
    https://github.com/docker-library/docs/blob/master/postgres/README.md
    or docker run --name some-postgres -e POSTGRES_PASSWORD=mysecretpassword -d postgres
    docker build --file ./connectionManagerPy/tests/docker/postgres --tag connectionmanager_postgrestest .
    docker run --name "connectionmanager_postgrestest" --publish 127.0.0.1:40000:5432 --detach connectionmanager_postgrestest

    docker exec postgrestest 'psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "CREATE TABLE testdocker (l1 int, l2 varchar(200))"'
    docker exec postgrestest psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "INSERT INTO testdocker VALUES (1, 'abcd'), (2, 'efgh')"



try docker for non public db maybe:
oracle database (express edition)
    https://hub.docker.com/r/oracleinanutshell/oracle-xe-11g
    docker run -d -p 1521:1521 -p 8080:8080 alexeiled/docker-oracle-xe-11g
    docker run -d -p 49161:1521 oracleinanutshell/oracle-xe-11g

sql server (express edition)
    https://hub.docker.com/r/microsoft/mssql-server-windows-express/
    docker run -d -p 1433:1433 -e sa_password=<SA_PASSWORD> -e ACCEPT_EULA=Y microsoft/mssql-server-windows-express

db2 (community edition)
    https://hub.docker.com/r/ibmcom/db2
    https://www.ibm.com/support/producthub/db2/docs/content/SSEPGG_11.5.0/com.ibm.db2.luw.db2u_openshift.doc/doc/t_install_db2CE_win_img.html
    docker pull ibmcom/db2
    type nul > ".env_list"
    # edit .env_list file to your need, see doc if needed
    LICENSE=accept
    DB2INSTANCE=db2inst1
    DB2INST1_PASSWORD=password
    DBNAME=testdb
    BLU=false
    ENABLE_ORACLE_COMPATIBILITY=false
    UPDATEAVAIL=NO
    TO_CREATE_SAMPLEDB=false
    REPODB=false
    IS_OSXFS=false
    PERSISTENT_HOME=false
    HADR_ENABLED=false
    ETCD_ENDPOINT=
    ETCD_USERNAME=
    ETCD_PASSWORD=
    docker run -h db2server --name db2server --restart=always --detach --privileged=true -p 50000:50000 --env-file .env_list -v /Docker:/database ibmcom/db2
    docker exec -ti db2server bash -c "su – db2inst1"
"""


def inc(x):
    return x + 1


def test_answer():
    assert inc(3) == 5
