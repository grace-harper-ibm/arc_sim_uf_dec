import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import PauliGate

from utils.circ_gen_shortcuts import create_pauli_measurement


class ArcCircSim:
    def __init__(
        self,
        no_link_bits,
        start_zx=True,
        pauli_noise_list=None,
    ):
        self.no_link_bits = no_link_bits
        self.start_zx = start_zx
        self.pauli_noise_list = pauli_noise_list
        self.I = "I" * no_link_bits
        if self.pauli_noise_list is None:
            self.pauli_noise_list = [None] * no_link_bits * 2

        self.code_circ = self._generate_arc_code_circ()
        self.check_matrix = self.generate_check_matrix(no_link_bits)

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
        encoding_circ = QuantumCircuit(
            QuantumRegister(1, "ancilla"),
            QuantumRegister(self.no_link_bits, "data qubits"),
            ClassicalRegister(self.no_link_bits - 1),
        )
        mod = 1 if self.start_zx else 0
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

    @classmethod
    def generate_all_unique_pauli_errors(cls, no_link_bits):
        def _append_error(cinput=None):
            if cinput is None:
                return ["I", "X", "Y", "Z"]
            ninput = []
            for i in cinput:
                ninput.append(i + "I")
                ninput.append(i + "Y")
                ninput.append(i + "X")
                ninput.append(i + "Z")
            return ninput

        ninput = None
        for i in range(no_link_bits):
            ninput = _append_error(ninput)
        return ninput

    @classmethod
    def generate_check_matrix(cls, no_link_bits):
        # has same structure as repetition code, just requires careful correction
        """an actual implementation would read off CNOTS in circuit and thus circuit would be source of truth"""
        # for round 1
        check_matrix = np.zeros((no_link_bits - 1, no_link_bits), dtype=int)
        for i in range(no_link_bits - 1):
            check_matrix[i][i] = check_matrix[i][i + 1] = int(1)

        return check_matrix

    @classmethod
    def save_external_check_matrix(cls, name, matrix):
        raise Exception("is ending w/ a newline that breaks things....")

        # def convert_check_matrix_to_UF_format(check_matrix):
        #     #qiskit is left to right and UF is right to left :......()
        #     return np.flip(check_matrix, axis=0)
        filename = f"./{name}.txt"
        np.savetxt(filename, matrix, fmt="%d", newline="\n")
        return filename
