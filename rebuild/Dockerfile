###################################
### CDK v2.15.0 (build 151055e) ###
###################################
FROM public.ecr.aws/lambda/python:latest
RUN yum update -y
RUN yum install coreutils e4fsprogs -y
COPY app.py ./
CMD ["app.lambdaHandler"]