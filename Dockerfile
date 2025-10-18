FROM python:3.13-slim

ARG wd=/repo
WORKDIR ${wd}

COPY pyproject.toml ${wd}/pyproject.toml
RUN pip install . --no-cache-dir

COPY src ${wd}/src
RUN pip install . --no-cache-dir

CMD ["python", "-m", "medbot.run"]
