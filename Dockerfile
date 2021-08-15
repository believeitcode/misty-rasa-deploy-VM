FROM rasa/rasa:latest-full 
USER root
WORKDIR /app
COPY . /app
COPY ./data /app/data
RUN pip3 install nltk
RUN rasa train

VOLUME /app
VOLUME /app/data
VOLUME /app/models

USER 1001

CMD [ "run","-m","/app/models","--enable-api","--cors","*","--debug" ]