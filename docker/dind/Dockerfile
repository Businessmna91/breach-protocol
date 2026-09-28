# Nested Docker daemon: the player's docker commands land here, never on the
# host daemon. Requires --privileged to run (the engine passes that flag
# automatically for this domain only).
FROM docker:27-dind
RUN mkdir -p /work
WORKDIR /work
