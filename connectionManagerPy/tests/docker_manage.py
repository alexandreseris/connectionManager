import docker
import docker.models.containers
import docker.models.images
import docker.client
import docker.errors
import io
import asyncio


class DockerConfig(object):
    """Store docker config. Use the method run to build image if needed, run container if needed and run init scripts
    """
    hostServerAdr: str = "127.0.0.1"
    user: str = "cntmgr"
    password: str = "123456789"
    database: str = "testdocker"
    defaultTag = "latest"
    dockerClient: docker.client.DockerClient = docker.from_env()

    def __init__(self, name: str, dockerfile: list, initcommand: list, hostServerPort: str, dockerPort: str, forceRunInitScripts: bool = False, healthCheck: str = "", removeImg: bool = False, removeContainer: bool = False, customConnectionInfos: dict = {}):
        """
        Args:
            name (str): the name of the container (also the name used for the image)
            dockerfile (list): a list of dockerfile actions. can contain the following formated values: {user}, {pwd}, {db}
            initcommand (list): a list of command to run when the container is at the running state
            hostServerPort (str): the port you wish to expose on your host
            dockerPort (str): the port used for the databse
            forceRunInitScripts (bool, optional): force the init script to run in any case. Defaults to False.
            healthCheck (str, optional): command to check if the service is running. Defaults to "".
            removeImg (bool, optional): if you wish to remove image if found. Defaults to False.
            removeContainer (bool, optional): if you wish to remove container if found. Defaults to False.
            customConnectionInfos (dict, optional): override informations for user, password, database if needed. Defaults to {}
        """
        self.name = name
        self.fullImageName = name + ":" + self.defaultTag
        self.dockerfile = dockerfile
        self.hostServerPort = hostServerPort
        self.dockerPort = dockerPort
        self.initcommand = initcommand
        self.forceRunInitScripts = forceRunInitScripts
        self.healthCheck = healthCheck
        self.removeImg = removeImg
        self.removeContainer = removeContainer
        if "user" in customConnectionInfos.keys():
            self.user = customConnectionInfos["user"]
        if "password" in customConnectionInfos.keys():
            self.password = customConnectionInfos["password"]
        if "database" in customConnectionInfos.keys():
            self.database = customConnectionInfos["database"]
        self.image: docker.models.images.Image
        self.container: docker.models.containers.Container

    def createDockerFile(self):
        formatDict = {
            "user": self.user,
            "pwd": self.password,
            "db": self.database
        }
        dockerFileStr = "\n".join(
                [line.format(**formatDict) for line in self.dockerfile]
        )
        return io.BytesIO(dockerFileStr.encode("utf8"))

    def buildImage(self):
        """build the image or retrieve the available one"""
        try:
            self.image = self.dockerClient.images.get(self.fullImageName)
            print("image {}: already built".format(*[self.fullImageName]))
            if self.removeImg:
                try:
                    container = self.dockerClient.containers.get(self.name)
                    if container.status != "exited":
                        container.stop()
                    container.remove()
                    print("container {}: removed".format(*[self.name]))
                except docker.errors.NotFound:
                    pass
                self.dockerClient.images.remove(self.fullImageName)
                print("image {}: removed".format(*[self.fullImageName]))
                raise docker.errors.NotFound("image manually removed")
        except docker.errors.NotFound:
            print("image {}: start build".format(*[self.fullImageName]))
            self.image, stream = self.dockerClient.images.build(
                fileobj=self.createDockerFile(),
                tag=self.fullImageName,
                rm=True  # rm does not seems to work fully, intermediate images remains visibles
            )
            for streamline in stream:
                for key, value in streamline.items():
                    print("image {}: {} :: {}".format(*[self.fullImageName, key, value]))

    def runContainer(self):
        """run or retrieve the already started container"""
        try:
            self.container = self.dockerClient.containers.get(self.name)
            if self.removeContainer:
                if self.container.status != "exited":
                    self.container.stop()
                self.container.remove()
                print("container {}: removed".format(*[self.name]))
                raise docker.errors.NotFound("container manually removed")
            if self.container.status == "exited":
                print("container {}: restarting".format(*[self.name]))
                self.container.restart()
            else:
                print("container {}: already started, status is {}".format(*[self.name, self.container.status]))
            if not self.forceRunInitScripts:
                self.forceRunInitScripts = False
        except docker.errors.NotFound:
            print("container {}: start run".format(*[self.name]))
            self.container: docker.models.containers.Container = self.dockerClient.containers.run(
                self.fullImageName,
                detach=True,
                name=self.name,
                ports={self.dockerPort: (self.hostServerAdr, self.hostServerPort)}
            )
            self.forceRunInitScripts = True

    def runInitScripts(self):
        """run init scripts"""
        print("container {}: start init script".format(*[self.name]))
        for cmd in self.initcommand:
            print("container {} init script: {}".format(*[self.name, cmd]))
            returnOfRun = self.container.exec_run(cmd)
            returnOutput = returnOfRun.output.decode("utf8")
            # check if return code is not 0 and output is not "" to exclude 2> /dev/null
            if returnOfRun.exit_code != 0 and returnOutput != "":
                raise Exception("container {} init script: exited with status {}, output: {}".format(*[
                    self.name,
                    returnOfRun.exit_code,
                    returnOutput
                ]))
            print("container {} init script output: {}".format(*[self.name, returnOutput]))

    def stopContainer(self):
        self.container.stop()

    async def waitForRunningStatus(self):
        secToWait = 0.5
        retryChances = 10
        currentRetryCount = 0
        while self.container.status != "running" and currentRetryCount < retryChances:
            print("container {}: status is {}, waiting {} seconds".format(*[self.name, self.container.status, secToWait]))
            await asyncio.sleep(secToWait)
            self.container.reload()
            currentRetryCount += 1
        if self.container.status != "running":
            raise Exception("container {}: did not start, status is {}".format(*[self.name, self.container.status]))
        print("container {}: container is now running!".format(*[self.name]))
        # cant get the build in docker health check to work so doing it manually :(
        if self.healthCheck != "":
            retryChancesHealth = 100
            currentRetryCountHealth = 0
            minOkRunCount = 3
            currentOkRunCount = 0
            healthCheckRes = self.container.exec_run(self.healthCheck)
            while currentRetryCountHealth < retryChancesHealth:
                if healthCheckRes.exit_code == 0:
                    currentOkRunCount += 1
                    if currentOkRunCount >= minOkRunCount:
                        break
                else:
                    currentOkRunCount = 0
                await asyncio.sleep(0.5)
                print(self.healthCheck, healthCheckRes.output.decode("utf8"), sep="\n")
                healthCheckRes = self.container.exec_run(self.healthCheck)
                currentRetryCountHealth += 1
            if healthCheckRes.exit_code != 0:
                raise Exception("the service does not seems to be up. Check the output of the healthcheck:\ncommand:\n{}\nnoutput:\n{}".format(*[
                    self.healthCheck,
                    healthCheckRes.output.decode("utf8")
                ]))
            else:
                print("container {}: the service is now available!".format(*[self.name]))

    async def run(self):
        self.buildImage()
        self.runContainer()
        await self.waitForRunningStatus()
        if self.forceRunInitScripts:
            self.runInitScripts()


