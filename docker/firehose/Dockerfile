# Interpreter matches the checkpoint's Python minor version. Runtime has no network.
ARG BASE_IMAGE=python:3.8.20-slim-bookworm@sha256:1d52838af602b4b5a831beb13a0e4d073280665ea7be7f69ce2382f29c5a613f
FROM ${BASE_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MPLBACKEND=Agg OMP_NUM_THREADS=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ make libboost-dev libeigen3-dev && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir pip==23.0.1 setuptools==65.5.0 wheel==0.38.4
COPY requirements/firehose-legacy.txt /opt/requirements.txt
RUN python -m pip install --no-cache-dir -r /opt/requirements.txt
COPY external/sb3-contrib-legacy /opt/contrib
RUN python -m pip install --no-cache-dir --no-deps /opt/contrib && python -m pip check
COPY external/firehose/cell2fire /opt/firehose/cell2fire
COPY external/firehose/data/Sub20x20 /opt/firehose/data/Sub20x20
COPY external/firehose/pretrained_models/20x20-fixed-ppo-maskable.zip /opt/firehose/pretrained_models/20x20-fixed-ppo-maskable.zip
COPY external/firehose/pretrained_models/20x20-random-20m-ppo-maskable.zip /opt/firehose/pretrained_models/20x20-random-20m-ppo-maskable.zip
COPY external/firehose/LICENSE /opt/firehose/LICENSE
RUN make -C /opt/firehose/cell2fire/Cell2FireC -f Makefile_serial -j2 \
    CC=g++ EIGENDIR=/usr/include/eigen3 \
    CFLAGS='-std=c++11 -O2 -I/usr/include/eigen3 -fopenmp' \
    LIBS='-fPIC -fno-strict-aliasing -fexceptions -DNDEBUG -DIL_STD -lm -lpthread -ldl -fopenmp'
ENV PYTHONPATH=/opt/firehose:/opt/firehose/cell2fire
COPY src/wildfire_rl/firehose_probe.py /opt/firehose_probe.py
COPY docker/firehose/verify_batch.py /opt/firehose_verify_batch.py
WORKDIR /opt/firehose
CMD ["python", "/opt/firehose_verify_batch.py"]
