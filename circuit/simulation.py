"""Simulation driven by the truth tables declared by each component."""

def _component_value(circuit, node, values):
    spec = circuit.components.require(node.kind)
    index = 0
    for value in values:
        index = (index << 1) | int(bool(value))
    return spec.truth_table[index]

def _component_packed_value(circuit, node, values, mask):
    spec = circuit.components.require(node.kind)
    result = 0
    for index, bit in enumerate(spec.truth_table):
        if bit:
            pattern = index
            condition = mask
            for source in reversed(node.inputs):
                if pattern & 1:
                    condition &= values[source]
                else:
                    condition &= ~values[source]
                pattern >>= 1
            result |= condition
    return result & mask
def _simulate_values(circuit, input_values, overrides=None):
    values = [0] * len(circuit.nodes)
    if isinstance(input_values, dict):
        input_values = [input_values[node_id] for node_id in circuit.input_ids]
    if len(input_values) != len(circuit.input_ids):
        raise ValueError("input_values must match input_ids")
    for node_id, value in zip(circuit.input_ids, input_values):
        values[node_id] = int(bool(value))
    input_ids = set(circuit.input_ids)
    for i, node in enumerate(circuit.nodes):
        if overrides is not None and i in overrides:
            values[i] = overrides[i]
        elif i not in input_ids:
            values[i] = _component_value(
                circuit, node, [values[source] for source in node.inputs]
            )
    return values

def simulate(circuit, input_values):
    values = _simulate_values(circuit, input_values)
    raw = sum(values[i] << bit for bit, i in enumerate(circuit.output_ids))
    width = len(circuit.output_ids)
    return raw - (1 << width) if raw & (1 << (width - 1)) else raw

def _simulate_packed_values(circuit, inputs, overrides=None, input_width=None):
    mask = (1 << len(inputs)) - 1
    values = [0] * len(circuit.nodes)
    if input_width is None:
        if any(len(sample) != len(circuit.input_ids) for sample in inputs):
            raise ValueError("packed samples must match input_ids unless input_width is provided")
        for port, i in enumerate(circuit.input_ids):
            values[i] = sum((int(bool(sample[port])) << index)
                            for index, sample in enumerate(inputs))
    else:
        if len(circuit.input_ids) % input_width:
            raise ValueError("input_ids length must be divisible by input_width")
        for bus_index in range(len(circuit.input_ids) // input_width):
            bus = circuit.input_ids[bus_index * input_width:(bus_index + 1) * input_width]
            for bit, i in enumerate(bus):
                values[i] = sum(((((sample[bus_index] if bus_index < len(sample) else 0) >> bit) & 1) << index)
                                for index, sample in enumerate(inputs))
    input_ids = set(circuit.input_ids)
    for i, node in enumerate(circuit.nodes):
        if overrides is not None and i in overrides:
            values[i] = overrides[i] & mask
        elif i not in input_ids:
            values[i] = _component_packed_value(circuit, node, values, mask)
    return values

def simulate_many(circuit, input_values, chunk_size=64):
    results = []
    for start in range(0, len(input_values), chunk_size):
        chunk = input_values[start:start + chunk_size]
        values = _simulate_packed_values(circuit, chunk)
        results.extend(sum(((values[i] >> index) & 1) << bit for bit, i in enumerate(circuit.output_ids))
                       for index in range(len(chunk)))
    width = len(circuit.output_ids)
    sign_bit, modulus = 1 << (width - 1), 1 << width
    return [raw - modulus if raw & sign_bit else raw for raw in results]
