FROM apache/superset:latest

USER root
RUN /app/.venv/bin/python -m ensurepip || true
RUN /app/.venv/bin/python -m pip install psycopg2-binary

USER superset

# Copy the initialization script
COPY docker-init.sh /app/docker-init.sh

# Make it executable
RUN chmod +x /app/docker-init.sh

# Use the script as the entrypoint
ENTRYPOINT ["/app/docker-init.sh"]