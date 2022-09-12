import numpy as np
from mqt.qecc import Code, UFHeuristic
from qiskit import IBMQ, transpile
from qiskit.quantum_info import PauliList

from arc_circ_sim import ArcCircSim
from utils.get_backend import get_backend

n = 3
error_list = ArcCircSim.generate_all_unique_pauli_errors(n)
backend = get_backend()

basic_tests = [
    ["XII", "III", "III"],
    ["ZII", "III", "III"],
    ["IXI", "III", "III"],
    ["IZI", "III", "III"],
    ["IIX", "III", "III"],
    ["IIZ", "III", "III"],
]


experiments = []
for noise in basic_tests:
    res = [
        0
    ] * 9  # [[arc, trans, job, counts, UFSyndrome, UFResults], [apply correction], [corrected vs  OG]]
    res[0] = ArcCircSim(n, pauli_noise_list=noise)
    res[1] = transpile(res[0].code_circ, backend=backend)
    res[2] = backend.run(res[1])
    res[3] = res[2].result().get_counts()
    experiments.append(res)

checkm = ArcCircSim.generate_check_matrix(n)
filepath = "/Users/graceharperibm/correcting/QEC Benchmarking/arc_circ/arccirc_3.txt"


for res in experiments:

    output = list(res[3].keys())[0]
    syndrome = output[len(output) - (n - 1) :]
    uf_format = [True if k == "1" else False for k in syndrome]
    res[4] = uf_format
    code = Code(filepath)
    decoder = UFHeuristic()
    decoder.set_code(code)
    decoder.decode(uf_format)
    result = decoder.result
    res[5] = result.estimate

    # apply results
    circ = res[0]
    error_matrix = np.identity(2 ** (circ.no_link_bits), dtype=int)
    for err in circ.pauli_noise_list:
        pauli_err = PauliList(err).to_matrix(array=True)  # numpy array
        error_matrix = np.matmul(pauli_err, error_matrix)

    qubit_ordering = circ.qubit_ordering
    correction = np.identity(2 ** (circ.no_link_bits), dtype=int)
    res[6] = []
    for quindex in range(len(result.estimate)):
        istring = "I" * circ.no_link_bits
        if result.estimate[quindex] == 1:
            corr_pauli_str = (
                istring[:quindex] + qubit_ordering[quindex] + istring[quindex + 1 :]
            )
            res[6].append(corr_pauli_str)
            corr_pauli = PauliList(corr_pauli_str).to_matrix(array=True)
            correction = np.matmul(correction, corr_pauli)

    # apply errors/corrections together to see if we get I
    final = np.matmul(correction, error_matrix)
    res[7] = final

    print(circ.qubit_ordering)
    print(circ.pauli_noise_list)
    print(res[6])
    print(np.all(np.equal(final, np.identity(2 ** (circ.no_link_bits)))) == True)
    print()


# make (xz, zx) circs and test each against all errors ; see if together they catch all errors. x
# naive application of decoding
