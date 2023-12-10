# CDMO-project

## Project installation
To build the docker image, run the following command in the root directory of the project:
```
docker compose build
```

To run the docker image, first run the following command in the root directory of the project:
```
docker compose up
```

Then, in a new terminal, keeping the previous one running, run the following command in the root directory of the project:
```
docker exec -it cdmo-container /bin/bash
```
