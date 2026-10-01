[graphify] MultiDiGraph edge-collapse diagnostic
input: <in-memory>
input_stage: provided JSON (normal graph.json is post-build)
effective_directed: <direct-call>
nodes: 476
unverified_code_nodes: 0
raw_edges: 1112
valid_candidate_edges: 1112
missing_endpoint_edges: 0
dangling_endpoint_edges: 0
external_reference_edges: 0
self_loop_edges: 2
exact_duplicate_edges: 0
directed_unique_endpoint_pairs: 1112
directed_same_endpoint_collapsed_edges: 0
undirected_unique_endpoint_pairs: 1112
undirected_same_endpoint_collapsed_edges: 0
same_endpoint_group_count: 0
relation_variant_groups: 0
source_file_variant_groups: 0
source_location_variant_groups: 0
context_variant_groups: 0
post_build_graph_type: DiGraph
post_build_edges: 1112
producer_suppression_sites: 12
producer_suppression_examples:
  - L1349 seen_ids arity=unknown
  - L1882 seen_ids arity=unknown
  - L1884 seen_doc_refs arity=unknown
  - L2254 seen_ids arity=unknown
  - L2401 seen_ids arity=unknown
  - L3127 seen_keys arity=unknown
  - L3296 seen_keys arity=unknown
  - L5370 seen_ids arity=unknown
note: normal graph.json is post-build; raw producer loss must be measured earlier.