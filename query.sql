INSERT { GRAPH <http://farsbase.net> {
        ?p rdf:DBPediaInstance ?o
}
}
using  <http://farsbase.net>
using named <http://dbpedia.org>
where {
              ?p rdf:instanceOf <http://fkg.iust.ac.ir/ontology/Thing>.
              ?p owl:sameAs ?d.
              filter(strstarts(str(?d), "http://dbpedia.org/")).
        {GRAPH <http://dbpedia.org>
           {
               ?d rdf:type ?o
           }
        }
}
