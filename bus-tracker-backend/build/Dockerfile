FROM python:3.7 as builder
COPY . /build
WORKDIR /build
RUN pip install poetry \
    && poetry build


FROM pypy:3.6
COPY --from=builder /build/dist/*.whl /dist/
RUN pypy3 -m pip install /dist/*.whl
EXPOSE 8080 8000
CMD ["bus-tracker"]
