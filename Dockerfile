FROM rappdw/docker-java-python:latest

MAINTAINER Abdulrahman Alabrash <aalabrash18@ku.edu.tr>

RUN apt-get update
RUN apt-get -y install g++ python-dev python3-dev ant python-pip

RUN apt-get install --yes --no-install-recommends \
    wget \
    git \
    locales \
    cmake \
    build-essential \
    apt-utils

ENV _JAVA_OPTIONS="-Xmx1g"
RUN git clone https://github.com/emerging-welfare/emw_pipeline_nf.git
RUN pip3 install --upgrade pip
RUN pip2 install --upgrade pip

# nextflow installation
ENV NXF_VER=19.04.1
RUN wget -qO- https://get.nextflow.io | bash
RUN mv nextflow ./bin
RUN nextflow

# Extract & Doc Preprocess Dependencies
RUN cd /emw_pipeline_nf && git checkout comprehensive && pip2 install --no-cache-dir -r requirements2.txt && pip3 install --no-cache-dir -r requirements.txt
RUN git clone https://github.com/OsmanMutlu/python-boilerpipe.git && cd python-boilerpipe && python2 setup.py install && cd .. && rm -rf python-boilerpipe

# BERT
RUN git clone https://github.com/OsmanMutlu/pytorch-pretrained-BERT.git && cd pytorch-pretrained-BERT && python3 setup.py install
RUN mkdir /.pytorch_pretrained_bert && cd /.pytorch_pretrained_bert && wget https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased.tar.gz && wget https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased-vocab.txt && wget "https://www.dropbox.com/s/4eu8ib47vusqupk/doc_model.pt?dl=1" && mv doc_model.pt\?dl=1 doc_model.pt

# Tokenizer
RUN python3 -c "import nltk;nltk.download('popular', halt_on_error=False)"

# DTC depenedecy
RUN git clone https://github.com/Jekub/Wapiti && cd Wapiti && make install

RUN echo "cd /emw_pipeline_nf && git checkout comprehensive && git pull origin comprehensive" >> ~/.bashrc
RUN echo "nohup python3 /emw_pipeline_nf/bin/classifier/classifier_flask.py 2> /dev/null &" >> ~/.bashrc
RUN echo "cd emw_pipeline_nf" >> ~/.bashrc
RUN echo "export PYTHONPATH=$PYTHONPATH:/emw_pipeline_nf/bin" >> ~/.bashrc
