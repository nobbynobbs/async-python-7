FROM python:3.7 as builder
COPY . /build
WORKDIR /build
RUN pip install poetry \
    && poetry build


FROM python:3.7
COPY --from=builder /build/dist/*.whl /dist/
RUN pip install /dist/*.whl
EXPOSE 8080 8000
CMD ["bus-tracker"]
