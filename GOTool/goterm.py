from collections import defaultdict

import numpy as np


class GOTerm:

    VALID_RELATIONS = ['is_a', 'part_of']

    def __init__(self, go_id, name, domain, ontology):
        self.go_id = go_id
        self.name = name
        self.relations = defaultdict(set)
        self.annotations = defaultdict(dict)
        self.domain = domain
        self.aliases = set()
        self.is_obsolete = False
        self.ic = {}
        self.ontology = ontology

    def information_content(self, organism_name):
        if organism_name not in self.ic:
            annotations_df = self.ontology.get_annotations(organism_name)
            len_annotations = len(self.annotations[organism_name])
            if len_annotations > 0:
                self.ic[organism_name] = -np.log(len_annotations /
                                                 annotations_df.shape[0]) /\
                    np.log(2)
            else:
                self.ic[organism_name] = 0
        return self.ic[organism_name]

    def add_relation(self, go_term, relation_type):
        if relation_type in GOTerm.VALID_RELATIONS:
            self.relations[relation_type].add(go_term)
            go_term.relations['a_'+relation_type].add(self)

    def up_propagate_annotations(self, organism_name,
                                 relations=VALID_RELATIONS,
                                 same_domain=True):
        """
        Recursively up-propagates the annotations until the root term

        Parameters
        ----------
        organism_name : str
            The annotation set to up-propagate
        relations : list, optional
            a list of relations that will be considered during up-propagation,
            (defaults to ['is_a', 'part_of']).
            All relations are assumed to be transitive
        same_domain : bool, optional
            If True, the up-propagation is constrained to terms belonging
            to the same domain
        """
        for relation in relations:
            for term in self.relations[relation]:
                if (same_domain and term.domain == self.domain) or\
                        not same_domain:
                    for prot, score in self.annotations[organism_name].items():
                        if prot in term.annotations[organism_name].keys():
                            term.annotations[organism_name][prot] = max(
                                term.annotations[organism_name][prot],
                                score)
                        else:
                            term.annotations[organism_name][prot] = score
                    term.up_propagate_annotations(organism_name,
                                                  relations=relations,
                                                  same_domain=same_domain)

    def get_parents(self, relations=VALID_RELATIONS):
        parents = set()
        for relation in relations:
            parents |= self.relations[relation]
        return parents

    def get_ancestors(self, relations=VALID_RELATIONS):
        ancestors = set()
        for relation in relations:
            ancestors |= self.relations[relation]
            for term in self.relations[relation]:
                ancestors |= term.get_ancestors(relations)
        return ancestors

    def get_children(self, relations=VALID_RELATIONS):
        children = set()
        for relation in relations:
            children |= self.relations['a_' + relation]
        return children

    def get_descendants(self, relations=VALID_RELATIONS):
        descendants = set()
        for relation in relations:
            descendants |= self.relations['a_' + relation]
            for term in self.relations['a_' + relation]:
                descendants |= term.get_descendants(relations)
        return descendants
