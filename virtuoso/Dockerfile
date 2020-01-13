FROM tenforce/virtuoso
RUN curl -O -cN http://farsbase.net/download/last_ttls.tar.gz && tar -xzf last_ttls.tar.gz -C dumps/farsbase && \
    curl -O -cN http://data.dws.informatik.uni-mannheim.de/dbpedia/2014/en/instance_types_en.ttl.bz2 && tar -xzf instance_types_en.ttl.bz2 -C dumps/dbpedia
RUN isql-v 1111 dba dba load_dbpedia.isql && isql-v 1111 dba dba load_farsbase.isql
