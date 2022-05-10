FROM python:3.8
COPY . .
RUN ./scripts/setup
ENTRYPOINT [ "./scripts/run" ]
