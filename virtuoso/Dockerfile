FROM tenforce/virtuoso
RUN apt update && apt install -y curl && mkdir dumps && mkdir dumps/farsbase && echo "Downloading farsbase" &&\
    curl -O -cN http://farsbase.net/download/last_ttls.tar.gz && echo "Farsbase download completed." && ls &&\
    tar xzf last_ttls.tar.gz -C dumps/farsbase && echo "Downloading dbpedia" &&\
    curl -O -cN http://data.dws.informatik.uni-mannheim.de/dbpedia/2014/en/instance_types_en.ttl.bz2 && \
    bzip2 -dk instance_types_en.ttl.bz2 && mkrid dumps/dbpedia && mv instance_types_en.ttl dumps/dbpedia/
RUN isql-v 1111 dba dba load_dbpedia.isql && isql-v 1111 dba dba load_farsbase.isql
