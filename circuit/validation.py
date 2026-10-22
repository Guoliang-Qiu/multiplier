"""Circuit structural validation."""
def validate_circuit(circuit):
    if not isinstance(circuit.input_ids, (list, tuple)):
        raise ValueError("input_ids must be a list or tuple")
    if not circuit.output_ids:
        raise ValueError("circuit must have at least one output bit")
    for index, node in enumerate(circuit.nodes):
        spec = circuit.components.require(node.kind)
        if len(node.inputs) != spec.arity:
            raise ValueError(f"{node.kind} node {index} requires {spec.arity} inputs")
        if any(source < 0 or source >= index for source in node.inputs):
            raise ValueError(f"node {index} must reference earlier valid nodes")
    if len(set(circuit.input_ids)) != len(circuit.input_ids):
        raise ValueError("input_ids must contain distinct nodes")
    if any(i < 0 or i >= len(circuit.nodes) for i in circuit.input_ids):
        raise ValueError("input_ids contains an invalid node")
    if any(i < 0 or i >= len(circuit.nodes) for i in circuit.output_ids):
        raise ValueError("output_ids contains an invalid node")
