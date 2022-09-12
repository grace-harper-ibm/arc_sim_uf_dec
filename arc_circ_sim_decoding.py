from mqt.qecc import Code, UFHeuristic
from qiskit import IBMQ, transpile

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
    res = [0] * 6  # [[arc, trans, job, counts, UFSyndrome, UFResults]]
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

for res in experiments:
    print(res[0].pauli_noise_list)
    print(list(res[3].keys())[0])
    print(res[5])
    print()
