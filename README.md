# connectionManager

> Don't bother anymore managing your connections!

_currently in developpment!_

This project allow you to connect to usual services (sql, ssh, etc...).
Operations on the connection such as execute a command/query and output of theses operations are standardized so you don't have to worry about which method to call on a specific lib.

## Requiered

Currently, this project is based on a Keepass file to retrieve connection data
Later the *ConnectionManager* class will accept any *passwordManager*, so you'll be able to create custom interface for your favorite password manager if not implemented.

On *ConnectionManager* init:

- The class will try to retrieve a configuration file is located in your user home directory in the sub directory .connectionManagerpy/config.py
This file should contain a dict variable *configDict* with the following keys: *keePassFilePath*, *keePassNotesSeparator*, *driversTypes*, *password* (not recommended for security reason)
*driversTypes* should be a dict mapping driver type (ssh, sql, etc) to the xpath root of the entries in the Keepass file
- Else it will fallback to the *configDict* paramter (same keys as above)
you can specify some custom keys for *configDict* in the constructor to override your configuration file if needed

The Keepass file can be structured:

- As you like but you should then specify the absolute path (xpath) to the entry when calling *autoConnect* using the *connectionPath* parameter
- Following this structure: driverTypeRoot/connectionName/connectionEnv where connectionEnv is the entry name in Keepass

## Usage

```python
import ConnectionManager
connectionManager = connectionManager.ConnectionManager()
# with a context manager:
with connectionManager.autoConnect(driverType="sql", connectionName="yourBddName", connectionEnv="yourEnvName") as connection:
    connection.exec("your command/query")
# without context manager:
connection = manager.autoConnect(driverType="sql", connectionName="yourBddName", connectionEnv="yourEnvName")
connection.connect()
connection.exec("your command/query")
connection.close()
```
