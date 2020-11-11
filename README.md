#Entity typing in farsbase using wikipedia dumps
###Used database and datasets
<ul>
    <li>farsbase dump</li>
    <li>DBPedia dump</li>
    <li>Wikidata wb_items_per_site</li>
</ul>

###How to run

First you need to run virtuoso docker.
```
docker run --name entityTypingVirtuoso\
    -p 8890:8890 -p 1111:1111\
    -e DBA_PASSWORD=myDbaPassword \
    -e SPARQL_UPDATE=true \
    -v /my/path/to/the/virtuoso/db:/data \
    -d tenforce/virtuos
```

###Steps of program
