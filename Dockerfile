FROM python:3.10

WORKDIR /managing_database

COPY requirements.txt /managing_database/

RUN pip install --trusted-host pypi.python.org -r requirements.txt

COPY . /managing_database/

EXPOSE 8200

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8200"]


