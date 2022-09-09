from qiskit import QuantumCircuit


def create_controlled_pauli(pauli_gate_init, leftmost_index_is_zeroth=True):
    if leftmost_index_is_zeroth:
        pauli_gate = pauli_gate_init[::-1]
    else:
        pauli_gate = pauli_gate_init
    pauli_num = len(pauli_gate)
    pauli_input = range(0, pauli_num)
    pauli_circ = QuantumCircuit(pauli_num, name=pauli_gate)
    pauli_circ.pauli(pauli_gate, pauli_input)
    return pauli_circ.control(1, f"controlled {pauli_gate}")


def create_pauli_measurement(pauli_gate, extra_qubits=0, extra_cbits=0):
    controlled_pauli = create_controlled_pauli(pauli_gate)
    pauli_num = len(pauli_gate)
    pauli_meas = QuantumCircuit(1 + pauli_num + extra_qubits, 1 + extra_cbits)
    pauli_meas.h(0)  # |+>
    pauli_meas.compose(
        controlled_pauli,
        range(0, pauli_num + 1),
        inplace=True,
    )
    pauli_meas.barrier()
    pauli_meas.h(0)
    pauli_meas.measure(0, 0)
    pauli_meas.barrier()
    return pauli_meas
