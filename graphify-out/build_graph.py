"""Finalize this graphify run without changing product files."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from graphify.export import to_json
from graphify.diagnostics import diagnose_extraction, format_diagnostic_report
from graphify.detect import save_manifest
from graphify.cache import save_semantic_cache
from graphify.cli import _stamped_manifest_files

root = Path('.').resolve()
out = root / 'graphify-out'
detection = json.loads((out / '.graphify_detect.json').read_text(encoding='utf-8'))
ast = json.loads((out / '.graphify_ast.json').read_text(encoding='utf-8'))
previous = json.loads((out / '.graphify_semantic.json').read_text(encoding='utf-8'))
nodes, edges = [], []

def identifier(value):
    return re.sub('[^a-z0-9]+', '_', value.lower()).strip('_')

def edge(source, target, relation, file, line, confidence='EXTRACTED', score=1.0):
    edges.append(dict(source=source, target=target, relation=relation,
                      confidence=confidence, confidence_score=score,
                      source_file=file, source_location=f'L{line}', weight=1.0))

documents = {}
for filename in detection['files']['document']:
    path = Path(filename)
    relative = path.relative_to(root).as_posix()
    stem = identifier(str(Path(relative).with_suffix('')))
    lines = path.read_text(encoding='utf-8').splitlines()
    title = next((line.lstrip('# ').strip() for line in lines if line.startswith('#')), path.name)
    doc_id = stem + '_document'
    nodes.append(dict(id=doc_id, label=title, file_type='document', source_file=filename, source_location='L1'))
    documents[relative] = (doc_id, filename, lines)
    for line_number, line in enumerate(lines, 1):
        if re.match(r'^#{2,4} ', line):
            heading = line.lstrip('# ').strip()
            node_id = stem + '_' + identifier(heading)
            nodes.append(dict(id=node_id, label=heading, file_type='concept', source_file=filename, source_location=f'L{line_number}'))
            edge(doc_id, node_id, 'describes', filename, line_number)

# Explicit file references from the documents bridge to the existing AST roots.
code_roots = [n for n in ast['nodes'] if n['label'] == Path(n.get('source_file', '')).name and n.get('file_type') == 'code']
for relative, (doc_id, filename, lines) in documents.items():
    for code in code_roots:
        source = code['source_file'].replace('\\', '/')
        matches = [i for i, line in enumerate(lines, 1) if source in line or ('`' + Path(source).name + '`') in line]
        if matches:
            edge(doc_id, code['id'], 'references', filename, matches[0])
    for other, (other_id, _, _) in documents.items():
        if other == relative:
            continue
        matches = [i for i, line in enumerate(lines, 1) if other in line or ('(' + Path(other).name + ')') in line]
        if matches:
            edge(doc_id, other_id, 'references', filename, matches[0])

# Host-reviewed domain concepts, anchored to explicit statements in the docs.
facts = [
 ('SPEC.md','Parent USD ownership','The parent USD scene owns', 'Issue records belong to the parent scene rather than referenced building layers.'),
 ('SPEC.md','Independent pin anchors','pin anchor and the editable related-element list are separate', 'Related-element edits must not move the spatial anchor.'),
 ('SPEC.md','Saved review context','A viewpoint records the camera', 'The initial view preserves the context of the original observation.'),
 ('SPEC.md','Editable Markup evidence','Markup annotations remain editable in USD', 'Reuse supported annotation APIs; BCF exchanges rendered evidence.'),
 ('SPEC.md','Conflict-aware BCF exchange','Conflicting descriptions and statuses', 'Local edits require review before imported values replace them.'),
 ('README.md','Normal scene Save','Use ordinary', 'Reviewers control persistence using the scene Save workflow.'),
 ('README.md','Unresolved component retention','BCF imports retain unresolved', 'Missing geometry must not remove issue descriptions and evidence.'),
 ('docs/bcf-profile.md','BCF XML 3.0','initial development profile', 'A concrete version bounds the implemented file exchange subset.'),
 ('docs/bcf-profile.md','Three-way import baseline','previous accepted import baseline', 'Compare both sides against the last accepted values.'),
 ('docs/bcf-profile.md','Bounded ZIP parsing','100 MiB', 'Read bounded content in memory without archive extraction.'),
 ('docs/bcf-profile.md','Native viewpoint metadata','omniverse.json', 'Optional native metadata preserves details other tools can ignore.'),
 ('docs/viewport-design.md','Scoped source identity','IFC GlobalId and Revit UniqueId', 'Repeated instances and referenced asset identity must distinguish attachments.'),
 ('docs/viewport-design.md','Pin eligibility','Eligibility is computed separately', 'Visibility and attachment confidence determine which pins draw.'),
 ('docs/viewport-design.md','Stage-safe picking','scene generation', 'Discard asynchronous results after scene replacement.'),
 ('docs/viewport-design.md','Session-layer restoration','Restore authors a dedicated camera', 'Transient review state must leave building source layers unchanged.'),
 ('docs/ui-design.md','Explicit import preview','BCF import opens a separate preview', 'A reviewer chooses which conflicting fields to import.'),
 ('docs/ui-design.md','Protected review drafts','Refresh must not overwrite', 'Refreshing a view must preserve text being edited.'),
 ('AGENTS.md','Graph-first navigation','first run `graphify query', 'Use a scoped graph query before broad source browsing.'),
]
concepts = {}
for relative, label, snippet, rationale in facts:
    doc_id, filename, lines = documents[relative]
    matches = [i for i, line in enumerate(lines, 1) if snippet.lower() in line.lower()]
    if not matches:
        raise ValueError(f'Unverified semantic assertion: {relative}: {snippet}')
    node_id = identifier(str(Path(relative).with_suffix(''))) + '_' + identifier(label)
    concepts[label] = node_id
    nodes.append(dict(id=node_id, label=label, file_type='rationale', source_file=filename,
                      source_location=f'L{matches[0]}', rationale=rationale))
    edge(doc_id, node_id, 'describes', filename, matches[0])

links = [
 ('Parent USD ownership', 'Normal scene Save', 'conceptually_related_to'),
 ('Conflict-aware BCF exchange', 'Three-way import baseline', 'conceptually_related_to'),
 ('Conflict-aware BCF exchange', 'Explicit import preview', 'conceptually_related_to'),
 ('Saved review context', 'Session-layer restoration', 'conceptually_related_to'),
 ('Independent pin anchors', 'Scoped source identity', 'conceptually_related_to'),
 ('Unresolved component retention', 'Pin eligibility', 'conceptually_related_to'),
 ('Editable Markup evidence', 'Native viewpoint metadata', 'conceptually_related_to'),
]
for first, second, relation in links:
    node = next(n for n in nodes if n['id'] == concepts[first])
    edge(concepts[first], concepts[second], relation, node['source_file'], int(node['source_location'][1:]), 'INFERRED', 0.85)

semantic = dict(nodes=nodes, edges=edges, hyperedges=[], input_tokens=previous.get('input_tokens', 0), output_tokens=previous.get('output_tokens', 0))
(out / '.graphify_semantic.json').write_text(json.dumps(semantic, ensure_ascii=False), encoding='utf-8')
save_semantic_cache(nodes, edges, [], root=root, allowed_source_files=detection['files']['document'],
                    prompt_file=Path('C:/Users/StevenGomba/.codex/skills/graphify/references/extraction-spec.md'))
existing = {n['id'] for n in ast['nodes']}
extraction = dict(nodes=ast['nodes'] + [n for n in nodes if n['id'] not in existing], edges=ast['edges'] + edges,
                  hyperedges=[], input_tokens=semantic['input_tokens'], output_tokens=semantic['output_tokens'])
(out / '.graphify_extract.json').write_text(json.dumps(extraction, ensure_ascii=False), encoding='utf-8')
graph = build_from_json(extraction, root=str(root), directed=False)
if not graph.number_of_nodes():
    raise SystemExit('Empty extraction; refusing to publish.')
communities = cluster(graph)
cohesion = score_all(graph, communities)
gods = god_nodes(graph)
surprises = surprising_connections(graph, communities)
labels = {cid: f'Community {cid}' for cid in communities}
questions = suggest_questions(graph, communities, labels)
tokens = {'input': extraction['input_tokens'], 'output': extraction['output_tokens']}
if not to_json(graph, communities, str(out / 'graph.json')):
    raise SystemExit('Shrink guard refused graph export.')
report = generate(graph, communities, cohesion, labels, gods, surprises, detection, tokens, str(root), suggested_questions=questions)
report += '\n## Extraction audit\n\nAll seven documents were recovered by host-reviewed extraction after the Gemini pass omitted five. The Gemini token counts include that unsuccessful pass; host reasoning tokens are unavailable. AST extraction is deterministic. This graph is a source snapshot, not a claim that implementation acceptance tests pass.\n'
(out / 'GRAPH_REPORT.md').write_text(report, encoding='utf-8')
(out / '.graphify_analysis.json').write_text(json.dumps(dict(communities=communities, cohesion=cohesion, gods=gods, surprises=surprises, questions=questions), ensure_ascii=False), encoding='utf-8')
summary = diagnose_extraction(extraction, directed=False, root=str(root))
(out / 'GRAPH_HEALTH.md').write_text(format_diagnostic_report(summary), encoding='utf-8')
print(format_diagnostic_report(summary))
manifest = _stamped_manifest_files(detection['files'], extraction, root)
save_manifest(manifest, root=root, scan_corpus={f for files in detection['files'].values() for f in files})
cost_path = out / 'cost.json'
cost = json.loads(cost_path.read_text(encoding='utf-8')) if cost_path.exists() else dict(runs=[],total_input_tokens=0,total_output_tokens=0)
cost['runs'].append(dict(date=datetime.now(timezone.utc).isoformat(),input_tokens=tokens['input'],output_tokens=tokens['output'],files=detection['total_files']))
cost['total_input_tokens'] += tokens['input']
cost['total_output_tokens'] += tokens['output']
cost_path.write_text(json.dumps(cost, indent=2), encoding='utf-8')
print(f'Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges, {len(communities)} communities')
for cid, members in communities.items():
    print(cid, [graph.nodes[n].get('label', n) for n in members][:12])
