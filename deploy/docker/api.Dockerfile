FROM python:3.12-slim
WORKDIR /app
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt psycopg[binary]
COPY services/api /app
COPY course-materials /course-materials
ENV PYTHONPATH=/app COURSE_MATERIALS_DIR=/course-materials
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