oracleCommandPattern = """/bin/bash -c '(
/u01/app/oracle/product/11.2.0/xe/bin/sqlplus -s "$ORACLE_USER"/"$ORACLE_PASSWORD"@"$ORACLE_HOST":"$ORACLE_PORT"/"$ORACLE_DATABASE" <<EOF
{command}
exit;
EOF
){after}'"""
postgresCommandPattern = "/bin/bash -c 'psql --username \"$POSTGRES_USER\" --dbname \"$POSTGRES_DB\" -c \"{command}\"{after}'"
mysqlCommandPattern = "/bin/bash -c 'mysql --user=\"$MYSQL_USER\" --password=\"$MYSQL_PASSWORD\" --database=\"$MYSQL_DATABASE\" --protocol=TCP --host=\"$MYSQL_HOST\" --port=\"$MYSQL_PORT\" --execute=\"{command}\"{after}'"

configs = [
    # https://hub.docker.com/r/oracleinanutshell/oracle-xe-11g
    DockerConfig(
        name="connectionmanager_oracle",
        dockerfile=[
            "FROM oracleinanutshell/oracle-xe-11g",
            "ENV ORACLE_DATABASE=\"{db}\"",
            "ENV ORACLE_PORT=\"1521\"",
            "ENV ORACLE_HOST=\"localhost\"",
            "ENV ORACLE_USER=\"{user}\"",
            "ENV ORACLE_PASSWORD=\"{pwd}\"",
            "ENV ORACLE_ALLOW_REMOTE=\"true\"",
            "ENV ORACLE_DISABLE_ASYNCH_IO=\"true\"",
            "ENV ORACLE_ENABLE_XDB=\"true\"",
            "ENV ORACLE_HOME=\"/u01/app/oracle/product/11.2.0/xe\"",
            "ENV DROPTABLE=\"DROP TABLE testdocker;\"",
            "ENV CREATETABLE=\"CREATE TABLE testdocker (l1 int, l2 varchar(200));\"",
            "ENV INSERTTABLE1=\"INSERT INTO testdocker VALUES (1, 'abcd');\"",
            "ENV INSERTTABLE2=\"INSERT INTO testdocker VALUES (2, 'efgh');\"",
        ],
        initcommand=[
            oracleCommandPattern.format(**{"command": "$DROPTABLE", "after": " > /dev/null 2>&1"}),
            oracleCommandPattern.format(**{"command": "$CREATETABLE", "after": ""}),
            oracleCommandPattern.format(**{"command": "$INSERTTABLE1", "after": ""}),
            oracleCommandPattern.format(**{"command": "$INSERTTABLE2", "after": ""}),
        ],
        hostServerPort="40002",
        dockerPort="1521",
        customConnectionInfos={"user": "system", "password": "oracle", "database": "xe"},
        forceRunInitScripts=True,
        healthCheck=oracleCommandPattern.format(**{"command":
            "set pagesize 0 feedback off verify off heading off echo off;\n" + \
            "select count(*) from ALL_TABLES;",
            "after": ""}),
    ),
    https://github.com/docker-library/docs/blob/master/postgres/README.md
    DockerConfig(
        name="connectionmanager_postgrestest",
        dockerfile=[
            "FROM postgres",
            "ENV POSTGRES_USER=\"{user}\"",
            "ENV POSTGRES_PASSWORD=\"{pwd}\"",
            "ENV POSTGRES_DB=\"{db}\"",
            "ENV PGPASSWORD=\"$POSTGRES_PASSWORD\"",
            "ENV DROPTABLE=\"DROP TABLE testdocker\"",
            "ENV CREATETABLE=\"CREATE TABLE testdocker (l1 int, l2 varchar(200))\"",
            "ENV INSERTTABLE=\"INSERT INTO testdocker VALUES (1, 'abcd'), (2, 'efgh')\""
        ],
        initcommand=[
            postgresCommandPattern.format(**{"command": "$DROPTABLE", "after": " 2> /dev/null"}),
            postgresCommandPattern.format(**{"command": "$CREATETABLE", "after": ""}),
            postgresCommandPattern.format(**{"command": "$INSERTTABLE", "after": ""})
        ],
        hostServerPort="40000",
        dockerPort="5432",
        forceRunInitScripts=True,
    ),
    https://hub.docker.com/_/mysql
    DockerConfig(
        name="connectionmanager_mysql",
        dockerfile=[
            "FROM mysql",
            "ENV MYSQL_DATABASE=\"{db}\"",
            "ENV MYSQL_PORT=\"3306\"",
            "ENV MYSQL_HOST=\"localhost\"",
            "ENV MYSQL_ROOT_PASSWORD=\"{pwd}\"",
            "ENV MYSQL_USER=\"{user}\"",
            "ENV MYSQL_PASSWORD=\"{pwd}\"",
            "ENV DROPTABLE=\"DROP TABLE testdocker\"",
            "ENV CREATETABLE=\"CREATE TABLE testdocker (l1 int, l2 varchar(200))\"",
            "ENV INSERTTABLE=\"INSERT INTO testdocker VALUES (1, 'abcd'), (2, 'efgh')\""
        ],
        initcommand=[
            mysqlCommandPattern.format(**{"command": "$DROPTABLE", "after": " > /dev/null 2>&1"}),
            mysqlCommandPattern.format(**{"command": "$CREATETABLE", "after": ""}),
            mysqlCommandPattern.format(**{"command": "$INSERTTABLE", "after": ""}),
        ],
        hostServerPort="40001",
        dockerPort="3306/tcp",
        healthCheck=mysqlCommandPattern.format(**{"command": "select 1", "after": ""}),
        forceRunInitScripts=True,
    ),
]

loop = asyncio.get_event_loop()
loop.run_until_complete(
    asyncio.gather(
        *[x.run() for x in configs]
    )
)
loop.close()

# carefull, docker take a lot of space (ram and disk :O )
