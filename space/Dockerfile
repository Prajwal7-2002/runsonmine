FROM python:3.12-slim
RUN pip install --no-cache-dir "runsonmine[service] @ git+https://github.com/Prajwal7-2002/runsonmine"
RUN useradd -m app
USER app
EXPOSE 7860
CMD ["uvicorn", "runsonmine.service:create_app", "--factory", "--host", "0.0.0.0", "--port", "7860"]
