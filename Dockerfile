FROM python:3.8
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY . .
RUN pip install --upgrade pip
	&& pip install --no-cache-dir -r requirements.txt
	&& python manage.py makemigrations
	&& python manage.py migrate
CMD ["python", "manage.py", "runserver"]