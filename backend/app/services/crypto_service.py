import json
import logging
from web3 import Web3
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)

# Try to load a provider URL from environment, fallback to public nodes
WEB3_PROVIDER = os.getenv("WEB3_PROVIDER_URL", "https://eth.llamarpc.com")

class CryptoService:
    _w3 = None

    @classmethod
    def get_w3(cls):
        if cls._w3 is None:
            cls._w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))
            if not cls._w3.is_connected():
                logger.warning("Failed to connect to Ethereum provider. Using mock mode.")
        return cls._w3

    @classmethod
    def is_valid_address(cls, address: str) -> bool:
        if not address or not isinstance(address, str):
            return False
        w3 = cls.get_w3()
        return w3.is_address(address)

    @classmethod
    def get_balance(cls, address: str) -> Dict:
        """Get ETH balance and basic stats for an address"""
        if not cls.is_valid_address(address):
            return {"error": "Invalid address format", "balance": 0.0, "address": address}
            
        w3 = cls.get_w3()
        try:
            if not w3.is_connected():
                return {"balance": 0.0, "status": "disconnected", "address": address}
            
            checksum_addr = w3.to_checksum_address(address)
            balance_wei = w3.eth.get_balance(checksum_addr)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            
            return {
                "balance": float(balance_eth),
                "symbol": "ETH",
                "status": "connected",
                "address": checksum_addr
            }
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return {"error": str(e), "balance": 0.0}

    @classmethod
    def get_transactions(cls, address: str, limit: int = 5) -> List[Dict]:
        """Get recent transactions (Simplified/Mocked if no explorer API)"""
        # In a real app, we'd use Etherscan API. 
        # For now, we return an empty list or mock data
        return [
            {"hash": "0x123...", "from": "0xABC...", "to": address, "value": "0.1 ETH", "status": "confirmed", "date": "2026-01-09"},
            {"hash": "0x456...", "from": address, "to": "0xDEF...", "value": "0.05 ETH", "status": "confirmed", "date": "2026-01-10"}
        ]

    @classmethod
    def prepare_transfer(cls, from_address: str, to_address: str, amount_eth: float) -> Dict:
        """Prepare transaction data for frontend signing"""
        w3 = cls.get_w3()
        try:
            checksum_from = w3.to_checksum_address(from_address)
            checksum_to = w3.to_checksum_address(to_address)
            value_wei = w3.to_wei(amount_eth, 'ether')
            
            gas_estimate = w3.eth.estimate_gas({
                'to': checksum_to,
                'from': checksum_from,
                'value': value_wei
            })
            
            # This doesn't sign! It just gives the data needed for MetaMask to sign.
            return {
                "from": checksum_from,
                "to": checksum_to,
                "value": hex(value_wei),
                "gas": hex(gas_estimate),
                "chainId": 1 # Mainnet, could be dynamic
            }
        except Exception as e:
            return {"error": str(e)}
        
        
#NP: this feature will most likely be removed unless you find it cool or smth make sure to dm me on discord or email
