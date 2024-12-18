import warnings

from pytoniq_core import Address

from core import get_env_key


class DedustSwapModule:
    SWAP_FEE = float(get_env_key("SWAP_FEE") or 0)
    if not SWAP_FEE or SWAP_FEE > 1:
        warnings.warn("Swap Fee is not set or too big.")

    SWAP_FEE_RECIPIENT = Address(get_env_key("SWAP_FEE_RECIPIENT"))
    SWAP_ADDRESS = Address("EQCo_dAv39DAV62oG5HIC_nVeVjIaVZi-Zmlzjbx8AoPqjZb")
    NATIVE_VAULT_ADDRESS = Address("EQDa4VOnTYlLvDJ0gZjNYm5PXfSmmtL6Vs6A_CZEtXCNICq_")
    TON_TOKEN_ADDRESS = "ton_EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c"
    JETTON_SWAP_SELECTOR = 3818968194
    TON_JETTON_SWAP = 3926267997
    JETTON_TRANSFER_SELECTOR = 260734629
