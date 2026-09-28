# Real AWS CLI v2, pointed permanently at the LocalStack container on the
# shared breach-net network. No real credentials, no real account, no bill.
FROM public.ecr.aws/aws-cli/aws-cli:2.17.62
RUN mkdir -p /work /root/.aws
ENV AWS_ACCESS_KEY_ID=test \
    AWS_SECRET_ACCESS_KEY=test \
    AWS_DEFAULT_REGION=us-east-1 \
    AWS_ENDPOINT_URL=http://breach-localstack:4566
WORKDIR /work
# ENTRYPOINT/CMD are overridden by the game engine at `docker run` time
# (it needs the container to idle, not immediately invoke aws), so no
# ENTRYPOINT/CMD is set here.
