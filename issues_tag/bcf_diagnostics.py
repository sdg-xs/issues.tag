"""Read-only camera evidence for BCF import review and offline reports."""
from copy import deepcopy


def camera_diagnostics(source_document, converted_document=None) -> tuple[dict, ...]:
    """Pair retained source evidence with converted cameras by viewpoint UUID."""
    topics = {view.id: [] for view in source_document.viewpoints}
    for identity, topic in source_document.viewpoint_topics:
        if identity in topics and topic not in topics[identity]:
            topics[identity].append(topic)
    for issue in source_document.issues:
        identities = dict.fromkeys((issue.initial_viewpoint_id, *(c.viewpoint_id for c in issue.comments)))
        for identity in identities:
            if identity in topics:
                topic = issue.bcf_topic_id or issue.id
                if topic not in topics[identity]:
                    topics[identity].append(topic)
    converted = {view.id: view for view in converted_document.viewpoints} if converted_document is not None else {}
    rows = []
    for view in source_document.viewpoints:
        mapped = converted.get(view.id)
        frame = mapped.coordinate_frame if mapped is not None else view.coordinate_frame
        source = view.coordinate_frame.get('bcf_source_camera', {})
        native = view.id in source_document.native_viewpoints
        rows.append({
            'viewpoint_id': view.id,
            'topic_ids': topics[view.id],
            'source_position': source.get('position'),
            'converted_position': list(mapped.camera['transform'][12:15]) if mapped is not None and mapped.camera else None,
            'projection': view.camera.get('projection'),
            'source_version': source.get('version'),
            'reference_path': frame.get('bcf_reference_prim') or None,
            'coordinate_mode': frame.get('bcf_coordinate_mode', 'native' if native else 'source_world'),
            'fov_mode': frame.get('bcf_fov_mode', 'native' if native else 'file'),
            'source_fov_degrees': source.get('field_of_view'),
            'source_aspect_ratio': source.get('aspect_ratio'),
        })
    return tuple(deepcopy(rows))
