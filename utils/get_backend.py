from qiskit import IBMQ, Aer
from qiskit.providers.ibmq import least_busy


def get_backend(is_simulator=True):
    if is_simulator:
        return Aer.get_backend("aer_simulator")
    IBMQ.load_account()
    provider = IBMQ.providers()[0]
    backend = least_busy(
        provider.backends(
            filters=lambda x: x.configuration().simulator == is_simulator
            and x.status().operational
        )
    )

    return backend
