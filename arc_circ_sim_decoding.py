import random

import numpy as np
from mqt.qecc import Code, UFHeuristic
from qiskit import IBMQ, transpile
from qiskit.quantum_info import PauliList

from arc_circ_sim import ArcCircSim
from utils.get_backend import get_backend

n = 5
start_zx = True
qubit_ordering = (
    ["Z", "X"] * ((n - 1) // 2) + ["Z"]
    if start_zx
    else ["X", "Z"] * ((n - 1) // 2) + ["X"]
)


error_list = ArcCircSim.generate_all_unique_pauli_errors(n)
backend = get_backend()

istring = "I" * n

ERROR_BLOCKS = [
    "X" + "I" * (n - 2) + "X",
    "XIX",
]


errors = []
for i in range(3):

    if qubit_ordering[i] != "Z":
        errors.append([istring[:i] + "X" + istring[i + 1 :]] + [istring] * (n - 1))

    # if qubit_ordering[i] != "Y":
    #     errors.append([istring[:i] + "Y" + istring[i + 1 :]] + [istring] * (n - 1))

    if qubit_ordering[i] != "X":
        errors.append([istring[:i] + "Z" + istring[i + 1 :]] + [istring] * (n - 1))

if start_zx:
    errors.append(["ZIZ" + "I" * (n - 3)] + [istring] * (n - 1))
    errors.append(["Z" + "I" * (n - 2) + "Z"] + [istring] * (n - 1))
    if len(qubit_ordering) > 3:
        errors.append(["IZIZ" + "I" * (n - 4)] + [istring] * (n - 1))
else:
    errors.append(["XIX" + "I" * (n - 3)] + [istring] * (n - 1))
    errors.append(["X" + "I" * (n - 2) + "X"] + [istring] * (n - 1))
    if len(qubit_ordering) > 3:
        errors.append(["IXIX" + "I" * (n - 4)] + [istring] * (n - 1))

# basic_tests = [
#     ["XII", "III", "III"],
#     ["ZII", "III", "III"],
#     ["IXI", "III", "III"],
#     ["IZI", "III", "III"],
#     ["IIX", "III", "III"],
#     ["IIZ", "III", "III"],
# ]

basic_tests = errors
print(errors)


experiments = []
for noise in basic_tests:
    res = [
        0
    ] * 9  # [[arc, trans, job, counts, UFSyndrome, UFResults], [apply correction], [corrected vs  OG]]
    res[0] = ArcCircSim(n, pauli_noise_list=noise, start_zx=start_zx)
    res[1] = transpile(res[0].code_circ, backend=backend)
    res[2] = backend.run(res[1])
    res[3] = res[2].result().get_counts()
    experiments.append(res)

checkm = ArcCircSim.generate_check_matrix(n)
filepath = f"./test_{n}.txt"
np.savetxt(filepath, checkm, fmt="%d", newline="\n")

correct = 0
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
    yes = np.all(np.equal(final, np.identity(2 ** (circ.no_link_bits)))) == True
    if yes:
        correct += 1
    print(np.all(np.equal(final, np.identity(2 ** (circ.no_link_bits)))) == True)
print(correct / (len(basic_tests)))

print(basic_tests)
# make (xz, zx) circs and test each against all errors ; see if together they catch all errors. x
# naive application of decoding
