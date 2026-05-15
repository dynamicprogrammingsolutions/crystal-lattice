FROM public.ecr.aws/docker/library/alpine:3.20

RUN apk add --no-cache bash openssh-server rsync && \
    adduser -D -h /transfer -s /usr/local/bin/managed-rsync-wrapper transfer && \
    mkdir -p /run/sshd /transfer

COPY entrypoint.sh /usr/local/bin/managed-ssh-entrypoint
COPY managed-rsync-wrapper.sh /usr/local/bin/managed-rsync-wrapper
RUN chmod +x /usr/local/bin/managed-ssh-entrypoint /usr/local/bin/managed-rsync-wrapper

EXPOSE 2222

ENTRYPOINT ["managed-ssh-entrypoint"]