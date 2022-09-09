from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

from utils.circ_gen_shortcuts import create_pauli_measurement


class ArcCircSim:
    def __init__(self, no_link_bits, start_zx=True, pauli_noise_list=None):
        self.no_link_bits = no_link_bits
        self.start_zx = start_zx
        self.pauli_noise_list = pauli_noise_list
        self.I = "I" * no_link_bits
        if self.pauli_noise_list is None:
            self.pauli_noise_list = [None] * no_link_bits * 2

        self.code_circ = self._generate_arc_code_circ()

    def _generate_arc_code_circ(self):
        """Assumes ancillla/ancilla measurements and encoding are perfect"""
        # TODO: make each round a seperate circuit in a list so can easily add in noise at indexes instead of
        # this forloop nightmare
        qubits = QuantumRegister(self.no_link_bits + 1, name="qubits")
        meas_bits = ClassicalRegister((self.no_link_bits - 1), name="measurement")
        base_circ = QuantumCircuit(qubits, meas_bits)
        meas_count = 0
        round_no = 0
        base_circ.compose(
            self._generate_noise(self.pauli_noise_list[round_no]), inplace=True
        )
        round_no += 1
        for i in range(1, self.no_link_bits - 1, 2):
            zx_gate = create_pauli_measurement("ZX")
            xz_gate = create_pauli_measurement("XZ")
            if self.start_zx:
                base_circ.reset([0])
                base_circ.compose(
                    zx_gate, qubits=[0, i, i + 1], clbits=[meas_count], inplace=True
                )
                base_circ.barrier()
                base_circ.compose(
                    self._generate_noise(self.pauli_noise_list[round_no]),
                    inplace=True,
                )
                round_no += 1

                base_circ.reset([0])

                base_circ.compose(
                    xz_gate,
                    qubits=[0, i + 1, i + 2],
                    clbits=[meas_count + 1],
                    inplace=True,
                )
                base_circ.barrier()

                base_circ.compose(
                    self._generate_noise(self.pauli_noise_list[round_no]),
                    inplace=True,
                )
                round_no += 1

            else:
                base_circ.reset([0])

                base_circ.compose(
                    xz_gate, qubits=[0, i, i + 1], clbits=[meas_count], inplace=True
                )
                base_circ.barrier()

                base_circ.compose(
                    self._generate_noise(self.pauli_noise_list[round_no]),
                    inplace=True,
                )
                round_no += 1

                base_circ.reset([0])

                base_circ.compose(
                    zx_gate,
                    qubits=[0, i + 1, i + 2],
                    clbits=[meas_count + 1],
                    inplace=True,
                )
                base_circ.barrier()

                base_circ.compose(
                    self._generate_noise(self.pauli_noise_list[round_no]),
                    inplace=True,
                )
                round_no += 1

            meas_count += 2
        full_circ = base_circ
        full_circ = self._generate_encoding_circ().compose(base_circ)
        return full_circ

    def _generate_encoding_circ(self, encoding_only=False):
        # should get n from arccirc in future
        if encoding_only:
            encoding_circ = QuantumCircuit(
                QuantumRegister(self.no_link_bits, name="data_qubits")
            )
            mod = 1 if self.start_zx else 0
            for i in range(self.no_link_bits):
                if i % 2 == mod:
                    encoding_circ.h(i)
            encoding_circ.barrier()
            return encoding_circ
        encoding_circ = QuantumCircuit(
            QuantumRegister(1, "ancilla"),
            QuantumRegister(self.no_link_bits, "data qubits"),
            ClassicalRegister(self.no_link_bits - 1),
        )
        mod = 0 if self.start_zx else 1
        for i in range(1, self.no_link_bits + 1):
            if i % 2 == mod:
                encoding_circ.h(i)
        encoding_circ.barrier()
        return encoding_circ

    def _generate_noise(self, noise: str = None):
        circ = QuantumCircuit(
            QuantumRegister(1, "ancilla"),
            QuantumRegister(self.no_link_bits, "data qubits"),
            ClassicalRegister(self.no_link_bits - 1),
        )
        if noise is None:
            return circ
        circ.pauli(noise, range(1, len(noise) + 1))
        circ.barrier()
        return circ
