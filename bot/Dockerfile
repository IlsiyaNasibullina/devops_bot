FROM python:3.10-alpine

WORKDIR /bot

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5050

CMD ["python", "./bot.py"]
